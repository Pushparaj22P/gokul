import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import json
import os

from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(
    page_title="Tamil Nadu Job Market Dashboard",
    layout="wide"
)

# ---------------------------
# AUTH (VERTEX AI)
# ---------------------------
if "GCP_SERVICE_ACCOUNT" not in st.secrets:
    st.error("GCP credentials not found in secrets")
    st.stop()

# Write service account to temp file
sa_info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
with open("gcp_key.json", "w") as f:
    json.dump(sa_info, f)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp_key.json"

PROJECT_ID = st.secrets["GCP_PROJECT_ID"]
LOCATION = st.secrets.get("GCP_LOCATION", "us-central1")

aiplatform.init(project=PROJECT_ID, location=LOCATION)

model = GenerativeModel("gemini-1.5-flash")

# ---------------------------
# LOAD DATA
# ---------------------------
@st.cache_data
def load_data():
    return pd.read_csv("gokul/tamilnadu_job_market_200_enriched.csv")

df = load_data()

# ---------------------------
# UI
# ---------------------------
st.title("📊 Tamil Nadu Job Market Dashboard")

districts = st.multiselect(
    "District",
    sorted(df["District"].unique()),
    sorted(df["District"].unique())
)

filtered_df = df[df["District"].isin(districts)]

st.dataframe(filtered_df, use_container_width=True)

# ---------------------------
# AI SECTION (VERTEX AI)
# ---------------------------
st.markdown("---")
st.subheader("🤖 Ask Gemini (Vertex AI)")

question = st.text_input("Ask about skills, salaries, trends")

if st.button("Ask AI"):
    if question.strip():
        with st.spinner("Analyzing with Vertex AI..."):
            sample = filtered_df.head(20).to_string()

            prompt = f"""
You are a job market analyst for Tamil Nadu.

Here is job data:
{sample}

User question:
{question}

Give a clear, data-driven answer.
"""

            try:
                response = model.generate_content(prompt)
                st.success("AI Response")
                st.write(response.text)
            except Exception as e:
                st.error(e)
    else:
        st.warning("Enter a question")
