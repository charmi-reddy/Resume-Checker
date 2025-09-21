import streamlit as st
from parser import extract_resume_text, extract_jd_text
from matcher import calculate_relevance
from feedback import generate_feedback
from database import save_result, save_job, get_jobs
import pandas as pd
import altair as alt

st.set_page_config(page_title="Resume Relevance Checker", layout="wide")
st.title("Automated Resume Relevance Check System")

# --- JOB POSTING SECTION ---
st.sidebar.header("Post a New Job")
job_role = st.sidebar.text_input("Job Role")
job_id = st.sidebar.text_input("Job ID")
location = st.sidebar.text_input("Location")
jd_file_post = st.sidebar.file_uploader("Upload JD (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"])

if st.sidebar.button("Post Job"):
    if job_role and job_id and location and jd_file_post:
        jd_text_post = extract_jd_text(jd_file_post)
        save_job(job_role, job_id, location, jd_file_post.name, jd_text_post)
        st.sidebar.success(f"Job '{job_role}' ({job_id}) posted successfully!")
    else:
        st.sidebar.error("Please fill all fields and upload JD.")

# --- RESUME UPLOAD SECTION ---
st.header("Upload Resume for Evaluation")
resume_file = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"])

jobs_df = get_jobs()

if not jobs_df.empty and resume_file:
    # Filters for job selection
    st.subheader("Select Job for Evaluation")
    loc_filter = st.selectbox("Filter by Location", ["All"] + sorted(jobs_df["location"].unique().tolist()))
    job_id_filter = st.text_input("Search by Job ID")

    filtered_df = jobs_df.copy()
    if loc_filter != "All":
        filtered_df = filtered_df[filtered_df["location"] == loc_filter]
    if job_id_filter:
        filtered_df = filtered_df[filtered_df["job_id"].str.contains(job_id_filter, case=False)]

    job_options = filtered_df.apply(lambda x: f"{x['job_role']} ({x['job_id']}) - {x['location']}", axis=1)
    if not job_options.empty:
        selected_job_display = st.selectbox("Select Job to Apply", job_options)
        selected_job_id = selected_job_display.split("(")[1].split(")")[0]
        jd_text = filtered_df[filtered_df["job_id"] == selected_job_id]["jd_text"].values[0]

        # --- Process Resume ---
        with st.spinner("Analyzing resume..."):
            resume_text = extract_resume_text(resume_file)
            score, verdict, missing, score_hard, score_semantic, section_scores = calculate_relevance(resume_text, jd_text)
            feedback = generate_feedback(missing)

            # Save result
            save_result(resume_file.name, selected_job_id, score, verdict, missing)

            # --- Layout: columns ---
            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("Score Breakdown")
                df_chart = pd.DataFrame({
                    "Match Type": ["Hard Match (Keywords)", "Semantic Match (Context)"],
                    "Score": [score_hard, score_semantic]
                })
                chart = alt.Chart(df_chart).mark_bar().encode(
                    x=alt.X("Score:Q", title="Score (%)"),
                    y=alt.Y("Match Type:N", sort="-x", title=""),
                    color=alt.Color("Match Type:N", legend=None)
                ).properties(height=200)
                st.altair_chart(chart, use_container_width=True)
                st.markdown(f"**Verdict:** {verdict}  |  **Relevance Score:** {score}/100")

            with col2:
                st.subheader("Feedback & Missing Elements")
                if missing:
                    for item in missing:
                        st.markdown(f"- {item}")
                else:
                    st.write("None! Your resume is comprehensive.")
                st.write("**Suggestions:**", feedback)

    else:
        st.warning("No jobs match your filter. Please adjust location or Job ID.")
elif resume_file and jobs_df.empty:
    st.warning("No job postings available yet. Post a job in the sidebar first!")
st.markdown("---")  # horizontal line
st.markdown(
    "<p style='text-align:center; color:gray; font-size:12px;'>Made with ❤️ by Charmi Reddy</p>", 
    unsafe_allow_html=True
)

# --- PLACEMENT TEAM DASHBOARD ---
st.header("Placement Team Dashboard")
import sqlite3

# Load all results and join with job details
def get_results_df():
    conn = sqlite3.connect("results.db")
    query = """
        SELECT 
            r.resume_name AS Resume,
            j.job_role AS Role,
            j.job_id AS JobID,
            j.location AS Location,
            r.score AS Score,
            r.verdict AS Verdict,
            r.missing AS 'Missing Elements'
        FROM results r
        JOIN jobs j ON r.job_id = j.job_id
        ORDER BY j.job_id ASC, r.score DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

results_df = get_results_df()
if not results_df.empty:
    # Shortlisted column: High & Medium verdicts = YES, else NO
    results_df["Shortlisted"] = results_df["Verdict"].apply(lambda v: "YES" if v in ["High", "Medium"] else "NO")
    
    st.subheader("Resume Shortlisting Table")
    # Optional filters for job role, location, and shortlisting
    col1, col2, col3 = st.columns(3)
    with col1:
        role_filter = st.selectbox("Filter by Role", ["All"] + sorted(results_df["Role"].unique()))
    with col2:
        loc_filter = st.selectbox("Filter by Location", ["All"] + sorted(results_df["Location"].unique()))
    with col3:
        shortlist_filter = st.selectbox("Shortlisted Only?", ["All", "YES", "NO"])

    filtered_df = results_df.copy()
    if role_filter != "All":
        filtered_df = filtered_df[filtered_df["Role"] == role_filter]
    if loc_filter != "All":
        filtered_df = filtered_df[filtered_df["Location"] == loc_filter]
    if shortlist_filter != "All":
        filtered_df = filtered_df[filtered_df["Shortlisted"] == shortlist_filter]

    st.dataframe(
        filtered_df[
            [
                "Resume",
                "Role",
                "JobID",
                "Location",
                "Score",
                "Verdict",
                "Shortlisted",
                "Missing Elements"
            ]
        ],
        use_container_width=True,
        height=500,
    )
else:
    st.info("No resume evaluations to display yet. Once students upload resumes, results will appear here.")
