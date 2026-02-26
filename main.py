from app.okavango import OkavangoData

#instantiates OkavangoData and prints a basic summary of each dataset (row count + latest year)
def main() -> None:
    """Download all datasets, merge with the world map, and print a basic summary."""
    data = OkavangoData()

    summary = {
        "forest_change": data.forest_change,
        "deforestation": data.deforestation,
        "land_protected": data.land_protected,
        "land_degraded": data.land_degraded,
        "forest_cover": data.forest_cover,
    }

    for name, df in summary.items():
        latest = int(df["Year"].max())
        print(f"{name}: {len(df)} rows, latest year = {latest}")

    print("All datasets loaded and merged successfully.")


if __name__ == "__main__":
    main()
