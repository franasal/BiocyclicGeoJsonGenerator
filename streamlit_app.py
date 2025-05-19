import streamlit as st
import pandas as pd
import json
import time
import traceback
import hashlib
from io import BytesIO

# --- PASSWORD AUTHENTICATION ---
def check_password():
    def password_entered():
        if hashlib.sha256(st.session_state["password"].encode()).hexdigest() == PASSWORD_HASH:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Incorrect password")
        return False
    else:
        return True

PASSWORD_HASH = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"

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

                # Convert to BytesIO and store in session
                buffer1 = BytesIO(json.dumps(geojson_certified, ensure_ascii=False, indent=2).encode("utf-8"))
                buffer2 = BytesIO(json.dumps(geojson_non_certified, ensure_ascii=False, indent=2).encode("utf-8"))

                st.session_state["buffer_certified"] = buffer1
                st.session_state["buffer_non_certified"] = buffer2
                st.session_state["warnings"] = warnings
                st.session_state["processed"] = True

                st.success("🎉 Files generated successfully!")

            except Exception:
                st.error("❌ An error occurred during processing.")
                st.code(traceback.format_exc())

    # If data is processed, show downloads
    if st.session_state.get("processed"):
        if st.session_state.get("warnings"):
            st.warning("Some entries were skipped:")
            for warn in st.session_state["warnings"]:
                st.markdown(f"- {warn}")

        st.download_button(
            label="⬇ Download Certified GeoJSON",
            data=st.session_state["buffer_certified"],
            file_name="certified_certifications.geojson",
            mime="application/geo+json"
        )

        st.download_button(
            label="⬇ Download Non-Certified GeoJSON",
            data=st.session_state["buffer_non_certified"],
            file_name="non_certified_certifications.geojson",
            mime="application/geo+json"
        )

if __name__ == "__main__":
    main()
