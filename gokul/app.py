import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import smtplib
from email.message import EmailMessage
from google import genai

# Optional: for PDF export
try:
    from fpdf import FPDF
    has_fpdf = True
except ImportError: 
    has_fpdf = False

# ---------------------------
# 🤖 GEMINI API CONFIG
# ---------------------------
# Note: In a production app, use st.secrets for API keys
GEMINI_API_KEY = "AIzaSyBUNK20EnWC-_2OCJODPPoNCtomnKUC26o"
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(page_title="Tamil Nadu Job Market Dashboard", layout="wide")

# Session state to manage navigation
if "show_dashboard" not in st.session_state:
    st.session_state.show_dashboard = False

# -------------------------------
# 1️⃣ User Info Page
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

                # Setup Email
                msg = EmailMessage()
                msg.set_content(f"Name: {name}\nEmail: {email}")
                msg["Subject"] = "New User Info Submission"
                msg["From"] = "vmgokul07vmg@gmail.com" # Should match login email
                msg["To"] = "vmgokul07vmg@gmail.com"

                try:
                    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                        smtp.login("vmgokul07vmg@gmail.com", "wujj mctj bcmr qkxj")
                        smtp.send_message(msg)
                except Exception as e:
                    st.error(f"❌ Failed to send email alert: {e}")

                st.session_state.show_dashboard = True
                st.rerun()
            else:
                st.warning("Please fill in both Name and Email.")

# -------------------------------
# 2️⃣ Dashboard Page
# -------------------------------
else:
    st.title("📊 Tamil Nadu Job Market Dashboard")
    st.markdown("Analyze job trends across districts, sectors, and companies in Tamil Nadu.")

    @st.cache_data
    def load_data():
        return pd.read_csv("gokul/tamilnadu_job_market_200_enriched.csv")

    df = load_data()

    # Improved classification logic to avoid mislabeling Mechanical Engineers as IT
    def classify_job(row):
        it_keywords = [
            "software", "developer", "it", "python", "java",
            "cloud", "machine learning", "ai", "tech", "full stack",
            "backend", "frontend", "network", "cyber"
        ]
        text = f"{row['Job_Title']} {row['Skills_Required']}".lower()
        return "IT" if any(k in text for k in it_keywords) else "Non-IT"

    # You can use the existing 'IT_or_Non_IT' column from CSV or this dynamic one
    df["Job_Type_Calculated"] = df.apply(classify_job, axis=1)

    # -------------------------------
    # Filters
    # -------------------------------
    st.sidebar.header("🔍 Filter Jobs")

    district_filter = st.sidebar.multiselect(
        "Select District(s)",
        options=sorted(df["District"].unique()),
        default=sorted(df["District"].unique())
    )

    sector_filter = st.sidebar.multiselect(
        "Select Job Sector(s)",
        options=sorted(df["Job_Sector"].unique()),
        default=sorted(df["Job_Sector"].unique())
    )

    exp_filter = st.sidebar.multiselect(
        "Select Experience Level",
        options=sorted(df["Experience_Level"].unique()),
        default=sorted(df["Experience_Level"].unique())
    )

    filtered_df = df[
        (df["District"].isin(district_filter)) &
        (df["Job_Sector"].isin(sector_filter)) &
        (df["Experience_Level"].isin(exp_filter))
    ]

    search_query = st.text_input("🔎 Search Job Title, Skills, Company...")
    if search_query:
        filtered_df = filtered_df[
            filtered_df["Job_Title"].str.contains(search_query, case=False) |
            filtered_df["Skills_Required"].str.contains(search_query, case=False) |
            filtered_df["Company_Name"].str.contains(search_query, case=False)
        ]

    st.markdown(f"### 📌 {len(filtered_df)} Jobs Found")

    # Metrics Row
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Jobs", len(filtered_df))
    if not filtered_df.empty:
        m2.metric("Avg Salary", f"₹{int(filtered_df['Salary_Monthly'].mean()):,}")
        m3.metric("Top District", filtered_df['District'].mode()[0])

    st.write("### 💻 IT vs Non-IT Job Distribution")
    # Using the IT_or_Non_IT column from your CSV for accuracy
    st.bar_chart(filtered_df["IT_or_Non_IT"].value_counts())

    st.dataframe(filtered_df, use_container_width=True)

    # -------------------------------
    # Export Section
    # -------------------------------
    st.subheader("📤 Export Filtered Data")
    col1, col2, col3 = st.columns(3)

    with col1:
        csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇ Download CSV", csv, "filtered_jobs.csv", "text/csv")

    with col2:
        try:
            excel_io = io.BytesIO()
            with pd.ExcelWriter(excel_io, engine="xlsxwriter") as writer:
                filtered_df.to_excel(writer, index=False)
            st.download_button(
                "⬇ Download Excel",
                excel_io.getvalue(),
                "filtered_jobs.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception:
            st.info("Excel export requires 'xlsxwriter' library.")

    with col3:
        if has_fpdf:
            def df_to_pdf(df_input):
                pdf = FPDF()
                pdf.set_auto_page_break(auto=True, margin=10)
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                pdf.cell(200, 10, txt="Tamil Nadu Job Market Report", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", size=8)
                for _, row in df_input.iterrows():
                    # Clean strings to avoid encoding errors in FPDF
                    line = f"{row['Job_Title']} | {row['Company_Name']} | {row['District']} | {row['Salary_Monthly']}"
                    pdf.cell(0, 8, line.encode('latin-1', 'replace').decode('latin-1'), ln=1)
                return pdf.output(dest="S").encode("latin1")

            if st.button("Generate PDF Preview"):
                pdf_data = df_to_pdf(filtered_df.head(30))
                st.download_button("⬇ Download PDF", pdf_data, "filtered_jobs.pdf", "application/pdf")
        else:
            st.info("PDF export requires 'fpdf' library.")

    # -------------------------------
    # Visualizations
    # -------------------------------
    st.subheader("📈 Job Market Visualizations")

    viz_option = st.radio("Choose a chart", [
        "Job Count by District",
        "Average Salary by Sector",
        "Top Hiring Companies",
        "Job Count by Experience Level",
        "Job Sector Distribution"
    ], horizontal=True)

    if not filtered_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        
        if viz_option == "Job Count by District":
            filtered_df["District"].value_counts().plot(kind="barh", ax=ax, color="skyblue")
            ax.set_title("Jobs per District")

        elif viz_option == "Average Salary by Sector":
            filtered_df.groupby("Job_Sector")["Salary_Monthly"].mean().sort_values().plot(kind="barh", ax=ax, color="lightgreen")
            ax.set_title("Avg Monthly Salary (INR)")

        elif viz_option == "Top Hiring Companies":
            filtered_df["Company_Name"].value_counts().head(10).plot(kind="bar", ax=ax, color="orange")
            ax.set_title("Top 10 Companies")

        elif viz_option == "Job Count by Experience Level":
            filtered_df["Experience_Level"].value_counts().plot(kind="pie", autopct="%1.1f%%", ax=ax)
            ax.set_ylabel("") # Remove the 'count' label
            ax.set_title("Experience Level Split")

        elif viz_option == "Job Sector Distribution":
            filtered_df["Job_Sector"].value_counts().plot(kind="bar", ax=ax, color="purple")
            ax.set_title("Jobs by Sector")

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig) # Clean up memory
    else:
        st.warning("No data available for the selected filters.")

    # -------------------------------
    # 🤖 GEMINI AI SECTION
    # -------------------------------
    st.markdown("---")
    st.subheader("🤖 Ask Gemini AI About Job Market")

    user_question = st.text_input(
        "Ask about skills, salary trends, IT vs Non-IT, districts, careers, etc."
    )

    if st.button("Ask Gemini"):
        if user_question.strip():
            with st.spinner("Gemini is analyzing job market data..."):
                # Sending a subset of data to stay within token limits
                data_summary = filtered_df.head(30).to_string()
                prompt = f"""
                You are an AI job market analyst for Tamil Nadu.
                Here is a sample of the current job data:
                {data_summary}

                User Question: {user_question}
                
                Provide a helpful, data-driven answer based on the provided jobs.
                """
                try:
                    response = gemini_model.generate_content(prompt)
                    st.info(response.text)
                except Exception as e:
                    st.error(f"AI Error: {e}")
        else:
            st.warning("Please enter a question.")

    st.markdown("---")

    st.markdown("👨‍💻 Developed by **Gokul & Gokulakrishnan**")


