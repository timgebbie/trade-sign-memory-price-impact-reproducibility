#!/usr/bin/env python3
"""Stage the four science and methods tables from controlled CSV and captions."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v1.0"

TABLES = {
    "T01": {
        "title": "Notation crosswalk and exclusions",
        "widths": [3.0, 4.2, 5.0, 12.0],
    },
    "T02": {
        "title": "Clock taxonomy",
        "widths": [3.3, 4.3, 5.0, 5.0, 5.2, 2.6],
    },
    "T03": {
        "title": "Execution-schedule conventions",
        "widths": [3.7, 4.0, 5.0, 4.0, 7.0, 1.5],
    },
    "T04": {
        "title": "Controlled parameter register",
        "widths": [1.6, 2.6, 2.8, 4.7, 4.6, 4.7, 2.4],
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def latex_cell(header: str, value: str) -> str:
    if header.endswith("_tex"):
        return value
    return latex_escape(value)


def display_header(header: str) -> str:
    return latex_escape(header.removesuffix("_tex").replace("_", " ").title())


def caption_text(path: Path) -> str:
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        if line.startswith("Artefact status:"):
            continue
        lines.append(line.strip())
    text = " ".join(part for part in lines if part)
    text = text.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


def write_table(table_id: str, spec: dict) -> dict:
    csv_path = ROOT / "tables" / "csv" / f"RDL-{table_id}-{VERSION}.csv"
    tex_path = ROOT / "tables" / "tex" / f"RDL-{table_id}-{VERSION}.tex"
    caption_path = ROOT / "captions" / f"RDL-{table_id}-CAP-{VERSION}.md"

    with csv_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        rows = list(reader)
    if not headers or not rows:
        raise ValueError(f"{table_id}: empty CSV or header")
    if len(headers) != len(spec["widths"]):
        raise ValueError(f"{table_id}: width count does not match CSV columns")
    if any(set(row) != set(headers) for row in rows):
        raise ValueError(f"{table_id}: inconsistent CSV row schema")

    column_spec = "@{}" + "".join(
        rf">{{\RaggedRight\arraybackslash}}p{{{width:.1f}cm}}"
        for width in spec["widths"]
    ) + "@{}"
    header_row = " & ".join(rf"\textbf{{{display_header(h)}}}" for h in headers)
    body_rows = [
        " & ".join(latex_cell(h, row[h]) for h in headers) + r" \\"
        for row in rows
    ]
    caption = latex_escape(caption_text(caption_path))

    content = [
        f"% RDL {table_id} {VERSION} -- generated publication-table staging file.",
        "% Artefact status: diagnostic output.",
        "% Required packages: geometry, booktabs, longtable, array, ragged2e, caption.",
        f"% Source CSV: tables/csv/RDL-{table_id}-{VERSION}.csv",
        f"% Caption source: captions/RDL-{table_id}-CAP-{VERSION}.md",
        "% Generating script: scripts/RDL-TAB.py",
        "% Copy the block between CUT-PASTE markers into the supplement; retain the packages above.",
        r"\documentclass[10pt,a4paper,landscape]{article}",
        r"\usepackage[margin=12mm]{geometry}",
        r"\usepackage{booktabs,longtable,array,ragged2e,caption}",
        r"\setlength{\tabcolsep}{3pt}",
        r"\renewcommand{\arraystretch}{1.15}",
        r"\begin{document}",
        r"\footnotesize",
        "% ===== CUT-PASTE TABLE BEGIN =====",
        rf"\begin{{longtable}}{{{column_spec}}}",
        rf"\caption{{{caption}}}\label{{tab:rdl-{table_id.lower()}}}\\",
        r"\toprule",
        header_row + r" \\",
        r"\midrule",
        r"\endfirsthead",
        rf"\multicolumn{{{len(headers)}}}{{l}}{{\tablename\ \thetable\ continued}}\\",
        r"\toprule",
        header_row + r" \\",
        r"\midrule",
        r"\endhead",
        r"\midrule",
        rf"\multicolumn{{{len(headers)}}}{{r}}{{Continued on next page}}\\",
        r"\endfoot",
        r"\bottomrule",
        r"\endlastfoot",
        *body_rows,
        r"\end{longtable}",
        "% ===== CUT-PASTE TABLE END =====",
        r"\end{document}",
        "",
    ]
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    tex_path.write_text("\n".join(content), encoding="utf-8")
    return {
        "table_id": table_id,
        "row_count": len(rows),
        "column_count": len(headers),
        "csv_sha256": sha256(csv_path),
        "caption_sha256": sha256(caption_path),
        "tex_sha256": sha256(tex_path),
    }


def main() -> int:
    report = {
        "version": VERSION,
        "tables": [write_table(table_id, spec) for table_id, spec in TABLES.items()],
    }
    report["checks"] = {
        "four_tables_staged": len(report["tables"]) == 4,
        "all_tables_nonempty": all(item["row_count"] > 0 for item in report["tables"]),
        "all_hashes_recorded": all(
            all(item[key] for key in ("csv_sha256", "caption_sha256", "tex_sha256"))
            for item in report["tables"]
        ),
    }
    output = ROOT / "diagnostics" / f"RDL-TAB-TST-{VERSION}.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["checks"], sort_keys=True))
    return 0 if all(report["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
