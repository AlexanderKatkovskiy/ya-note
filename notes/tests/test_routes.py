from http import HTTPStatus

from django.test import Client
from django.urls import reverse

from .test_utils.base_test_case import BaseNoteTestCase


class TestRedirectsForAnonymousUsers(BaseNoteTestCase):
    def setUp(self):
        # Используем заметку из базового класса
        super().setUp()
        # Создаем анонимного клиента
        self.anonymous_client = Client()

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

                response = self.anonymous_client.get(url)
                self.assertRedirects(
                    response,
                    expected_url,
                    status_code=302,
                    target_status_code=200
                )

    def test_home_page_accessibility(self):
        # Проверяем доступность домашней страницы для анонимного пользователя
        url = reverse('notes:home')
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)


class TestPagesAvailability(BaseNoteTestCase):
    def test_basic_pages_availability(self):
        # Проверяем базовые страницы для всех авторизованных пользователей
        basic_urls = [
            'notes:list',
            'notes:add',
            'notes:success'
        ]

        # Проверяем для обоих клиентов
        for client in [self.author_client, self.not_author_client]:
            with self.subTest(client=client):
                for name in basic_urls:
                    with self.subTest(name=name):
                        url = reverse(name)
                        response = client.get(url)
                        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_note_specific_pages_availability(self):
        # Определяем тестовые случаи для страниц конкретной заметки
        test_cases = [
            (self.not_author_client, HTTPStatus.NOT_FOUND),  # Клиент не-автора
            (self.author_client, HTTPStatus.OK)  # Клиент автора
        ]

        note_specific_urls = [
            'notes:detail',
            'notes:edit',
            'notes:delete'
        ]

        for client, expected_status in test_cases:
            for name in note_specific_urls:
                with self.subTest(
                    client=client,
                    name=name,
                    expected_status=expected_status
                ):
                    url = reverse(name, args=(self.note.slug,))
                    response = client.get(url)
                    self.assertEqual(response.status_code, expected_status)

    def test_note_creation(self):
        # Проверяем корректность создания заметки
        self.assertEqual(self.note.title, 'Test Note')
        self.assertEqual(self.note.author, self.author)
        self.assertTrue(self.note.slug)
