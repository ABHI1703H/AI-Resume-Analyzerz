import PyPDF2
import spacy
from flask import Flask, request, render_template
import re

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

# Flask application
app = Flask(__name__)

# Required skills for roles
required_skills = {
    "software_engineer": ["python", "java", "c++", "machine learning", "data structures"],
    "project_manager": ["project management", "agile", "scrum", "risk management", "stakeholder management"]
}

# Extract text from PDF
def extract_text_from_pdf(file):
    text = ""
    reader = PyPDF2.PdfReader(file)
    for page in range(len(reader.pages)):
        text += reader.pages[page].extract_text()
    return text

# Extract information from text
def extract_information(text):
    doc = nlp(text)
    name = ""
    email = ""
    phone = ""
    skills = []
    awards = []
    projects = []

    # Extract email using regex
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    email_matches = email_pattern.findall(text)
    if email_matches:
        email = email_matches[0]

    # Extract phone number using regex
    phone_pattern = re.compile(r'\+?\d[\d -]{8,12}\d')
    phone_matches = phone_pattern.findall(text)
    if phone_matches:
        phone = phone_matches[0]

    # Extract name using spaCy NER
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text
            break  # Take the first found name

    # Extract skills by looking for known skill terms
    for token in doc:
        if token.text.lower() in required_skills["software_engineer"] or token.text.lower() in required_skills["project_manager"]:
            skills.append(token.text.lower())

    # Remove duplicates from skills
    skills = list(set(skills))

    # Extract awards and recognitions
    award_keywords = ["award", "recognition", "honor", "prize", "certificate"]
    for sent in doc.sents:
        if any(keyword in sent.text.lower() for keyword in award_keywords):
            awards.append(sent.text.strip())

    # Extract projects
    project_keywords = ["project", "developed", "implemented", "designed"]
    for sent in doc.sents:
        if any(keyword in sent.text.lower() for keyword in project_keywords):
            projects.append(sent.text.strip())

    return {"name": name, "email": email, "phone": phone, "skills": skills, "awards": awards, "projects": projects}

# Match extracted skills with required skills
def match_skills(extracted_skills, role):
    role_skills = required_skills.get(role, [])
    matched_skills = set(extracted_skills).intersection(set(role_skills))
    return len(matched_skills) / len(role_skills)

# Analyze experience
def analyze_experience(text):
    experience_keywords = ["years of experience", "experience in", "worked as", "employment history"]
    for keyword in experience_keywords:
        if keyword in text.lower():
            return True
    return False

# Calculate resume score
def calculate_score(matched_skills_ratio, experience_relevant, awards_count, projects_count):
    score = matched_skills_ratio * 0.5
    if experience_relevant:
        score += 0.2
    score += min(awards_count * 0.1, 0.1)  # Cap at 10%
    score += min(projects_count * 0.2, 0.2)  # Cap at 20%
    return score

# Provide feedback based on score
def provide_feedback(score):
    if score < 0.5:
        return "Your resume needs significant improvements in skills and experience."
    elif score < 0.7:
        return "Your resume is good but can be improved in some areas."
    else:
        return "Your resume is strong and well-matched to the job requirements."

# Flask routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files['resume']
    text = extract_text_from_pdf(file)
    info = extract_information(text)
    matched_skills_ratio = match_skills(info['skills'], 'software_engineer')
    experience_relevant = analyze_experience(text)
    score = calculate_score(matched_skills_ratio, experience_relevant, len(info['awards']), len(info['projects']))
    feedback = provide_feedback(score)
    return render_template('result.html', info=info, score=score, feedback=feedback)

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)
