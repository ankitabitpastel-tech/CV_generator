from django.db import models
from django.contrib.postgres.fields import ArrayField

class jobs(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=150)
    company = models.CharField(max_length=150)
    location = models.CharField(max_length=100)
    
    experience_required = models.IntegerField()
    job_type = models.CharField(max_length=50)
    
    skills = ArrayField(
        base_field=models.TextField()
    )
    
    soft_skills = ArrayField(
        base_field=models.TextField()
    )
    
    education_required = models.CharField(max_length=150, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField()

    class Meta:
        managed = False                 
        db_table = 'jobs'               

    def __str__(self):
        return f"{self.title} - {self.company}"
