"""FitOS backend: sizing-intelligence API (recommendation engine + Gemma)."""

import sys
from pathlib import Path

# The deterministic engine is the repo-root `core/` package, shared with the
# persona CLI and the engine test suite (single source of truth). Make it
# importable no matter how the backend is launched: uvicorn/pytest from
# backend/, or the Docker image (which mirrors the repo layout, see Dockerfile).
_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

__version__ = "0.1.0"
