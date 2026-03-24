from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    NAME_MAX_LENGTH = 30
    ABOUT_MAX_LENGTH = 100
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    picture = models.ImageField(upload_to='profile_images', blank=True)
    about = models.CharField(max_length=ABOUT_MAX_LENGTH, blank=True)

    def __str__(self):
        return self.user.username
    

class PetCategory(models.Model):
    NAME_MAX_LENGTH = 30
    
    name = models.CharField(max_length=NAME_MAX_LENGTH, unique=True)

    def __str__(self):
        return self.name

class Post(models.Model):
    IMAGE_AND_CAPTION_MAX_LENGTH = 200
    
    user_name = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(PetCategory, on_delete=models.CASCADE)
    
    image_url = models.URLField(max_length=IMAGE_AND_CAPTION_MAX_LENGTH)
    caption = models.CharField(max_length=IMAGE_AND_CAPTION_MAX_LENGTH)
    likes = models.IntegerField(default=0)

    def __str__(self):
        return self.caption

class Comment(models.Model):
    CONTENT_MAX_LENGTH = 300
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user_name = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.CharField(max_length=CONTENT_MAX_LENGTH)

    def __str__(self):
        return self.content[:30]


class Message(models.Model):
    CONTENT_MAX_LENGTH = 500

    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.CharField(max_length=CONTENT_MAX_LENGTH)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return "{} -> {}".format(self.sender, self.receiver)


#class Notification(models.Model):
#    user_name = models.ForeignKey(User, on_delete=models.CASCADE)
#    message = models.CharField(max_length=100)
#    type = models.CharField(max_length=30)
#    is_read = models.BooleanField(default=False)

#    def __str__(self):
#        return self.message

#We'll need to implement the actual views first.

#class Friendship(models.Model):
#    requester_name = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
#    reciever_name = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
#    status = models.CharField(max_length=30)

#    def __str__(self):
#        return "{} -> {} ({})".format(self.requester, self.receiver, self.status)

#We'll need to implement the actual friendship first.

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()