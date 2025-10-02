# src/paths.py
from pathlib import Path
import os

# Determine the repository root
REPO_ROOT = Path(__file__).resolve().parents[1]  # points to /opt/render/project

# Data directories - prefer persistent disk in production
DATA_DIR = Path(os.environ.get("DATA_DIR", "/var/data"))  # prefers persistent disk
TMP_DIR = Path("/tmp")

# Ensure directories exist
for p in (DATA_DIR, TMP_DIR):
    p.mkdir(parents=True, exist_ok=True)

# Export paths for use in other modules
__all__ = ['REPO_ROOT', 'DATA_DIR', 'TMP_DIR']
