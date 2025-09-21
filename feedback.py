def generate_feedback(missing):
    if not missing:
        return "Your resume is a strong match! 🎉"
    return f"Consider adding these missing skills or keywords: {', '.join(missing)}"
