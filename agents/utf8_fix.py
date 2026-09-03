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
    reconfig_out = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfig_out):
        try:
            reconfig_out(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass
    reconfig_err = getattr(sys.stderr, "reconfigure", None)
    if callable(reconfig_err):
        try:
            reconfig_err(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass

# Execute automatically on import
init_utf8()
