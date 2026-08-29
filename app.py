import streamlit as st
import tempfile
import os

from ocr.extractor import process_document


st.set_page_config(
    page_title="AI Document Screening",
    page_icon="📄",
    layout="centered"
)

st.title("📄 AI Document Screening System")
st.write("Upload a document to perform preliminary screening.")

uploaded_file = st.file_uploader(
    "Upload Document",
    type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:

    st.image(
        uploaded_file,
        caption="Uploaded Document",
        use_container_width=True
    )

    if st.button("🔍 Analyze Document"):

        # Save uploaded file temporarily
        suffix = os.path.splitext(
            uploaded_file.name
        )[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            temp_file.write(
                uploaded_file.getbuffer()
            )

            temp_path = temp_file.name

        try:
            # Run your existing OCR pipeline
            result, raw_text = process_document(temp_path)

            st.success("Document analysis completed!")

            st.subheader("Extracted Information")

            st.write("**Name:**", result.get("name"))
            st.write(
                "**Date of Birth:**",
                result.get("date_of_birth")
            )
            st.write(
                "**Document ID:**",
                result.get("document_id")
            )

            st.subheader("OCR Evidence")

            st.write(
                "**Overall OCR Confidence:**",
                result.get("ocr_confidence"),
                "%"
            )

            st.write(
                "**Name Confidence:**",
                result.get("name_confidence"),
                "%"
            )

            st.write(
                "**DOB Confidence:**",
                result.get("dob_confidence"),
                "%"
            )

            st.subheader("Validation")

            st.write(
                "Name Valid:",
                "✅" if result.get("name_valid") else "❌"
            )

            st.write(
                "DOB Valid:",
                "✅" if result.get("dob_valid") else "❌"
            )

            st.write(
                "Document ID Valid:",
                "✅"
                if result.get("document_id_valid")
                else "❌"
            )

            st.subheader("Risk Assessment")

            risk = result.get(
                "risk_assessment", {}
            )

            st.write(
                "**Risk Score:**",
                risk.get("risk_score")
            )

            st.write(
                "**Risk Category:**",
                risk.get("risk_category")
            )

            st.write("**Reasons:**")

            for reason in risk.get("reasons", []):
                st.write("•", reason)

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)