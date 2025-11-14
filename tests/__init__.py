"""Package init for tests.

This file ensures the project root (repository root) is on sys.path so tests
can import the application package (``backend``) reliably. Placing this in the
package init centralizes the behaviour so individual test modules and
``conftest.py`` don't need to each modify sys.path.

Notes:
- This runs when Python imports test modules as part of the ``tests`` package.
- Alternatively you can use `pip install -e .` or set PYTHONPATH in CI; this
  file is a lightweight, local approach that avoids developer env changes.
"""

import os
import sys

# Compute repository root (parent of the tests directory)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    # Insert at front so local package takes precedence during tests
    sys.path.insert(0, PROJECT_ROOT)
