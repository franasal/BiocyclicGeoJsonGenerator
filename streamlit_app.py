try:
    geojson_certified, geojson_non_certified, warnings = generate_geojson(uploaded_file)

    if warnings:
        st.warning("Some entries were skipped:")
        for warn in warnings:
            st.markdown(f"- {warn}")

    buffer1 = BytesIO(json.dumps(geojson_certified, ensure_ascii=False, indent=2).encode("utf-8"))
    buffer2 = BytesIO(json.dumps(geojson_non_certified, ensure_ascii=False, indent=2).encode("utf-8"))

    st.download_button(
        label="⬇ Download Certified GeoJSON",
        data=buffer1,
        file_name="certified_certifications.geojson",
        mime="application/geo+json"
    )

    st.download_button(
        label="⬇ Download Non-Certified GeoJSON",
        data=buffer2,
        file_name="non_certified_certifications.geojson",
        mime="application/geo+json"
    )

    st.success("🎉 Files generated successfully!")

except Exception as e:
    st.error("❌ An error occurred during processing.")
    import traceback
    st.code(traceback.format_exc())
