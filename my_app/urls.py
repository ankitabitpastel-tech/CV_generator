from django.urls import path 
from . import views

urlpatterns = [
    path('', views.cv_form, name='cv_form'),
    path('result/', views.cv_result, name='cv_result'),
    path('download_pdf/', views.download_pdf, name='download_pdf'),
]

    # path('signin/', views.signin, name='signin'),
    # path('signup/', views.signup, name='signup'),
    # path('signout/', views.signout, name='signout'),
    # path('home/', views.home, name='home'),

