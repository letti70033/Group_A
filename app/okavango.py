import requests
import geopandas as gpd
import pandas as pd
from pathlib import Path
from pydantic import validate_call

DATASETS = [
    "https://ourworldindata.org/grapher/annual-change-forest-area.csv",  # Annual Change in forest area
    "https://ourworldindata.org/grapher/annual-deforestation.csv",  # Annual deforestation
    "https://ourworldindata.org/grapher/terrestrial-protected-areas.csv",  # Share of land that is protected
    "https://ourworldindata.org/grapher/share-degraded-land.csv",  # Share of land that is degraded
    "https://ourworldindata.org/grapher/forest-area-as-share-of-land-area.csv",  # 5th dataset
    "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip",  # Map dataset
]


class OkavangoData:
    # Integrate Functions 1 and 2 in your class: During the __init__ method, both functions are executed.
    def __init__(self) -> None:
        """Initializes the class by downloading and merging all datasets."""
        self.download_dir = Path("downloads")
        self.download_dir.mkdir(exist_ok=True)

        # Function 1: download all datasets into downloads/
        for url in DATASETS:
            self.download_dataset(url)

        # Read datasets into corresponding dataframes (attributes)
        self.forest_change = pd.read_csv(self.download_dir / "annual-change-forest-area.csv")
        self.deforestation = pd.read_csv(self.download_dir / "annual-deforestation.csv")
        self.land_protected = pd.read_csv(self.download_dir / "terrestrial-protected-areas.csv")
        self.land_degraded = pd.read_csv(self.download_dir / "share-degraded-land.csv")
        self.forest_cover = pd.read_csv(self.download_dir / "forest-area-as-share-of-land-area.csv")

        # Function 2: merge map with datasets
        self.merge_with_map()

    # Function 1: download a single dataset into downloads/
    @validate_call #validates that url is a proper string at runtime
    
    def download_dataset(self, url: str) -> None:
        """Downloads a single dataset from the given URL and stores it in the downloads/ directory.
            If the file already exists, the download is skipped.
            
            Parameters
            ----------
            url : str
            The URL of the dataset to download."""
        
        filename = url.split("/")[-1]
        filepath = self.download_dir / filename

        #before downloading, checks if the file is already in downloads/. If yes, skips it. So the app doesn't re-download everything from scratch on every restart.
        if filepath.exists():
            print(f"Already exists, skipping: {filename}")
            return

        try:
            print(f"Downloading {filename}...")
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
            response.raise_for_status()
            filepath.write_bytes(response.content)
            print(f"Saved {filename}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download {filename}: {e}")
            raise

    # Function 2: merge the world map with our datasets
    def merge_with_map(self) -> None:
        """
    Merges all downloaded datasets with the Natural Earth world map
    using ISO3 country codes.

    The method:
    - Loads the world shapefile (Natural Earth dataset)
    - Cleans missing ISO3 codes
    - Performs left joins between the map and each dataset
    - Creates GeoDataFrame attributes for visualization

    Raises
    ------
    Exception
        If merging fails for any reason.
    """
    
        try:
            world = gpd.read_file(self.download_dir / "ne_110m_admin_0_countries.zip")

            # Natural Earth uses "-99" when ISO3 is missing
            world["ADM0_A3"] = world["ADM0_A3"].replace("-99", pd.NA)

            # Merge using ISO3 codes (more reliable than country names)
            self.geo_forest_change = world.merge(self.forest_change, left_on="ADM0_A3", right_on="Code", how="left")
            self.geo_deforestation = world.merge(self.deforestation, left_on="ADM0_A3", right_on="Code", how="left")
            self.geo_land_protected = world.merge(self.land_protected, left_on="ADM0_A3", right_on="Code", how="left")
            self.geo_land_degraded = world.merge(self.land_degraded, left_on="ADM0_A3", right_on="Code", how="left")
            self.geo_forest_cover = world.merge(self.forest_cover, left_on="ADM0_A3", right_on="Code", how="left")

        except Exception as e:
            print(f"Failed to merge datasets: {e}")
            raise


# only run the code when the file is executed directly, not when imported
if __name__ == "__main__":
    data = OkavangoData()
    print("Done!")