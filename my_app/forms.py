from django import forms

QUALIFICATION_CHOICES = [
    ('high_school', 'High School'),
    ('diploma', 'Diploma'),
    ('bachelor', 'Bachelor\'s Degree'),
    ('master', 'Master\'s Degree'),
    ('phd', 'PhD'),
    ('associate', 'Associate Degree'),
    ('professional', 'Professional Certification'),
]

FIELD_CHOICES = [
    ('cs', 'Computer Science'),
    ('engineering', 'Engineering'),
    ('business', 'Business Administration'),
    ('medicine', 'Medicine'),
    ('arts', 'Arts & Humanities'),
    ('science', 'Natural Sciences'),
    ('law', 'Law'),
    ('education', 'Education'),
    ('other', 'Other'),
]

TECH_SKILLS = [
    ('python', 'Python'),
    ('javascript', 'JavaScript'),
    ('java', 'Java'),
    ('django', 'Django'),
    ('react', 'React'),
    ('nodejs', 'Node.js'),
    ('sql', 'SQL'),
    ('aws', 'AWS'),
    ('docker', 'Docker'),
    ('git', 'Git'),
    ('html', 'HTML/CSS'),
    ('ml', 'Machine Learning'),
    ('microsoft office', 'Microsoft Office'),
    ('g-suit', 'G-Suit'),


]

SOFT_SKILLS = [
    ('communication', 'Communication'),
    ('leadership', 'Leadership'),
    ('teamwork', 'Teamwork'),
    ('problem_solving', 'Problem Solving'),
    ('time_management', 'Time Management'),
    ('adaptability', 'Adaptability'),
    ('creativity', 'Creativity'),
    ('critical_thinking', 'Critical Thinking'),
]

PROJECT_CHOICES = [
    ('web', 'Web Development'),
    ('mobile', 'Mobile App'),
    ('ml', 'Machine Learning'),
    ('business', 'Business Marketing'),
    ('media', 'Media Handling'),
]



WORK_TYPE_CHOICES = [
    ('full_time', 'Full-time'),
    ('part_time', 'Part-time'),
    ('contract', 'Contract'),
    ('freelance', 'Freelance'),
    ('internship', 'Internship'),
    ('remote', 'Remote'),
]

class CVForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    
    highest_qualification = forms.ChoiceField(
        choices=QUALIFICATION_CHOICES, 
        required=True
    )

    field_of_study = forms.ChoiceField(
        choices=FIELD_CHOICES, 
        required=True
    )
    institution = forms.CharField(max_length=200, required=True)
    passing_year = forms.IntegerField(
        min_value=1900, 
        max_value=2030, 
        required=True
    )
    grade = forms.CharField(max_length=10, required=True)
    
    technical_skills = forms.MultipleChoiceField(
        choices=TECH_SKILLS,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    soft_skills = forms.MultipleChoiceField(
        choices=SOFT_SKILLS,
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    selected_projects = forms.MultipleChoiceField(
        choices=PROJECT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select the types of projects you have worked on"
    )

    projects = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Describe any custom projects (one per line)"
    )
    
    # projects = forms.CharField(
    #     widget=forms.Textarea,
    #     required=False,
    #     help_text="Describe your projects (one per line)"
    # )
    
    years_experience = forms.IntegerField(
        min_value=0,
        max_value=50,
        required=True
    )
    work_type = forms.ChoiceField(
        choices=WORK_TYPE_CHOICES,
        required=False
    )
    role = forms.CharField(max_length=100, required=False)
    organization = forms.CharField(max_length=100, required=False)

    __all__ = ['CVForm', 'QUALIFICATION_CHOICES', 'FIELD_CHOICES', 'TECH_SKILLS', 'SOFT_SKILLS', 'WORK_TYPE_CHOICES']


class CVStepForm(forms.Form):

    def __init__(self, *args, **kwargs):
        fields_to_include = kwargs.pop('fields', [])
        super().__init__(*args, **kwargs)
        
        for field_name in list(self.fields.keys()):
            if field_name not in fields_to_include:
                del self.fields[field_name]