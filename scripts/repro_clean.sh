#!/bin/zsh
# Reproduce tests + benchmark from a clean copy and a fresh virtual environment.
# Usage: zsh scripts/repro_clean.sh   (writes logs/results to artifacts/repro/)
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO/artifacts/repro"
CLEAN="/tmp/slotsmith_clean_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT" "$CLEAN"
rsync -a --exclude .venv --exclude artifacts --exclude .pytest_cache --exclude .hypothesis --exclude reference \
      --exclude deliverables --exclude .playwright-mcp --exclude data --exclude '__pycache__' --exclude '*.egg-info' \
      "$REPO/" "$CLEAN/repo/"
cd "$CLEAN/repo"
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.lock.txt
.venv/bin/pip install -q --no-deps -e .
{
  echo "clean_dir: $CLEAN"; date; sw_vers; sysctl -n machdep.cpu.brand_string; sysctl -n hw.ncpu
  .venv/bin/python -VV; .venv/bin/pip freeze
} > "$OUT/environment.txt" 2>&1
.venv/bin/python -m pytest -q > "$OUT/pytest.log" 2>&1 || true
tail -3 "$OUT/pytest.log"
for i in 1 2; do
  SLOTSMITH_BENCH_DIR="$CLEAN/bench$i" SLOTSMITH_BENCH_JSON="$OUT/benchmarks_clean_run$i.json" \
    .venv/bin/python scripts/benchmark.py > "$OUT/benchmark_clean_run$i.log" 2>&1
  tail -25 "$OUT/benchmark_clean_run$i.log"
done
echo "done: $CLEAN"
