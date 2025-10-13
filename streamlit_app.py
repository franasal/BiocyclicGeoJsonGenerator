import streamlit as st
import pandas as pd
import json
import time
import traceback
import os
from dotenv import load_dotenv
from github import Github

# --- Load env vars ---
load_dotenv()
PASSWORD = os.getenv("APP_PASSWORD")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
GITHUB_PATH = os.getenv("GITHUB_PATH", "geojson")              # Production folder
GITHUB_DEV_PATH = os.getenv("GITHUB_DEV_PATH", "geojson-dev")  # Dev/staging folder

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

# --- GEOJSON creation ---
def create_feature(row, lon, lat, icon_url, certified_status):
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
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
            certified_features.append(create_feature(row, lon, lat, icon_url, "yes"))
        else:
            icon_url = "https://www.biocyclic-vegan.org/wp-content/uploads/2022/11/WEB__EN_Biocyclic_Vegan_Agriculture_red_white-background_-201x300.png"
            non_certified_features.append(create_feature(row, lon, lat, icon_url, cert_status))

        time.sleep(0.2)

    geojson_certified = {"type": "FeatureCollection", "features": certified_features}
    geojson_non_certified = {"type": "FeatureCollection", "features": non_certified_features}
    return geojson_certified, geojson_non_certified, warnings

# --- Generic publisher ---
def publish_to_github(geojson_certified, geojson_non_certified, target_path, commit_message):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    files_to_upload = {
        f"{target_path}/certified.geojson": json.dumps(geojson_certified, indent=2, ensure_ascii=False),
        f"{target_path}/non_certified.geojson": json.dumps(geojson_non_certified, indent=2, ensure_ascii=False)
    }

    # Delete old files
    try:
        contents = repo.get_contents(target_path, ref=GITHUB_BRANCH)
        for file in contents:
            repo.delete_file(file.path, f"Delete old file {file.name}", file.sha, branch=GITHUB_BRANCH)
    except Exception:
        pass  # Folder might not exist

    # Upload new
    for path, content in files_to_upload.items():
        repo.create_file(path, commit_message, content, branch=GITHUB_BRANCH)

# --- Promote dev → prod ---
def promote_dev_to_prod():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    try:
        dev_contents = repo.get_contents(GITHUB_DEV_PATH, ref=GITHUB_BRANCH)
        # Delete old prod files
        try:
            prod_contents = repo.get_contents(GITHUB_PATH, ref=GITHUB_BRANCH)
            for file in prod_contents:
                repo.delete_file(file.path, f"Delete old prod file {file.name}", file.sha, branch=GITHUB_BRANCH)
        except Exception:
            pass

        # Copy dev files to prod
        for file in dev_contents:
            file_content = file.decoded_content.decode("utf-8")
            prod_path = file.path.replace(GITHUB_DEV_PATH, GITHUB_PATH, 1)
            repo.create_file(prod_path, f"Promote {file.name} from dev to prod", file_content, branch=GITHUB_BRANCH)

        return True
    except Exception as e:
        st.error(f"Failed to promote: {e}")
        return False

# --- Main App ---
def main():
    st.set_page_config(page_title="GeoJSON Publisher", page_icon="🌍")
    st.title("🌱 Biozyklisch-Vegan GeoJSON Publisher")

    if not check_password():
        st.stop()

    uploaded_file = st.file_uploader("Upload your Excel file (.xlsx)", type=["xlsx"])

    if uploaded_file is not None:
        st.success("✅ File uploaded. Click below to publish.")

        if st.button("🧪 Publish to Dev (Staging)"):
            try:
                geojson_certified, geojson_non_certified, warnings = generate_geojson(uploaded_file)
                publish_to_github(geojson_certified, geojson_non_certified, GITHUB_DEV_PATH, "Publish to dev")
                st.success(f"✅ Published to DEV folder `{GITHUB_DEV_PATH}` — review it on your dev pages URL.")
                if warnings:
                    st.warning("Some entries were skipped:")
                    for warn in warnings:
                        st.markdown(f"- {warn}")
            except Exception:
                st.error("❌ Error during DEV publishing")
                st.code(traceback.format_exc())

    st.markdown("---")
    st.subheader("🚀 Promote Reviewed Changes to Production")
    if st.button("⬆️ Promote Dev → Production"):
        if promote_dev_to_prod():
            st.success("🎉 Dev files promoted to Production successfully!")

if __name__ == "__main__":
    main()
