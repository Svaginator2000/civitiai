# civitiai

Tracked result sink for `civitai-prompt-parser`.

## Purpose

This repository stores two things:

1. Benchmark history for parser changes.
2. Published export artifacts produced by the skill.

## Layout

- `benchmarks/results.tsv`: autoresearch-style keep/discard history
- `benchmarks/latest.json`: most recent benchmark summary
- `exports/<YYYY-MM-DD>/<run-name>/`: published skill outputs plus a manifest
- `exports/index.jsonl`: append-only export index
- `scripts/publish_skill_results.py`: copy a completed skill run into this repo

## Benchmark Rule

The parser only advances when it is not worse on either gated metric:

- quality score must not go down
- median benchmark-workload time must not go up

Prefer changes that are both better and faster.
Benchmark rows are workload-versioned so new benchmark workloads can establish their own baseline.

## Benchmark Command

```bash
python3 /home/mpax/.codex/skills/civitai-prompt-parser/scripts/benchmark_civitai_prompt_parser.py \
  --results-tsv /home/mpax/civitiai/benchmarks/results.tsv \
  --write-json /home/mpax/civitiai/benchmarks/latest.json \
  --description "describe the parser change"
```

## Publish Command

```bash
python3 /home/mpax/civitiai/scripts/publish_skill_results.py \
  --run-name enigmata-noobai-alltime \
  --source-url "https://civitai.com/user/enigmata/images?baseModels=NoobAI&period=AllTime" \
  --benchmark-json /home/mpax/civitiai/benchmarks/latest.json \
  --files /path/to/export_images.json /path/to/export_images.csv /path/to/export_posts.json /path/to/export_posts.csv /path/to/export_summary.json
```
