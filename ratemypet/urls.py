from django.urls import path
from ratemypet import views
from django.contrib.auth import views as auth_views


app_name = 'ratemypet'

urlpatterns = [
    path('home/', views.home, name='home')
]