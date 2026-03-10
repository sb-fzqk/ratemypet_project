from django.urls import path
from ratemypet import views
from django.contrib.auth import views as auth_views


app_name = 'ratemypet'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('post/', views.post, name='post'),
    path('notifications/', views.notifications, name='notifications'),
    path('messages/', views.messages, name='messages'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('settings/', views.settings_views, name='settings'),
    path('search/', views.search, name='search'),
    path('search/users/', views.search_users, name='search_users'),
    path('search/pets/', views.search_pets, name='search_pets'),
]