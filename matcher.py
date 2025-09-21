from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz
import numpy as np
from sentence_transformers import SentenceTransformer, util

# Load embedding model once
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def calculate_relevance(resume_text, jd_text):
    # --- Hard Match (keywords using fuzzy ratio) ---
    keywords = jd_text.split()
    score_hard = np.mean([fuzz.partial_ratio(resume_text.lower(), kw.lower()) for kw in keywords])

    # --- Semantic Match (sentence-transformers embeddings) ---
    jd_embedding = embedder.encode(jd_text, convert_to_tensor=True)
    resume_embedding = embedder.encode(resume_text, convert_to_tensor=True)
    score_semantic = util.cos_sim(resume_embedding, jd_embedding).item() * 100

    # --- Weighted Final Score ---
    final_score = int((0.3 * score_hard + 0.7 * score_semantic))  # give more weight to semantic

    # Verdict
    if final_score > 75:
        verdict = "High"
    elif final_score > 50:
        verdict = "Medium"
    else:
        verdict = "Low"

    # Missing elements (optional, just keywords not found)
    missing = [kw for kw in keywords if kw.lower() not in resume_text.lower()]

    return final_score, verdict, missing[:10], score_hard, score_semantic
