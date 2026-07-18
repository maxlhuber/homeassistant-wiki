#!/bin/bash
set -euo pipefail

REPO_DIR="${WIKI_REPO_DIR:-/srv/homeassistant-wiki/source}"
STATE_DIR="${WIKI_STATE_DIR:-/var/lib/homeassistant-wiki}"
BACKUP_DIR="${WIKI_BACKUP_DIR:-/mnt/homeassistant-backups}"
PYTHON="${WIKI_PYTHON:-/opt/homeassistant-wiki-venv/bin/python}"
RUNNER_DIR="${WIKI_RUNNER_DIR:-/opt/homeassistant-wiki-runner}"
KNOWN_HOSTS="${WIKI_GITHUB_KNOWN_HOSTS:-/etc/homeassistant-wiki/github-known-hosts}"

if [ -n "${CREDENTIALS_DIRECTORY:-}" ]; then
  BACKUP_KEY_FILE="${CREDENTIALS_DIRECTORY}/ha_backup_key"
  OPENAI_KEY_FILE="${CREDENTIALS_DIRECTORY}/openai_api_key"
  GITHUB_KEY_FILE="${CREDENTIALS_DIRECTORY}/github_key"
  KNOWN_HOSTS="${CREDENTIALS_DIRECTORY}/github_known_hosts"
  WEBHOOK_FILE="${CREDENTIALS_DIRECTORY}/ha_webhook_url"
else
  BACKUP_KEY_FILE="/etc/homeassistant-wiki/ha-backup-key"
  OPENAI_KEY_FILE="/etc/homeassistant-wiki/openai-api-key"
  GITHUB_KEY_FILE="/home/wikiadmin/.ssh/github_homeassistant_wiki"
  WEBHOOK_FILE="/etc/homeassistant-wiki/ha-webhook-url"
fi

NOTIFICATION_QUEUE="${STATE_DIR}/notification-queue.json"
RUN_MARKER="${STATE_DIR}/run-in-progress"
RUN_MARKER_NEW="${STATE_DIR}/run-in-progress.new"
PUBLISH_READY="${STATE_DIR}/publish-ready"

notify_kind() {
  "${PYTHON}" "${RUNNER_DIR}/wiki_notify.py" \
    --webhook-file "${WEBHOOK_FILE}" \
    --queue "${NOTIFICATION_QUEUE}" \
    --kind "$1" >/dev/null 2>&1 || true
}

notify_status() {
  "${PYTHON}" "${RUNNER_DIR}/wiki_notify.py" \
    --webhook-file "${WEBHOOK_FILE}" \
    --queue "${NOTIFICATION_QUEUE}" \
    --status "${STATE_DIR}/last_status.json" >/dev/null 2>&1 || true
}

mark_failure_handled() {
  touch "${STATE_DIR}/failure-handled"
}

abort_recovery() {
  notify_kind "$1"
  mark_failure_handled
  exit 30
}

clear_run_marker() {
  rm -f -- "${RUN_MARKER}" "${RUN_MARKER_NEW}"
}

is_git_oid() {
  [[ "$1" =~ ^[0-9a-f]{40}$ || "$1" =~ ^[0-9a-f]{64}$ ]]
}

# The marker is a small state machine.  STAGED closes the otherwise unavoidable
# crash window between git commit and recording COMMIT_HEAD: its tree lets the
# next run prove that the new commit is exactly the one prepared by this run.
write_run_marker() {
  local phase="$1"
  local base_head="$2"
  local phase_oid="${3:-}"

  is_git_oid "${base_head}" || return 1
  case "${phase}" in
    RUNNING) [ -z "${phase_oid}" ] || return 1 ;;
    STAGED|COMMITTED) is_git_oid "${phase_oid}" || return 1 ;;
    *) return 1 ;;
  esac

  rm -f -- "${RUN_MARKER_NEW}" || return 1
  if ! (
    umask 077
    {
      printf 'VERSION=2\n'
      printf 'PHASE=%s\n' "${phase}"
      printf 'BASE_HEAD=%s\n' "${base_head}"
      case "${phase}" in
        STAGED) printf 'STAGED_TREE=%s\n' "${phase_oid}" ;;
        COMMITTED) printf 'COMMIT_HEAD=%s\n' "${phase_oid}" ;;
      esac
    } > "${RUN_MARKER_NEW}"
    chmod 0600 "${RUN_MARKER_NEW}"
    mv -f -- "${RUN_MARKER_NEW}" "${RUN_MARKER}"
  ); then
    rm -f -- "${RUN_MARKER_NEW}"
    return 1
  fi
}

finish_run() {
  local exit_code="$1"
  if ! clear_run_marker; then
    notify_kind validation_failed
    mark_failure_handled
    exit 30
  fi
  exit "${exit_code}"
}

recovery_paths_are_safe() {
  local exclusions=(
    ':(exclude)docs'
    ':(exclude)docs/**'
    ':(exclude).docs-weekly-new'
    ':(exclude).docs-weekly-new/**'
    ':(exclude).docs-weekly-old'
    ':(exclude).docs-weekly-old/**'
  )
  local unexpected_untracked

  git diff --quiet -- . "${exclusions[@]}" || return 1
  git diff --cached --quiet -- . "${exclusions[@]}" || return 1
  unexpected_untracked="$(
    git ls-files --others --exclude-standard -- . "${exclusions[@]}"
  )" || return 1
  [ -z "${unexpected_untracked}" ]
}

pipeline_changes_are_safe() {
  local exclusions=(
    ':(exclude)docs'
    ':(exclude)docs/**'
  )
  local unexpected_untracked

  git diff --quiet -- . "${exclusions[@]}" || return 1
  git diff --cached --quiet -- . "${exclusions[@]}" || return 1
  unexpected_untracked="$(
    git ls-files --others --exclude-standard -- . "${exclusions[@]}"
  )" || return 1
  [ -z "${unexpected_untracked}" ]
}

cleanup_generator_temps() {
  # These are the only fixed repository-level temporary directories created by
  # the generator. REPO_REAL is the verified physical repository directory.
  rm -rf -- \
    "${REPO_REAL}/.docs-weekly-new" \
    "${REPO_REAL}/.docs-weekly-old"
}

cleanup_generated_paths() {
  local base_head="$1"

  git restore --source="${base_head}" --staged --worktree -- docs || return 1
  git clean -fdx -- docs || return 1
  cleanup_generator_temps
}

working_tree_is_clean() {
  local status
  status="$(git status --porcelain --untracked-files=normal)" || return 1
  [ -z "${status}" ]
}

commit_is_safe_successor() {
  local base_head="$1"
  local commit_head="$2"
  local expected_tree="${3:-}"
  local parent_line actual_tree
  local commit_parts=()
  local exclusions=(
    ':(exclude)docs'
    ':(exclude)docs/**'
  )

  is_git_oid "${base_head}" || return 1
  is_git_oid "${commit_head}" || return 1
  git cat-file -e "${base_head}^{commit}" 2>/dev/null || return 1
  git cat-file -e "${commit_head}^{commit}" 2>/dev/null || return 1

  parent_line="$(git rev-list --parents -n 1 "${commit_head}")" || return 1
  read -r -a commit_parts <<< "${parent_line}"
  [ "${#commit_parts[@]}" -eq 2 ] || return 1
  [ "${commit_parts[0]}" = "${commit_head}" ] || return 1
  [ "${commit_parts[1]}" = "${base_head}" ] || return 1

  # The recovered commit must contain at least one docs change and no change
  # anywhere else in the repository.
  git diff --quiet "${base_head}" "${commit_head}" -- . "${exclusions[@]}" \
    || return 1
  if git diff --quiet "${base_head}" "${commit_head}" -- docs; then
    return 1
  fi

  if [ -n "${expected_tree}" ]; then
    is_git_oid "${expected_tree}" || return 1
    actual_tree="$(git rev-parse --verify "${commit_head}^{tree}")" || return 1
    [ "${actual_tree}" = "${expected_tree}" ] || return 1
  fi
}

legacy_commit_matches_automation() {
  local commit_head="$1"
  local subject

  [ "$(git show -s --format=%an "${commit_head}")" = "Homeassistant-Wiki Automatik" ] \
    || return 1
  [ "$(git show -s --format=%ae "${commit_head}")" = "homeassistant-wiki@local.invalid" ] \
    || return 1
  subject="$(git show -s --format=%s "${commit_head}")" || return 1
  [[ "${subject}" =~ ^Wiki\ automatisch\ aktualisiert:\ [0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]
}

read_run_marker() {
  local marker_lines=()

  RECOVERY_PHASE=""
  RECOVERY_BASE_HEAD=""
  RECOVERY_PHASE_OID=""
  mapfile -t marker_lines < "${RUN_MARKER}" || return 1

  # Backward compatibility for a marker written by the previous script.  A
  # legacy post-commit recovery is accepted only with additional commit
  # metadata checks below.
  if [ "${#marker_lines[@]}" -eq 1 ]; then
    case "${marker_lines[0]}" in
      BASE_HEAD=*)
        RECOVERY_PHASE="LEGACY"
        RECOVERY_BASE_HEAD="${marker_lines[0]#BASE_HEAD=}"
        ;;
      *) return 1 ;;
    esac
    is_git_oid "${RECOVERY_BASE_HEAD}"
    return
  fi

  [ "${marker_lines[0]:-}" = "VERSION=2" ] || return 1
  case "${marker_lines[1]:-}" in
    PHASE=RUNNING)
      [ "${#marker_lines[@]}" -eq 3 ] || return 1
      RECOVERY_PHASE="RUNNING"
      ;;
    PHASE=STAGED)
      [ "${#marker_lines[@]}" -eq 4 ] || return 1
      case "${marker_lines[3]}" in
        STAGED_TREE=*) RECOVERY_PHASE_OID="${marker_lines[3]#STAGED_TREE=}" ;;
        *) return 1 ;;
      esac
      RECOVERY_PHASE="STAGED"
      ;;
    PHASE=COMMITTED)
      [ "${#marker_lines[@]}" -eq 4 ] || return 1
      case "${marker_lines[3]}" in
        COMMIT_HEAD=*) RECOVERY_PHASE_OID="${marker_lines[3]#COMMIT_HEAD=}" ;;
        *) return 1 ;;
      esac
      RECOVERY_PHASE="COMMITTED"
      ;;
    *) return 1 ;;
  esac
  case "${marker_lines[2]:-}" in
    BASE_HEAD=*) RECOVERY_BASE_HEAD="${marker_lines[2]#BASE_HEAD=}" ;;
    *) return 1 ;;
  esac
  is_git_oid "${RECOVERY_BASE_HEAD}" || return 1
  if [ "${RECOVERY_PHASE}" != "RUNNING" ]; then
    is_git_oid "${RECOVERY_PHASE_OID}" || return 1
  fi
}

resume_committed_run() {
  local base_head="$1"
  local commit_head="$2"
  local expected_tree="${3:-}"
  local current_head

  current_head="$(git rev-parse --verify HEAD)" || abort_recovery github_failed
  [ "${current_head}" = "${commit_head}" ] || abort_recovery github_failed
  if [ "${commit_head}" != "${base_head}" ]; then
    commit_is_safe_successor "${base_head}" "${commit_head}" "${expected_tree}" \
      || abort_recovery validation_failed
  fi
  recovery_paths_are_safe || abort_recovery validation_failed
  cleanup_generator_temps || abort_recovery validation_failed
  working_tree_is_clean || abort_recovery validation_failed

  # Push is intentionally idempotent.  A crash after a successful push, or a
  # transient network failure, therefore resumes here without regenerating or
  # creating a second commit.
  if ! git push origin HEAD:main; then
    notify_kind github_failed
    mark_failure_handled
    exit 30
  fi
  if ! touch "${PUBLISH_READY}"; then
    notify_kind validation_failed
    mark_failure_handled
    exit 30
  fi
  finish_run 0
}

install -d -m 0700 "${STATE_DIR}" "${STATE_DIR}/work"

# systemd's timer may catch up after a reboot.  Never let two runs overlap.
exec 9>"${STATE_DIR}/weekly.lock"
if ! flock -n 9; then
  exit 75
fi
rm -f "${PUBLISH_READY}"
rm -f "${STATE_DIR}/failure-handled"
exec 8>"${STATE_DIR}/notification.lock"
flock 8

cd "${REPO_DIR}"
REPO_REAL="$(pwd -P)"

if [ ! -d .git ]; then
  notify_kind github_failed
  mark_failure_handled
  exit 30
fi

if [ "$(git symbolic-ref --quiet --short HEAD || true)" != "main" ]; then
  notify_kind github_failed
  mark_failure_handled
  exit 30
fi

export GIT_SSH_COMMAND="ssh -i ${GITHUB_KEY_FILE} -o IdentitiesOnly=yes -o UserKnownHostsFile=${KNOWN_HOSTS} -o StrictHostKeyChecking=yes"
if ! git remote set-url origin git@github.com:maxlhuber/homeassistant-wiki.git; then
  notify_kind github_failed
  mark_failure_handled
  exit 30
fi

# A marker survives an abrupt interruption or a retryable post-commit failure.
# Pre-commit phases are rolled back.  A proven post-commit phase resumes the
# idempotent push and hands the already generated docs to the publisher.
if [ -e "${RUN_MARKER}" ] || [ -L "${RUN_MARKER}" ]; then
  if [ -L "${RUN_MARKER}" ] || [ ! -f "${RUN_MARKER}" ]; then
    abort_recovery github_failed
  fi
  read_run_marker || abort_recovery github_failed
  if ! git cat-file -e "${RECOVERY_BASE_HEAD}^{commit}" 2>/dev/null; then
    abort_recovery github_failed
  fi
  CURRENT_HEAD="$(git rev-parse --verify HEAD)" || abort_recovery github_failed

  if [ "${RECOVERY_PHASE}" = "COMMITTED" ]; then
    [ "${CURRENT_HEAD}" = "${RECOVERY_PHASE_OID}" ] \
      || abort_recovery github_failed
    resume_committed_run "${RECOVERY_BASE_HEAD}" "${RECOVERY_PHASE_OID}"
  fi

  if [ "${CURRENT_HEAD}" = "${RECOVERY_BASE_HEAD}" ]; then
    recovery_paths_are_safe || abort_recovery validation_failed
    cleanup_generated_paths "${RECOVERY_BASE_HEAD}" \
      || abort_recovery validation_failed
    working_tree_is_clean || abort_recovery validation_failed
    clear_run_marker || abort_recovery validation_failed
  elif [ "${RECOVERY_PHASE}" = "STAGED" ]; then
    git cat-file -e "${RECOVERY_PHASE_OID}^{tree}" 2>/dev/null \
      || abort_recovery github_failed
    commit_is_safe_successor \
      "${RECOVERY_BASE_HEAD}" "${CURRENT_HEAD}" "${RECOVERY_PHASE_OID}" \
      || abort_recovery validation_failed
    recovery_paths_are_safe || abort_recovery validation_failed
    cleanup_generator_temps || abort_recovery validation_failed
    working_tree_is_clean || abort_recovery validation_failed
    write_run_marker COMMITTED "${RECOVERY_BASE_HEAD}" "${CURRENT_HEAD}" \
      || abort_recovery validation_failed
    resume_committed_run \
      "${RECOVERY_BASE_HEAD}" "${CURRENT_HEAD}" "${RECOVERY_PHASE_OID}"
  elif [ "${RECOVERY_PHASE}" = "LEGACY" ]; then
    commit_is_safe_successor "${RECOVERY_BASE_HEAD}" "${CURRENT_HEAD}" \
      || abort_recovery validation_failed
    legacy_commit_matches_automation "${CURRENT_HEAD}" \
      || abort_recovery validation_failed
    recovery_paths_are_safe || abort_recovery validation_failed
    cleanup_generator_temps || abort_recovery validation_failed
    working_tree_is_clean || abort_recovery validation_failed
    write_run_marker COMMITTED "${RECOVERY_BASE_HEAD}" "${CURRENT_HEAD}" \
      || abort_recovery validation_failed
    resume_committed_run "${RECOVERY_BASE_HEAD}" "${CURRENT_HEAD}"
  else
    abort_recovery github_failed
  fi
fi

if [ -n "$(git status --porcelain --untracked-files=normal)" ]; then
  notify_kind github_failed
  mark_failure_handled
  exit 30
fi

# Adopt only an already reviewed, straight-ahead GitHub state. A divergent or
# locally ahead history is never merged automatically.
if ! git fetch --no-tags origin \
  refs/heads/main:refs/remotes/origin/main; then
  notify_kind github_failed
  mark_failure_handled
  exit 30
fi
CURRENT_HEAD="$(git rev-parse --verify HEAD)" || {
  notify_kind github_failed
  mark_failure_handled
  exit 30
}
REMOTE_HEAD="$(git rev-parse --verify origin/main)" || {
  notify_kind github_failed
  mark_failure_handled
  exit 30
}
if ! git merge-base --is-ancestor "${CURRENT_HEAD}" "${REMOTE_HEAD}"; then
  notify_kind github_failed
  mark_failure_handled
  exit 30
fi
if [ "${CURRENT_HEAD}" != "${REMOTE_HEAD}" ]; then
  if ! git merge --ff-only "${REMOTE_HEAD}"; then
    notify_kind github_failed
    mark_failure_handled
    exit 30
  fi
fi
working_tree_is_clean || {
  notify_kind github_failed
  mark_failure_handled
  exit 30
}

BASE_HEAD="$(git rev-parse --verify HEAD)"

if ! write_run_marker RUNNING "${BASE_HEAD}"; then
  notify_kind github_failed
  mark_failure_handled
  exit 30
fi

rollback_docs() {
  cleanup_generated_paths "${BASE_HEAD}" >/dev/null 2>&1
}

set +e
"${PYTHON}" "${RUNNER_DIR}/weekly_update.py" \
  --repo "${REPO_DIR}" \
  --state-dir "${STATE_DIR}" \
  --backup-root "${BACKUP_DIR}" \
  --backup-key-file "${BACKUP_KEY_FILE}" \
  --openai-key-file "${OPENAI_KEY_FILE}"
PIPELINE_EXIT=$?
set -e

if [ "${PIPELINE_EXIT}" -ne 0 ]; then
  if ! rollback_docs; then
    notify_kind validation_failed
    mark_failure_handled
    exit 30
  fi
  notify_status
  mark_failure_handled
  finish_run "${PIPELINE_EXIT}"
fi

# Warnings (especially exhausted API credit) do not block the factual update.
notify_status

if ! pipeline_changes_are_safe; then
  if ! rollback_docs; then
    notify_kind validation_failed
    mark_failure_handled
    exit 30
  fi
  notify_kind validation_failed
  mark_failure_handled
  finish_run 30
fi

if ! git add -A -- docs; then
  if ! rollback_docs; then
    notify_kind validation_failed
    mark_failure_handled
    exit 30
  fi
  notify_kind github_failed
  mark_failure_handled
  finish_run 30
fi

if ! pipeline_changes_are_safe; then
  if ! rollback_docs; then
    notify_kind validation_failed
    mark_failure_handled
    exit 30
  fi
  notify_kind validation_failed
  mark_failure_handled
  finish_run 30
fi

STAGED_TREE=""
if ! git diff --cached --quiet; then
  if ! STAGED_TREE="$(git write-tree)" \
    || ! write_run_marker STAGED "${BASE_HEAD}" "${STAGED_TREE}"; then
    if ! rollback_docs; then
      notify_kind validation_failed
      mark_failure_handled
      exit 30
    fi
    notify_kind github_failed
    mark_failure_handled
    finish_run 30
  fi
  if ! git config user.name "Homeassistant-Wiki Automatik" \
    || ! git config user.email "homeassistant-wiki@local.invalid"; then
    if ! rollback_docs; then
      notify_kind validation_failed
      mark_failure_handled
      exit 30
    fi
    notify_kind github_failed
    mark_failure_handled
    finish_run 30
  fi

  set +e
  git commit -m "Wiki automatisch aktualisiert: $(date +%F)"
  COMMIT_EXIT=$?
  set -e
  COMMIT_HEAD="$(git rev-parse --verify HEAD)" || COMMIT_HEAD=""
  if [ "${COMMIT_EXIT}" -ne 0 ] && [ "${COMMIT_HEAD}" = "${BASE_HEAD}" ]; then
    if ! rollback_docs; then
      notify_kind validation_failed
      mark_failure_handled
      exit 30
    fi
    notify_kind github_failed
    mark_failure_handled
    finish_run 30
  fi
  if ! commit_is_safe_successor "${BASE_HEAD}" "${COMMIT_HEAD}" "${STAGED_TREE}" \
    || ! working_tree_is_clean; then
    # HEAD may already have advanced.  Keep the STAGED marker so the next run
    # can either prove and adopt that exact tree or fail closed.
    notify_kind validation_failed
    mark_failure_handled
    exit 30
  fi
else
  COMMIT_HEAD="${BASE_HEAD}"
fi

if ! write_run_marker COMMITTED "${BASE_HEAD}" "${COMMIT_HEAD}"; then
  # After a commit, clearing the older marker would lose the recovery proof.
  # Leave RUNNING/STAGED in place and let the next invocation recover safely.
  notify_kind validation_failed
  mark_failure_handled
  exit 30
fi

resume_committed_run "${BASE_HEAD}" "${COMMIT_HEAD}" "${STAGED_TREE}"
