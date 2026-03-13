import streamlit as st
import plotly.express as px
import pandas as pd
from okavango import OkavangoData
from page2 import show_page2

@st.cache_resource
def load_data() -> OkavangoData:
    return OkavangoData()

# Sidebar
st.sidebar.title("Okavango Dashboard")
st.sidebar.markdown("*Tracking Our Planet's Green Cover*")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    ["Page 1 - Analysis", "Page 2 - AI Risk Assessment"],
    label_visibility="collapsed",
)

st.sidebar.divider()
st.sidebar.markdown(
    "**Data sources**\n\n"
    "[Our World in Data](https://ourworldindata.org) · "
    "[Natural Earth](https://naturalearthdata.com)\n\n"
    "**Group A** · Advanced Programming\n\n"
    "Nova SBE · 2026"
)

if page == "Page 1 - Analysis":

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

    # Dataset descriptions: what the indicator shows and what high/low means
    dataset_descriptions = {
        "Annual Change in Forest Area": (
            "Measures how much forest area (in hectares) a country gained or lost each year. "
            "A **high value** means significant forest growth or reforestation. "
            "A **low (negative) value** means large-scale forest loss."
        ),
        "Annual Deforestation": (
            "Tracks the total area of forest cleared per year, in hectares. "
            "A **high value** means heavy deforestation. "
            "A **low value** means little to no forest is being cleared."
        ),
        "Forest Area as Share of Land": (
            "Shows what percentage of a country's total land area is covered by forest. "
            "A **high value** means the country is heavily forested. "
            "A **low value** means most land is non-forested (urban, agricultural, or arid)."
        ),
        "Share of Degraded Land": (
            "Estimates the proportion of land that has lost productivity due to degradation. "
            "A **high value** means a large share of land is degraded — a serious environmental concern. "
            "A **low value** means most land remains productive and healthy."
        ),
        "Terrestrial Protected Areas": (
            "Shows what percentage of a country's land is under formal environmental protection. "
            "A **high value** means strong conservation efforts. "
            "A **low value** means little land is protected from development."
        ),
    }

    st.title("Okavango Dashboard — Tracking Our Planet's Green Cover")
    st.markdown(
        "*This tool tracks how the world's forests, protected areas, and land conditions are changing over time. "
        "Explore five global datasets by country and year, then use the AI Risk Assessment page to analyse "
        "any location on Earth via satellite imagery.*"
    )

    # --- Dataset selector ---
    selected = st.selectbox("Select a dataset", options=list(datasets.keys()))

    geo_df, raw_df, column = datasets[selected]

    # --- Dataset description ---
    st.info(dataset_descriptions[selected])

    # --- Year slider ---
    available_years = sorted(geo_df["Year"].dropna().unique().astype(int).tolist())
    selected_year = st.select_slider("Select year", options=available_years, value=max(available_years))

    # Filter to real countries only (3-letter ISO code, excludes World/Africa/etc.)
    raw_countries = raw_df[raw_df["Code"].str.len() == 3].copy() if "Code" in raw_df.columns else raw_df.copy()
    df_year_countries = raw_countries[raw_countries["Year"] == selected_year].dropna(subset=[column])

    # --- KPIs (driven by selected dataset + year) ---
    if not df_year_countries.empty:
        top_row = df_year_countries.loc[df_year_countries[column].idxmax()]
        bottom_row = df_year_countries.loc[df_year_countries[column].idxmin()]
        n_countries = len(df_year_countries)
        top_val = top_row[column]
        bottom_val = bottom_row[column]

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Countries with data", n_countries)
        k2.metric("Highest value", top_row["Entity"], f"{top_val:,.1f}")
        k3.metric("Lowest value", bottom_row["Entity"], f"{bottom_val:,.1f}")
        k4.metric("Selected year", selected_year)

    # --- Interactive choropleth map (plotly) ---
    st.subheader(f"{selected} — {selected_year}")

    # Session state key scoped to selected dataset so switching datasets resets the selection
    multiselect_key = f"countries_{selected}"

    # Build country list for the time series (used later)
    countries_df = raw_countries.copy()
    country_list = sorted(countries_df["Entity"].unique().tolist())

    # Default selection: top 3 countries by value for the selected year
    top3_codes: list[str] = []
    if not df_year_countries.empty:
        top3 = df_year_countries.nlargest(3, column)
        top3_codes = top3["Code"].tolist()

    default_countries = (
        countries_df[
            countries_df["Code"].isin(top3_codes) &
            (countries_df["Year"] == selected_year)
        ]["Entity"].tolist()
    )

    # Initialise session state for this dataset (reset when dataset changes)
    if multiselect_key not in st.session_state:
        st.session_state[multiselect_key] = default_countries

    # Build plotly choropleth from raw country data
    fig = px.choropleth(
        df_year_countries,
        locations="Code",
        locationmode="ISO-3",
        color=column,
        hover_name="Entity",
        color_continuous_scale="YlGn",
        labels={column: column},
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title=""),
        geo=dict(showframe=False, showcoastlines=True),
    )

    st.caption("Click a country on the map to add it to the time series below.")
    # on_select="rerun" triggers a rerun when user clicks a country
    map_event = st.plotly_chart(fig, on_select="rerun", selection_mode="points", use_container_width=True)

    # If a country was clicked, add it to the time series selection
    if map_event and map_event.selection and map_event.selection.points:
        clicked_code = map_event.selection.points[0].get("location")
        if clicked_code:
            match = countries_df[countries_df["Code"] == clicked_code]["Entity"]
            if not match.empty:
                clicked_entity = match.iloc[0]
                current = st.session_state[multiselect_key]
                if clicked_entity in country_list and clicked_entity not in current:
                    st.session_state[multiselect_key] = current + [clicked_entity]
                    st.rerun()

    # --- Bar chart: top 5 and bottom 5 countries ---
    df_map_sorted = df_year_countries.sort_values(column)
    n_each = min(5, len(df_map_sorted) // 2)

    if n_each >= 1:
        import plotly.graph_objects as go
        bottom_n = df_map_sorted.head(n_each)
        top_n = df_map_sorted.tail(n_each)
        combined = pd.concat([bottom_n, top_n])
        colors = ["#de2d26"] * n_each + ["#2ca25f"] * n_each

        st.subheader(f"Top {n_each} and Bottom {n_each} Countries — {selected_year}")
        fig2 = go.Figure(go.Bar(
            x=combined[column],
            y=combined["Entity"],
            orientation="h",
            marker_color=colors,
        ))
        fig2.add_vline(x=0, line_color="black", line_width=1, line_dash="dash")
        fig2.update_layout(
            xaxis_title=column,
            yaxis_title="",
            margin=dict(l=0, r=0, t=20, b=0),
            height=max(250, n_each * 50),
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Not enough country data to display the bar chart.")

    # --- Time series ---
    st.subheader(f"{selected} over time")
    st.caption("Click a country on the map above to add it here, or select manually.")

    # Filter session state to valid countries in current list
    valid_defaults = [c for c in st.session_state[multiselect_key] if c in country_list]
    if valid_defaults != st.session_state[multiselect_key]:
        st.session_state[multiselect_key] = valid_defaults

    selected_countries: list[str] = st.multiselect(
        "Select countries",
        options=country_list,
        key=multiselect_key,
    )

    if selected_countries:
        import plotly.graph_objects as go
        fig3 = go.Figure()
        for country in selected_countries:
            series = (
                countries_df[countries_df["Entity"] == country]
                .sort_values("Year")
                .dropna(subset=[column])
            )
            fig3.add_trace(go.Scatter(
                x=series["Year"], y=series[column],
                mode="lines+markers", name=country,
                marker=dict(size=4),
            ))
        fig3.update_layout(
            xaxis_title="Year",
            yaxis_title=column,
            legend_title="Country",
            margin=dict(l=0, r=0, t=20, b=0),
            height=400,
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Select at least one country to display the time series.")

elif page == "Page 2 - AI Risk Assessment":
    show_page2()

# Run with: streamlit run app/streamlit_app.py
