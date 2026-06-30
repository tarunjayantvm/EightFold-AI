import json
import os
import tempfile
import streamlit as st

from pipeline import run_pipeline

st.set_page_config(page_title="Candidate Transformer", page_icon="🧠", layout="wide")

st.title("Multi-Source Candidate Data Transformer")
st.write("Upload or provide candidate sources such as CSV, ATS JSON, resume PDF, GitHub URL, or LinkedIn URL.")

with st.sidebar:
    st.header("Inputs")
    recruiter_csv = st.file_uploader("Recruiter CSV", type=["csv"])
    ats_json = st.file_uploader("ATS JSON", type=["json"])
    resume_pdfs = st.file_uploader("Resume PDFs", type=["pdf"], accept_multiple_files=True)
    github_url = st.text_input("GitHub URL")
    linkedin_url = st.text_input("LinkedIn URL")
    projection_config = st.file_uploader("Projection Config JSON", type=["json"])
    process = st.button("Process")

if process:
    temp_files = []
    try:
        input_paths = []

        if recruiter_csv is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(recruiter_csv.read())
                input_paths.append(tmp.name)
                temp_files.append(tmp.name)

        if ats_json is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
                tmp.write(ats_json.read())
                input_paths.append(tmp.name)
                temp_files.append(tmp.name)

        for resume_pdf in resume_pdfs or []:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(resume_pdf.read())
                input_paths.append(tmp.name)
                temp_files.append(tmp.name)

        if github_url.strip():
            input_paths.append(github_url.strip())

        if linkedin_url.strip():
            input_paths.append(linkedin_url.strip())

        if not input_paths:
            st.error("Please provide at least one input source.")
            st.stop()

        config_path = None
        if projection_config is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
                tmp.write(projection_config.read())
                config_path = tmp.name
                temp_files.append(tmp.name)

        results = run_pipeline(input_paths=input_paths, config_path=config_path, output_path="output/output.json")

        st.success("Processing complete")
        st.json(results)

    finally:
        for path in temp_files:
            try:
                os.remove(path)
            except OSError:
                pass
