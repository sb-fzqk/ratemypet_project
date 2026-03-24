from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from ratemypet.models import Message, Post, Comment, UserProfile

def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        UserProfile.objects.create(
            user=user
        )
        login(request, user)
        return redirect("ratemypet:home")
    return render(request, "ratemypet/register.html")

@login_required
def home(request):
    return render(request, 'ratemypet/home.html')

@login_required
def post(request):
    return render(request, 'ratemypet/post.html')

@login_required
def notifications(request):
    # Get comments on the current user's posts
    user_posts = Post.objects.filter(user_name=request.user)
    recent_comments = Comment.objects.filter(post__in=user_posts).exclude(
        user_name=request.user
    ).order_by('-id')[:20]

    # Get posts by the user that have likes
    liked_posts = user_posts.filter(likes__gt=0)

    context = {
        'recent_comments': recent_comments,
        'liked_posts': liked_posts,
    }
    return render(request, 'ratemypet/notifications.html', context)

@login_required
def messages(request):
    # Get all users the current user has exchanged messages with
    sent = Message.objects.filter(sender=request.user).values_list('receiver', flat=True)
    received = Message.objects.filter(receiver=request.user).values_list('sender', flat=True)
    contact_ids = set(sent) | set(received)
    contacts = User.objects.filter(id__in=contact_ids)

    # Get all users for starting new conversations
    all_users = User.objects.exclude(id=request.user.id)

    context = {'contacts': contacts, 'all_users': all_users}
    return render(request, 'ratemypet/messages.html', context)

@login_required
def conversation(request, username):
    other_user = get_object_or_404(User, username=username)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                content=content,
            )
        return redirect('ratemypet:conversation', username=username)

    # Get all messages between the two users
    chat_messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    )

    context = {'chat_messages': chat_messages, 'other_user': other_user}
    return render(request, 'ratemypet/conversation.html', context)

@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    return render(request, 'ratemypet/profile.html')

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        profile.about = request.POST.get('caption')

        if 'image' in request.FILES:
            profile.picture = request.FILES['image']

        profile.save()

        return redirect('accounts:profile')
    
    return render(request, 'ratemypet/edit.html', {'profile': profile})

@login_required
def settings_views(request):
    return render(request, 'ratemypet/settings.html')

@login_required
def delete_account(request):
    if request.method == 'POST':
        request.user.delete()
        return redirect('login')

@login_required
def search(request):
    return render(request, 'ratemypet/search.html')    

@login_required
def search_users(request):
    return render(request, 'ratemypet/users.html')  

@login_required
def search_pets(request):
    return render(request, 'ratemypet/pets.html')  
