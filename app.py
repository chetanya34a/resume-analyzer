import streamlit as st
import PyPDF2
import re
import json
import spacy
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="AI Resume Analyzer", layout="wide")


# ---------- CUSTOM UI ----------
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: white;
}

.title {
    text-align: center;
    font-size: 55px;
    font-weight: 800;
    color: #00FFAA;
    letter-spacing: 1px;
}

.card {
    background: #1e1e1e;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 12px;
}

.skill {
    display: inline-block;
    background: #00FFAA;
    color: black;
    padding: 6px 12px;
    border-radius: 10px;
    margin: 5px;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)


# ---------- HEADER ----------
st.markdown("""
<h1 style='
text-align: center;
font-size: 70px;
font-weight: 900;
background: linear-gradient(90deg, #00FFAA, #00D4FF);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
'>
🚀 AI Resume Analyzer
</h1>
""", unsafe_allow_html=True)
st.caption("Smart resume insights powered by Python & NLP 🚀")
st.markdown("---")


# ---------- NLP ----------
nlp = spacy.load("en_core_web_sm")


# ---------- FILE UPLOAD ----------
uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])


# ---------- TEXT EXTRACTION ----------
def extract_text(file):
    text = ""
    pdf = PyPDF2.PdfReader(file)

    for page in pdf.pages:
        content = page.extract_text()
        if content:
            text += content

    return text


# ---------- DATA EXTRACTION ----------
def extract_data(text):

    # Clean text
    text = text.replace("?", "")
    text = re.sub(r'[^a-zA-Z0-9@.\s]', ' ', text)
    text_lower = text.lower()

    # Name (simple logic)
    name = ""
    lines = text.split("\n")
    for line in lines[:8]:
        line = line.strip()
        if line and len(line.split()) <= 4:
            name = line
            break

    # Email
    email = re.findall(r'\S+@\S+', text)

    # Phone
    phone = list(set(re.findall(r'\d{10}', text)))

    # Skills
    skills_db = [
        "python","java","c++","html","css","javascript",
        "sql","machine learning","data analysis",
        "react","node","cloud","ai"
    ]

    skills = []
    for skill in skills_db:
        if skill in text_lower:
            skills.append(skill)

    # ---------- EDUCATION FIX ----------
    education = []

    if re.search(r"\bb\.?tech\b", text_lower):
        education.append("B.Tech")

    if re.search(r"\bm\.?tech\b", text_lower):
        education.append("M.Tech")

    if re.search(r"\bbachelor('?s)?\b", text_lower):
        education.append("Bachelor's")

    # FIX: avoid "mastering"
    if re.search(r"\bmaster('?s)?\b", text_lower) and not re.search(r"\bmastering\b", text_lower):
        education.append("Master's")

    if re.search(r"\bbsc\b", text_lower):
        education.append("B.Sc")

    if re.search(r"\bmsc\b", text_lower):
        education.append("M.Sc")

    education = list(set(education))

    return {
        "Name": name,
        "Email": email,
        "Phone": phone,
        "Skills": skills,
        "Education": education
    }


# ---------- SCORE ----------
def calculate_score(data):
    score = 0

    if data["Email"]:
        score += 15
    if data["Phone"]:
        score += 15

    skill_count = len(data["Skills"])
    if skill_count >= 5:
        score += 30
    elif skill_count >= 3:
        score += 20
    elif skill_count >= 1:
        score += 10

    if data["Education"]:
        score += 20

    if "machine learning" in data["Skills"] or "ai" in data["Skills"]:
        score += 20

    return min(score, 100)


# ---------- PDF ----------
def generate_pdf(data, score):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph(f"Name: {data['Name']}", styles["Normal"]))
    content.append(Paragraph(f"Email: {', '.join(data['Email'])}", styles["Normal"]))
    content.append(Paragraph(f"Phone: {', '.join(data['Phone'])}", styles["Normal"]))
    content.append(Paragraph(f"Skills: {', '.join(data['Skills'])}", styles["Normal"]))
    content.append(Paragraph(f"Education: {', '.join(data['Education'])}", styles["Normal"]))
    content.append(Paragraph(f"Score: {score}/100", styles["Normal"]))

    doc.build(content)
    buffer.seek(0)
    return buffer


# ---------- SUGGESTIONS ----------
def get_suggestions(data):
    suggestions = []

    if not data["Skills"]:
        suggestions.append("Add technical skills like Python, SQL etc.")

    if len(data["Skills"]) < 3:
        suggestions.append("Add more relevant skills.")

    if not data["Education"]:
        suggestions.append("Mention your education clearly.")

    return suggestions


# ---------- MAIN ----------
if uploaded_file:

    text = extract_text(uploaded_file)

    with st.spinner("Analyzing resume..."):
        data = extract_data(text)
        score = calculate_score(data)
        suggestions = get_suggestions(data)

    st.success("Resume processed successfully ✅")

    # ---------- DISPLAY ----------
    st.markdown(f'<div class="card"><b>👤 Name:</b> {data["Name"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><b>📧 Email:</b> {", ".join(data["Email"])}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><b>📱 Phone:</b> {", ".join(data["Phone"])}</div>', unsafe_allow_html=True)

    # Skills
    st.markdown('<div class="card"><b>💻 Skills:</b><br>', unsafe_allow_html=True)
    for skill in data["Skills"]:
        st.markdown(f'<span class="skill">{skill}</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Education
    st.markdown(f'<div class="card"><b>🎓 Education:</b> {", ".join(data["Education"])}</div>', unsafe_allow_html=True)

    # ---------- SCORE ----------
    st.markdown("---")
    st.subheader("📊 Resume Score")

    st.progress(score / 100)

    if score >= 80:
        st.success(f"🔥 Excellent: {score}/100")
    elif score >= 50:
        st.warning(f"⚠️ Good: {score}/100")
    else:
        st.error(f"❌ Needs Improvement: {score}/100")

    # ---------- PDF ----------
    if st.button("📄 Generate Report"):
        pdf = generate_pdf(data, score)

        st.download_button(
            "⬇ Download PDF",
            pdf,
            file_name="resume_report.pdf",
            mime="application/pdf"
        )

    # ---------- SUGGESTIONS ----------
    st.markdown("---")
    st.subheader("💡 Suggestions")

    if suggestions:
        for s in suggestions:
            st.warning(s)
    else:
        st.success("Great resume! No major improvements needed 🎉")

    # ---------- JSON ----------
    json_data = json.dumps(data, indent=4)

    st.download_button(
        "⬇ Download JSON",
        json_data,
        file_name="resume.json",
        mime="application/json"
    )

else:
    st.warning("Please upload a resume PDF to start 🚀")
