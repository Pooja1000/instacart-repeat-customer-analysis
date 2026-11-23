# run.ps1 - PowerShell equivalent of `make run`
# Runs tests, SQL pipeline, analysis, and document generation.

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "▶ Running automated tests" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
python -m pytest tests/ -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "▶ Phase 0: Data reality check" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
python src/generate_phase0_results.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "▶ Phase 1: DuckDB SQL feature pipeline" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
python src/run_pipeline.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "▶ Phase 2: Statistical analysis & figures" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
python src/analysis.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "▶ Phase 4: Generate docs from results.json" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
python src/generate_docs.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "✅ Full pipeline complete! All results in results/ and docs/" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
