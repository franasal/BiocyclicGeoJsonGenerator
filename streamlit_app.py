import streamlit as st
import pandas as pd
import json
import os
from io import StringIO, BytesIO
from dotenv import load_dotenv

# Load password from environment
load_dotenv()
PASSWORD = os.getenv("APP_PASSWORD")

# --- Password protection ---
def check_password():
    def password_entered():
        if st.session_state["password"] == PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter password", type="password", on_change=password_entered, key="password")
        st.error("Incorrect password")
        return False
    else:
        return True

# --- GeoJSON generator ---
def create_feature(row, lon, lat, icon_url, certified_status):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "properties": {
            "name": row['Title'],
            "iconUrl": icon_url,
            "iconSize": [40, 60],
            "certified": certified_status,
            "website": row.get('Website', ''),
            "email": row.get('Email', ''),
            "social": row.get('Social Network', ''),
            "certifications": row.get('Certifications', ''),
            "certification_status": row.get('Certification Status', '').lower(),
            "description": row.get('Description', '')
        }
    }

def generate_geojson(excel_file):
    xls = pd.ExcelFile(excel_file, engine='openpyxl')
    sheet_names = xls.sheet_names
    second_sheet_name = sheet_names[1]
    df = pd.read_excel(xls, sheet_name=second_sheet_name).fillna("")

    certified_features = []
    non_certified_features = []

    for _, row in df.iterrows():
        lon, lat = row['Coordinates Lon'], row['Coordinates Lat']

        try:
            lon, lat = float(lon), float(lat)
        except ValueError:
            continue  # Skip invalid coordinates

        cert_status = row['Certification Status'].lower()

        if cert_status == 'certified':
            icon_url = "https://www.biocyclic-vegan.org/wp-content/uploads/2022/11/WEB__EN_Biocyclic_Vegan_Agriculture_green_white-background_-201x300.png"
            certified_features.append(
                create_feature(row, lon, lat, icon_url, "yes")
            )
        else:
            icon_url = "https://www.biocyclic-vegan.org/wp-content/uploads/2022/11/WEB__EN_Biocyclic_Vegan_Agriculture_red_white-background_-201x300.png"
            non_certified_features.append(
                create_feature(row, lon, lat, icon_url, cert_status)
            )

    geojson1 = {"type": "FeatureCollection", "features": certified_features}
    geojson2 = {"type": "FeatureCollection", "features": non_certified_features}

    return geojson1, geojson2

# --- Streamlit app ---
if check_password():
    st.title("Excel to GeoJSON Converter")

    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

    if uploaded_file:
        st.success("File uploaded successfully.")
        st.info("Processing file...")

        try:
            geojson_certified, geojson_non_certified = generate_geojson(uploaded_file)

            # Convert to string buffers
            buffer1 = StringIO()
            json.dump(geojson_certified, buffer1, ensure_ascii=False, indent=2)
            buffer1.seek(0)

            buffer2 = StringIO()
            json.dump(geojson_non_certified, buffer2, ensure_ascii=False, indent=2)
            buffer2.seek(0)

            st.download_button(
                label="Download Certified GeoJSON",
                data=buffer1,
                file_name="certified_certifications.geojson",
                mime="application/geo+json"
            )

            st.download_button(
                label="Download Non-Certified GeoJSON",
                data=buffer2,
                file_name="non_certified_certifications.geojson",
                mime="application/geo+json"
            )

            st.success("Files generated successfully!")

        except Exception as e:
            st.error(f"❌ Error processing file: {e}")
