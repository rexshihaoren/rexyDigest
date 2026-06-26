"""Make the `rexy` package importable for tests without an editable install.

Without this, `pytest` from `python/` would fail to find `rexy` because there
is no installed package on the sys.path.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # python/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
