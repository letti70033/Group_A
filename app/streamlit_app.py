import streamlit as st
import matplotlib.pyplot as plt
from okavango import OkavangoData

data = OkavangoData()

# mapping names to the actual dataframe attributes
datasets = {
    "Annual Change in Forest Area": (data.geo_forest_change, "Annual change in forest area"),
    "Annual Deforestation": (data.geo_deforestation, "Deforestation"),
    "Forest Area as Share of Land": (data.geo_forest_cover, "Share of land covered by forest"),
    "Share of Degraded Land": (data.geo_land_degraded, "Proportion of land that is degraded over total land area (%)"),
    "Terrestrial Protected Areas": (data.geo_land_protected, "Terrestrial protected areas (% of total land area)"),
}

st.title("Project Okavango - Get to know more about Forests, Deforestation, and Coverages of Land ")

selected = st.selectbox("Select a dataset", options=list(datasets.keys()))

df, column = datasets[selected]

# most recent year only
latest_year = df["Year"].max()
df_latest = df[df["Year"] == latest_year]

st.subheader(f"{selected} — {int(latest_year)}")

fig, ax = plt.subplots(1, 1, figsize=(15, 8))
df_latest.plot(column=column, ax=ax, legend=True, cmap="YlGn", missing_kwds={"color": "lightgrey"})
ax.set_axis_off()
st.pyplot(fig)



## always run with #streamlit run app/streamlit_app.py# in terminal !!!