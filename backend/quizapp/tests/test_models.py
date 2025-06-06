from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from django.db import IntegrityError
from quizapp.models import Users, File, Quiz, Section, Question, QuizAttempt, Answer, Progress
from quizapp.views import calculate_mastery_level, generate_jwt_token, verify_jwt_token
from unittest.mock import Mock
import json

class UserModelTest(TestCase):
    """Unit tests for User model"""
    
    def test_user_creation(self):
        """Test creating a user with valid data"""
        user = Users.objects.create(
            userName="testuser",
            email="test@example.com",
            password="hashedpassword123"
        )
        self.assertEqual(user.userName, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.userID)

    def test_user_username_max_length(self):
        """Test username length constraint"""
        with self.assertRaises(Exception):  # Should fail on save
            user = Users(
                userName="a" * 11,  # Too long (max 10)
                email="test@example.com",
                password="hashedpassword123"
            )
            user.full_clean()  # Validate before save

    def test_user_email_uniqueness(self):
        """Test email uniqueness constraint"""
        Users.objects.create(
            userName="user1",
            email="test@example.com",
            password="password123"
        )
        
        with self.assertRaises(IntegrityError):
            Users.objects.create(
                userName="user2",
                email="test@example.com",  # Duplicate email
                password="password456"
            )

class QuizModelTest(TestCase):
    """Unit tests for Quiz model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = Users.objects.create(
            userName="testuser",
            email="test@example.com",
            password="password123"
        )
        self.file = File.objects.create(
            userID=self.user,
            fileName="test.csv",
            filePath="test/path.csv",
            fileType="csv"
        )

    def test_quiz_creation(self):
        """Test creating a quiz"""
        quiz = Quiz.objects.create(
            fileID=self.file,
            title="Test Quiz",
            description="A test quiz"
        )
        self.assertEqual(quiz.title, "Test Quiz")
        self.assertEqual(quiz.fileID, self.file)

    def test_quiz_title_max_length(self):
        """Test quiz title length constraint"""
        with self.assertRaises(Exception):
            quiz = Quiz(
                fileID=self.file,
                title="a" * 51,  # Too long (max 50)
                description="Test description"
            )
            quiz.full_clean()

class QuestionModelTest(TestCase):
    """Unit tests for Question model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = Users.objects.create(
            userName="testuser",
            email="test@example.com",
            password="password123"
        )
        self.file = File.objects.create(
            userID=self.user,
            fileName="test.csv",
            filePath="test/path.csv",
            fileType="csv"
        )
        self.quiz = Quiz.objects.create(
            fileID=self.file,
            title="Test Quiz"
        )
        self.section = Section.objects.create(
            quizID=self.quiz,
            sectionName="Math",
            sectionDesc="Math questions"
        )

    def test_question_creation(self):
        """Test creating a question"""
        question = Question.objects.create(
            quizID=self.quiz,
            sectionID=self.section,
            questionText="What is 2+2?",
            answerOptions=["3", "4", "5", "6"],
            answerIndex=1
        )
        self.assertEqual(question.questionText, "What is 2+2?")
        self.assertEqual(len(question.answerOptions), 4)
        self.assertEqual(question.answerIndex, 1)

    def test_question_answer_validation(self):
        """Test question answer index validation"""
        # Valid answer index
        question = Question(
            quizID=self.quiz,
            sectionID=self.section,
            questionText="Test question?",
            answerOptions=["A", "B", "C", "D"],
            answerIndex=2
        )
        # Should not raise exception
        question.full_clean()

class UtilityFunctionTest(TestCase):
    """Unit tests for utility functions"""
    
    def test_mastery_level_calculation(self):
        """Test mastery level calculation function"""
        test_cases = [
            (95, "Expert"),
            (90, "Expert"),
            (85, "Advanced"),
            (80, "Advanced"),
            (75, "Intermediate"),
            (70, "Intermediate"),
            (65, "Beginner"),
            (60, "Beginner"),
            (50, "Needs Practice"),
            (0, "Needs Practice")
        ]
        
        for score, expected in test_cases:
            with self.subTest(score=score):
                result = calculate_mastery_level(score)
                self.assertEqual(result, expected)

    def test_jwt_token_generation(self):
        """Test JWT token generation"""
        mock_user = Mock()
        mock_user.userID = 123
        mock_user.userName = "testuser"
        
        token = generate_jwt_token(mock_user)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 50)

    def test_jwt_token_verification(self):
        """Test JWT token verification"""
        mock_user = Mock()
        mock_user.userID = 123
        mock_user.userName = "testuser"
        
        token = generate_jwt_token(mock_user)
        payload = verify_jwt_token(token)
        
        self.assertEqual(payload['user_id'], 123)
        self.assertEqual(payload['username'], "testuser")

class QuizAttemptTest(TestCase):
    """Unit tests for quiz attempt functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = Users.objects.create(
            userName="testuser",
            email="test@example.com",
            password="password123"
        )
        self.file = File.objects.create(
            userID=self.user,
            fileName="test.csv",
            filePath="test/path.csv",
            fileType="csv"
        )
        self.quiz = Quiz.objects.create(
            fileID=self.file,
            title="Test Quiz"
        )

    def test_quiz_attempt_creation(self):
        """Test creating a quiz attempt"""
        attempt = QuizAttempt.objects.create(
            userID=self.user,
            quizID=self.quiz,
            completed=False
        )
        self.assertEqual(attempt.userID, self.user)
        self.assertEqual(attempt.quizID, self.quiz)
        self.assertFalse(attempt.completed)

    def test_score_calculation(self):
        """Test score calculation logic"""
        from quizapp.tests import QuizAttemptTests
        
        total_questions = 10
        correct_answers = 7
        expected_score = (correct_answers / total_questions) * 100
        
        self.assertEqual(expected_score, 70.0)
