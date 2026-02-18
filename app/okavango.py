import os
import requests
import geopandas as gpd
import pandas as pd

DATASETS = [
    "https://ourworldindata.org/grapher/annual-change-forest-area.csv",#[Anual Change in forest area]
    "https://ourworldindata.org/grapher/annual-deforestation.csv",#[Annual deforestation]
    "https://ourworldindata.org/grapher/terrestrial-protected-areas.csv",#[Share of land that is protected]
    "https://ourworldindata.org/grapher/share-degraded-land.csv",#[Share of land that is degraded]
    "https://ourworldindata.org/grapher/forest-area-as-share-of-land-area.csv", #[A fifth dataset you find relevant]
    "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip", #Map dataset
]
class OkavangoData:
    
    #Integrate Functions 1 and 2 in your class: During the _init_ method, both functions are execured.
    def __init__(self) -> None:
        """Initializes the class by downloading and merging all datasets."""
        self.download_dir = "downloads"
        os.makedirs(self.download_dir, exist_ok=True)

        for url in DATASETS:
            self.download_dataset(url) #function 1 called

        # The _init_ method must also read the datasets into corresponding dataframes which become attributes for your class.
        self.forest_change = pd.read_csv(f"{self.download_dir}/annual-change-forest-area.csv")
        self.deforestation = pd.read_csv(f"{self.download_dir}/annual-deforestation.csv")
        self.land_protected = pd.read_csv(f"{self.download_dir}/terrestrial-protected-areas.csv")
        self.land_degraded = pd.read_csv(f"{self.download_dir}/share-degraded-land.csv")
        self.forest_cover = pd.read_csv(f"{self.download_dir}/forest-area-as-share-of-land-area.csv")

        self.geo_df = self.merge_with_map() #function 2 called

    #function 1: Downloads a single dataset into the downloads directory.
    def download_dataset(self, url: str) -> None:
        filename = url.split("/")[-1]  # extracts filename from URL
        filepath = os.path.join(self.download_dir, filename)
        try:
            print(f"Downloading {filename}...")
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()  # raises an error if status code is 4xx or 5xx
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"Saved {filename}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download {filename}: {e}")
    
    #fucntion2: then merge the world map with our datasets
    def merge_with_map(self) -> gpd.GeoDataFrame:
        try:
            world = gpd.read_file(f"{self.download_dir}/ne_110m_admin_0_countries.zip")
            # Merge with all datasets
            merged = world.merge(self.forest_change, left_on="NAME", right_on="Entity", how="left", suffixes=('', '_forest'))
            merged = merged.merge(self.deforestation, left_on="NAME", right_on="Entity", how="left", suffixes=('', '_deforest'))
            merged = merged.merge(self.land_protected, left_on="NAME", right_on="Entity", how="left", suffixes=('', '_protected'))
            merged = merged.merge(self.land_degraded, left_on="NAME", right_on="Entity", how="left", suffixes=('', '_degraded'))
            merged = merged.merge(self.forest_cover, left_on="NAME", right_on="Entity", how="left", suffixes=('', '_cover'))
        
            return merged
        except Exception as e:
            print(f"Failed to merge datasets: {e}")
            raise

if __name__ == "__main__":
    data = OkavangoData()
    print("Done!")
