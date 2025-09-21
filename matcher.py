from sentence_transformers import SentenceTransformer, util
import re

# ------------------------------
# Load embedding model
# ------------------------------
# all-MiniLM-L6-v2 is small, fast, and effective for semantic similarity
model = SentenceTransformer('all-MiniLM-L6-v2')

# ------------------------------
# Predefined impact verbs to boost project/achievement relevance
# ------------------------------
IMPACT_VERBS = [
    "developed", "designed", "optimized", "launched", 
    "implemented", "engineered", "created", "improved", "built", "automated"
]

# Common filler/buzzwords to ignore
FILLER_WORDS = {"by", "and", "for", "responsible", "assisted", "the", "a", "an", "of", "in", "on"}

# ------------------------------
# Section extraction
# ------------------------------
def extract_sections(text):
    """
    Splits a resume or JD into meaningful sections.
    Returns a dictionary: skills, projects, education, certifications, others
    """
    sections = {
        "skills": "",
        "projects": "",
        "education": "",
        "certifications": "",
        "others": ""
    }
    current_section = "others"
    lines = text.split('\n')
    for line in lines:
        lc = line.strip().lower()
        if re.search(r'skills|technologies|tech stack', lc):
            current_section = "skills"
        elif re.search(r'project|experience|achievements|work', lc):
            current_section = "projects"
        elif re.search(r'education|degree|university|college', lc):
            current_section = "education"
        elif re.search(r'certification|certified|course', lc):
            current_section = "certifications"
        sections[current_section] += " " + line.strip()
    return sections

# ------------------------------
# Hard keyword match with section weighting and impact verb boost
# ------------------------------
def hard_match(resume_sections, jd_sections):
    """
    Compute a weighted hard match based on exact keyword overlap.
    Skills and Projects get highest weight.
    Impact verbs in Projects/Experience are boosted.
    """
    weights = {"skills":0.4, "projects":0.3, "certifications":0.15, "education":0.1, "others":0.05}
    total_score = 0

    for section, weight in weights.items():
        resume_words = set(re.findall(r'\w+', resume_sections[section].lower())) - FILLER_WORDS
        jd_words = set(re.findall(r'\w+', jd_sections[section].lower())) - FILLER_WORDS
        matches = resume_words & jd_words
        base_score = (len(matches) / max(len(jd_words),1)) * 100

        # Add boost for impactful verbs in Projects/Experience
        boost = 0
        if section == "projects":
            boost = sum(2 for w in resume_words if w in IMPACT_VERBS)
        
        section_score = min(base_score + boost, 100)  # Cap at 100 per section
        total_score += section_score * weight

    return round(total_score,2)

# ------------------------------
# Sentence-level semantic match
# ------------------------------
def semantic_section_score(resume_text, jd_text):
    """
    Compute semantic similarity at the sentence level.
    This allows small but important details to be captured.
    """
    resume_sentences = [s.strip() for s in re.split(r'\.|\n', resume_text) if s.strip()]
    jd_sentences = [s.strip() for s in re.split(r'\.|\n', jd_text) if s.strip()]

    if not resume_sentences or not jd_sentences:
        return 0.0

    resume_embs = model.encode(resume_sentences, convert_to_tensor=True)
    jd_embs = model.encode(jd_sentences, convert_to_tensor=True)

    sim_matrix = util.cos_sim(resume_embs, jd_embs)
    # Max similarity per resume sentence (captures most relevant context)
    max_sim_per_sentence = sim_matrix.max(dim=1).values
    score = max_sim_per_sentence.mean().item() * 100
    return round(score,2)

def semantic_match(resume_sections, jd_sections):
    """
    Compute weighted semantic match across sections.
    Skills and Projects dominate the scoring.
    """
    weights = {"skills":0.4, "projects":0.3, "certifications":0.15, "education":0.1, "others":0.05}
    total_score = 0
    section_scores = {}

    for section, weight in weights.items():
        sem_score = semantic_section_score(resume_sections[section], jd_sections[section])
        section_scores[section] = sem_score
        total_score += sem_score * weight

    total_score = min(total_score, 100)
    return round(total_score,2), section_scores

# ------------------------------
# Detect missing elements per section
# ------------------------------
def detect_missing(resume_sections, jd_sections):
    """
    Returns a list of missing key items per section (skills/projects/certifications)
    """
    missing = []
    for section in jd_sections:
        resume_words = set(re.findall(r'\w+', resume_sections.get(section,"").lower())) - FILLER_WORDS
        jd_words = set(re.findall(r'\w+', jd_sections.get(section,"").lower())) - FILLER_WORDS
        missing_items = jd_words - resume_words
        if missing_items:
            missing.append(f"{section.title()}: {', '.join(list(missing_items)[:10])}")
    return missing

# ------------------------------
# Main relevance calculation
# ------------------------------
def calculate_relevance(resume_text, jd_text):
    """
    Returns:
    - final_score (0-100)
    - verdict (High/Medium/Low)
    - missing elements list
    - hard match score
    - semantic match score
    - semantic scores per section
    """
    # Extract sections
    resume_sections = extract_sections(resume_text)
    jd_sections = extract_sections(jd_text)

    # Hard match
    score_hard = hard_match(resume_sections, jd_sections)

    # Semantic match
    score_semantic, section_sem_scores = semantic_match(resume_sections, jd_sections)

    # Combine weighted final score
    final_score = round(0.4*score_hard + 0.6*score_semantic,2)

    # Verdict
    if final_score >= 75:
        verdict = "High"
    elif final_score >= 50:
        verdict = "Medium"
    else:
        verdict = "Low"

    # Missing elements
    missing = detect_missing(resume_sections, jd_sections)

    return final_score, verdict, missing, score_hard, score_semantic, section_sem_scores
# ------------------------------
# Feedback generation
