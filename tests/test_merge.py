import geopandas as gpd
import pandas as pd
from pathlib import Path
from shapely.geometry import Point

from app.okavango import OkavangoData


def test_merge_with_map_creates_geodataframes(monkeypatch):
    """
    Test Function 2: merge_with_map
    Ensures GeoDataFrames are created with geometry column.
    """

    # Fake world GeoDataFrame
    world = gpd.GeoDataFrame(
        {
            "ADM0_A3": ["PRT"],
            "geometry": [Point(0, 0)]
        },
        geometry="geometry",
        crs="EPSG:4326"
    )

    # Mock geopandas.read_file
    monkeypatch.setattr(gpd, "read_file", lambda path: world)

    # Create instance without running __init__
    data = OkavangoData.__new__(OkavangoData)
    data.download_dir = Path("downloads")

    # Minimal fake datasets
    df = pd.DataFrame({
        "Code": ["PRT"],
        "Year": [2020],
        "Value": [1]
    })

    data.forest_change = df
    data.deforestation = df
    data.land_protected = df
    data.land_degraded = df
    data.forest_cover = df

    data.merge_with_map()

    assert isinstance(data.geo_forest_change, gpd.GeoDataFrame)
    assert "geometry" in data.geo_forest_change.columns
    assert "Code" in data.geo_forest_change.columns