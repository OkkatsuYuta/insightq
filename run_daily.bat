@echo off
cd C:\Users\siddh\OneDrive\Desktop\insightq_vrndr
call .venv\Scripts\activate
python -m scripts.fetch_companies
python -m scripts.fetch_results
python -m scripts.fetch_bulk_filings
git add data/earnings_tracker.db
git commit -m "auto: daily data update"
git push origin main