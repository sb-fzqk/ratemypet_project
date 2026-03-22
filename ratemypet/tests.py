from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from ratemypet.models import UserProfile, PetCategory, Post, Comment, Message
from ratemypet import views


# ===========================================================================
# MODEL TESTS
# ===========================================================================

class UserProfileModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.profile = UserProfile.objects.create(user=self.user, about='I love pets')

    def test_str_returns_username(self):
        self.assertEqual(str(self.profile), 'testuser')

    def test_about_max_length(self):
        self.assertEqual(UserProfile._meta.get_field('about').max_length, 100)

    def test_cascade_delete_with_user(self):
        self.user.delete()
        self.assertEqual(UserProfile.objects.count(), 0)


class PetCategoryModelTest(TestCase):

    def setUp(self):
        self.category = PetCategory.objects.create(name='Dog')

    def test_str_returns_name(self):
        self.assertEqual(str(self.category), 'Dog')

    def test_duplicate_name_raises_error(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            PetCategory.objects.create(name='Dog')


class PostModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='poster', password='pass123')
        self.category = PetCategory.objects.create(name='Cat')
        self.post = Post.objects.create(
            user_name=self.user,
            category=self.category,
            image_url='http://example.com/cat.jpg',
            caption='My cute cat',
        )

    def test_str_returns_caption(self):
        self.assertEqual(str(self.post), 'My cute cat')

    def test_default_likes_is_zero(self):
        self.assertEqual(self.post.likes, 0)

    def test_cascade_delete_when_user_deleted(self):
        self.user.delete()
        self.assertEqual(Post.objects.count(), 0)

    def test_cascade_delete_when_category_deleted(self):
        self.category.delete()
        self.assertEqual(Post.objects.count(), 0)


class CommentModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='commenter', password='pass123')
        self.post_user = User.objects.create_user(username='poster', password='pass123')
        self.category = PetCategory.objects.create(name='Rabbit')
        self.post = Post.objects.create(
            user_name=self.post_user,
            category=self.category,
            image_url='http://example.com/rabbit.jpg',
            caption='My rabbit',
        )

    def test_str_truncated_to_30_chars(self):
        comment = Comment.objects.create(
            post=self.post, user_name=self.user, content='A' * 40
        )
        self.assertEqual(str(comment), 'A' * 30)

    def test_str_short_content(self):
        comment = Comment.objects.create(
            post=self.post, user_name=self.user, content='Cute!'
        )
        self.assertEqual(str(comment), 'Cute!')

    def test_cascade_delete_when_post_deleted(self):
        Comment.objects.create(post=self.post, user_name=self.user, content='Cute!')
        self.post.delete()
        self.assertEqual(Comment.objects.count(), 0)


class MessageModelTest(TestCase):

    def setUp(self):
        self.sender = User.objects.create_user(username='sender', password='pass123')
        self.receiver = User.objects.create_user(username='receiver', password='pass123')
        self.message = Message.objects.create(
            sender=self.sender, receiver=self.receiver, content='Hello!'
        )

    def test_str_format(self):
        self.assertEqual(str(self.message), 'sender -> receiver')

    def test_timestamp_is_set_on_create(self):
        self.assertIsNotNone(self.message.timestamp)

    def test_messages_ordered_by_timestamp(self):
        msg2 = Message.objects.create(
            sender=self.sender, receiver=self.receiver, content='Second!'
        )
        messages = list(Message.objects.all())
        self.assertEqual(messages[0], self.message)
        self.assertEqual(messages[1], msg2)

    def test_sent_messages_related_name(self):
        self.assertIn(self.message, self.sender.sent_messages.all())

    def test_received_messages_related_name(self):
        self.assertIn(self.message, self.receiver.received_messages.all())

    def test_cascade_delete_when_sender_deleted(self):
        self.sender.delete()
        self.assertEqual(Message.objects.count(), 0)

    def test_cascade_delete_when_receiver_deleted(self):
        self.receiver.delete()
        self.assertEqual(Message.objects.count(), 0)


# ===========================================================================
# URL TESTS
# ===========================================================================

class URLResolutionTest(TestCase):

    def test_home_url(self):
        self.assertEqual(reverse('ratemypet:home'), '/home/')

    def test_post_url(self):
        self.assertEqual(reverse('ratemypet:post'), '/post/')

    def test_notifications_url(self):
        self.assertEqual(reverse('ratemypet:notifications'), '/notifications/')

    def test_messages_url(self):
        self.assertEqual(reverse('ratemypet:messages'), '/messages/')

    def test_conversation_url(self):
        self.assertEqual(
            reverse('ratemypet:conversation', kwargs={'username': 'bob'}),
            '/messages/bob/'
        )

    def test_profile_url(self):
        self.assertEqual(reverse('ratemypet:profile'), '/profile/')

    def test_search_url(self):
        self.assertEqual(reverse('ratemypet:search'), '/search/')

    def test_delete_account_url(self):
        self.assertEqual(reverse('ratemypet:delete_account'), '/settings/delete/')

    def test_home_resolves_to_correct_view(self):
        self.assertEqual(resolve('/home/').func, views.home)

    def test_conversation_resolves_to_correct_view(self):
        self.assertEqual(resolve('/messages/bob/').func, views.conversation)


# ===========================================================================
# VIEW TESTS
# ===========================================================================

class LoginRequiredTest(TestCase):

    def test_home_redirects_if_not_logged_in(self):
        response = Client().get(reverse('ratemypet:home'))
        self.assertEqual(response.status_code, 302)

    def test_notifications_redirects_if_not_logged_in(self):
        response = Client().get(reverse('ratemypet:notifications'))
        self.assertEqual(response.status_code, 302)

    def test_messages_redirects_if_not_logged_in(self):
        response = Client().get(reverse('ratemypet:messages'))
        self.assertEqual(response.status_code, 302)

    def test_profile_redirects_if_not_logged_in(self):
        response = Client().get(reverse('ratemypet:profile'))
        self.assertEqual(response.status_code, 302)


class StubViewsTest(TestCase):
    """Views that currently render a template with no extra logic."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.client.login(username='testuser', password='pass123')

    def test_home_returns_200(self):
        self.assertEqual(self.client.get(reverse('ratemypet:home')).status_code, 200)

    def test_home_uses_correct_template(self):
        self.assertTemplateUsed(self.client.get(reverse('ratemypet:home')), 'ratemypet/home.html')

    def test_post_returns_200(self):
        self.assertEqual(self.client.get(reverse('ratemypet:post')).status_code, 200)

    def test_profile_returns_200(self):
        self.assertEqual(self.client.get(reverse('ratemypet:profile')).status_code, 200)

    def test_search_returns_200(self):
        self.assertEqual(self.client.get(reverse('ratemypet:search')).status_code, 200)

    def test_settings_returns_200(self):
        self.assertEqual(self.client.get(reverse('ratemypet:settings')).status_code, 200)


class MessagesViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='msguser', password='pass123')
        self.friend = User.objects.create_user(username='friend', password='pass123')
        self.stranger = User.objects.create_user(username='stranger', password='pass123')
        Message.objects.create(sender=self.user, receiver=self.friend, content='Hey')
        self.client.login(username='msguser', password='pass123')

    def test_returns_200(self):
        self.assertEqual(self.client.get(reverse('ratemypet:messages')).status_code, 200)

    def test_contacts_in_context(self):
        response = self.client.get(reverse('ratemypet:messages'))
        self.assertIn(self.friend, response.context['contacts'])

    def test_stranger_not_in_contacts(self):
        response = self.client.get(reverse('ratemypet:messages'))
        self.assertNotIn(self.stranger, response.context['contacts'])

    def test_self_excluded_from_all_users(self):
        response = self.client.get(reverse('ratemypet:messages'))
        self.assertNotIn(self.user, response.context['all_users'])

    def test_received_message_adds_sender_to_contacts(self):
        Message.objects.create(sender=self.stranger, receiver=self.user, content='Hi')
        response = self.client.get(reverse('ratemypet:messages'))
        self.assertIn(self.stranger, response.context['contacts'])


class ConversationViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.alice = User.objects.create_user(username='alice', password='pass123')
        self.bob = User.objects.create_user(username='bob', password='pass123')
        self.client.login(username='alice', password='pass123')

    def test_get_returns_200(self):
        response = self.client.get(
            reverse('ratemypet:conversation', kwargs={'username': 'bob'})
        )
        self.assertEqual(response.status_code, 200)

    def test_post_creates_message(self):
        self.client.post(
            reverse('ratemypet:conversation', kwargs={'username': 'bob'}),
            {'content': 'Hello Bob'},
        )
        self.assertTrue(
            Message.objects.filter(sender=self.alice, receiver=self.bob).exists()
        )

    def test_nonexistent_user_returns_404(self):
        response = self.client.get(
            reverse('ratemypet:conversation', kwargs={'username': 'nobody'})
        )
        self.assertEqual(response.status_code, 404)

    def test_whitespace_message_not_saved(self):
        self.client.post(
            reverse('ratemypet:conversation', kwargs={'username': 'bob'}),
            {'content': '   '},
        )
        self.assertEqual(Message.objects.count(), 0)

    def test_post_redirects_after_sending(self):
        response = self.client.post(
            reverse('ratemypet:conversation', kwargs={'username': 'bob'}),
            {'content': 'Hey'},
        )
        self.assertEqual(response.status_code, 302)

    def test_both_sides_of_conversation_shown(self):
        m1 = Message.objects.create(sender=self.alice, receiver=self.bob, content='Hi')
        m2 = Message.objects.create(sender=self.bob, receiver=self.alice, content='Hey back')
        response = self.client.get(
            reverse('ratemypet:conversation', kwargs={'username': 'bob'})
        )
        self.assertIn(m1, response.context['chat_messages'])
        self.assertIn(m2, response.context['chat_messages'])


class DeleteAccountViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='deleteuser', password='pass123')
        self.client.login(username='deleteuser', password='pass123')

    def test_post_deletes_user(self):
        self.client.post(reverse('ratemypet:delete_account'))
        self.assertFalse(User.objects.filter(username='deleteuser').exists())

    def test_post_redirects_after_deletion(self):
        response = self.client.post(reverse('ratemypet:delete_account'))
        self.assertEqual(response.status_code, 302)


class NotificationsViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='notifuser', password='pass123')
        self.other = User.objects.create_user(username='other', password='pass123')
        self.category = PetCategory.objects.create(name='Dog')
        self.post = Post.objects.create(
            user_name=self.user,
            category=self.category,
            image_url='http://example.com/dog.jpg',
            caption='My dog',
            likes=3,
        )
        self.client.login(username='notifuser', password='pass123')

    def test_returns_200(self):
        response = self.client.get(reverse('ratemypet:notifications'))
        self.assertEqual(response.status_code, 200)

    def test_other_users_comment_appears(self):
        comment = Comment.objects.create(
            post=self.post, user_name=self.other, content='Nice dog!'
        )
        response = self.client.get(reverse('ratemypet:notifications'))
        self.assertIn(comment, response.context['recent_comments'])

    def test_own_comments_excluded(self):
        own_comment = Comment.objects.create(
            post=self.post, user_name=self.user, content='My own comment'
        )
        response = self.client.get(reverse('ratemypet:notifications'))
        self.assertNotIn(own_comment, response.context['recent_comments'])

    def test_liked_posts_in_context(self):
        response = self.client.get(reverse('ratemypet:notifications'))
        self.assertIn(self.post, response.context['liked_posts'])

    def test_post_with_zero_likes_not_in_liked_posts(self):
        unloved = Post.objects.create(
            user_name=self.user,
            category=self.category,
            image_url='http://example.com/x.jpg',
            caption='Nobody likes this',
            likes=0,
        )
        response = self.client.get(reverse('ratemypet:notifications'))
        self.assertNotIn(unloved, response.context['liked_posts'])
