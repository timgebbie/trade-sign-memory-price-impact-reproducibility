#!/usr/bin/env python3
"""Run the single active v1.0.0 RDL reproducibility route."""

from __future__ import annotations

import importlib.metadata
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_PACKAGES = {
    "numpy": "2.3.5",
    "scipy": "1.17.0",
    "matplotlib": "3.10.8",
}

ACTIVE_STEPS = (
    ("F02 route-separated clock projections", ["scripts/RDL-F02.py"]),
    ("F03 exact LMF correlation and seeded Monte Carlo", ["scripts/RDL-F03.py", "--with-mc"]),
    ("F05 finite-width child-order response", ["scripts/RDL-F05.py"]),
    ("F06 reaction-boundary impact and relaxation", ["scripts/RDL-F06.py"]),
    ("F07 completion schedule and clock comparison", ["scripts/RDL-F07.py"]),
    ("T01--T04 table staging", ["scripts/RDL-TAB.py"]),
    ("W09 robustness diagnostics", ["scripts/RDL-W09.py"]),
    ("v1.0.0 release-surface verification", ["scripts/00_verify_release.py"]),
)


def verify_environment() -> None:
    observed = {name: importlib.metadata.version(name) for name in EXPECTED_PACKAGES}
    mismatches = {
        name: (EXPECTED_PACKAGES[name], observed[name])
        for name in EXPECTED_PACKAGES
        if observed[name] != EXPECTED_PACKAGES[name]
    }
    print(f"Python {sys.version.split()[0]}")
    print("Package contract: " + ", ".join(f"{k} {v}" for k, v in observed.items()))
    if mismatches:
        details = "; ".join(
            f"{name}: expected {expected}, found {found}"
            for name, (expected, found) in mismatches.items()
        )
        raise RuntimeError(f"Package-version mismatch: {details}")


def run(label: str, arguments: list[str], environment: dict[str, str]) -> None:
    command = [sys.executable, *arguments]
    print(f"\n[{label}] {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=PROJECT_ROOT, env=environment, check=True)


def main() -> int:
    try:
        verify_environment()
    except RuntimeError as error:
        print(f"Preflight failed: {error}")
        return 1

    environment = os.environ.copy()
    environment.setdefault("MPLBACKEND", "Agg")
    environment.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    environment.setdefault("SOURCE_DATE_EPOCH", "0")
    environment.setdefault(
        "MPLCONFIGDIR",
        str(Path(tempfile.gettempdir()) / "rdl-matplotlib"),
    )

    try:
        for label, arguments in ACTIVE_STEPS:
            run(label, arguments, environment)
    except subprocess.CalledProcessError as error:
        print(
            f"\nActive route stopped after an unsuccessful command "
            f"(exit code {error.returncode})."
        )
        return error.returncode or 1

    print("\nActive v1.0.0 reproducibility route completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
