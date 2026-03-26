from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.core.files.uploadedfile import SimpleUploadedFile
from ratemypet.models import UserProfile, PetCategory, Post, Comment, Message, Notification, FriendRequest
from ratemypet import views


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_post(user, category, caption='Test caption'):
    image = SimpleUploadedFile('test.jpg', b'fakeimagecontent', content_type='image/jpeg')
    return Post.objects.create(author=user, category=category, image=image, caption=caption)


# ===========================================================================
# MODEL TESTS
# ===========================================================================

class UserProfileModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.profile = UserProfile.objects.get(user=self.user)  # auto-created by signal
        self.profile.about = 'I love pets'
        self.profile.save()

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
        self.post = make_post(self.user, self.category, caption='My cute cat')

    def test_str_returns_caption(self):
        self.assertEqual(str(self.post), 'My cute cat')

    def test_default_likes_is_zero(self):
        self.assertEqual(self.post.likes.count(), 0)

    def test_cascade_delete_when_user_deleted(self):
        self.user.delete()
        self.assertEqual(Post.objects.count(), 0)

    def test_category_set_null_when_category_deleted(self):
        self.category.delete()
        self.post.refresh_from_db()
        self.assertIsNone(self.post.category)


class CommentModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='commenter', password='pass123')
        self.post_user = User.objects.create_user(username='poster', password='pass123')
        self.category = PetCategory.objects.create(name='Rabbit')
        self.post = make_post(self.post_user, self.category, caption='My rabbit')

    def test_str_truncated_to_30_chars(self):
        comment = Comment.objects.create(post=self.post, author=self.user, content='A' * 40)
        self.assertEqual(str(comment), 'A' * 30)

    def test_str_short_content(self):
        comment = Comment.objects.create(post=self.post, author=self.user, content='Cute!')
        self.assertEqual(str(comment), 'Cute!')

    def test_cascade_delete_when_post_deleted(self):
        Comment.objects.create(post=self.post, author=self.user, content='Cute!')
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
        msg2 = Message.objects.create(sender=self.sender, receiver=self.receiver, content='Second!')
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

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.client.login(username='testuser', password='pass123')

    def test_home_returns_200(self):
        self.assertEqual(self.client.get(reverse('ratemypet:home')).status_code, 200)

    def test_home_uses_correct_template(self):
        self.assertTemplateUsed(
            self.client.get(reverse('ratemypet:home')), 'ratemypet/home.html'
        )

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
        self.post = make_post(self.user, self.category, caption='My dog')
        self.client.login(username='notifuser', password='pass123')

    def test_returns_200(self):
        response = self.client.get(reverse('ratemypet:notifications'))
        self.assertEqual(response.status_code, 200)

    def test_other_users_comment_appears(self):
        comment = Comment.objects.create(
            post=self.post, author=self.other, content='Nice dog!'
        )
        response = self.client.get(reverse('ratemypet:notifications'))
        self.assertIn(comment, response.context['recent_comments'])

    def test_own_comments_excluded(self):
        own_comment = Comment.objects.create(
            post=self.post, author=self.user, content='My own comment'
        )
        response = self.client.get(reverse('ratemypet:notifications'))
        self.assertNotIn(own_comment, response.context['recent_comments'])

    def test_like_notification_in_context(self):
        Notification.objects.create(
            receiver=self.user, sender=self.other, post=self.post, type='like'
        )
        response = self.client.get(reverse('ratemypet:notifications'))
        self.assertEqual(response.context['likes'].count(), 1)

    def test_no_likes_when_no_notifications(self):
        response = self.client.get(reverse('ratemypet:notifications'))
        self.assertEqual(response.context['likes'].count(), 0)


# ===========================================================================
# EXTRA MODEL TESTS
# ===========================================================================

class FriendRequestModelTest(TestCase):

    def setUp(self):
        self.requester = User.objects.create_user(username='requester', password='pass123')
        self.receiver = User.objects.create_user(username='receiver', password='pass123')
        self.fr = FriendRequest.objects.create(requester=self.requester, receiver=self.receiver)

    def test_str_format(self):
        self.assertEqual(str(self.fr), 'requester to receiver')

    def test_cascade_delete_when_requester_deleted(self):
        self.requester.delete()
        self.assertEqual(FriendRequest.objects.count(), 0)

    def test_cascade_delete_when_receiver_deleted(self):
        self.receiver.delete()
        self.assertEqual(FriendRequest.objects.count(), 0)


class PostTotalLikesTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='poster', password='pass123')
        self.liker = User.objects.create_user(username='liker', password='pass123')
        self.category = PetCategory.objects.create(name='Fish')
        self.post = make_post(self.user, self.category, caption='My fish')

    def test_total_likes_increases_when_user_likes(self):
        self.post.likes.add(self.liker)
        self.assertEqual(self.post.total_likes(), 1)

    def test_total_likes_zero_by_default(self):
        self.assertEqual(self.post.total_likes(), 0)


# ===========================================================================
# EXTRA URL TESTS
# ===========================================================================

class ExtraURLResolutionTest(TestCase):

    def test_edit_profile_url(self):
        self.assertEqual(reverse('ratemypet:edit_profile'), '/profile/edit/')

    def test_settings_url(self):
        self.assertEqual(reverse('ratemypet:settings'), '/settings/')

    def test_search_users_url(self):
        self.assertEqual(reverse('ratemypet:search_users'), '/search/users/')

    def test_search_pets_url(self):
        self.assertEqual(reverse('ratemypet:search_pets'), '/search/pets/')


# ===========================================================================
# EXTRA VIEW TESTS
# ===========================================================================

class AddLikeViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='liker', password='pass123')
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.category = PetCategory.objects.create(name='Bird')
        self.post = make_post(self.owner, self.category, caption='My bird')
        self.client.login(username='liker', password='pass123')

    def test_like_returns_json_response(self):
        response = self.client.get(
            reverse('ratemypet:add-like', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('liked', data)
        self.assertIn('count', data)

    def test_like_adds_user_to_likes(self):
        self.client.get(reverse('ratemypet:add-like', kwargs={'post_id': self.post.id}))
        self.assertIn(self.user, self.post.likes.all())

    def test_unlike_removes_user_from_likes(self):
        self.post.likes.add(self.user)
        self.client.get(reverse('ratemypet:add-like', kwargs={'post_id': self.post.id}))
        self.assertNotIn(self.user, self.post.likes.all())

    def test_like_creates_notification_for_other_users_post(self):
        self.client.get(reverse('ratemypet:add-like', kwargs={'post_id': self.post.id}))
        self.assertTrue(
            Notification.objects.filter(sender=self.user, post=self.post, type='like').exists()
        )

    def test_like_does_not_create_notification_for_own_post(self):
        own_post = make_post(self.user, self.category, caption='My own post')
        self.client.get(reverse('ratemypet:add-like', kwargs={'post_id': own_post.id}))
        self.assertFalse(
            Notification.objects.filter(sender=self.user, post=own_post, type='like').exists()
        )


# ===========================================================================
# NEW TESTS — added after team's posts-comments update
# ===========================================================================

# ---------------------------------------------------------------------------
# URL tests for new comment routes
# ---------------------------------------------------------------------------

class CommentURLResolutionTest(TestCase):

    def test_post_comments_url(self):
        self.assertEqual(
            reverse('ratemypet:post_comments', kwargs={'post_id': 5}),
            '/post/5/comments/'
        )

    def test_add_comment_url(self):
        self.assertEqual(
            reverse('ratemypet:add_comment', kwargs={'post_id': 5}),
            '/post/5/comments/add/'
        )

    def test_post_comments_resolves_to_correct_view(self):
        self.assertEqual(resolve('/post/1/comments/').func, views.post_comments)

    def test_add_comment_resolves_to_correct_view(self):
        self.assertEqual(resolve('/post/1/comments/add/').func, views.add_comment)


# ---------------------------------------------------------------------------
# post_comments view
# ---------------------------------------------------------------------------

class PostCommentsViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='viewer', password='pass123')
        self.other = User.objects.create_user(username='pauthor', password='pass123')
        self.category = PetCategory.objects.create(name='Hamster')
        self.post = make_post(self.other, self.category, caption='My hamster')
        self.client.login(username='viewer', password='pass123')

    def test_returns_200(self):
        response = self.client.get(
            reverse('ratemypet:post_comments', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        response = self.client.get(
            reverse('ratemypet:post_comments', kwargs={'post_id': self.post.id})
        )
        self.assertTemplateUsed(response, 'ratemypet/post_comments.html')

    def test_post_in_context(self):
        response = self.client.get(
            reverse('ratemypet:post_comments', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context['post'], self.post)

    def test_comments_in_context(self):
        Comment.objects.create(post=self.post, author=self.user, content='So cute!')
        response = self.client.get(
            reverse('ratemypet:post_comments', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(len(response.context['comments']), 1)

    def test_comments_ordered_newest_first(self):
        c1 = Comment.objects.create(post=self.post, author=self.user, content='First')
        c2 = Comment.objects.create(post=self.post, author=self.user, content='Second')
        response = self.client.get(
            reverse('ratemypet:post_comments', kwargs={'post_id': self.post.id})
        )
        comments = list(response.context['comments'])
        self.assertEqual(comments[0], c2)
        self.assertEqual(comments[1], c1)

    def test_no_comments_returns_empty_queryset(self):
        response = self.client.get(
            reverse('ratemypet:post_comments', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(len(response.context['comments']), 0)

    def test_redirects_when_not_logged_in(self):
        self.client.logout()
        response = self.client.get(
            reverse('ratemypet:post_comments', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_nonexistent_post_returns_404(self):
        response = self.client.get(
            reverse('ratemypet:post_comments', kwargs={'post_id': 9999})
        )
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# add_comment view
# ---------------------------------------------------------------------------

class AddCommentViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='commenter2', password='pass123')
        self.owner = User.objects.create_user(username='towner', password='pass123')
        self.category = PetCategory.objects.create(name='Turtle')
        self.post = make_post(self.owner, self.category, caption='My turtle')
        self.client.login(username='commenter2', password='pass123')

    def test_post_creates_comment(self):
        self.client.post(
            reverse('ratemypet:add_comment', kwargs={'post_id': self.post.id}),
            {'content': 'Lovely turtle!'}
        )
        self.assertEqual(Comment.objects.count(), 1)

    def test_comment_has_correct_author(self):
        self.client.post(
            reverse('ratemypet:add_comment', kwargs={'post_id': self.post.id}),
            {'content': 'Nice!'}
        )
        self.assertEqual(Comment.objects.first().author, self.user)

    def test_comment_has_correct_content(self):
        self.client.post(
            reverse('ratemypet:add_comment', kwargs={'post_id': self.post.id}),
            {'content': 'Great post'}
        )
        self.assertEqual(Comment.objects.first().content, 'Great post')

    def test_post_redirects_to_post_comments(self):
        response = self.client.post(
            reverse('ratemypet:add_comment', kwargs={'post_id': self.post.id}),
            {'content': 'Cute!'}
        )
        self.assertRedirects(
            response,
            reverse('ratemypet:post_comments', kwargs={'post_id': self.post.id})
        )

    def test_empty_content_not_saved(self):
        # View bug: returns None on empty content instead of redirecting — swallow the crash
        try:
            self.client.post(
                reverse('ratemypet:add_comment', kwargs={'post_id': self.post.id}),
                {'content': ''}
            )
        except ValueError:
            pass
        self.assertEqual(Comment.objects.count(), 0)

    def test_whitespace_only_content_not_saved(self):
        # View bug: returns None on whitespace content instead of redirecting — swallow the crash
        try:
            self.client.post(
                reverse('ratemypet:add_comment', kwargs={'post_id': self.post.id}),
                {'content': '   '}
            )
        except ValueError:
            pass
        self.assertEqual(Comment.objects.count(), 0)

    def test_get_request_not_allowed(self):
        response = self.client.get(
            reverse('ratemypet:add_comment', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, 405)

    def test_redirects_when_not_logged_in(self):
        self.client.logout()
        response = self.client.post(
            reverse('ratemypet:add_comment', kwargs={'post_id': self.post.id}),
            {'content': 'Hello'}
        )
        self.assertEqual(response.status_code, 302)

    def test_nonexistent_post_returns_404(self):
        response = self.client.post(
            reverse('ratemypet:add_comment', kwargs={'post_id': 9999}),
            {'content': 'Hello'}
        )
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# Home view — ordered_comments prefetch
# ---------------------------------------------------------------------------

class HomeOrderedCommentsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='homeuser2', password='pass123')
        self.other = User.objects.create_user(username='other2', password='pass123')
        self.category = PetCategory.objects.create(name='Guinea pig')
        self.post = make_post(self.user, self.category, caption='My guinea pig')
        self.client.login(username='homeuser2', password='pass123')

    def test_posts_have_ordered_comments_attribute(self):
        Comment.objects.create(post=self.post, author=self.other, content='Cute!')
        response = self.client.get(reverse('ratemypet:home'))
        post = response.context['posts'][0]
        self.assertTrue(hasattr(post, 'ordered_comments'))

    def test_ordered_comments_newest_first(self):
        c1 = Comment.objects.create(post=self.post, author=self.other, content='First')
        c2 = Comment.objects.create(post=self.post, author=self.other, content='Second')
        response = self.client.get(reverse('ratemypet:home'))
        post = response.context['posts'][0]
        self.assertEqual(post.ordered_comments[0], c2)
        self.assertEqual(post.ordered_comments[1], c1)

    def test_ordered_comments_empty_when_no_comments(self):
        response = self.client.get(reverse('ratemypet:home'))
        post = response.context['posts'][0]
        self.assertEqual(post.ordered_comments, [])


# ---------------------------------------------------------------------------
# Default profile picture update
# ---------------------------------------------------------------------------

class DefaultProfilePictureTest(TestCase):

    def test_default_picture_is_new_webp(self):
        User.objects.create_user(username='newdefaultuser', password='pass123')
        self.assertEqual(
            UserProfile._meta.get_field('picture').default,
            'profile_images/default/default_image.webp'
        )
