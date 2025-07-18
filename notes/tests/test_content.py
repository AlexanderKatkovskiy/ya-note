from django.urls import reverse

from notes.forms import NoteForm
from .test_utils.base_test_case import BaseNoteTestCase


class TestNotesListForDifferentUsers(BaseNoteTestCase):
    def test_notes_list_for_different_users(self):
        test_cases = [
            (self.author_client, True),
            (self.not_author_client, False)
        ]

        for client, note_in_list in test_cases:
            with self.subTest(client=client, note_in_list=note_in_list):
                url = reverse('notes:list')
                response = client.get(url)
                object_list = response.context['object_list']
                self.assertEqual(note_in_list, self.note in object_list)


class TestPagesContainForm(BaseNoteTestCase):
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
