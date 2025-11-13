from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class user(models.Model):
    full_name = models.CharField(max_length=255, blank=False, null=False)
    email = models.EmailField(unique=True, blank=False, null=False)
    phone = models.CharField(max_length=15, blank=True, null=True)
    password = models.CharField(max_length=255, blank=False, null=False)

    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    class Meta:
        db_table = 'users'

