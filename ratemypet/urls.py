from django.urls import path
from ratemypet import views
from django.contrib.auth import views as auth_views


app_name = 'ratemypet'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('post/', views.post, name='post'),
    path('notifications/', views.notifications, name='notifications'),
    path('messages/', views.messages, name='messages'),
    path('messages/<str:username>/', views.conversation, name='conversation'),
    path('messages/<str:username>/send/', views.send_message, name='send_message'),
    path('messages/<str:username>/get/', views.get_message, name='get_message'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('settings/', views.settings_views, name='settings'),
    path('settings/delete/', views.delete_account, name='delete_account'),
    path('search/', views.search, name='search'),
    path('search/users/', views.search_users, name='search_users'),
    path('search/pets/', views.search_pets, name='search_pets'),
    path('send-friend/<int:user_id>/', views.add_friend, name='send_request'),
    path('accept-friend/<int:request_id>', views.accept_friend_request, name='accept_request'),
    path('decline-friend/<int:request_id>/', views.decline_friend_request, name='decline_request'),
    path('add-like/<int:post_id>/', views.add_like, name='add-like'),
]
