.PHONY: run db test clean

# Run the full pipeline: SQL → parquet → analysis
run: test
	python src/generate_phase0_results.py
	python src/run_pipeline.py
	python src/analysis.py
	@echo "✅ Full pipeline complete. Results in results/ and data/processed/"

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
