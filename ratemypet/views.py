from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from ratemypet.models import Message, Post, Comment, UserProfile, FriendRequest, PetCategory
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
def home(request):
    user = request.user
    posts = Post.objects.all().order_by('-date_posted')

    user_friends = request.user.profile.friends.all()
    friend_requests_received = FriendRequest.objects.filter(receiver=user)
    friend_requests_sent = FriendRequest.objects.filter(requester=user)

    context = {
        'posts': posts,
        'user_friends': user_friends,
        'friend_requests_received': friend_requests_received,
        'friend_requests_sent': friend_requests_sent
    }
    
    return render(request, 'ratemypet/home.html', context)

@login_required
def post(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        caption = request.POST.get('caption')
        
        existing_category_id = request.POST.get('category')
        new_category = request.POST.get('new_category')
        category = None

        if new_category:
            category, created = PetCategory.objects.get_or_create(name=new_category)
        elif existing_category_id:
            category = PetCategory.objects.get(id=existing_category_id)

        if image and caption and category:
            new_post = Post.objects.create(
                author=request.user,
                image=image,
                caption=caption,
                category=category
            )
            return redirect('ratemypet:home')
    
    pet_categories = PetCategory.objects.all()
    return render(request, 'ratemypet/post.html', {'pet_categories': pet_categories})

@login_required
def add_like(request):
    post_id = request.POST.get('id')
    post = get_object_or_404(Post, id=post_id)
    user = request.user

    if user in post.total_likes:
        post.likes.remove(user)
        liked = False
    else:
        post.likes.add(user)
        liked = True

    return JsonResponse({
        'liked': liked,
        'count': post.total_likes
    })

@login_required
def add_friend(request, user_id):
    receiving_user = get_object_or_404(User, id=user_id)
    FriendRequest.objects.get_or_create(requester=request.user, receiver=receiving_user)
    return redirect('ratemypet:home')
    
@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id)

    if friend_request.receiver == request.user:
        request.user.profile.friends.add(friend_request.requester)
        friend_request.requester.profile.friends.add(request.user)
        friend_request.delete()
    
    return redirect('ratemypet:notifications')

@login_required
def decline_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id)

    if friend_request.receiver == request.user:
        friend_request.delete()
    return redirect('ratemypet:notifications')
    
@login_required
def notifications(request):
    # Get comments on the current user's posts
    user_posts = Post.objects.filter(author=request.user)
    recent_comments = Comment.objects.filter(post__in=user_posts).exclude(
        author=request.user
    ).order_by('-id')[:20]
    pending_requests = FriendRequest.objects.filter(receiver=request.user)

    # Get posts by the user that have likes
    liked_posts = user_posts.filter(likes__gt=False).distinct()

    context = {
        'recent_comments': recent_comments,
        'liked_posts': liked_posts,
        'pending_requests': pending_requests
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
    ).order_by('timestamp')

    context = {'chat_messages': chat_messages, 'other_user': other_user}
    return render(request, 'ratemypet/conversation.html', context)

@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    user_posts = Post.objects.filter(author=request.user)

    return render(request, 'ratemypet/profile.html', {'user_posts': user_posts})

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        profile.about = request.POST.get('caption')

        if 'image' in request.FILES:
            profile.picture = request.FILES['image']

        profile.save()

        return redirect('ratemypet:profile')
    
    return render(request, 'ratemypet/edit.html', {'profile': profile})

@login_required
def settings_views(request):
    if request.method == "POST":
        new_password = request.POST.get("new_password")

        if new_password:
            request.user.set_password(new_password)
            request.user.save()

            return redirect('login')

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

@login_required
@require_POST
def send_message(request, username):
    other_user = get_object_or_404(User, user = username)
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'success': False, 'error': 'message can not be empty'})
        message = Message.objects.create(sender = request.user, receiver= other_user, content = content)

        return JsonResponse({'success' : True, 'message' :{
            'sender: ': message.sender.username,
            'content: ': message.content,
            'timestamp': message.timestamp.strftime('%b %d, %H:%M')
        }})
@login_required
def get_message(request, username):
    other_user = get_object_or_404(User, username=username)
    chat_messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('timestamp')

    message_data = []
    for message in chat_messages:
        message_data.append({
            'sender': message.sender.username,
            'content': message.content,
            'timestamp': message.timestamp.strftime('%b %d, %H:%M'),
            'is_own': message.sender == request.user
        })
        return JsonResponse({'message': message_data})
        
    
