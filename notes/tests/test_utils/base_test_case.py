from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from notes.models import Note


class BaseNoteTestCase(TestCase):
    def setUp(self):
        # Создаем пользователей
        self.author = get_user_model().objects.create_user(
            username='author',
            password='password123',
            email='author@example.com'
        )

        self.not_author = get_user_model().objects.create_user(
            username='not_author',
            password='password123',
            email='not_author@example.com'
        )

        # Базовые данные формы
        self.form_data = {
            'title': 'Test Note',
            'text': 'This is a test note',
            'slug': 'test-note'
        }

        # Создаем заметку
        self.note = self.create_note()

        # Добавляем клиентов для разных пользователей
        self.author_client = self.client
        self.author_client.force_login(self.author)

        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)

    def create_note(self, **kwargs):
        defaults = {
            'title': 'Test Note',
            'text': 'This is a test note',
            'slug': 'test-note',
            'author': self.author
        }
        defaults.update(kwargs)
        return Note.objects.create(**defaults)

    def tearDown(self):
        self.note.delete()
        self.author.delete()
        self.not_author.delete()
