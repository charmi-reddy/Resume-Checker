from sentence_transformers import SentenceTransformer, util
import re

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# --- Section extraction ---
def extract_sections(text):
    """
    Split resume into meaningful sections:
    - Skills
    - Projects
    - Education
    - Certifications
    Returns a dictionary with section_name: text
    """
    sections = {
        "skills": "",
        "projects": "",
        "education": "",
        "certifications": "",
        "others": ""
    }

    lines = text.split('\n')
    current_section = "others"

    for line in lines:
        line_clean = line.strip().lower()
        if re.search(r'skills|technologies|tech stack', line_clean):
            current_section = "skills"
        elif re.search(r'project|experience|achievements|work', line_clean):
            current_section = "projects"
        elif re.search(r'education|degree|university|college', line_clean):
            current_section = "education"
        elif re.search(r'certification|certified|course', line_clean):
            current_section = "certifications"
        # Append line to current section
        sections[current_section] += " " + line.strip()
    
    return sections

# --- Extract important keywords from JD ---
def extract_jd_keywords(jd_text):
    keywords = set(re.findall(r'\w+', jd_text.lower()))
    return keywords

# --- Hard match ---
def hard_match(resume_sections, jd_keywords):
    """
    Weighted hard match: Skills > Projects > Certifications > Education > Others
    """
    weights = {
        "skills": 0.4,
        "projects": 0.3,
        "certifications": 0.15,
        "education": 0.1,
        "others": 0.05
    }

    score = 0
    for section, weight in weights.items():
        section_words = set(re.findall(r'\w+', resume_sections[section].lower()))
        matches = jd_keywords & section_words
        section_score = (len(matches)/max(len(jd_keywords),1)) * weight * 100
        score += section_score
    return round(score,2)

# --- Semantic match ---
def semantic_match(resume_sections, jd_sections):
    """
    Embedding similarity per section, weighted
    """
    weights = {
        "skills": 0.4,
        "projects": 0.3,
        "certifications": 0.15,
        "education": 0.1,
        "others": 0.05
    }
    score = 0
    for section, weight in weights.items():
        resume_text = resume_sections.get(section, "")
        jd_text = jd_sections.get(section, "")
        if resume_text and jd_text:
            resume_emb = model.encode(resume_text, convert_to_tensor=True)
            jd_emb = model.encode(jd_text, convert_to_tensor=True)
            section_score = util.cos_sim(resume_emb, jd_emb).item() * weight * 100
            score += section_score
    return round(score,2)

# --- Detect missing important elements ---
def detect_missing(resume_sections, jd_sections):
    missing = []
    for section in jd_sections:
        resume_words = set(re.findall(r'\w+', resume_sections.get(section, "").lower()))
        jd_words = set(re.findall(r'\w+', jd_sections.get(section, "").lower()))
        missing_items = jd_words - resume_words
        if missing_items:
            missing.append(f"{section.title()}: {', '.join(list(missing_items)[:10])}")
    return missing

# --- Main relevance calculation ---
def calculate_relevance(resume_text, jd_text):
    # Split into sections
    resume_sections = extract_sections(resume_text)
    jd_sections = extract_sections(jd_text)

    jd_keywords = extract_jd_keywords(jd_text)

    # Hard match (weighted)
    score_hard = hard_match(resume_sections, jd_keywords)

    # Semantic match (section-aware)
    score_semantic = semantic_match(resume_sections, jd_sections)

    # Final weighted score: semantic > hard
    final_score = round(0.4*score_hard + 0.6*score_semantic, 2)

    # Verdict
    if final_score >= 75:
        verdict = "High"
    elif final_score >= 50:
        verdict = "Medium"
    else:
        verdict = "Low"

    # Missing elements
    missing = detect_missing(resume_sections, jd_sections)

    return final_score, verdict, missing, score_hard, score_semantic
