import sqlite3
import pandas as pd

# --- Initialize database and tables ---
def init_db():
    conn = sqlite3.connect("results.db")
    c = conn.cursor()
    # Results table: stores resume evaluation results
    c.execute('''CREATE TABLE IF NOT EXISTS results
                 (resume_name TEXT, job_id TEXT, score INT, verdict TEXT, missing TEXT)''')
    # Jobs table: stores job postings with role, ID, location, JD name & text
    c.execute('''CREATE TABLE IF NOT EXISTS jobs
                 (job_role TEXT, job_id TEXT PRIMARY KEY, location TEXT, jd_name TEXT, jd_text TEXT)''')
    conn.commit()
    conn.close()

# --- Save resume evaluation result ---
def save_result(resume_name, job_id, score, verdict, missing):
    conn = sqlite3.connect("results.db")
    c = conn.cursor()
    c.execute("INSERT INTO results VALUES (?, ?, ?, ?, ?)",
              (resume_name, job_id, score, verdict, ", ".join(missing)))
    conn.commit()
    conn.close()

# --- Save a job posting ---
def save_job(job_role, job_id, location, jd_name, jd_text):
    conn = sqlite3.connect("results.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO jobs VALUES (?, ?, ?, ?, ?)",
              (job_role, job_id, location, jd_name, jd_text))
    conn.commit()
    conn.close()

# --- Get all jobs ---
def get_jobs():
    conn = sqlite3.connect("results.db")
    df = pd.read_sql_query("SELECT * FROM jobs", conn)
    conn.close()
    return df

# Initialize DB automatically when this file is imported
init_db()
