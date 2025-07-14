from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from notes.models import Note
from notes.forms import NoteForm

class TestNotesListForDifferentUsers(TestCase):

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

        # Создаем заметку
        self.note = Note.objects.create(
            title='Test Note',
            text='This is a test note',
            author=self.author
        )

    def test_notes_list_for_different_users(self):
        test_cases = [
            (self.author, True),
            (self.not_author, False)
        ]

        for user, note_in_list in test_cases:
            with self.subTest(user=user, note_in_list=note_in_list):
                self.client.force_login(user)
                url = reverse('notes:list')
                response = self.client.get(url)
                object_list = response.context['object_list']
                self.assertEqual(note_in_list, self.note in object_list)

    def tearDown(self):
        self.note.delete()
        self.author.delete()
        self.not_author.delete()


class TestPagesContainForm(TestCase):

    def setUp(self):
        # Создаем автора и авторизуем его
        self.author = get_user_model().objects.create_user(
            username='author',
            password='password123',
            email='author@example.com'
        )
        self.client.force_login(self.author)

        # Создаем заметку для редактирования
        self.note = Note.objects.create(
            title='Test Note',
            text='This is a test note',
            author=self.author
        )

    def test_pages_contains_form(self):
        test_cases = [
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        ]

        for name, args in test_cases:
            with self.subTest(name=name, args=args):
                url = reverse(name, args=args if args else [])
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)

    def tearDown(self):
        self.note.delete()
        self.author.delete()
