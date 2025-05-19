import streamlit as st
import pandas as pd
import json
import time
import traceback
import hashlib
from io import BytesIO
import zipfile

# --- Load password from environment (.env or Streamlit secrets) ---
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
        
# --- GEOJSON FUNCTIONS ---
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

def generate_geojson(uploaded_file):
    xls = pd.ExcelFile(uploaded_file, engine='openpyxl')
    second_sheet = xls.sheet_names[1]
    df = pd.read_excel(xls, sheet_name=second_sheet).fillna("")

    certified_features = []
    non_certified_features = []
    warnings = []

    for _, row in df.iterrows():
        lon, lat = row['Coordinates Lon'], row['Coordinates Lat']
        try:
            lon, lat = float(lon), float(lat)
        except ValueError:
            warnings.append(f"⚠️ Invalid coordinates for '{row['Title']}' ({row['Address']}). Skipped.")
            continue

        cert_status = row['Certification Status'].lower()

        if cert_status == 'certified':
            icon_url = "https://www.biocyclic-vegan.org/wp-content/uploads/2022/11/WEB__EN_Biocyclic_Vegan_Agriculture_green_white-background_-201x300.png"
            certified_status = "yes"
            certified_features.append(
                create_feature(row, lon, lat, icon_url, certified_status)
            )
        else:
            icon_url = "https://www.biocyclic-vegan.org/wp-content/uploads/2022/11/WEB__EN_Biocyclic_Vegan_Agriculture_red_white-background_-201x300.png"
            non_certified_features.append(
                create_feature(row, lon, lat, icon_url, cert_status)
            )

        time.sleep(1)

    geojson_certified = {"type": "FeatureCollection", "features": certified_features}
    geojson_non_certified = {"type": "FeatureCollection", "features": non_certified_features}

    return geojson_certified, geojson_non_certified, warnings

def create_zip(geojson1, geojson2):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("certified.geojson", json.dumps(geojson1, indent=2, ensure_ascii=False))
        zip_file.writestr("non_certified.geojson", json.dumps(geojson2, indent=2, ensure_ascii=False))
    zip_buffer.seek(0)
    return zip_buffer

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="GeoJSON Generator", page_icon="🌍")
    st.title("🌱 Biozyklisch-Vegan GeoJSON Generator")

    if not check_password():
        st.stop()

    uploaded_file = st.file_uploader("Upload your Excel file (.xlsx)", type=["xlsx"])

    if uploaded_file is not None:
        st.success("✅ File uploaded. Click 'Process' to continue.")

        if st.button("🚀 Process File"):
            try:
                geojson_certified, geojson_non_certified, warnings = generate_geojson(uploaded_file)
                zip_buffer = create_zip(geojson_certified, geojson_non_certified)

                st.session_state["zip_buffer"] = zip_buffer
                st.session_state["warnings"] = warnings
                st.session_state["processed"] = True

                st.success("🎉 Files generated and packed into ZIP!")

            except Exception:
                st.error("❌ An error occurred during processing.")
                st.code(traceback.format_exc())

    if st.session_state.get("processed"):
        if st.session_state.get("warnings"):
            st.warning("Some entries were skipped:")
            for warn in st.session_state["warnings"]:
                st.markdown(f"- {warn}")

        st.download_button(
            label="⬇ Download GeoJSON ZIP Archive",
            data=st.session_state["zip_buffer"],
            file_name="biozyklisch_vegan_certifications.zip",
            mime="application/zip"
        )

if __name__ == "__main__":
    main()
