import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from okavango import OkavangoData


@st.cache_resource
def load_data() -> OkavangoData:
    return OkavangoData()


data = load_data()

# geo dataframes (for the map) and raw dataframes (for the time series)
datasets = {
    "Annual Change in Forest Area": (
        data.geo_forest_change, data.forest_change, "Annual change in forest area"
    ),
    "Annual Deforestation": (
        data.geo_deforestation, data.deforestation, "Deforestation"
    ),
    "Forest Area as Share of Land": (
        data.geo_forest_cover, data.forest_cover, "Share of land covered by forest"
    ),
    "Share of Degraded Land": (
        data.geo_land_degraded, data.land_degraded,
        "Proportion of land that is degraded over total land area (%)"
    ),
    "Terrestrial Protected Areas": (
        data.geo_land_protected, data.land_protected,
        "Terrestrial protected areas (% of total land area)"
    ),
}

st.title("Project Okavango — Forests, Deforestation, and Land Coverage")

selected = st.selectbox("Select a dataset", options=list(datasets.keys()))

geo_df, raw_df, column = datasets[selected]

# most recent year only
latest_year = int(geo_df["Year"].max())
df_latest = geo_df[geo_df["Year"] == latest_year].copy()

st.subheader(f"{selected} — {latest_year}")

# World map
fig, ax = plt.subplots(1, 1, figsize=(15, 8))
df_latest.plot(column=column, ax=ax, legend=True, cmap="YlGn", missing_kwds={"color": "lightgrey"})
ax.set_axis_off()
st.pyplot(fig)

# Bar chart: top 5 and bottom 5 countries
df_valid = (
    df_latest[["ADM0_A3", "NAME", column]]
    .dropna(subset=[column])
    .sort_values(column)
)

n_each = min(5, len(df_valid) // 2)
top3_codes: list[str] = []

if n_each >= 1:
    bottom_n = df_valid.head(n_each)
    top_n = df_valid.tail(n_each)
    top3_codes = top_n.tail(3)["ADM0_A3"].tolist()
    combined = pd.concat([bottom_n, top_n])
    colors = ["#de2d26"] * n_each + ["#2ca25f"] * n_each

    st.subheader(f"Top {n_each} and Bottom {n_each} Countries — {latest_year}")
    fig2, ax2 = plt.subplots(figsize=(10, max(4, n_each * 0.8)))
    ax2.barh(combined["NAME"], combined[column], color=colors)
    ax2.set_xlabel(column)
    ax2.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax2.axhline(n_each - 0.5, color="black", linewidth=1.2, linestyle="--", alpha=0.5)
    plt.tight_layout()
    st.pyplot(fig2)
else:
    st.info("Not enough country data to display the bar chart.")

# Time series
st.subheader(f"{selected} over time")

# Only rows with an ISO code (excludes continental/world aggregates)
countries_df = raw_df.dropna(subset=["Code"]).copy()
country_list = sorted(countries_df["Entity"].unique().tolist())

# Default: the top 3 countries shown in the bar chart above (matched by ISO code)
default_countries = (
    countries_df[
        countries_df["Code"].isin(top3_codes) &
        (countries_df["Year"] == latest_year)
    ]["Entity"]
    .tolist()
)

selected_countries = st.multiselect(
    "Select countries",
    options=country_list,
    default=default_countries,
)

if selected_countries:
    fig3, ax3 = plt.subplots(figsize=(12, 5))
    for country in selected_countries:
        series = (
            countries_df[countries_df["Entity"] == country]
            .sort_values("Year")
        )
        ax3.plot(series["Year"], series[column], marker="o", markersize=3, label=country)
    ax3.set_xlabel("Year")
    ax3.set_ylabel(column)
    ax3.legend()
    plt.tight_layout()
    st.pyplot(fig3)
else:
    st.info("Select at least one country to display the time series.")

# Run with: streamlit run app/streamlit_app.py
