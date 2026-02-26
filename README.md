# Group_A — Project Okavango

**Group A · Advanced Programming for Data Science**

A lightweight Streamlit app for exploring environmental and land-use data: forests, deforestation, protected areas, and land degradation. Data is from [Our World in Data](https://ourworldindata.org) and is joined with a world map (Natural Earth) so you can compare countries on a map and in charts.

---

## What this project does

- **Downloads** the required datasets into a `downloads/` folder (and skips files that are already there).
- **Merges** the data with a world map (GeoDataFrames) so each indicator can be shown by country.
- **Streamlit app** where you can:
  - Choose one of five indicators and see a **world map** for the most recent year.
  - See a **bar chart** of the top 5 and bottom 5 countries for that indicator.
  - Explore a **time series** by selecting countries and viewing trends over time.

All years are taken from the data (no hardcoded dates).

---

## Data sources

| Dataset | Source |
|--------|--------|
| Annual change in forest area | Our World in Data |
| Annual deforestation | Our World in Data |
| Terrestrial protected areas (% of land) | Our World in Data |
| Share of degraded land | Our World in Data |
| Forest area as share of land area | Our World in Data |
| World map (Admin 0 – Countries) | Natural Earth (110m cultural) |

---

## Requirements

- Python 3.10+ (or 3.9+ with compatible packages)
- Dependencies: `streamlit`, `geopandas`, `pandas`, `requests`, `shapely`, `matplotlib`, `pydantic`

---

## Installation

From the project root:

```bash
# Optional: use a virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install streamlit geopandas pandas requests shapely matplotlib pydantic
```

---

## How to run

**Streamlit app (recommended):**

```bash
streamlit run app/streamlit_app.py
```

Or use the helper script (activates `venv` if present):

```bash
./run
```

The app will open in your browser. The first run downloads all datasets into `downloads/`; later runs reuse them.

**Command-line summary (no browser):**

```bash
python main.py
```

This loads all data, merges with the map, and prints a short summary (row counts and latest year per dataset).

**Tests:**

```bash
pytest
```

Run from the project root so that `app` and `tests` are on the path.

---

## Team

| Name    | Email (copy-paste friendly) |
|---------|-----------------------------|
| Leticia | 70033@novasbe.pt            |
| Marie   | 73606@novasbe.pt            |
| Philipp | 66323@novasbe.pt            |
| Alex    | 70299@novasbe.pt            |

---

## License

See [LICENSE](LICENSE).
