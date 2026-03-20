#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish civitai-prompt-parser export artifacts into this repository.")
    parser.add_argument("--run-name", required=True, help="Short name for the export run.")
    parser.add_argument("--source-url", required=True, help="Original Civitai URL used for the export.")
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="One or more generated export files to publish.",
    )
    parser.add_argument(
        "--benchmark-json",
        help="Optional benchmark summary JSON to include in the manifest.",
    )
    parser.add_argument(
        "--generated-at",
        help="Optional UTC timestamp. Defaults to now.",
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root. Defaults to this script's parent repo.",
    )
    return parser.parse_args()


def slugify(value: str) -> str:
    out = []
    previous_dash = False
    for char in value.lower():
        if char.isalnum():
            out.append(char)
            previous_dash = False
            continue
        if not previous_dash:
            out.append("-")
            previous_dash = True
    slug = "".join(out).strip("-")
    return slug or "run"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    generated_at = (
        datetime.fromisoformat(args.generated_at.replace("Z", "+00:00")).astimezone(UTC)
        if args.generated_at
        else datetime.now(UTC)
    )
    date_dir = generated_at.strftime("%Y-%m-%d")
    run_slug = slugify(args.run_name)
    target_dir = repo_root / "exports" / date_dir / run_slug
    target_dir.mkdir(parents=True, exist_ok=True)

    benchmark_summary = None
    if args.benchmark_json:
        benchmark_summary = json.loads(Path(args.benchmark_json).expanduser().read_text(encoding="utf-8"))

    copied_files = []
    for file_arg in args.files:
        source_path = Path(file_arg).expanduser().resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Missing export file: {source_path}")
        target_path = target_dir / source_path.name
        shutil.copy2(source_path, target_path)
        copied_files.append(
            {
                "name": source_path.name,
                "bytes": target_path.stat().st_size,
                "sha256": sha256_file(target_path),
                "originalPath": str(source_path),
                "repoPath": str(target_path.relative_to(repo_root)),
            }
        )

    manifest = {
        "runName": args.run_name,
        "runSlug": run_slug,
        "sourceUrl": args.source_url,
        "generatedAtUtc": generated_at.isoformat(),
        "files": copied_files,
        "benchmarkSummary": benchmark_summary,
    }
    manifest_path = target_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    append_jsonl(
        repo_root / "exports" / "index.jsonl",
        {
            "runName": args.run_name,
            "runSlug": run_slug,
            "sourceUrl": args.source_url,
            "generatedAtUtc": generated_at.isoformat(),
            "manifestPath": str(manifest_path.relative_to(repo_root)),
        },
    )

    print(json.dumps({"manifestPath": str(manifest_path), "publishedFiles": copied_files}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
