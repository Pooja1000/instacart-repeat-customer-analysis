.PHONY: run db test clean

# Run the full pipeline: tests → Phase 0 → SQL → analysis → docs
run: test
	python src/generate_phase0_results.py
	python src/run_pipeline.py
	python src/analysis.py
	python src/generate_docs.py
	@echo "✅ Full pipeline complete. Results in results/ and docs/"

# Run just the SQL pipeline and export
db:
	python src/run_pipeline.py

# Run tests
test:
	python -m pytest tests/ -v

# Clean processed data (keeps raw)
clean:
	rm -rf data/processed/*
	rm -f results/results.json
	rm -rf results/figures/*
