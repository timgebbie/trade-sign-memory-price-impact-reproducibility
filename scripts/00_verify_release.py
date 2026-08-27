#!/usr/bin/env python3
"""Verify the retained v1.0.0 release surface after regeneration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = (
    "config/RDL-CFG-v1.1.json",
    "config/RDL-F02-v1.2.json",
    "config/RDL-W09-v1.0.json",
    "data/RDL-F02-v1.2.csv",
    "data/RDL-F03-v1.0.csv",
    "data/RDL-F05-v1.1.csv",
    "data/RDL-F06-v1.0.csv",
    "data/RDL-F07-v1.0.csv",
    "data/RDL-W09-v1.0.csv",
    "figures/python/RDL-F02-v1.2.pdf",
    "figures/python/RDL-F02-v1.2.png",
    "figures/python/RDL-F03-v1.0.pdf",
    "figures/python/RDL-F03-v1.0.png",
    "figures/python/RDL-F05-v1.1.pdf",
    "figures/python/RDL-F05-v1.1.png",
    "figures/python/RDL-F06-v1.0.pdf",
    "figures/python/RDL-F06-v1.0.png",
    "figures/python/RDL-F07-v1.0.pdf",
    "figures/python/RDL-F07-v1.0.png",
    "figures/tikz/RDL-F08-v1.0.tex",
    "figures/final/RDL-F08-v1.0.pdf",
    "figures/final/RDL-F08-v1.0.png",
    "raw-outputs/RDL-F02-WAITS-v1.2.csv",
    "raw-outputs/RDL-F03-MC-v1.0.csv",
    "outputs/RDL-F03-MC-SUM-v1.0.csv",
    "registers/RDL-ACC-v1.9.csv",
    "source/source-v0/RDL-SRC-v0.tex",
    "source/source-v0/RDL-REF-v0.bib",
)

DIAGNOSTIC_FILES = {
    "F02": "diagnostics/RDL-F02-TST-v1.2.json",
    "F03": "diagnostics/RDL-F03-TST-v1.0.json",
    "F05": "diagnostics/RDL-F05-TST-v1.1.json",
    "F06": "diagnostics/RDL-F06-TST-v1.0.json",
    "F07": "diagnostics/RDL-F07-TST-v1.0.json",
    "W09": "diagnostics/RDL-W09-TST-v1.0.json",
}

SOURCE_HASHES = {
    "source/source-v0/RDL-SRC-v0.tex": "6b5851e15a0c8f1a489b2f74cf54f85bca43c961e0bb3141a1d2656ad0c0ae9b",
    "source/source-v0/RDL-REF-v0.bib": "8ff04e3e56afe28c14641ee55f84d1574628614fe648ae2aa623d0bf0971a777",
}

F08_HASHES = {
    "figures/tikz/RDL-F08-v1.0.tex": "f8140c1285fe2bb3eebf8a9d760285eca4bbefe898dc296f611e99ec3af42b7a",
    "figures/final/RDL-F08-v1.0.pdf": "162c08bc68cc0f92ae644043f23378c0bf5cab2853e9608ba62d1133ee349d23",
    "figures/final/RDL-F08-v1.0.png": "6d45f8d068e22642402a8b33d07778cd06f8548f61df7198f1ea2e5841d6e67f",
}

FORBIDDEN_TOP_LEVEL = {
    "audits",
    "design",
    "run-notes",
    "archive",
    "final",
    "appendix",
    "supplement",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def all_checks_true(path: Path) -> bool:
    payload = json.loads(path.read_text(encoding="utf-8"))
    checks = payload.get("checks", {})
    return bool(checks) and all(value is True for value in checks.values())


def main() -> int:
    results: dict[str, bool] = {}

    results["required_paths_present"] = all((ROOT / path).exists() for path in REQUIRED_PATHS)
    results["diagnostic_checks_pass"] = all(
        all_checks_true(ROOT / path) for path in DIAGNOSTIC_FILES.values()
    )

    table_report = json.loads(
        (ROOT / "diagnostics/RDL-TAB-TST-v1.0.json").read_text(encoding="utf-8")
    )
    table_ids = [item["table_id"] for item in table_report.get("tables", [])]
    results["exactly_four_tables_staged"] = (
        table_ids == ["T01", "T02", "T03", "T04"]
        and all(value is True for value in table_report.get("checks", {}).values())
    )

    results["primary_source_hashes_match"] = all(
        sha256(ROOT / path) == expected for path, expected in SOURCE_HASHES.items()
    )
    results["F08_frozen_outputs_match"] = all(
        sha256(ROOT / path) == expected for path, expected in F08_HASHES.items()
    )
    results["development_scaffolding_absent"] = not any(
        (ROOT / name).exists() for name in FORBIDDEN_TOP_LEVEL
    )
    results["no_embedded_zip_archives"] = not any(ROOT.rglob("*.zip"))
    results["no_python_cache_artifacts"] = not any(ROOT.rglob("__pycache__")) and not any(ROOT.rglob("*.pyc"))
    results["four_table_csv_and_tex_only"] = (
        len(list((ROOT / "tables/csv").glob("RDL-T*-v1.0.csv"))) == 4
        and len(list((ROOT / "tables/tex").glob("RDL-T*-v1.0.tex"))) == 4
    )

    for key, value in results.items():
        print(f"{key}: {'PASS' if value else 'FAIL'}")

    if not all(results.values()):
        return 1
    print(f"Release-surface verification passed: {len(results)} checks, 0 failures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
