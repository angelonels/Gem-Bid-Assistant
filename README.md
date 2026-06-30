# GeM Bid Assistant

This project helps a seller check a GeM tender before placing a bid.

The app can:

- collect live tenders and past award data from GeM,
- read tender requirements with Groq,
- check whether a vendor meets those requirements,
- estimate the winning L1 price,
- estimate the chance of winning at a chosen bid price.

The app uses AI only to read tender text. All checks and calculations are done
with normal Python code.

## Main Tools

- Python 3.12
- `uv`
- Streamlit
- Playwright
- Groq
- Pydantic
- pandas and NumPy
- pytest and Ruff

## Project Layout

```text
app/
  streamlit_app.py       # Streamlit app
scripts/
  collect_live_data.py   # Downloads GeM data
src/procurement/
  modules/
    data_pipeline/       # Collects and saves data
    compliance/          # Reads and checks tender rules
    pricing/             # Predicts the L1 price
    probability/         # Calculates win probability
    orchestration/       # Runs all steps together
  shared/                # Common settings and helpers
tests/                   # Automated tests
LEARN.md                 # Detailed code guide
```

## Setup

Install the project:

```bash
uv sync
uv run playwright install chromium
```

Create the environment file:

```bash
cp .env.example .env
```

Open `.env` and add your Groq API key:

```dotenv
GROQ_API_KEY=your_key_here
```

The app still works without a Groq key. It uses a simple text parser instead.

## Collect GeM Data

```bash
uv run python scripts/collect_live_data.py
```

This saves tender details, tender documents, and past award data inside
`data/cache/`.

The repository already contains cached data, so this step is optional when
testing the app.

## Run the App

```bash
uv run streamlit run app/streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501).

Choose a tender, choose a vendor, enter a bid amount, and press **Predict**.

## Run the Tests

```bash
uv run pytest
```

Check formatting and code quality:

```bash
uv run ruff format --check
uv run ruff check
```
