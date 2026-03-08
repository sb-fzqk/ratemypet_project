from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    return render(request, 'ratemypet/home.html')

@login_required
def post(request):
    return render(request, 'ratemypet/post.html')

@login_required
def notifications(request):
    return render(request, 'ratemypet/notifications.html')

@login_required
def messages(request):
    return render(request, 'ratemypet/messages.html')

@login_required
def profile(request):
    return render(request, 'ratemypet/profile.html')

@login_required
def edit_profile(request):
    return render(request, 'ratemypet/edit.html')

@login_required
def settings_views(request):
    return render(request, 'ratemypet/settings.html')

@login_required
def search(request):
    return render(request, 'ratemypet/search.html')    

@login_required
def search_users(request):
    return render(request, 'ratemypet/users.html')  

@login_required
def search_pets(request):
    return render(request, 'ratemypet/pets.html')  