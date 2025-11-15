from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
import os, re
from .models import jobs
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import io
from django.conf import settings
from .forms import CVForm, QUALIFICATION_CHOICES, FIELD_CHOICES, TECH_SKILLS, SOFT_SKILLS, WORK_TYPE_CHOICES, PROJECT_CHOICES
from decouple import config
from openai import OpenAI

def cv_form(request):
    if request.method == 'POST':
        form = CVForm(request.POST)
        print("⚠️ CV FORM SUBMITTED")
        print("FORM VALID:", form.is_valid())

        if form.is_valid():
            print("CLEANED DATA:", form.cleaned_data)

            cv_data = format_cv_data(form.cleaned_data)
            request.session['cv_data'] = cv_data   

            ai_response = generate_cv_with_ai(cv_data)
            print("AI RESPONSE RAW:", ai_response)

            if ai_response and ai_response.get("content"):
                request.session['generated_cv'] = ai_response['content']
                return redirect('cv_result')
            else:
                print("ERROR: AI returned None or empty content")
                return render(request, 'cv_form.html', {
                    'form': form,
                    'error': 'Failed to generate CV. Please try again.'
                })

    else:
        form = CVForm()

    return render(request, 'cv_form.html', {'form': form})
   
def format_cv_data(form_data):

    selected_project_names = [
        dict(PROJECT_CHOICES).get(code)
        for code in form_data['selected_projects']
    ]
    typed_projects = form_data['projects'].split('\n') if form_data['projects'] else []

    return{
        'basic_info':{
            'name': form_data['name'],
            'email': form_data['email'],
            'phone': form_data['phone'],
            'address': form_data['address']
        },
        'education': {
            'qualification': dict(QUALIFICATION_CHOICES).get(form_data['highest_qualification']),
            'field': dict(FIELD_CHOICES).get(form_data['field_of_study']),
            'institution': form_data['institution'],
            'year': form_data['passing_year'],
            'grade': form_data['grade']
        },
        'skills': {
            'technical': [dict(TECH_SKILLS).get(skill) for skill in form_data['technical_skills']],
            'soft': [dict(SOFT_SKILLS).get(skill) for skill in form_data['soft_skills']]
        },
        'projects': {
            'selected': selected_project_names,
            'custom': typed_projects
        },

        # 'projects': form_data['projects'].split('\n') if form_data['projects'] else [],
        'experience': {
            'years': form_data['years_experience'],
            'work_type': dict(WORK_TYPE_CHOICES).get(form_data['work_type']),
            'role': form_data['role'],
            'organization': form_data['organization']
        }
        
    }

def generate_cv_with_ai(cv_data):
    """Generate CV content using OpenAI API with advanced prompt"""
    try:
        # client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        client = OpenAI(api_key=config("OPENAI_API_KEY"))

        prompt = f"""
        Create a professional, well-formatted CV/resume using the following information:

        {cv_data}

        IMPORTANT RULES:
        - Use clean formatting with section headers and bullet points
        - Keep everything left-aligned
        - If experience < 1, treat as fresher and adjust experience section
        - Add Professional Summary, Skills, Projects, Education, Experience
        """

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt

        )

        cv_text = response.output_text

        if not cv_text:
            return None

        return {"content": cv_text}

    
    except Exception as e:
        import traceback
        print("OpenAI API Error:", e)
        traceback.print_exc()
        return None

def generate_template_cv(cv_data):
    """Fallback template-based CV generation"""
    experience_years = cv_data['experience']['years']
    is_fresher = experience_years < 1
    if is_fresher:
        experience_section = "EXPERIENCE\n───────────\n• Fresher - Seeking entry-level opportunities to apply academic knowledge and technical skills"
    else:
        experience_section = f"EXPERIENCE\n───────────\n• {cv_data['experience']['role']}\n  {cv_data['experience']['organization']} | {cv_data['experience']['years']} years | {cv_data['experience']['work_type']}"
    if is_fresher:
        summary = f"""
        SUMMARY
        ───────
        Recent {cv_data['education']['field']} graduate with strong academic background ({cv_data['education']['grade']}) from {cv_data['education']['institution']}. 
        Proficient in {', '.join(cv_data['skills']['technical'][:3])} with hands-on experience through academic projects. 
        Demonstrated {', '.join(cv_data['skills']['soft'][:3])} skills with a passion for learning and contributing to innovative projects. 
        Seeking to leverage technical expertise and problem-solving abilities in an entry-level position.
        """
    else:
        summary = f"""
        SUMMARY
        ───────
        Experienced {cv_data['experience']['role']} with {cv_data['experience']['years']} years in the field. 
        Strong educational background in {cv_data['education']['field']} from {cv_data['education']['institution']}. 
        Expertise in {', '.join(cv_data['skills']['technical'][:4])} with proven track record in {cv_data['experience']['work_type'].lower()} environments. 
        Excellent {', '.join(cv_data['skills']['soft'][:3])} skills with ability to deliver results in challenging environments.
        """
    
    content = f"""
    PROFESSIONAL CURRICULUM VITAE
    
    PERSONAL INFORMATION
    ───────────────────
    Name: {cv_data['basic_info']['name']}
    Email: {cv_data['basic_info']['email']}
    Phone: {cv_data['basic_info']['phone']}
    Address: {cv_data['basic_info']['address']}
    
    EDUCATION
    ─────────
    • {cv_data['education']['qualification']} in {cv_data['education']['field']}
      {cv_data['education']['institution']} | {cv_data['education']['year']} | Grade: {cv_data['education']['grade']}
    
    TECHNICAL SKILLS
    ────────────────
    {chr(10).join(['• ' + skill for skill in cv_data['skills']['technical']])}
    
    SOFT SKILLS
    ───────────
    {chr(10).join(['• ' + skill for skill in cv_data['skills']['soft']])}
    
    WORK EXPERIENCE
    ───────────────
    • {cv_data['experience']['role']}
      {cv_data['experience']['organization']} | {cv_data['experience']['years']} years | {cv_data['experience']['work_type']}
    
    PROJECTS
    ────────
    {chr(10).join(['• ' + project for project in cv_data['projects']]) if cv_data['projects'] else '• No projects specified'}
    
    SUMMARY
    ───────
    Professional with {cv_data['experience']['years']} years of experience in {cv_data['experience']['role']}. 
    Strong background in {cv_data['education']['field']} with expertise in {', '.join(cv_data['skills']['technical'][:3])}.
    """
    
    return {'content': content}

def cv_result(request):
    cv_content = request.session.get('generated_cv', None)
    cv_data = request.session.get('cv_data', None)

    if cv_content is None or cv_data is None:
        return redirect('cv_form')
    recommended = recommended_jobs(cv_data)[:10]
    return render(request, 'cv_result.html', {
        'cv_content': cv_content,
        'recommended_jobs': recommended
    })

def download_pdf(request):
    cv_content = request.session.get('generated_cv', None)
    if not cv_content:
        return redirect('cv_form')

    buffer = io.BytesIO()

    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica", 10)

    lines = cv_content.split('\n')

    # Starting position
    y = height - 50
    line_height = 12

    for line in lines:
        # If the line is too long, split it
        if p.stringWidth(line) > width - 100:
            # Split the line into multiple lines
            wrapped_lines = simpleSplit(line, "Helvetica", 10, width - 100)
            for wrapped_line in wrapped_lines:
                if y < 50:  
                    p.showPage()
                    p.setFont("Helvetica", 10)
                    y = height - 50
                p.drawString(50, y, wrapped_line)
                y -= line_height
        else:
            if y < 50:
                p.showPage()
                p.setFont("Helvetica", 10)
                y = height - 50
            p.drawString(50, y, line)
            y -= line_height

    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="AI_Generated_CV.pdf"'

    return response

def normalize_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).lower().strip() for v in value if v]
    if isinstance(value, str):
        return [v.lower().strip() for v in value.split(",") if v.strip()]
    return []

def calculate_similarity(cv, job):

    cv_skills = normalize_list(cv["skills"]["technical"])
    job_skills = normalize_list(job.skills)

    skill_score = (
        len(set(cv_skills) & set(job_skills)) / len(set(cv_skills) | set(job_skills))
        if (cv_skills or job_skills) else 0
    )


    cv_soft = normalize_list(cv["skills"]["soft"])
    job_soft = normalize_list(job.soft_skills)

    soft_skill_score = (
        len(set(cv_soft) & set(job_soft)) / len(set(cv_soft) | set(job_soft))
        if (cv_soft or job_soft) else 0
    )


    edu = (cv["education"]["qualification"] or "").lower()
    job_edu = (job.education_required or "").lower()

    if job_edu and edu in job_edu:
        education_score = 1
    else:
        education_score = 0


    try:
        cv_exp = int(cv["experience"]["years"])
    except:
        cv_exp = 0

    job_exp = job.experience_required or 0

    diff = abs(cv_exp - job_exp)
    experience_score = max(0, 1 - (diff / max(job_exp, 1)))

    # --- Weighted total ---
    final_score = (
        skill_score * 0.40 +
        soft_skill_score * 0.15 +
        education_score * 0.20 +
        experience_score * 0.25
    ) * 100

    return round(final_score, 2)


def recommended_jobs(cv_data):
    all_jobs = jobs.objects.all()
    recommendations = []

    for job in all_jobs:
        try:
            score = calculate_similarity(cv_data, job)
            recommendations.append({"job": job, "score": score})
        except Exception as e:
            print("Error in job similarity:", e)
            continue
    
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    return recommendations


