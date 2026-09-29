"""Offline smoke checks for the upload and reporting workflow."""

import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import app as application


class AppTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        upload_patch = patch.object(application, 'UPLOAD_FOLDER', self.directory.name)
        upload_patch.start()
        self.addCleanup(upload_patch.stop)
        config_patch = patch.dict(application.app.config, TESTING=True, SECRET_KEY='test-only')
        config_patch.start()
        self.addCleanup(config_patch.stop)
        ai_patch = patch('utils.ai_advisor._ask_model', side_effect=RuntimeError('Offline test'))
        ai_patch.start()
        self.addCleanup(ai_patch.stop)
        self.client = application.app.test_client()

    def upload(self, filename='sample.csv'):
        return self.client.post('/upload', data={
            'file': (io.BytesIO(b'product,sales\napple,10\npear,20\napple,30\n'), filename)
        }, follow_redirects=True)

    def test_upload_dashboard_and_report(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.upload().status_code, 200)
        self.assertEqual(self.client.get('/suggestions').status_code, 200)
        report = self.client.get('/report')
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.get_json()['rows'], 3)
        self.assertEqual(len(report.get_json()['prediction']['predicted']), 5)
        self.assertTrue(report.get_json()['ai_advice']['fallback'])

    def test_replacement_removes_previous_upload(self):
        self.upload()
        previous = list(Path(self.directory.name).iterdir())[0]
        self.upload('replacement.csv')
        self.assertFalse(previous.exists())
        self.assertEqual(len(list(Path(self.directory.name).iterdir())), 1)

    def test_invalid_upload(self):
        response = self.upload('sample.txt')
        self.assertIn(b'Only CSV files are supported', response.data)
        self.assertEqual(list(Path(self.directory.name).iterdir()), [])

    def test_upload_limit(self):
        with patch.dict(application.app.config, MAX_CONTENT_LENGTH=32):
            response = self.upload()
        self.assertEqual(response.status_code, 413)

    def test_missing_session_redirects_to_upload(self):
        for route in ('/dashboard', '/suggestions', '/report'):
            self.assertEqual(self.client.get(route).status_code, 302)


if __name__ == '__main__':
    unittest.main()
