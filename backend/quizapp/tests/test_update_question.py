from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
import json

from quizapp.models import Users, File, Quiz, Section, Question
from quizapp.views import generate_jwt_token

class UpdateQuestionViewTest(TestCase):
    def setUp(self):
        settings.JWT_SECRET_KEY = 'testsecret'
        self.client = Client()
        self.owner = Users.objects.create(userName='owner', email='owner@example.com', password='pass')
        self.other = Users.objects.create(userName='other', email='other@example.com', password='pass')
        self.file = File.objects.create(userID=self.owner, fileName='test.csv', filePath='x.csv', fileType='csv')
        self.quiz = Quiz.objects.create(fileID=self.file, title='Quiz')
        self.section = Section.objects.create(quizID=self.quiz, sectionName='Sec')
        self.question = Question.objects.create(
            quizID=self.quiz,
            sectionID=self.section,
            questionText='Q1?',
            answerOptions=['A', 'B'],
            answerIndex=0
        )

    def auth(self, user):
        token = generate_jwt_token(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {token}'}

    def test_owner_can_update_question(self):
        url = reverse('quizapp:update_question', args=[self.quiz.quizID, self.question.questionID])
        data = {
            'questionText': 'Updated?',
            'answerOptions': ['A', 'B', 'C'],
            'answerIndex': 2
        }
        response = self.client.patch(url, data=json.dumps(data), content_type='application/json', **self.auth(self.owner))
        self.assertEqual(response.status_code, 200)
        self.question.refresh_from_db()
        self.assertEqual(self.question.questionText, 'Updated?')
        self.assertEqual(self.question.answerOptions, ['A', 'B', 'C'])
        self.assertEqual(self.question.answerIndex, 2)

    def test_non_owner_cannot_update(self):
        url = reverse('quizapp:update_question', args=[self.quiz.quizID, self.question.questionID])
        data = {'questionText': 'Nope'}
        response = self.client.patch(url, data=json.dumps(data), content_type='application/json', **self.auth(self.other))
        self.assertEqual(response.status_code, 403)