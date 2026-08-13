# Root Cause Profile

Fingerprint:

PYTHON_MODULE_NOT_FOUND_NEXUSLIB

Observed error:

ModuleNotFoundError: No module named 'nexuslib'

Root cause:

When Python executes:

    python tests/security-regression.py

Python places the `tests` directory at the beginning of `sys.path`.
The repository root is not guaranteed to be importable.

Permanent repair:

1. Determine repository root from `__file__`.
2. Insert repository root into `sys.path`.
3. Export `PYTHONPATH` in test and repair environments.
4. Test this behavior using `tests/import-regression.py`.

Regression rule:

This problem is only PASS when both:

    IMPORT REGRESSION PASS

and:

    SECURITY_REGRESSION PASS

are verified.
