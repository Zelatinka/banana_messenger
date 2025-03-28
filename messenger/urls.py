from django.urls import include, path, re_path
from . import views
from django.contrib.auth import views as auth_views
from messenger import views as messenger_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('', views.home, name='home'),
    path('start-conversation/<int:recipient_id>/', views.start_conversation, name='start_conversation'),
    path('start-group-conversation/', views.start_group_conversation, name='start_group_conversation'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('video-chat/<int:conversation_id>/', views.video_chat, name='video_chat'),
    #re_path(r'profile', views.home, name='home'),
    re_path(r'login', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', messenger_views.custom_logout, name='logout'),
    
    # Friend-related URLs
    path('update-profile/', views.update_profile, name='update_profile'),
    path('send-friend-request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('accept-friend-request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('reject-friend-request/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('friend-list/', views.friend_list, name='friend_list'),
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
]