# QUANTEDGE AI: Trading Intelligence Terminal (DEMO)

Desktop frontend built with Python, CustomTkinter, Matplotlib, Pandas, NumPy, SQLite and Pillow. Free and open-source only.

**All prices, signals and analytics shown are synthetic DEMO data, not real market information or advice.**

## Run
```
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
Linux needs Tk: `sudo apt install python3-tk`. Headless check of all 10 screens: `python main.py --selftest`.

## Screens
Overview · Live Markets · AI Signals · Strategy Lab · Backtesting · Portfolio · Risk Analytics · Market Research · Reports · Settings

## Data
Local state lives in `quantedge.db` (settings, positions, strategies, notes). Reports export to `exports/`.
To use your own prices, set a CSV folder in Settings: files `SYMBOL.csv` with `Date,Open,High,Low,Close,Volume`.
