# src/paths.py
from pathlib import Path
import os

# Determine the repository root
REPO_ROOT = Path(__file__).resolve().parents[1]  # points to /opt/render/project

# Data directories - prefer persistent disk in production
if os.environ.get("RENDER") or os.environ.get("DATA_DIR"):
    # Production - use environment variable or default
    DATA_DIR = Path(os.environ.get("DATA_DIR", "/var/data"))
else:
    # Local development - use current directory
    DATA_DIR = Path.cwd()

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
