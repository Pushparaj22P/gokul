import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import os
import smtplib
from email.message import EmailMessage
from google import genai

# Optional PDF export
try:
    from fpdf import FPDF
    has_fpdf = True
except ImportError:
    has_fpdf = False


# ---------------------------
# 🔐 CONFIG
# ---------------------------
st.set_page_config(
    page_title="Tamil Nadu Job Market Dashboard",
    layout="wide"
)

if "show_dashboard" not in st.session_state:
    st.session_state.show_dashboard = False


# ---------------------------
# 🤖 GEMINI CLIENT (SAFE)
# ---------------------------
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ GEMINI_API_KEY not found in Streamlit Secrets")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


# -------------------------------
# 1️⃣ USER INFO PAGE
# -------------------------------
if not st.session_state.show_dashboard:
    st.title("📝 Enter Your Information")

    with st.form("user_info_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        submitted = st.form_submit_button("Submit")

        if submitted:
            if name and email:
                st.success("✅ Information Submitted")

                msg = EmailMessage()
                msg.set_content(f"Name: {name}\nEmail: {email}")
                msg["Subject"] = "New User Info Submission"
                msg["From"] = "vmgokul07vmg@gmail.com"
                msg["To"] = "vmgokul07vmg@gmail.com"

                try:
                    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                        smtp.login(
                            "vmgokul07vmg@gmail.com",
                            st.secrets["EMAIL_PASSWORD"]
                        )
                        smtp.send_message(msg)
                except Exception as e:
                    st.warning(f"Email not sent: {e}")

                st.session_state.show_dashboard = True
                st.rerun()
            else:
                st.warning("Please enter both Name and Email.")


# -------------------------------
# 2️⃣ DASHBOARD PAGE
# -------------------------------
else:
    st.title("📊 Tamil Nadu Job Market Dashboard")
    st.markdown("Analyze job trends across districts, sectors, and companies.")

    @st.cache_data
    def load_data():
        return pd.read_csv("gokul/tamilnadu_job_market_200_enriched.csv")

    df = load_data()

    # -------------------------------
    # FILTERS
    # -------------------------------
    st.sidebar.header("🔍 Filters")

    district_filter = st.sidebar.multiselect(
        "District",
        sorted(df["District"].unique()),
        sorted(df["District"].unique())
    )

    sector_filter = st.sidebar.multiselect(
        "Job Sector",
        sorted(df["Job_Sector"].unique()),
        sorted(df["Job_Sector"].unique())
    )

    exp_filter = st.sidebar.multiselect(
        "Experience Level",
        sorted(df["Experience_Level"].unique()),
        sorted(df["Experience_Level"].unique())
    )

    filtered_df = df[
        (df["District"].isin(district_filter)) &
        (df["Job_Sector"].isin(sector_filter)) &
        (df["Experience_Level"].isin(exp_filter))
    ]

    search = st.text_input("🔎 Search jobs, skills, companies")
    if search:
        filtered_df = filtered_df[
            filtered_df["Job_Title"].str.contains(search, case=False) |
            filtered_df["Skills_Required"].str.contains(search, case=False) |
            filtered_df["Company_Name"].str.contains(search, case=False)
        ]

    st.markdown(f"### 📌 {len(filtered_df)} Jobs Found")

    # -------------------------------
    # METRICS
    # -------------------------------
    c1, c2, c3 = st.columns(3)

    c1.metric("Total Jobs", len(filtered_df))

    if not filtered_df.empty:
        c2.metric(
            "Avg Salary",
            f"₹{int(filtered_df['Salary_Monthly'].mean()):,}"
        )
        c3.metric(
            "Top District",
            filtered_df["District"].mode()[0]
        )

    st.bar_chart(filtered_df["IT_or_Non_IT"].value_counts())

    st.dataframe(filtered_df, use_container_width=True)

    # -------------------------------
    # EXPORTS
    # -------------------------------
    st.subheader("📤 Export Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇ CSV", csv, "jobs.csv", "text/csv")

    with col2:
        excel_io = io.BytesIO()
        with pd.ExcelWriter(excel_io, engine="xlsxwriter") as writer:
            filtered_df.to_excel(writer, index=False)
        st.download_button(
            "⬇ Excel",
            excel_io.getvalue(),
            "jobs.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col3:
        if has_fpdf and st.button("⬇ PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=8)
            for _, row in filtered_df.head(30).iterrows():
                line = f"{row['Job_Title']} | {row['Company_Name']} | {row['District']}"
                pdf.multi_cell(0, 6, line)
            st.download_button(
                "Download PDF",
                pdf.output(dest="S").encode("latin1"),
                "jobs.pdf",
                "application/pdf"
            )

    # -------------------------------
    # VISUALIZATION
    # -------------------------------
    st.subheader("📈 Visualizations")

    fig, ax = plt.subplots(figsize=(10, 5))
    filtered_df["District"].value_counts().plot(kind="barh", ax=ax)
    st.pyplot(fig)
    plt.close(fig)

    # -------------------------------
    # 🤖 GEMINI AI
    # -------------------------------
    st.markdown("---")
    st.subheader("🤖 Ask Gemini AI")

    user_question = st.text_input("Ask about skills, salaries, trends")

    if st.button("Ask Gemini"):
        if user_question.strip():
            with st.spinner("Analyzing job market..."):
                data_sample = filtered_df.head(30).to_string()

                prompt = f"""
You are a job market analyst for Tamil Nadu.

Job data sample:
{data_sample}

User question:
{user_question}

Answer clearly and concisely.
"""

                try:
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=prompt
                    )
                    st.success("Gemini Answer")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"AI Error: {e}")
        else:
            st.warning("Please enter a question.")

    st.markdown("---")
    st.markdown("👨‍💻 Developed by **Gokul & Gokulakrishnan**")

