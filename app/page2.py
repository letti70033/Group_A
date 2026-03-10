import streamlit as st
import requests
import ollama
from pathlib import Path

def show_page2():
    st.title("AI Environmental Risk Assessment")
    
    st.subheader("Select a Location")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=0.0, step=0.01)
    with col2:
        longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=0.0, step=0.01)
    with col3:
        zoom = st.slider("Zoom", min_value=1, max_value=19, value=12)
    
    run = st.button("Analyse Area")

    if run:
        # --- Step 2: Fetch satellite image ---
        image_dir = Path("images")
        image_dir.mkdir(exist_ok=True)
        image_path = image_dir / f"{latitude}_{longitude}_{zoom}.png"

        if not image_path.exists():
            import math
            lat_rad = math.radians(latitude)
            n = 2 ** zoom
            x_tile = int((longitude + 180.0) / 360.0 * n)
            y_tile = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)

            url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y_tile}/{x_tile}"
            response = requests.get(url)
            image_path.write_bytes(response.content)
            st.success("Satellite image downloaded!")
        else:
            st.info("Image already exists locally, skipping download.")

        st.image(str(image_path), caption=f"Lat: {latitude}, Lon: {longitude}, Zoom: {zoom}")

        # --- Step 3: LLaVA image description ---
        st.subheader("AI Image Description")

        with st.spinner("Analysing image with LLaVA... this may take a minute."):
            ollama.pull("llava")

            with open(image_path, "rb") as f:
                image_bytes = f.read()

            response = ollama.chat(
                model="llava",
                messages=[{
                    "role": "user",
                    "content": "Describe what you see in this satellite image in detail. Focus on land cover, vegetation, urban areas, water bodies, and any visible environmental features.",
                    "images": [image_bytes]
                }]
            )

        image_description = response["message"]["content"]
        st.write(image_description)

        # --- Step 4: Mistral risk assessment ---
        st.subheader("Environmental Risk Assessment")

        with st.spinner("Assessing environmental risk with Mistral..."):
            ollama.pull("mistral")

            risk_prompt = f"""Based on this satellite image description, answer the following questions with YES or NO and a brief explanation:
            1. Is there visible deforestation or loss of vegetation?
            2. Are there signs of urban sprawl or land degradation?
            3. Is there evidence of water pollution or drought?
            4. Does this area appear to be at environmental risk overall?

            Description: {image_description}
            
            End your response with a single line that says either DANGER or SAFE."""

            risk_response = ollama.chat(
                model="mistral",
                messages=[{
                    "role": "user",
                    "content": risk_prompt
                }]
            )

        risk_text = risk_response["message"]["content"]
        st.write(risk_text)

        # --- Visual risk indicator ---
        if "DANGER" in risk_text.upper():
            st.error("⚠️ This area has been flagged as AT ENVIRONMENTAL RISK")
        else:
            st.success("✅ This area appears to be SAFE")