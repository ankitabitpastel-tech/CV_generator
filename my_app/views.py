from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
import os, re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import io
from .forms import CVForm, QUALIFICATION_CHOICES, FIELD_CHOICES, TECH_SKILLS, SOFT_SKILLS, WORK_TYPE_CHOICES
from openai import OpenAI
from django.conf import settings
import logging
import html

logger = logging.getLogger(__name__)

# Initialize OpenAI client with error handling
try:
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    OPENAI_AVAILABLE = True
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.warning(f"OpenAI initialization failed: {e}")
    OPENAI_AVAILABLE = False
    client = None

def cv_form(request):
    if request.method == 'POST':
        form = CVForm(request.POST)
        if form.is_valid():
            logger.info("⚠️ CV FORM SUBMITTED")
            logger.info(f"FORM VALID: {form.is_valid()}")
            logger.info(f"CLEANED DATA: {form.cleaned_data}")
            
            try:
                cv_data = format_cv_data(form.cleaned_data)
                
                # Try AI generation first
                ai_response = generate_cv_with_ai(cv_data)
                logger.info(f"AI RESPONSE RAW: {ai_response}")
                
                if ai_response and 'content' in ai_response:
                    # Clean and encode the content before storing in session
                    cleaned_content = clean_cv_content(ai_response['content'])
                    request.session['generated_cv'] = cleaned_content
                    request.session.modified = True
                    logger.info("AI CV stored in session successfully")
                    messages.success(request, 'AI-generated CV created successfully!')
                    return redirect('cv_result')
                else:
                    # Fallback to template
                    template_cv = generate_template_cv(cv_data)
                    cleaned_content = clean_cv_content(template_cv['content'])
                    request.session['generated_cv'] = cleaned_content
                    request.session.modified = True
                    logger.info("Template CV stored in session")
                    messages.info(request, 'CV created using template (AI service temporarily unavailable)')
                    return redirect('cv_result')
                    
            except Exception as e:
                logger.error(f"CV generation error: {str(e)}", exc_info=True)
                # Final fallback
                try:
                    cv_data = format_cv_data(form.cleaned_data)
                    template_cv = generate_template_cv(cv_data)
                    cleaned_content = clean_cv_content(template_cv['content'])
                    request.session['generated_cv'] = cleaned_content
                    request.session.modified = True
                    messages.warning(request, 'CV created with basic template due to technical issues')
                    return redirect('cv_result')
                except Exception as final_error:
                    logger.error(f"Final fallback also failed: {final_error}")
                    messages.error(request, 'Failed to generate CV. Please try again.')
                    return render(request, 'cv_form.html', {'form': form})

    else:
        form = CVForm()
    return render(request, 'cv_form.html', {'form': form})

def clean_cv_content(content):
    """Clean CV content to prevent encoding/session issues"""
    if not content:
        return ""
    
    # Replace problematic characters
    content = content.replace('–', '-')  # Replace en-dash with regular dash
    content = content.replace('—', '-')  # Replace em-dash with regular dash
    content = content.replace('•', '*')  # Replace bullet points with asterisks
    content = content.replace('·', '*')  # Replace middle dots
    content = content.replace('“', '"')  # Replace smart quotes
    content = content.replace('”', '"')  # Replace smart quotes
    content = content.replace("'", "'")  # Replace smart single quotes
    
    # Remove any other non-ASCII characters if they persist
    content = content.encode('ascii', 'ignore').decode('ascii')
    
    return content

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
    """Generate CV content using OpenAI API with comprehensive error handling"""
    
    # Check if OpenAI is available
    if not OPENAI_AVAILABLE or client is None:
        logger.warning("OpenAI client not available")
        return generate_template_cv(cv_data)
    
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
        {chr(10).join(['* ' + project for project in cv_data['projects']]) if cv_data['projects'] else 'No projects specified'}
        
        EXPERIENCE:
        - Years of Experience: {experience_years}
        - Role: {cv_data['experience']['role']}
        - Organization: {cv_data['experience']['organization']}
        - Employment Type: {cv_data['experience']['work_type']}
        
        IMPORTANT INSTRUCTIONS:
        1. Use only basic ASCII characters (no special unicode characters)
        2. Use asterisks (*) for bullet points instead of special bullets
        3. Use regular dashes (-) instead of em-dashes or en-dashes
        4. Use regular quotes (") instead of smart quotes
        5. Create a professional CV with proper sections
        6. Use clean formatting with consistent spacing
        7. Include: Personal Info, Summary, Education, Skills, Experience, Projects
        8. Make it suitable for job applications
        9. Use proper section headers with simple characters
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a professional CV writer. Create well-structured, professional resumes using only basic ASCII characters (no unicode). Use asterisks for bullets, regular dashes, and simple formatting."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        generated_text = response.choices[0].message.content.strip()
        logger.info("AI CV generation successful")
        return {'content': generated_text}
        
    except Exception as e:
        logger.error(f"OpenAI API Error: {str(e)}")
        # Check for specific quota errors
        if "quota" in str(e).lower() or "429" in str(e) or "insufficient_quota" in str(e):
            logger.warning("OpenAI quota exceeded - using template")
        return generate_template_cv(cv_data)

def generate_template_cv(cv_data):
    """High-quality template-based CV generation with simple characters"""
    experience_years = cv_data['experience']['years']
    is_fresher = experience_years < 1
    
    # Professional Summary
    if is_fresher:
        summary = f"Recent {cv_data['education']['field']} graduate with strong academic background ({cv_data['education']['grade']}) from {cv_data['education']['institution']}. Proficient in {', '.join(cv_data['skills']['technical'][:3])} with hands-on experience through academic projects. Seeking to leverage technical expertise in an entry-level position."
    else:
        summary = f"Experienced {cv_data['experience']['role']} with {cv_data['experience']['years']} years in the field. Strong background in {cv_data['education']['field']} with expertise in {', '.join(cv_data['skills']['technical'][:3])}. Excellent {', '.join(cv_data['skills']['soft'][:3])} skills."
    
    # Experience Section
    if is_fresher or not cv_data['experience']['role']:
        experience_section = "Fresher - Seeking entry-level opportunities to apply academic knowledge and technical skills"
    else:
        experience_section = f"{cv_data['experience']['role']} at {cv_data['experience']['organization']} ({cv_data['experience']['years']} years, {cv_data['experience']['work_type']})"
    
    content = f"""
PROFESSIONAL CURRICULUM VITAE

PERSONAL INFORMATION
-------------------
Name: {cv_data['basic_info']['name']}
Email: {cv_data['basic_info']['email']}
Phone: {cv_data['basic_info']['phone']}
Address: {cv_data['basic_info']['address']}

PROFESSIONAL SUMMARY
-------------------
{summary}

EDUCATION
---------
* {cv_data['education']['qualification']} in {cv_data['education']['field']}
  {cv_data['education']['institution']} | {cv_data['education']['year']} | Grade: {cv_data['education']['grade']}

TECHNICAL SKILLS
----------------
{chr(10).join(['* ' + skill for skill in cv_data['skills']['technical']])}

SOFT SKILLS
-----------
{chr(10).join(['* ' + skill for skill in cv_data['skills']['soft']])}

EXPERIENCE
----------
* {experience_section}

PROJECTS
--------
{chr(10).join(['* ' + project for project in cv_data['projects']]) if cv_data['projects'] else '* No projects specified'}

---
Generated by CV Generator
"""
    
    return {'content': content.strip()}

def cv_result(request):
    try:
        cv_content = request.session.get('generated_cv', None)
        if cv_content is None:
            logger.warning("No CV content in session, redirecting to form")
            messages.error(request, 'No CV data found. Please fill out the form first.')
            return redirect('cv_form')
        
        logger.info("Rendering CV result template")
        return render(request, 'cv_result.html', {'cv_content': cv_content})
        
    except Exception as e:
        logger.error(f"Error in cv_result: {str(e)}", exc_info=True)
        messages.error(request, 'Error displaying CV. Please try again.')
        return redirect('cv_form')

def download_pdf(request):
    cv_content = request.session.get('generated_cv', None)
    if not cv_content:
        messages.error(request, 'No CV data found. Please generate a CV first.')
        return redirect('cv_form')

    try:
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        p.setFont("Helvetica", 10)
        lines = cv_content.split('\n')
        y = height - 50
        line_height = 12

        for line in lines:
            if p.stringWidth(line) > width - 100:
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
        response['Content-Disposition'] = 'attachment; filename="Professional_CV.pdf"'
        return response
        
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        messages.error(request, 'Error generating PDF. Please try again.')
        return redirect('cv_result')