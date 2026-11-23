"""
run.py — Single-command runner for the entire pipeline.
Cross-platform alternative to `make run` (especially on Windows where make.exe
may be blocked by Application Control policies).

Usage:
    python run.py
    python run.py --test-only
    python run.py --skip-tests
"""

import argparse
import subprocess
import sys


def run_step(cmd, desc):
    print(f"\n==================================================")
    print(f"▶ {desc}")
    print(f"  Command: {' '.join(cmd)}")
    print(f"==================================================")
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"\n❌ Step failed with exit code {res.returncode}: {desc}")
        sys.exit(res.returncode)


def main():
    parser = argparse.ArgumentParser(description="Run the Instacart repeat customer analysis pipeline.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running the pytest suite")
    parser.add_argument("--test-only", action="store_true", help="Run only the pytest suite")
    args = parser.parse_args()

    py = sys.executable

    if not args.skip_tests:
        run_step([py, "-m", "pytest", "tests/", "-v"], "Running automated tests")

    if args.test_only:
        print("\n✅ Tests passed.")
        return

    run_step([py, "src/generate_phase0_results.py"], "Phase 0: Data reality check & baseline results.json")
    run_step([py, "src/run_pipeline.py"], "Phase 1: DuckDB SQL feature pipeline & parquet exports")
    run_step([py, "src/analysis.py"], "Phase 2: Statistical modeling, CIs, regressions & figures")
    run_step([py, "src/generate_docs.py"], "Phase 4: Programmatic documentation generation from results.json")

    print("\n" + "=" * 60)
    print("✅ Full pipeline complete! All results in results/ and docs/")
    print("=" * 60)


if __name__ == "__main__":
    main()
