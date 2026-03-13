"""
page2.py — AI Environmental Risk Assessment (Day 2, Phase 1 + Phase 2)

Phase 1 (teammate): satellite image download, LLaVA image description,
                    Mistral risk assessment.
Phase 2 (data governance): configuration loaded from models.yaml,
                            every pipeline run logged to database/images.csv,
                            caching — cached results returned without
                            re-running the models.
"""

import logging
import math
from datetime import datetime
from pathlib import Path

import folium
import ollama
import pandas as pd
import requests
import streamlit as st
import yaml
from streamlit_folium import st_folium

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths  (relative to project root, where `streamlit run app/streamlit_app.py`
#         is executed)
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[1]
_CONFIG_PATH = _ROOT / "models.yaml"
_DATABASE_DIR = _ROOT / "database"
_DATABASE_PATH = _DATABASE_DIR / "images.csv"
_IMAGE_DIR = _ROOT / "images"

# CSV column order — must match database/images.csv header
_CSV_COLUMNS = [
    "timestamp",
    "latitude",
    "longitude",
    "zoom",
    "image_path",
    "image_prompt",
    "image_model",
    "image_description",
    "text_prompt",
    "text_model",
    "text_description",
    "danger",
]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Load AI workflow configuration from models.yaml.

    Returns
    -------
    dict
        Parsed YAML configuration.

    Raises
    ------
    FileNotFoundError
        If models.yaml is not found at the project root.
    """
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {_CONFIG_PATH}\n"
            "Ensure models.yaml is present in the project root."
        )
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    logger.info("Loaded configuration from %s", _CONFIG_PATH)
    return config


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _ensure_database() -> pd.DataFrame:
    """Ensure the database directory and CSV exist; return all existing records.

    Returns
    -------
    pd.DataFrame
        All previously logged pipeline runs (empty if none yet).
    """
    _DATABASE_DIR.mkdir(exist_ok=True)
    if not _DATABASE_PATH.exists():
        empty = pd.DataFrame(columns=_CSV_COLUMNS)
        empty.to_csv(_DATABASE_PATH, index=False)
        logger.info("Created new database at %s", _DATABASE_PATH)
        return empty
    return pd.read_csv(_DATABASE_PATH)


def _lookup_cache(
    db: pd.DataFrame,
    latitude: float,
    longitude: float,
    zoom: int,
) -> "pd.Series | None":
    """Return the most recent cached row for (latitude, longitude, zoom).

    Parameters
    ----------
    db : pd.DataFrame
        Full database loaded from images.csv.
    latitude : float
        Latitude of the requested location.
    longitude : float
        Longitude of the requested location.
    zoom : int
        Zoom level of the requested tile.

    Returns
    -------
    pd.Series or None
        Most recent matching row, or None if no cache entry exists.
    """
    matches = db[
        (db["latitude"] == latitude)
        & (db["longitude"] == longitude)
        & (db["zoom"] == zoom)
    ]
    if not matches.empty:
        return matches.iloc[-1]
    return None


def _append_to_database(record: dict) -> None:
    """Append one pipeline-run record to database/images.csv.

    Parameters
    ----------
    record : dict
        Keys must match _CSV_COLUMNS.
    """
    _DATABASE_DIR.mkdir(exist_ok=True)
    row = pd.DataFrame([record], columns=_CSV_COLUMNS)
    row.to_csv(
        _DATABASE_PATH,
        mode="a",
        header=not _DATABASE_PATH.exists(),
        index=False,
    )
    logger.info(
        "Logged to database: lat=%s lon=%s zoom=%s danger=%s",
        record["latitude"], record["longitude"], record["zoom"], record["danger"],
    )


# ---------------------------------------------------------------------------
# Satellite tile download
# ---------------------------------------------------------------------------

def _download_tile(
    latitude: float,
    longitude: float,
    zoom: int,
    tile_service: str,
) -> Path:
    """Download a satellite tile from ESRI World Imagery and save it locally.

    Parameters
    ----------
    latitude : float
        Latitude of the centre point.
    longitude : float
        Longitude of the centre point.
    zoom : int
        Zoom level (1–19).
    tile_service : str
        Base URL of the tile service.

    Returns
    -------
    Path
        Local path to the saved PNG image.
    """
    _IMAGE_DIR.mkdir(exist_ok=True)
    image_path = _IMAGE_DIR / f"{latitude}_{longitude}_{zoom}.png"

    if image_path.exists():
        logger.info("Tile already cached locally: %s", image_path)
        return image_path

    lat_rad = math.radians(latitude)
    n = 2 ** zoom
    x_tile = int((longitude + 180.0) / 360.0 * n)
    y_tile = int(
        (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi)
        / 2.0
        * n
    )
    url = f"{tile_service}/{zoom}/{y_tile}/{x_tile}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    image_path.write_bytes(response.content)
    logger.info("Downloaded satellite tile to %s", image_path)
    return image_path


# ---------------------------------------------------------------------------
# Shared display helper
# ---------------------------------------------------------------------------

def _display_results(
    image_path: Path,
    image_description: str,
    risk_text: str,
) -> None:
    """Render the satellite image, AI description, and risk indicator.

    Parameters
    ----------
    image_path : Path
        Local path to the tile image.
    image_description : str
        Text generated by the image model.
    risk_text : str
        Risk assessment text generated by the text model.
    """
    if image_path.exists():
        st.image(str(image_path))
    else:
        st.warning("Image file not found locally.")

    st.subheader("AI Image Description")
    st.write(image_description)

    st.subheader("Environmental Risk Assessment")
    st.write(risk_text)

    if "DANGER" in risk_text.upper():
        st.error("⚠️ This area has been flagged as AT ENVIRONMENTAL RISK")
    else:
        st.success("✅ This area appears to be SAFE")


# ---------------------------------------------------------------------------
# Main Streamlit page
# ---------------------------------------------------------------------------

def show_page2() -> None:
    """Render the AI Environmental Risk Assessment page.

    Workflow
    --------
    1. Load configuration from models.yaml.
    2. Accept user inputs: latitude, longitude, zoom.
    3. On "Analyse Area":
       - Cache hit  → display stored result immediately (no model calls).
       - Cache miss → download tile, run image model, run text model,
                      log to database/images.csv, display results.
    """
    st.title("Okavango AI Risk Assessment")
    st.markdown(
        "*Select any location on Earth by clicking the map or entering coordinates manually. "
        "A satellite image of the area will be analysed by an AI vision model, followed by an automated "
        "environmental risk assessment. Results are cached so repeated queries run instantly.*"
    )

    # --- Load config ---
    try:
        config = load_config()
    except FileNotFoundError as e:
        st.error(str(e))
        return

    img_cfg = config["image_model"]
    txt_cfg = config["text_model"]
    img_settings = config.get("image_settings", {})
    tile_service: str = img_settings.get(
        "tile_service",
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile",
    )
    default_zoom: int = img_settings.get("default_zoom", 12)

    # --- Location inputs ---
    st.subheader("Select a Location")
    st.caption("Click anywhere on the map to set the coordinates, or enter them manually below.")

    # Folium click map — satellite tiles from ESRI
    m = folium.Map(location=[20, 0], zoom_start=2, tiles=None)
    folium.TileLayer(
        tiles=f"{tile_service}/{{z}}/{{y}}/{{x}}",
        attr="Esri World Imagery",
        name="Satellite",
    ).add_to(m)
    map_data = st_folium(m, height=400, use_container_width=True)

    # Extract clicked coordinates (fall back to 0,0 if nothing clicked yet)
    clicked_lat = 0.0
    clicked_lon = 0.0
    if map_data and map_data.get("last_clicked"):
        clicked_lat = round(map_data["last_clicked"]["lat"], 4)
        clicked_lon = round(map_data["last_clicked"]["lng"], 4)

    col1, col2, col3 = st.columns(3)
    with col1:
        latitude = st.number_input(
            "Latitude", min_value=-90.0, max_value=90.0, value=clicked_lat, step=0.01
        )
    with col2:
        longitude = st.number_input(
            "Longitude", min_value=-180.0, max_value=180.0, value=clicked_lon, step=0.01
        )
    with col3:
        zoom = st.slider("Zoom", min_value=1, max_value=19, value=default_zoom)

    run = st.button("Analyse Area")

    if not run:
        return

    # --- Step 1: Check database cache ---
    db = _ensure_database()
    cached = _lookup_cache(db, latitude, longitude, zoom)

    if cached is not None:
        st.info("✅ Loaded from cache — this location was already analysed.")
        _display_results(
            image_path=_ROOT / str(cached["image_path"]),
            image_description=str(cached["image_description"]),
            risk_text=str(cached["text_description"]),
        )
        return

    # --- Step 2: Download satellite tile ---
    with st.spinner("Fetching satellite image..."):
        try:
            image_path = _download_tile(latitude, longitude, zoom, tile_service)
            st.success("Satellite image downloaded!")
        except Exception as e:
            st.error(f"Failed to download satellite image: {e}")
            logger.error("Tile download failed: %s", e)
            return

    # --- Step 3: Image description with model from config ---
    st.subheader("AI Image Description")
    image_prompt: str = img_cfg["prompt"]

    with st.spinner(f"Analysing image with {img_cfg['name']}… this may take a minute."):
        try:
            ollama.pull(img_cfg["name"])
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            img_response = ollama.chat(
                model=img_cfg["name"],
                messages=[{
                    "role": "user",
                    "content": image_prompt,
                    "images": [image_bytes],
                }],
            )
            image_description: str = img_response["message"]["content"]
        except Exception as e:
            st.error(f"Image model failed: {e}")
            logger.error("Image model error: %s", e)
            return

    # --- Step 4: Risk assessment with model from config ---
    st.subheader("Environmental Risk Assessment")
    text_prompt: str = txt_cfg["prompt"].replace("{description}", image_description)

    with st.spinner(f"Assessing environmental risk with {txt_cfg['name']}..."):
        try:
            ollama.pull(txt_cfg["name"])
            txt_response = ollama.chat(
                model=txt_cfg["name"],
                messages=[{"role": "user", "content": text_prompt}],
            )
            risk_text: str = txt_response["message"]["content"]
        except Exception as e:
            st.error(f"Text model failed: {e}")
            logger.error("Text model error: %s", e)
            return

    # --- Step 5: Log to database ---
    danger_flag = "Y" if "DANGER" in risk_text.upper() else "N"
    _append_to_database({
        "timestamp":         datetime.now().isoformat(timespec="seconds"),
        "latitude":          latitude,
        "longitude":         longitude,
        "zoom":              zoom,
        "image_path":        str(image_path.relative_to(_ROOT)),
        "image_prompt":      image_prompt,
        "image_model":       img_cfg["name"],
        "image_description": image_description,
        "text_prompt":       text_prompt,
        "text_model":        txt_cfg["name"],
        "text_description":  risk_text,
        "danger":            danger_flag,
    })

    # --- Step 6: Display results ---
    _display_results(image_path, image_description, risk_text)
