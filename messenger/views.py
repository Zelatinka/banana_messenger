from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import RegistrationForm
from django.contrib.auth.decorators import login_required
from .models import Conversation, Friendship, FriendRequest, UserProfile
from .forms import MessageForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # Redirect to home page after registration
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def custom_logout(request):
    logout(request)
    return redirect('login')  # Redirect to the login page after logout

@login_required
def home(request):
    conversations = request.user.conversations.all()
    all_users = User.objects.exclude(id=request.user.id)
    return render(request, 'home.html', {
        'conversations': conversations,
        'all_users': all_users
        })

@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            return redirect('conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()
    messages = conversation.messages.order_by('timestamp')
    participant_ids = list(conversation.participants.values_list('id', flat=True))
    return render(request, 'conversation_detail.html', {
        'conversation': conversation,
        'messages': messages,
        'participant_ids': participant_ids,
        'form': form,
        'user_name': request.user.username
        })

@login_required
def start_conversation(request, recipient_id):
    recipient = get_object_or_404(User, id=recipient_id)

    conversation = Conversation.objects.get_or_create_between(request.user, recipient)
    
    return redirect('conversation_detail', conversation_id=conversation.id)

@login_required
def start_group_conversation(request):
    if request.method == 'POST':
        participant_ids = request.POST.getlist('participants')
        participants = User.objects.filter(id__in=participant_ids)

        if len(participants) < 1:
            return redirect('home')

        conversation = Conversation.objects.create(is_group=True)
        conversation.participants.add(request.user, *participants)

        return redirect('conversation_detail', conversation_id=conversation.id)

    all_users = User.objects.exclude(id=request.user.id)
    return render(request, 'start_group_conversation.html', {
        'all_users': all_users
        })

@login_required
def video_chat(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    participant_ids = list(conversation.participants.values_list('id', flat=True))  # Get participant IDs
    return render(request, 'video_chat.html',
        {'conversation': conversation,
         'participant_ids': participant_ids
         })
    
@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    if to_user != request.user:  # Prevent sending requests to yourself
        FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
    return redirect('home')

@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    Friendship.objects.create(user=friend_request.to_user, friend=friend_request.from_user)
    Friendship.objects.create(user=friend_request.from_user, friend=friend_request.to_user)
    friend_request.delete()
    return redirect('home')

@login_required
def reject_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.delete()
    return redirect('home')

@login_required
def friend_list(request):
    friends = request.user.friends.all()
    incoming_requests = request.user.incoming_requests.all()
    outgoing_requests = request.user.outgoing_requests.all()
    return render(request, 'friend_list.html', {
        'friends': friends,
        'incoming_requests': incoming_requests,
        'outgoing_requests': outgoing_requests,
    })

@login_required
def user_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    is_friend = Friendship.objects.filter(user=request.user, friend=user).exists()
    has_pending_request = FriendRequest.objects.filter(from_user=request.user, to_user=user).exists()
    return render(request, 'user_profile.html', {
        'user': user,
        'is_friend': is_friend,
        'has_pending_request': has_pending_request,
    })
    
@login_required
@csrf_exempt
def update_profile(request):
    if request.method == 'POST':
        bio = request.POST.get('bio')
        profile_picture = request.FILES.get('profile_picture')

        profile = request.user.profile
        if bio:
            profile.bio = bio
        if profile_picture:
            profile.profile_picture = profile_picture
        profile.save()

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})