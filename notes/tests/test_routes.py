from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus
from django.contrib.auth import get_user_model
from notes.models import Note

class TestAuthenticatedUserPages(TestCase):

    def setUp(self):
        # Создаем тестового пользователя
        self.user = self.create_user()
        # Авторизуем пользователя
        self.client.force_login(self.user)

    def create_user(self):
        return get_user_model().objects.create_user(
            username='testuser',
            password='testpassword',
            email='test@example.com'
        )

    def test_pages_availability_for_auth_user(self):
        # Список URL-адресов для тестирования
        urls = [
            'notes:list',
            'notes:add',
            'notes:success'
        ]

        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)


class TestAuthorPagesAvailability(TestCase):

    def setUp(self):
        # Создаем автора и авторизуем его
        self.author = get_user_model().objects.create_user(
            username='testauthor',
            password='testpassword',
            email='author@example.com'
        )
        self.client.force_login(self.author)

        # Создаем тестовую заметку
        self.note = Note.objects.create(
            title='Test Note',
            text='This is a test note',
            author=self.author
        )

    def test_pages_availability_for_author(self):
        # Список URL-адресов для тестирования
        urls = [
            'notes:detail',
            'notes:edit',
            'notes:delete'
        ]

        for name in urls:
            with self.subTest(name=name):
                url = reverse(name, args=(self.note.slug,))
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_note_creation(self):
        # Проверяем, что заметка создана корректно
        self.assertEqual(self.note.title, 'Test Note')
        self.assertEqual(self.note.author, self.author)
        self.assertTrue(self.note.slug)


class TestPagesAvailabilityForDifferentUsers(TestCase):

    def setUp(self):
        # Создаем автора заметки
        self.author = get_user_model().objects.create_user(
            username='author',
            password='password123',
            email='author@example.com'
        )

        # Создаем другого пользователя
        self.not_author = get_user_model().objects.create_user(
            username='not_author',
            password='password123',
            email='not_author@example.com'
        )

        # Создаем тестовую заметку
        self.note = Note.objects.create(
            title='Test Note',
            text='This is a test note',
            author=self.author
        )

    def test_pages_availability(self):
        # Определяем тестовые случаи
        test_cases = [
            (self.not_author, HTTPStatus.NOT_FOUND),
            (self.author, HTTPStatus.OK)
        ]

        # Список URL-адресов для тестирования
        urls = [
            'notes:detail',
            'notes:edit',
            'notes:delete'
        ]

        for client, expected_status in test_cases:
            # Авторизуем соответствующего пользователя
            self.client.force_login(client)

            for name in urls:
                with self.subTest(client=client, name=name, expected_status=expected_status):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, expected_status)

    def test_note_creation(self):
        # Проверяем корректность создания заметки
        self.assertEqual(self.note.title, 'Test Note')
        self.assertEqual(self.note.author, self.author)
        self.assertTrue(self.note.slug)

    def tearDown(self):
        # Очищаем тестовые данные
        self.note.delete()
        self.author.delete()
        self.not_author.delete()


class TestRedirectsForAnonymousUsers(TestCase):

    def setUp(self):
        # Создаем анонимного клиента
        self.client = Client()
        # Создаем тестовую заметку для получения slug
        self.note = Note.objects.create(
            title='Test Note',
            text='This is a test note',
            author=get_user_model().objects.create_user(
                username='testuser',
                password='testpassword'
            )
        )

    def test_redirects(self):
        # Список тестовых случаев
        test_cases = [
            ('notes:detail', self.note.slug),
            ('notes:edit', self.note.slug),
            ('notes:delete', self.note.slug),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
        ]

        for name, args in test_cases:
            with self.subTest(name=name, args=args):
                login_url = reverse('users:login')
                url = reverse(name, args=[args] if args else [])
                expected_url = f'{login_url}?next={url}'

                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    expected_url,
                    status_code=302,
                    target_status_code=200
                )

    def tearDown(self):
        # Очищаем тестовые данные
        self.note.delete()

    def test_user_is_anonymous(self):
        # Проверяем, что пользователь действительно анонимный
        self.assertIsInstance(self.client.session.get('_auth_user_id'), type(None))
        self.assertEqual(self.client.session.get('_auth_user_backend'), None)
