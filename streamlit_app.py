import streamlit as st
import pandas as pd
import json
from io import StringIO
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PASSWORD = os.getenv("APP_PASSWORD")

# --- Secure Password Gate ---
def check_password():
    def password_entered():
        if st.session_state["password"] == PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Clean up
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

# --- Streamlit App ---
if check_password():
    st.title("Excel Processor to GeoJSON")

    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.success("File uploaded successfully.")

        # Placeholder for processing
        st.info("Processing file... (dummy step)")

        # Dummy GeoJSON output
        geojson1 = {
            "type": "FeatureCollection",
            "features": []
        }

        geojson2 = {
            "type": "FeatureCollection",
            "features": []
        }

        # Prepare for download
        buffer1 = StringIO()
        json.dump(geojson1, buffer1)
        buffer1.seek(0)

        buffer2 = StringIO()
        json.dump(geojson2, buffer2)
        buffer2.seek(0)

        st.download_button("Download GeoJSON 1", buffer1, file_name="output1.geojson", mime="application/geo+json")
        st.download_button("Download GeoJSON 2", buffer2, file_name="output2.geojson", mime="application/geo+json")
