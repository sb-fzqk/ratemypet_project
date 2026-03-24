import os 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ratemypet_project.settings')

from django.core.files import File
import django
django.setup()
from ratemypet.models import *
from django.conf import settings
import random

def create_users():
    data_users = [
        {"username": "Eleanor", "email": "eleanorP@gmail.com"},
        {"username": "aligator_johnny", "email": "johnny@outlook.com"},
        {"username": "puppy_photos", "email": "alex_brown@gmail.com"},
    ]

    users = []

    for data in data_users:
        user, created = User.objects.get_or_create(username=data["username"], email=data["email"])
        if created:
            user.set_password("pasword123")
            user.save()

        users.append(user)

    return users

def create_profile(users):
    bios = {
        "Eleanor": "My cats are the cutest",
        "aligator_johnny": "Gator is the best!",
        "puppy_photos": "This is the reason why I'm a dog walker"
    }

    images = {
        "Eleanor": os.path.join(settings.BASE_DIR, 'static/images/cat.jpg'),
        "aligator_johnny": os.path.join(settings.BASE_DIR, 'static/images/alligator.jpg')
    }

    for user in users:
        profile, created = UserProfile.objects.get_or_create(user = user)
        profile.about = bios.get(user.username, "hello")

        path = images.get(user.username)

        if path:
            with open(path, 'rb') as f:
                profile.picture.save(os.path.basename(path), File(f), save=False)
        profile.save()
       

def create_posts(users):
    user_dict = {user.username: user for user in users}
    all_posts = []

    posts_data = {
        "Eleanor": [
            ("Luna is playing hide and seek","cat_hiding.jpg","Cat"),
            ("Isnt she the cutest","cute_cat.jpg","Cat"),
            ("My heart cant take this","cute_cat2.jpg","Cat"),
            ("Poppy is trying to show off","showoff_cat.jpg","Cat")
        ],
        "puppy_photos": [
            ("I love my job","dog_job.jpg","Dog"),
            ("A change in scenary","scenary_dog.jpg","Dog")
        ]
    }

    for username, posts in posts_data.items():
        user = user_dict.get(username)

        if not user:
            continue

        for caption, img, pet_category in posts:
            obj, _ = PetCategory.objects.get_or_create(name=pet_category)

            post = Post.objects.create(
                user_name=user,
                caption=caption,
                image_url=f'/static/images/{img}',
                category=obj
            )

            all_posts.append(post)
    return all_posts


def add_likes(posts):
    for post in posts:
        post.likes = random.randint(0, 10)
        post.save()

def populate():
    users = create_users()
    create_profile(users)
    posts = create_posts(users)
    add_likes(posts)


if __name__ == '__main__':
    print("Populating...")
    populate()
    print("Done")
