"""
Permanent Windows UTF-8 Stdio Fixer.
Ensures sys.stdout, sys.stderr, and subprocesses use UTF-8 with backslashreplace error handling on Windows.
"""

import sys
import os

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

def init_utf8():
    """Configures stdout and stderr to handle UTF-8 safely on Windows."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass

# Execute automatically on import
init_utf8()
