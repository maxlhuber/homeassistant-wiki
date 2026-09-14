import sys
from pathlib import Path


# Home Assistant's s6 service environment does not reliably preserve the
# Dockerfile PYTHONPATH.  The update engine intentionally lives with the
# project scripts, so make that runtime dependency explicit before importing
# the server (and, transitively, the engine and snapshot helpers).
PROJECT_SCRIPTS = Path("/app/project/scripts")
if PROJECT_SCRIPTS.is_dir():
    sys.path.insert(0, str(PROJECT_SCRIPTS))

from .server import main

main()
