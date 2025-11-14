from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
# from .models import user
import os, re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import io
from .forms import CVForm, QUALIFICATION_CHOICES, FIELD_CHOICES, TECH_SKILLS, SOFT_SKILLS, WORK_TYPE_CHOICES
# import openai
from decouple import config
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def cv_form(request):
    if request.method == 'POST':
        form = CVForm(request.POST)
        if form.is_valid():
            cv_data = format_cv_data(form.cleaned_data)
            ai_response = generate_cv_with_ai(cv_data)
            if ai_response and 'content' in ai_response:
                request.session['generated_cv'] = ai_response['content']

                return redirect('cv_result') 
            else:
                return render(request, 'cv_form.html', {
                    'form': form,
                    'error': 'Failed to generate CV. Please try again.'
                })

    else:
        form = CVForm()
    return render(request, 'cv_form.html', {'form': form})
   
def format_cv_data(form_data):
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
        'projects': form_data['projects'].split('\n') if form_data['projects'] else [],
        'experience': {
            'years': form_data['years_experience'],
            'work_type': dict(WORK_TYPE_CHOICES).get(form_data['work_type']),
            'role': form_data['role'],
            'organization': form_data['organization']
        }
        
    }

def generate_cv_with_ai(cv_data):
    """Generate CV content using OpenAI API with advanced prompt engineering"""
    try:
        experience_years = cv_data['experience']['years']
        is_fresher = experience_years < 1
        
        prompt = f"""
        Create a professional, well-formatted CV/resume using the following information.
        
        PERSONAL INFORMATION:
        - Full Name: {cv_data['basic_info']['name']}
        - Email: {cv_data['basic_info']['email']}
        - Phone: {cv_data['basic_info']['phone']}
        - Address: {cv_data['basic_info']['address']}
        
        EDUCATION:
        - Highest Qualification: {cv_data['education']['qualification']} in {cv_data['education']['field']}
        - Institution: {cv_data['education']['institution']}
        - Passing Year: {cv_data['education']['year']}
        - Grade: {cv_data['education']['grade']}
        
        TECHNICAL SKILLS: {', '.join(cv_data['skills']['technical'])}
        SOFT SKILLS: {', '.join(cv_data['skills']['soft'])}
        
        PROJECTS:
        {chr(10).join(['• ' + project for project in cv_data['projects']]) if cv_data['projects'] else 'No projects specified'}
        
        EXPERIENCE:
        - Years of Experience: {experience_years}
        - Role: {cv_data['experience']['role']}
        - Organization: {cv_data['experience']['organization']}
        - Employment Type: {cv_data['experience']['work_type']}
        
        IMPORTANT INSTRUCTIONS:
        1. If experience years is less than 1, treat as FRESHER and emphasize education, projects, and skills
        2. Create a comprehensive professional summary (3-4 lines) highlighting key strengths, education, technical skills, and career objectives
        3. If role is "NA", focus on academic projects and learning capabilities
        4. Make the CV look professional and suitable for entry-level positions
        5. Include sections: Personal Information, Professional Summary, Education, Technical Skills, Soft Skills, Projects, and any relevant certifications or achievements
        1. Use consistent spacing - exactly ONE blank line between sections
        2. Align all bullet points and content properly
        3. Use simple dash lines (────) for section headers, NOT box characters
        4. For bullet points:
           - Use "• " at the start of each bullet
           - Second line of bullet points should be indented with 2 spaces
        5. Section order: Personal Information, Education, Technical Skills, Soft Skills, Work Experience, Projects, Summary
        6. Keep all text left-aligned with consistent spacing
        7. If experience is 0 years, write "Fresher" in experience section
        8. Make sure there are no extra spaces at the start of lines
        9. Use proper line breaks and avoid long paragraphs
        
        EXAMPLE FORMAT:
        SECTION NAME
        ────────────
        • Bullet point one
            Additional details on next line
        • Bullet point two
            Additional details on next line
        
        Generate a clean, professionally formatted CV.
        that would be attractive to employers for { 'entry-level/fresher positions' if is_fresher else 'experienced positions' }.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert CV writer."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000
        )

        generated_text = response.choices[0].message.content.strip()
        return {"content": generated_text}

    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return generate_template_cv(cv_data)
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
    if cv_content is None:
        return redirect('cv_form')
    
    return render(request, 'cv_result.html', {'cv_content': cv_content})

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


