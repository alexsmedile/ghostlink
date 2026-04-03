from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def pytest_sessionstart(session) -> None:
    os.environ.setdefault("PYTHONPATH", str(SRC))


def require_exports(module, names: tuple[str, ...]) -> None:
    missing = [name for name in names if not hasattr(module, name)]
    assert not missing, f"missing exports from {module.__name__}: {missing}"


def require_dataclass_fields(cls, names: set[str]) -> None:
    actual = set(getattr(cls, "__dataclass_fields__", {}).keys())
    missing = names - actual
    assert not missing, f"missing dataclass fields on {cls.__name__}: {sorted(missing)}"
