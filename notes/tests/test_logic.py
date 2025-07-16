from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils.http import urlencode
from django.contrib.auth.models import AnonymousUser

from notes.models import Note
from notes.forms import WARNING
from pytils.translit import slugify


class BaseNoteTestCase(TestCase):
    def setUp(self):
        super().setUp()
        # Очищаем базу данных перед каждым тестом
        Note.objects.all().delete()

        # Создаем основного автора
        self.author = get_user_model().objects.create_user(
            username='author',
            password='password123',
            email='author@example.com'
        )
        self.client.force_login(self.author)
        
        # Базовые данные формы
        self.form_data = {
            'title': 'Test Note',
            'text': 'This is a test note',
            'slug': 'test-note'
        }

    def create_note(self):
        return Note.objects.create(
            title='Test Note',
            text='This is a test note',
            slug='test-note',
            author=self.author
        )

    def create_other_user(self):
        return get_user_model().objects.create_user(
            username='other_user',
            password='password123',
            email='other@example.com'
        )

    def tearDown(self):
        self.author.delete()

class TestNoteCreation(BaseNoteTestCase):
    def test_user_can_create_note(self):
        url = reverse('notes:add')
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)

        new_note = Note.objects.get()
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        anonymous_client = Client()
        url = reverse('notes:add')
        response = anonymous_client.post(url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 0)

    def test_not_unique_slug(self):
        note = self.create_note()

        url = reverse('notes:add')
        self.form_data['slug'] = note.slug
        response = self.client.post(url, data=self.form_data)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIn('slug', form.errors)
        self.assertEqual(
            form.errors['slug'][0],
            note.slug + WARNING
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        url = reverse('notes:add')
        form_data = self.form_data.copy()
        form_data.pop('slug')
        response = self.client.post(url, data=form_data)

        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)

        new_note = Note.objects.get()
        expected_slug = slugify(form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditing(BaseNoteTestCase):
    def setUp(self):
        super().setUp()
        self.note = self.create_note()
        self.form_data = {
            'title': 'Updated Title',
            'text': 'Updated text',
            'slug': 'updated-slug'
        }

    def test_author_can_edit_note(self):
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))

        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        other_user = self.create_other_user()
        other_client = Client()
        other_client.force_login(other_user)

        url = reverse('notes:edit', args=(self.note.slug,))
        response = other_client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def tearDown(self):
        self.note.delete()
        super().tearDown()

class TestNoteDeletion(BaseNoteTestCase):
    def setUp(self):
        super().setUp()
        self.note = self.create_note()

    def test_author_can_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        other_user = self.create_other_user()
        other_client = Client()

        # Реализуем реальную авторизацию через POST-запрос
        login_url = reverse('users:login')
        login_response = other_client.post(login_url, {
            'username': other_user.username,
            'password': 'password123'
        })

        # Проверяем, что авторизация прошла успешно
        self.assertEqual(login_response.status_code, 302)

        # Пытаемся удалить заметку
        url = reverse('notes:delete', args=(self.note.slug,))
        response = other_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)

    def tearDown(self):
        self.note.delete()
        super().tearDown()