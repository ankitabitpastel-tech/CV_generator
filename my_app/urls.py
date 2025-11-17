from django.urls import path 
from . import views

urlpatterns = [
    path('', views.cv_form, name='cv_form'),
    path('step/<int:step>/', views.cv_stepper, name='cv_stepper'),
    path('result/', views.cv_result, name='cv_result'),
    path('download_pdf/', views.download_pdf, name='download_pdf'),
    path('legacy/', views.cv_form, name='cv_form_legacy'),

]

    # path('signin/', views.signin, name='signin'),
    # path('signup/', views.signup, name='signup'),
    # path('signout/', views.signout, name='signout'),
    # path('home/', views.home, name='home'),

