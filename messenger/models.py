from django.db import models
from django.contrib.auth.models import User

class ConversationManager(models.Manager):
    def get_or_create_between(self, user1, user2):
        participants = sorted([user1, user2], key=lambda user: user.id)
        conversation = self.filter(participants=participants[0]).filter(participants=participants[1]).first()
        
        if not conversation:
            conversation = self.create()
            conversation.participants.add(*participants)
        
        return conversation

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')

    objects = ConversationManager()

    is_group = models.BooleanField(default=False)

    def __str__(self):
        if self.is_group:
            return f"Group: {', '.join([user.username for user in self.participants.all()])}"
        else:
            return ", ".join([user.username for user in self.participants.all()])

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.username}: {self.content[:20]}'
    
class Friendship(models.Model):
    user = models.ForeignKey(User, related_name='friends', on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name='friend_of', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'friend')  # Prevent duplicate friendships

    def __str__(self):
        return f"{self.user.username} is friends with {self.friend.username}"

class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='outgoing_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='incoming_requests', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')  # Prevent duplicate requests

    def __str__(self):
        return f"Request from {self.from_user.username} to {self.to_user.username}"
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return self.user.username