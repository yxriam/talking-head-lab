"""Replace EchoMimic V3 rows in a multi-sample visual-results file."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main(run_root: Path) -> None:
    results_path = run_root / "visual-results.json"
    parts_path = run_root / "visual-v3-parts"
    previous = json.loads(results_path.read_text(encoding="utf-8"))
    retained = [row for row in previous if row.get("model") != "echomimic_v3_flash"]
    replacements = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(parts_path.glob("*.json"))]
    if len(replacements) != 14:
        raise RuntimeError(f"Expected 14 V3 results, found {len(replacements)}")
    errors = [row for row in replacements if "error" in row]
    if errors:
        raise RuntimeError(f"V3 visual evaluation errors: {errors}")
    merged = sorted(retained + replacements, key=lambda row: (row["case_id"], row["model"]))
    results_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(merged)} rows: {len(retained)} retained + {len(replacements)} V3")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
