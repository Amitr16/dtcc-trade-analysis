# src/paths.py
import os
from pathlib import Path

# Determine the repository root
REPO_ROOT = Path(__file__).resolve().parents[1]  # points to /opt/render/project

# Data directories - force /var/data in production, current dir locally
if os.environ.get("RENDER"):
    # Production - MUST use /var/data for persistence
    DATA_DIR = Path("/var/data")
else:
    # Local development - use current directory
    DATA_DIR = Path(os.environ.get("DATA_DIR", Path.cwd()))

TMP_DIR = Path("/tmp")

# Ensure directories exist (only if we have permission)
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # Fallback to current directory if we can't create the target
    DATA_DIR = Path.cwd()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

try:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # Fallback to temp directory
    import tempfile
    TMP_DIR = Path(tempfile.gettempdir())

# Export paths for use in other modules
__all__ = ['REPO_ROOT', 'DATA_DIR', 'TMP_DIR']