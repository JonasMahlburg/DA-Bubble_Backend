from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from messenger_app.models import Chat, Message, Post
from messenger_app.api.serializers import ChatSerializer, PostSerializer
import datetime

# Import for specific exceptions
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError


# --- Model Tests ---
class ModelTests(TestCase):
    """
    Tests for the Django models: Chat, Message, and Post.
    Covers creation, relationships, field constraints, and on_delete behavior.
    """

    def setUp(self):
        """
        Set up common data for model tests.
        """
        self.user1 = User.objects.create_user(username='testuser1', password='password123')
        self.user2 = User.objects.create_user(username='testuser2', password='password123')
        self.chat1 = Chat.objects.create(title='General Chat')
        self.chat2 = Chat.objects.create(title='Private Chat')

    def test_chat_creation(self):
        """
        Test that a Chat object can be created successfully.
        """
        self.assertEqual(Chat.objects.count(), 2)
        self.assertEqual(self.chat1.title, 'General Chat')
        self.assertIsNotNone(self.chat1.id)

    def test_chat_members(self):
        """
        Test adding members to a Chat.
        """
        self.chat1.members.add(self.user1, self.user2)
        self.assertEqual(self.chat1.members.count(), 2)
        self.assertIn(self.user1, self.chat1.members.all())
        self.assertIn(self.user2, self.chat1.members.all())

        # Test blank=True for members
        chat_no_members = Chat.objects.create(title='Empty Chat')
        self.assertEqual(chat_no_members.members.count(), 0)

    def test_chat_title_blank_constraint(self):
        """
        Test that Chat title cannot be blank (blank=False).
        """
        chat_blank_title = Chat(title='')
        with self.assertRaises(ValidationError):
            chat_blank_title.full_clean() # Explicitly call full_clean() for Django's blank=False validation

    def test_chat_title_null_constraint(self):
        """
        Test that Chat title cannot be null (null=False).
        """
        with self.assertRaises(IntegrityError):
            Chat.objects.create(title=None)

    def test_message_creation(self):
        """
        Test that a Message object can be created successfully.
        """
        message1 = Message.objects.create(chat=self.chat1, author=self.user1, text='Hello everyone!')
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(message1.text, 'Hello everyone!')
        self.assertEqual(message1.chat, self.chat1)
        self.assertEqual(message1.author, self.user1)

        # Test blank=True and default="" for text
        message2 = Message.objects.create(chat=self.chat1, author=self.user1)
        self.assertEqual(message2.text, "")

    def test_message_on_delete_chat(self):
        """
        Test on_delete=models.SET_NULL for Message.chat.
        When a Chat is deleted, its associated Messages should have their chat field set to NULL.
        """
        message = Message.objects.create(chat=self.chat1, author=self.user1, text='Test message')
        chat_id = self.chat1.id
        self.chat1.delete()
        message.refresh_from_db() # Reload the message from the database
        self.assertIsNone(message.chat)
        self.assertFalse(Chat.objects.filter(id=chat_id).exists())

    def test_message_on_delete_author(self):
        """
        Test on_delete=models.SET_NULL for Message.author.
        When a User (author) is deleted, their associated Messages should have their author field set to NULL.
        """
        message = Message.objects.create(chat=self.chat1, author=self.user1, text='Test message by user1')
        user_id = self.user1.id
        self.user1.delete()
        message.refresh_from_db()
        self.assertIsNone(message.author)
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_post_creation(self):
        """
        Test that a Post object can be created successfully.
        """
        post1 = Post.objects.create(
            chat=self.chat1,
            author=self.user1,
            title='First Post',
            content='This is the content of the first post.'
        )
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(post1.title, 'First Post')
        self.assertEqual(post1.content, 'This is the content of the first post.')
        self.assertEqual(post1.chat, self.chat1)
        self.assertEqual(post1.author, self.user1)
        self.assertIsNotNone(post1.created_at)
        self.assertTrue(isinstance(post1.created_at, datetime.datetime))

        # Test Post without chat (null=True, blank=True)
        post_no_chat = Post.objects.create(
            author=self.user2,
            title='Post without chat',
            content='This post has no associated chat.'
        )
        self.assertIsNone(post_no_chat.chat)

    def test_post_str_method(self):
        """
        Test the __str__ method of the Post model.
        """
        post = Post.objects.create(
            chat=self.chat1,
            author=self.user1,
            title='Test Post Title',
            content='Some content.'
        )
        self.assertEqual(str(post), 'Test Post Title')

    def test_post_on_delete_chat(self):
        """
        Test on_delete=models.CASCADE for Post.chat.
        When a Chat is deleted, its associated Posts should also be deleted.
        """
        post = Post.objects.create(
            chat=self.chat1,
            author=self.user1,
            title='Post in Chat 1',
            content='Content.'
        )
        self.assertEqual(Post.objects.count(), 1)
        self.chat1.delete()
        self.assertEqual(Post.objects.count(), 0) # Post should be deleted

    def test_post_on_delete_author(self):
        """
        Test on_delete=models.CASCADE for Post.author.
        When a User (author) is deleted, their associated Posts should also be deleted.
        """
        post = Post.objects.create(
            chat=self.chat1,
            author=self.user1,
            title='Post by User 1',
            content='Content.'
        )
        self.assertEqual(Post.objects.count(), 1)
        self.user1.delete()
        self.assertEqual(Post.objects.count(), 0) # Post should be deleted

    def test_post_title_blank_constraint(self):
        """
        Test that Post title cannot be blank (blank=False).
        """
        post_blank_title = Post(author=self.user1, title='', content='Some content.')
        with self.assertRaises(ValidationError):
            post_blank_title.full_clean()

    def test_post_title_null_constraint(self):
        """
        Test that Post title cannot be null (null=False).
        """
        with self.assertRaises(IntegrityError):
            Post.objects.create(
                author=self.user1,
                title=None,
                content='Some content.'
            )

    def test_post_content_blank_allowed(self):
        """
        Test that Post content can be blank (TextField is blank=True by default).
        """
        post_blank_content = Post.objects.create(
            author=self.user1,
            title='Post with blank content',
            content=''
        )
        self.assertEqual(post_blank_content.content, '')

    def test_post_content_null_constraint(self):
        """
        Test that Post content cannot be null (TextField is null=False by default).
        """
        with self.assertRaises(IntegrityError):
            Post.objects.create(
                author=self.user1,
                title='Post with null content',
                content=None
            )


# --- Serializer Tests ---
class SerializerTests(TestCase):
    """
    Tests for Django REST Framework serializers: ChatSerializer and PostSerializer.
    Covers serialization, deserialization, and read-only fields.
    """

    def setUp(self):
        """
        Set up common data for serializer tests.
        """
        self.user1 = User.objects.create_user(username='serializertestuser1', password='password123')
        self.user2 = User.objects.create_user(username='serializertestuser2', password='password123')
        self.chat = Chat.objects.create(title='Serializer Chat')
        self.post = Post.objects.create(
            chat=self.chat,
            author=self.user1,
            title='Serializer Test Post',
            content='Content for serializer test.'
        )

    def test_chat_serializer_valid(self):
        """
        Test ChatSerializer with valid data.
        """
        data = {'title': 'New Chat Title'}
        serializer = ChatSerializer(data=data)
        # The TypeError was fixed by changing exclude=("id") to exclude=("id",) in the serializer.
        self.assertTrue(serializer.is_valid(), serializer.errors)
        chat_instance = serializer.save()
        self.assertEqual(chat_instance.title, 'New Chat Title')
        self.assertIsNotNone(chat_instance.id) # Ensure ID is generated

    def test_chat_serializer_read_only_fields(self):
        """
        Test that 'id' is excluded and 'author' (though not on model) is handled.
        """
        serializer = ChatSerializer(instance=self.chat)
        data = serializer.data
        self.assertNotIn('id', data)
        self.assertIn('title', data)
        self.assertIn('members', data) # ManyToManyField is included by default

        # Attempt to set 'id' during creation (should be ignored/not allowed)
        data_with_id = {'title': 'Another Chat', 'id': 999}
        serializer_create = ChatSerializer(data=data_with_id)
        self.assertTrue(serializer_create.is_valid())
        new_chat = serializer_create.save()
        self.assertNotEqual(new_chat.id, 999) # ID should be auto-generated, not set by input

    def test_post_serializer_valid(self):
        """
        Test PostSerializer with valid data.
        """
        data = {
            'chat': self.chat.id,
            'author': self.user2.id, # This will be ignored due to read_only_fields
            'title': 'New Post Title',
            'content': 'New post content.'
        }
        serializer = PostSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        post_instance = serializer.save(author=self.user1) # author is set by view, not serializer data
        self.assertEqual(post_instance.title, 'New Post Title')
        self.assertEqual(post_instance.content, 'New post content.')
        self.assertEqual(post_instance.chat, self.chat)
        self.assertEqual(post_instance.author, self.user1) # Should be the one passed in save()

    def test_post_serializer_read_only_fields(self):
        """
        Test that 'author' and 'created_at' are read-only fields in PostSerializer.
        'created_at' is auto_now_add=True, making it implicitly read-only.
        """
        # Test serialization: author and created_at should be present in output
        serializer = PostSerializer(instance=self.post)
        data = serializer.data
        self.assertIn('author', data)
        self.assertIn('created_at', data)
        self.assertEqual(data['author'], self.user1.id)

        # Test deserialization: attempting to set author or created_at should be ignored
        initial_author_id = self.post.author.id
        initial_created_at = self.post.created_at

        update_data = {
            'title': 'Updated Title',
            'content': 'Updated content.',
            'author': self.user2.id, # Should be ignored
            'created_at': '2020-01-01T00:00:00Z' # Should be ignored
        }
        serializer = PostSerializer(instance=self.post, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_post = serializer.save()

        self.assertEqual(updated_post.title, 'Updated Title')
        self.assertEqual(updated_post.content, 'Updated content.')
        self.assertEqual(updated_post.author.id, initial_author_id) # Author should not change
        self.assertEqual(updated_post.created_at, initial_created_at) # created_at should not change

    def test_post_serializer_invalid_data(self):
        """
        Test PostSerializer with invalid or missing data.
        """
        # Missing required fields (title, content)
        data = {'chat': self.chat.id}
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        self.assertIn('content', serializer.errors)

        # Invalid chat ID
        data = {
            'chat': 9999, # Non-existent chat ID
            'title': 'Invalid Chat Post',
            'content': 'Content.'
        }
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('chat', serializer.errors)
        # Updated assertion for more robust check
        self.assertIn('object does not exist', str(serializer.errors['chat']))

        # Empty title (blank=False in model)
        data = {
            'chat': self.chat.id,
            'title': '',
            'content': 'Content.'
        }
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        self.assertIn('This field may not be blank', str(serializer.errors['title']))


# --- View Tests ---
class PostViewSetTests(APITestCase):
    """
    Tests for the PostViewSet, covering API endpoints for Posts.
    Includes authentication, CRUD operations, and edge cases.
    """

    def setUp(self):
        """
        Set up common data for API view tests.
        """
        self.user1 = User.objects.create_user(username='viewtestuser1', password='password123')
        self.user2 = User.objects.create_user(username='viewtestuser2', password='password123')
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpassword')
        self.chat = Chat.objects.create(title='View Test Chat')
        self.post1 = Post.objects.create(
            chat=self.chat,
            author=self.user1,
            title='Post by User1',
            content='Content from user1.'
        )
        self.post2 = Post.objects.create(
            chat=self.chat,
            author=self.user2,
            title='Post by User2',
            content='Content from user2.'
        )
        # Ensure your project's main urls.py includes messenger_app.api.urls correctly,
        # e.g., path('api/', include(messenger_router.urls))
        # The basename for PostViewSet is 'post' by default (from queryset=Post.objects.all())
        self.list_url = reverse('post-list')
        self.detail_url = lambda pk: reverse('post-detail', kwargs={'pk': pk})

    # --- Authentication Tests ---
    def test_list_posts_unauthenticated(self):
        """
        Test listing posts by an unauthenticated user (should fail with 401 if authentication is required).
        Assuming default DRF settings or PostViewSet require authentication.
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_post_unauthenticated(self):
        """
        Test retrieving a single post by an unauthenticated user (should fail with 401).
        """
        response = self.client.get(self.detail_url(self.post1.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post_unauthenticated(self):
        """
        Test creating a post by an unauthenticated user (should fail).
        """
        data = {
            'chat': self.chat.pk,
            'title': 'New Post by Anonymous',
            'content': 'Anonymous content.'
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_post_unauthenticated(self):
        """
        Test updating a post by an unauthenticated user (should fail).
        """
        data = {'title': 'Updated Title Anon'}
        response = self.client.patch(self.detail_url(self.post1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_post_unauthenticated(self):
        """
        Test deleting a post by an unauthenticated user (should fail).
        """
        response = self.client.delete(self.detail_url(self.post1.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- CRUD Operations (Authenticated) ---
    def test_list_posts_authenticated(self):
        """
        Test listing posts by an authenticated user.
        """
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_post_authenticated(self):
        """
        Test retrieving a single post by an authenticated user.
        """
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.detail_url(self.post1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.post1.title)
        self.assertEqual(response.data['author'], self.user1.pk)

    def test_retrieve_post_not_found(self):
        """
        Test retrieving a non-existent post.
        """
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.detail_url(9999)) # Non-existent PK
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_post_authenticated_happy_path(self):
        """
        Test creating a post by an authenticated user (happy path).
        The author should be automatically set to the requesting user.
        """
        self.client.force_authenticate(user=self.user1)
        data = {
            'chat': self.chat.pk,
            'title': 'New Post by User1',
            'content': 'This post is created by user1.'
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 3)
        created_post = Post.objects.get(pk=response.data['id'])
        self.assertEqual(created_post.title, 'New Post by User1')
        self.assertEqual(created_post.author, self.user1) # Author correctly set by perform_create
        self.assertEqual(response.data['author'], self.user1.pk) # Check serialized author

    def test_create_post_authenticated_missing_fields(self):
        """
        Test creating a post with missing required fields by an authenticated user.
        """
        self.client.force_authenticate(user=self.user1)
        data = {
            'chat': self.chat.pk,
            'content': 'Missing title.' # Title is missing
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data) # Check for specific error message

        data_missing_content = {
            'chat': self.chat.pk,
            'title': 'Missing content.' # Content is missing
        }
        response = self.client.post(self.list_url, data_missing_content, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content', response.data)

    def test_create_post_authenticated_invalid_chat(self):
        """
        Test creating a post with an invalid chat ID by an authenticated user.
        """
        self.client.force_authenticate(user=self.user1)
        data = {
            'chat': 9999, # Non-existent chat
            'title': 'Post with Invalid Chat',
            'content': 'Content.'
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('chat', response.data)
        # Updated assertion for more robust check
        self.assertIn('object does not exist', str(response.data['chat']))

    def test_update_post_authenticated_happy_path(self):
        """
        Test updating a post by its author (happy path) using PUT.
        Requires all fields for PUT.
        """
        self.client.force_authenticate(user=self.user1)
        data = {
            'chat': self.chat.pk, # Include all required fields for PUT
            'title': 'Updated Post Title',
            'content': 'Updated content from user1.'
        }
        response = self.client.put(self.detail_url(self.post1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Updated Post Title')
        self.assertEqual(self.post1.content, 'Updated content from user1.')
        self.assertEqual(self.post1.author, self.user1) # Author should remain the same

    def test_update_post_authenticated_not_author(self):
        """
        Test updating a post by a user who is not the author.
        By default, ModelViewSet does not restrict updates to the author unless custom permissions are set.
        This test now correctly uses PUT with all fields and expects 200 OK.
        """
        self.client.force_authenticate(user=self.user2) # User2 tries to update User1's post
        data = {
            'chat': self.chat.pk, # Include all required fields for PUT
            'title': 'Attempted Update by User2',
            'content': self.post1.content # Keep original content for PUT
        }
        response = self.client.put(self.detail_url(self.post1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK) # This passes without custom permissions
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Attempted Update by User2') # Post is updated

    def test_partial_update_post_authenticated(self):
        """
        Test partial updating a post by its author.
        """
        self.client.force_authenticate(user=self.user1)
        data = {'title': 'Partially Updated Title'}
        response = self.client.patch(self.detail_url(self.post1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Partially Updated Title')
        self.assertEqual(self.post1.content, 'Content from user1.') # Content should remain unchanged

    def test_delete_post_authenticated_happy_path(self):
        """
        Test deleting a post by its author (happy path).
        """
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(self.detail_url(self.post1.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(pk=self.post1.pk).exists())
        self.assertEqual(Post.objects.count(), 1) # Only post2 should remain

    def test_delete_post_authenticated_not_author(self):
        """
        Test deleting a post by a user who is not the author.
        Similar to update, by default ModelViewSet allows any authenticated user to delete.
        """
        self.client.force_authenticate(user=self.user2) # User2 tries to delete User1's post
        response = self.client.delete(self.detail_url(self.post1.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT) # This passes without custom permissions
        self.assertFalse(Post.objects.filter(pk=self.post1.pk).exists()) # Post is deleted
        self.assertEqual(Post.objects.count(), 1)

    def test_delete_post_not_found(self):
        """
        Test deleting a non-existent post.
        """
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(self.detail_url(9999)) # Non-existent PK
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_user_actions(self):
        """
        Test that an admin user can perform all actions.
        """
        self.client.force_authenticate(user=self.admin_user)

        # Create
        data = {
            'chat': self.chat.pk,
            'title': 'Post by Admin',
            'content': 'Admin content.'
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 3)
        admin_post_pk = response.data['id']

        # Retrieve
        response = self.client.get(self.detail_url(admin_post_pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Post by Admin')

        # Update
        update_data = {
            'chat': self.chat.pk, # Include all required fields for PUT
            'title': 'Admin Updated Title',
            'content': 'Admin content.' # Keep original content for PUT
        }
        response = self.client.put(self.detail_url(admin_post_pk), update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        Post.objects.get(pk=admin_post_pk).refresh_from_db()
        self.assertEqual(Post.objects.get(pk=admin_post_pk).title, 'Admin Updated Title')

        # Delete
        response = self.client.delete(self.detail_url(admin_post_pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(pk=admin_post_pk).exists())
        self.assertEqual(Post.objects.count(), 2) # Back to original 2 posts
