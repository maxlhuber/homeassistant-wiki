"""Select and safely extract the small Home Assistant subset used by the wiki."""

from __future__ import annotations

import datetime as dt
import gzip
import json
import shutil
import struct
import tarfile
import tempfile
import time
import zlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO, IO, Any


ALLOWED_MEMBERS = (
    "automations.yaml",
    "scenes.yaml",
    ".storage/core.floor_registry",
    ".storage/core.area_registry",
    ".storage/core.label_registry",
    ".storage/core.device_registry",
    ".storage/core.entity_registry",
)
REQUIRED_MEMBERS = frozenset(ALLOWED_MEMBERS)
MAX_MEMBER_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 192 * 1024 * 1024
MAX_INNER_ARCHIVE_BYTES = 8 * 1024 * 1024 * 1024
MAX_METADATA_BYTES = 2 * 1024 * 1024
MAX_OUTER_MEMBERS = 4096
DRAIN_CHUNK_BYTES = 4 * 1024 * 1024
CORE_ARCHIVE_NAMES = frozenset({"homeassistant.tar", "homeassistant.tar.gz"})


class BackupExtractionError(RuntimeError):
    """Raised when a backup is missing, unsafe or cannot be decrypted."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


@dataclass(frozen=True)
class ExtractedBackup:
    source: Path
    destination: Path
    backup_date: str | None
    backup_name: str | None


@dataclass(frozen=True)
class _BackupMetadata:
    raw: dict[str, Any]
    date: str
    name: str
    timestamp: float
    protected: bool
    compressed: bool


@dataclass(frozen=True)
class _OuterLayout:
    metadata: _BackupMetadata
    inner_member: tarfile.TarInfo


@dataclass(frozen=True)
class _FileStamp:
    size: int
    mtime_ns: int


@dataclass(frozen=True)
class _Candidate:
    path: Path
    backup_timestamp: float
    mtime_ns: int


def _normalise_member(name: str) -> str | None:
    """Return a harmless POSIX member name without extracting it."""
    clean = name.replace("\\", "/")
    while clean.startswith("./"):
        clean = clean[2:]
    path = PurePosixPath(clean)
    if not clean or path.is_absolute() or ".." in path.parts:
        return None
    return str(path)


def _wiki_name(name: str) -> str | None:
    clean = _normalise_member(name)
    if clean is None:
        return None
    if clean.startswith("data/"):
        clean = clean.removeprefix("data/")
    return clean if clean in REQUIRED_MEMBERS else None


def _metadata_from_bytes(raw: bytes) -> tuple[str | None, str | None]:
    """Read the two optional display fields from inner metadata."""
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, None
    if not isinstance(document, dict):
        return None, None
    date = document.get("date")
    name = document.get("name")
    return (
        str(date) if isinstance(date, str) and date else None,
        str(name) if isinstance(name, str) and name else None,
    )


def _parse_backup_date(value: str) -> float:
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.timestamp()
    except (ValueError, OverflowError) as error:
        raise BackupExtractionError(
            "backup_invalid", "Das Datum in backup.json ist ungültig."
        ) from error


def _parse_backup_metadata(raw: bytes) -> _BackupMetadata:
    """Validate the identifying fields of an official Supervisor backup."""
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BackupExtractionError(
            "backup_invalid", "backup.json ist keine gültige JSON-Datei."
        ) from error
    if not isinstance(document, dict):
        raise BackupExtractionError(
            "backup_invalid", "backup.json enthält kein gültiges Objekt."
        )

    version = document.get("version")
    slug = document.get("slug")
    date = document.get("date")
    name = document.get("name")
    protected = document.get("protected")
    compressed = document.get("compressed")
    homeassistant = document.get("homeassistant")
    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or not isinstance(slug, str)
        or not slug
        or not isinstance(date, str)
        or not date
        or not isinstance(name, str)
        or not name
        or not isinstance(protected, bool)
        or not isinstance(compressed, bool)
        or not isinstance(homeassistant, dict)
    ):
        raise BackupExtractionError(
            "backup_invalid",
            "backup.json besitzt nicht die erwartete Home-Assistant-Struktur.",
        )
    return _BackupMetadata(
        raw=document,
        date=date,
        name=name,
        timestamp=_parse_backup_date(date),
        protected=protected,
        compressed=compressed,
    )


def _read_member_bytes(
    archive: tarfile.TarFile, member: tarfile.TarInfo, limit: int
) -> bytes:
    if (
        not member.isfile()
        or member.issym()
        or member.islnk()
        or member.size < 0
        or member.size > limit
    ):
        raise BackupExtractionError(
            "unsafe_member", f"{member.name} ist keine sichere reguläre Datei."
        )
    source = archive.extractfile(member)
    if source is None:
        raise BackupExtractionError(
            "invalid_member", f"{member.name} konnte nicht gelesen werden."
        )
    with source:
        raw = source.read(member.size + 1)
    if len(raw) != member.size:
        raise BackupExtractionError(
            "truncated_member", f"{member.name} ist unvollständig."
        )
    return raw


def _inspect_outer_archive(archive: tarfile.TarFile) -> _OuterLayout | None:
    """Return a strict official HA layout, or None for an isolated core tar."""
    metadata_member: tarfile.TarInfo | None = None
    inner_member: tarfile.TarInfo | None = None
    has_direct_wiki_member = False
    member_count = 0

    for member in archive:
        member_count += 1
        if member_count > MAX_OUTER_MEMBERS:
            raise BackupExtractionError(
                "backup_invalid", "Das äußere Backup enthält unplausibel viele Einträge."
            )
        clean = _normalise_member(member.name)
        if clean is None:
            continue
        if clean == "backup.json":
            if metadata_member is not None:
                raise BackupExtractionError(
                    "duplicate_member", "Das Backup enthält backup.json mehrfach."
                )
            metadata_member = member
            continue
        if clean in CORE_ARCHIVE_NAMES:
            if inner_member is not None:
                raise BackupExtractionError(
                    "duplicate_member",
                    "Das Backup enthält mehr als ein Home-Assistant-Kernarchiv.",
                )
            inner_member = member
            continue
        if _wiki_name(clean) is not None:
            has_direct_wiki_member = True

    if metadata_member is None and inner_member is None:
        return None
    if metadata_member is None or inner_member is None:
        raise BackupExtractionError(
            "backup_invalid",
            "Das äußere Backup enthält backup.json und Kernarchiv nicht vollständig.",
        )
    if has_direct_wiki_member:
        raise BackupExtractionError(
            "mixed_backup_layout",
            "Das äußere Backup mischt direkte Konfigurationsdateien mit dem geschützten Kernarchiv.",
        )
    if (
        not inner_member.isfile()
        or inner_member.issym()
        or inner_member.islnk()
        or inner_member.size <= 0
        or inner_member.size > MAX_INNER_ARCHIVE_BYTES
    ):
        raise BackupExtractionError(
            "backup_too_large",
            "Das Home-Assistant-Kernarchiv hat eine unplausible Größe.",
        )

    metadata = _parse_backup_metadata(
        _read_member_bytes(archive, metadata_member, MAX_METADATA_BYTES)
    )
    expected_inner = (
        "homeassistant.tar.gz" if metadata.compressed else "homeassistant.tar"
    )
    if _normalise_member(inner_member.name) != expected_inner:
        raise BackupExtractionError(
            "backup_invalid",
            "Name und Komprimierungsangabe des Kernarchivs widersprechen sich.",
        )
    return _OuterLayout(metadata=metadata, inner_member=inner_member)


def _copy_limited(source: BinaryIO, destination: BinaryIO, limit: int) -> int:
    written = 0
    while True:
        block = source.read(min(1024 * 1024, limit - written + 1))
        if not block:
            return written
        written += len(block)
        if written > limit:
            raise BackupExtractionError(
                "backup_too_large", "Ein Bestandteil der Sicherung ist unerwartet groß."
            )
        destination.write(block)


def _write_whitelist(archive: tarfile.TarFile, destination: Path) -> set[str]:
    written: set[str] = set()
    total = 0
    for member in archive:
        target_name = _wiki_name(member.name)
        if target_name is None:
            continue
        if target_name in written:
            raise BackupExtractionError(
                "duplicate_member", f"Die Sicherung enthält {target_name} mehrfach."
            )
        if not member.isfile() or member.issym() or member.islnk():
            raise BackupExtractionError(
                "unsafe_member", f"{target_name} ist keine reguläre Datei."
            )
        if member.size < 0 or member.size > MAX_MEMBER_BYTES:
            raise BackupExtractionError(
                "backup_too_large", f"{target_name} ist unerwartet groß."
            )
        total += member.size
        if total > MAX_TOTAL_BYTES:
            raise BackupExtractionError(
                "backup_too_large",
                "Die freigegebenen Sicherungsdateien sind unerwartet groß.",
            )
        source = archive.extractfile(member)
        if source is None:
            raise BackupExtractionError(
                "invalid_member", f"{target_name} konnte nicht gelesen werden."
            )
        target = destination.joinpath(*PurePosixPath(target_name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        with source, target.open("wb") as output:
            copied = _copy_limited(source, output, MAX_MEMBER_BYTES)
        if copied != member.size:
            raise BackupExtractionError(
                "truncated_member", f"{target_name} ist unvollständig."
            )
        written.add(target_name)
    return written


def _drain_tar_stream(archive: tarfile.TarFile) -> None:
    """Consume gzip trailers and, for SecureTar v3, the authenticated final tag."""
    stream = archive.fileobj
    if stream is None:
        return
    while stream.read(DRAIN_CHUNK_BYTES):
        pass


def _raise_backup_invalid(error: BaseException) -> None:
    raise BackupExtractionError(
        "backup_invalid", "Die Sicherung ist beschädigt oder unvollständig."
    ) from error


def _extract_plain_stream(
    source: IO[bytes],
    destination: Path,
    *,
    compressed: bool | None,
) -> set[str]:
    if compressed is None:
        mode = "r|*"
    else:
        mode = "r|gz" if compressed else "r|"
    try:
        with tarfile.open(fileobj=source, mode=mode) as archive:
            written = _write_whitelist(archive, destination)
            _drain_tar_stream(archive)
            return written
    except BackupExtractionError:
        raise
    except (tarfile.TarError, gzip.BadGzipFile, zlib.error, EOFError) as error:
        _raise_backup_invalid(error)


def _extract_secure_stream(
    source: IO[bytes],
    destination: Path,
    *,
    password: str | None,
    compressed: bool,
) -> set[str]:
    if not password:
        raise BackupExtractionError(
            "backup_key_missing", "Für das geschützte Backup fehlt der Backup-Code."
        )
    try:
        from nacl.exceptions import CryptoError
        from securetar import (
            InvalidPasswordError,
            SecureTarError,
            SecureTarFile,
            SecureTarReadError,
        )
    except ImportError as error:
        raise BackupExtractionError(
            "backup_dependency_missing",
            "Die SecureTar-Unterstützung ist auf dem Wiki-System nicht installiert.",
        ) from error

    secure = SecureTarFile(
        fileobj=source,
        gzip=compressed,
        password=password,
        bufsize=DRAIN_CHUNK_BYTES,
    )
    try:
        try:
            archive = secure.open()
        except InvalidPasswordError as error:
            raise BackupExtractionError(
                "backup_key_invalid", "Der hinterlegte Backup-Code ist ungültig."
            ) from error
        except SecureTarReadError as error:
            # SecureTar v2 cannot distinguish a wrong key from damaged ciphertext.
            raise BackupExtractionError(
                "backup_key_invalid",
                "Backup-Code oder verschlüsseltes Archiv sind ungültig.",
            ) from error
        except (SecureTarError, CryptoError, tarfile.TarError, struct.error, ValueError) as error:
            _raise_backup_invalid(error)

        try:
            written = _write_whitelist(archive, destination)
            _drain_tar_stream(archive)
            return written
        except BackupExtractionError:
            raise
        except (
            SecureTarError,
            CryptoError,
            tarfile.TarError,
            gzip.BadGzipFile,
            zlib.error,
            EOFError,
            struct.error,
        ) as error:
            _raise_backup_invalid(error)
    finally:
        secure.close()


def _stamp(path: Path) -> _FileStamp:
    stat = path.stat()
    return _FileStamp(size=stat.st_size, mtime_ns=stat.st_mtime_ns)


def _ensure_unchanged(path: Path, before: _FileStamp) -> None:
    try:
        after = _stamp(path)
    except OSError as error:
        raise BackupExtractionError(
            "backup_changed", "Die Sicherung wurde während des Lesens verändert."
        ) from error
    if after != before:
        raise BackupExtractionError(
            "backup_changed", "Die Sicherung wurde während des Lesens verändert."
        )


def _extract_inner_path(
    inner_path: Path,
    destination: Path,
    password: str | None,
    *,
    protected: bool | None = None,
    compressed: bool | None = None,
) -> set[str]:
    if inner_path.is_symlink() or not inner_path.is_file():
        raise BackupExtractionError(
            "unsafe_member", "Das Home-Assistant-Kernarchiv ist keine reguläre Datei."
        )
    before = _stamp(inner_path)
    if before.size <= 0 or before.size > MAX_INNER_ARCHIVE_BYTES:
        raise BackupExtractionError(
            "backup_too_large", "Das Home-Assistant-Kernarchiv hat eine unplausible Größe."
        )

    if protected is True:
        with inner_path.open("rb") as source:
            written = _extract_secure_stream(
                source,
                destination,
                password=password,
                compressed=(
                    inner_path.name.endswith(".gz")
                    if compressed is None
                    else compressed
                ),
            )
    elif protected is False:
        with inner_path.open("rb") as source:
            written = _extract_plain_stream(
                source, destination, compressed=compressed
            )
    else:
        # Compatibility path for an explicitly supplied, isolated core archive.
        source: IO[bytes] | None = None
        try:
            source = inner_path.open("rb")
            archive = tarfile.open(fileobj=source, mode="r:*")
        except (tarfile.ReadError, EOFError):
            if source is not None:
                source.close()
            with inner_path.open("rb") as secure_source:
                written = _extract_secure_stream(
                    secure_source,
                    destination,
                    password=password,
                    compressed=(
                        inner_path.name.endswith(".gz")
                        if compressed is None
                        else compressed
                    ),
                )
        else:
            assert source is not None
            try:
                with source, archive:
                    written = _write_whitelist(archive, destination)
                    _drain_tar_stream(archive)
            except BackupExtractionError:
                raise
            except (tarfile.TarError, gzip.BadGzipFile, zlib.error, EOFError) as error:
                _raise_backup_invalid(error)

    _ensure_unchanged(inner_path, before)
    return written


def _extract_outer(
    outer_path: Path, destination: Path, password: str | None
) -> tuple[set[str], str | None, str | None]:
    """Stream a strict official outer backup or accept an isolated core archive."""
    before = _stamp(outer_path)
    try:
        outer = tarfile.open(outer_path, mode="r:")
    except (tarfile.ReadError, EOFError):
        written = _extract_inner_path(outer_path, destination, password)
        return written, None, None

    with outer:
        try:
            layout = _inspect_outer_archive(outer)
        except BackupExtractionError:
            raise
        except (tarfile.TarError, EOFError) as error:
            _raise_backup_invalid(error)

        if layout is None:
            # An uncompressed isolated core tar opened successfully as an outer tar.
            pass
        else:
            source = outer.extractfile(layout.inner_member)
            if source is None:
                raise BackupExtractionError(
                    "invalid_member", "Das Kernarchiv konnte nicht gestreamt werden."
                )
            with source:
                if layout.metadata.protected:
                    written = _extract_secure_stream(
                        source,
                        destination,
                        password=password,
                        compressed=layout.metadata.compressed,
                    )
                else:
                    written = _extract_plain_stream(
                        source,
                        destination,
                        compressed=layout.metadata.compressed,
                    )
            _ensure_unchanged(outer_path, before)
            return written, layout.metadata.date, layout.metadata.name

    written = _extract_inner_path(outer_path, destination, password)
    return written, None, None


def _directory_layout(path: Path) -> tuple[_BackupMetadata, Path, _FileStamp, _FileStamp]:
    metadata_path = path / "backup.json"
    if metadata_path.is_symlink() or not metadata_path.is_file():
        raise BackupExtractionError(
            "backup_invalid", "Im Backup-Ordner fehlt eine reguläre backup.json."
        )
    metadata_stamp = _stamp(metadata_path)
    if metadata_stamp.size <= 0 or metadata_stamp.size > MAX_METADATA_BYTES:
        raise BackupExtractionError(
            "backup_invalid", "backup.json hat eine unplausible Größe."
        )
    metadata = _parse_backup_metadata(metadata_path.read_bytes())
    expected_name = "homeassistant.tar.gz" if metadata.compressed else "homeassistant.tar"
    inner_path = path / expected_name
    other_path = path / (
        "homeassistant.tar" if metadata.compressed else "homeassistant.tar.gz"
    )
    if (
        inner_path.is_symlink()
        or not inner_path.is_file()
        or other_path.exists()
        or any((path / member).exists() for member in ALLOWED_MEMBERS)
        or any((path / "data" / member).exists() for member in ALLOWED_MEMBERS)
    ):
        raise BackupExtractionError(
            "backup_invalid", "Der Backup-Ordner besitzt keine eindeutige HA-Struktur."
        )
    inner_stamp = _stamp(inner_path)
    if inner_stamp.size <= 0 or inner_stamp.size > MAX_INNER_ARCHIVE_BYTES:
        raise BackupExtractionError(
            "backup_too_large", "Das Home-Assistant-Kernarchiv hat eine unplausible Größe."
        )
    return metadata, inner_path, metadata_stamp, inner_stamp


def extract_home_assistant_backup(
    backup: Path, destination: Path, password: str | None = None
) -> ExtractedBackup:
    """Atomically create a whitelisted wiki input directory from a backup."""
    if backup.is_symlink():
        raise BackupExtractionError(
            "unsafe_member", "Die Sicherung darf kein symbolischer Link sein."
        )
    backup = backup.resolve()
    destination = destination.resolve()
    if not backup.exists():
        raise BackupExtractionError("backup_missing", "Die Sicherung wurde nicht gefunden.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}-", dir=str(destination.parent))
    )
    metadata_date: str | None = None
    metadata_name: str | None = None
    try:
        if backup.is_dir():
            metadata, inner, metadata_stamp, inner_stamp = _directory_layout(backup)
            written = _extract_inner_path(
                inner,
                staging,
                password,
                protected=metadata.protected,
                compressed=metadata.compressed,
            )
            _ensure_unchanged(backup / "backup.json", metadata_stamp)
            _ensure_unchanged(inner, inner_stamp)
            metadata_date = metadata.date
            metadata_name = metadata.name
        elif backup.is_file():
            written, metadata_date, metadata_name = _extract_outer(
                backup, staging, password
            )
        else:
            raise BackupExtractionError("backup_missing", "Die Sicherung ist keine Datei.")

        missing = REQUIRED_MEMBERS - written
        if missing:
            raise BackupExtractionError(
                "required_member_missing",
                "Benötigte Dateien fehlen: " + ", ".join(sorted(missing)),
            )
        metadata_document = {
            "source_name": backup.name,
            "backup_name": metadata_name,
            "backup_date": metadata_date,
            "whitelist": list(ALLOWED_MEMBERS),
        }
        (staging / ".wiki_backup_metadata.json").write_text(
            json.dumps(metadata_document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        previous = destination.with_name(destination.name + ".old")
        if previous.exists():
            shutil.rmtree(previous)
        moved_previous = destination.exists()
        if moved_previous:
            destination.replace(previous)
        try:
            staging.replace(destination)
        except Exception:
            if moved_previous and previous.exists() and not destination.exists():
                previous.replace(destination)
            raise
        if previous.exists():
            shutil.rmtree(previous)
    except BackupExtractionError:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    except (tarfile.TarError, gzip.BadGzipFile, zlib.error, EOFError) as error:
        shutil.rmtree(staging, ignore_errors=True)
        _raise_backup_invalid(error)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return ExtractedBackup(
        source=backup,
        destination=destination,
        backup_date=metadata_date,
        backup_name=metadata_name,
    )


def _inspect_outer_candidate(
    path: Path, now: float, min_age_seconds: int
) -> _Candidate | None:
    if path.is_symlink() or not path.is_file():
        return None
    try:
        before = _stamp(path)
    except OSError:
        return None
    if before.size <= 0 or now - before.mtime_ns / 1_000_000_000 < min_age_seconds:
        return None
    try:
        with tarfile.open(path, mode="r:") as archive:
            layout = _inspect_outer_archive(archive)
        if layout is None:
            return None
        after = _stamp(path)
    except (BackupExtractionError, tarfile.TarError, OSError, EOFError):
        return None
    if after != before:
        return None
    return _Candidate(path, layout.metadata.timestamp, before.mtime_ns)


def _inspect_directory_candidate(
    path: Path, now: float, min_age_seconds: int
) -> _Candidate | None:
    if path.is_symlink() or not path.is_dir():
        return None
    try:
        metadata, inner, metadata_before, inner_before = _directory_layout(path)
        newest_mtime_ns = max(metadata_before.mtime_ns, inner_before.mtime_ns)
        if now - newest_mtime_ns / 1_000_000_000 < min_age_seconds:
            return None
        metadata_after = _stamp(path / "backup.json")
        inner_after = _stamp(inner)
    except (BackupExtractionError, OSError):
        return None
    if metadata_after != metadata_before or inner_after != inner_before:
        return None
    return _Candidate(path, metadata.timestamp, newest_mtime_ns)


def discover_latest_backup(root: Path, min_age_seconds: int = 300) -> Path:
    """Pick the newest structurally valid completed HA backup from a NAS share."""
    if root.is_symlink():
        raise BackupExtractionError(
            "backup_root_missing", "Der Backup-Pfad darf kein symbolischer Link sein."
        )
    root = root.resolve()
    now = time.time()
    min_age_seconds = max(0, min_age_seconds)

    if root.is_file():
        candidate = _inspect_outer_candidate(root, now, min_age_seconds)
        if candidate is None:
            raise BackupExtractionError(
                "backup_invalid", "Die angegebene Datei ist kein vollständiges HA-Backup."
            )
        return candidate.path
    if not root.is_dir():
        raise BackupExtractionError(
            "backup_root_missing", "Der Backup-Ordner ist nicht erreichbar."
        )

    candidates: dict[Path, _Candidate] = {}
    for candidate_path in root.rglob("*"):
        if candidate_path.is_symlink() or not candidate_path.is_file():
            continue
        lower = candidate_path.name.casefold()
        if lower in {"homeassistant.tar", "homeassistant.tar.gz"}:
            continue
        if not lower.endswith((".tar", ".tar.gz", ".backup")):
            continue
        candidate = _inspect_outer_candidate(
            candidate_path, now, min_age_seconds
        )
        if candidate is not None:
            candidates[candidate.path] = candidate

    for metadata_path in root.rglob("backup.json"):
        if metadata_path.is_symlink() or not metadata_path.is_file():
            continue
        candidate = _inspect_directory_candidate(
            metadata_path.parent, now, min_age_seconds
        )
        if candidate is not None:
            candidates[candidate.path] = candidate

    if not candidates:
        raise BackupExtractionError(
            "backup_missing",
            "Im NAS-Ordner wurde keine abgeschlossene Home-Assistant-Sicherung gefunden.",
        )
    return max(
        candidates.values(),
        key=lambda item: (item.backup_timestamp, item.mtime_ns),
    ).path
