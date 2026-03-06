from django.shortcuts import render

def home(request):
    return render(request, 'ratemypet/home.html')
