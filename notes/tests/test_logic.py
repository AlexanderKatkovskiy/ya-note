from http import HTTPStatus

from django.test import Client
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING
from pytils.translit import slugify
from .test_utils.base_test_case import BaseNoteTestCase


class TestNoteCreation(BaseNoteTestCase):
    def setUp(self):
        super().setUp()
        # Очищаем заметки перед каждым тестом
        Note.objects.all().delete()
        # Фиксируем начальное состояние базы данных
        self.initial_notes_count = Note.objects.count()

    def test_user_can_create_note(self):
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.form_data)

        # Проверяем, что заметка создана
        self.assertEqual(response.status_code, HTTPStatus.FOUND)  # 302
        self.assertEqual(Note.objects.count(), self.initial_notes_count + 1)

        new_note = Note.objects.last()
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
        # Проверяем, что заметка не была создана
        self.assertEqual(Note.objects.count(), self.initial_notes_count)

    def test_not_unique_slug(self):
        # Создаём существующую заметку чтобы было с чем сравнивать slug
        note = self.create_note()
        # Формируем URL и данные для создания новой заметки
        url = reverse('notes:add')
        self.form_data['slug'] = note.slug
        # Отправляем POST-запрос
        response = self.client.post(url, data=self.form_data)
        # Проверяем наличие формы в контексте
        self.assertIn('form', response.context)
        form = response.context['form']
        # Проверяем наличие ошибки валидации для поля slug
        self.assertIn('slug', form.errors)
        self.assertEqual(
            form.errors['slug'][0],
            note.slug + WARNING
        )
        # Проверяем, что количество заметок НЕ изменилось
        # (т.е только та что мы сами создали в начале теста)
        self.assertEqual(Note.objects.count(), self.initial_notes_count + 1)

    def test_empty_slug(self):
        url = reverse('notes:add')
        form_data = self.form_data.copy()
        form_data.pop('slug')
        response = self.author_client.post(url, data=form_data)
        # Проверяем успешный редирект
        self.assertEqual(response.status_code, HTTPStatus.FOUND)  # 302
        # Проверяем создание заметки
        self.assertEqual(Note.objects.count(), self.initial_notes_count + 1)
        new_note = Note.objects.last()
        expected_slug = slugify(form_data['title'])
        # Проверяем корректность сгенерированного slug
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditing(BaseNoteTestCase):
    def setUp(self):
        super().setUp()
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
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.not_author_client.post(url, data=self.form_data)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.note.refresh_from_db()
        self.assertNotEqual(self.note.title, self.form_data['title'])
        self.assertNotEqual(self.note.text, self.form_data['text'])
        self.assertNotEqual(self.note.slug, self.form_data['slug'])


class TestNoteDeletion(BaseNoteTestCase):
    def setUp(self):
        super().setUp()
        # Фиксируем начальное состояние базы данных
        self.initial_notes_count = Note.objects.count()

    def test_other_user_cant_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.not_author_client.post(url)

        # Проверяем статус и количество заметок
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), self.initial_notes_count)

    def test_anonymous_cant_delete_note(self):
        anonymous_client = Client()
        url = reverse('notes:delete', args=(self.note.slug,))
        response = anonymous_client.post(url)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'

        # Проверяем редирект и количество заметок
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), self.initial_notes_count)

    def test_author_can_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.client.post(url)

        # Проверяем успешное удаление
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), self.initial_notes_count - 1)
