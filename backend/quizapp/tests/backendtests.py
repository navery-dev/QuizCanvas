import requests
import json
import io
import time
import sys
import os
import django
from pathlib import Path

# Setup Django for unit tests
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Import Django components for unit testing
from django.test import TestCase
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from unittest.mock import Mock, patch
import unittest

# Import your models and utilities
from quizapp.models import *
from quizapp.views import calculate_mastery_level, generate_jwt_token, verify_jwt_token
from quizapp.tests import UserRegistrationTests, FileUploadTests

class QuizCanvasTestSuite:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            'integration_tests': {'passed': 0, 'failed': 0, 'details': []},
            'unit_tests': {'passed': 0, 'failed': 0, 'details': []},
            'system_tests': {'passed': 0, 'failed': 0, 'details': []},
            'total_passed': 0,
            'total_failed': 0
        }

    def log_result(self, category, test_name, passed, details=""):
        """Log test results by category"""
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {test_name}")
        if details:
            print(f"    └─ {details}")
        
        self.results[category]['passed' if passed else 'failed'] += 1
        self.results[category]['details'].append({
            'test': test_name,
            'passed': passed,
            'details': details
        })

    # =====================================
    # UNIT TESTS - Test Individual Functions
    # =====================================
    
    def run_unit_tests(self):
        """Run unit tests for individual functions and methods"""
        print("\n Unit Tests - Testing Individual Components")
        print("=" * 60)
        
        # Test 1: Password hashing utility
        self.test_password_hashing()
        
        # Test 2: JWT token generation and verification
        self.test_jwt_functions()
        
        # Test 3: Mastery level calculation
        self.test_mastery_calculation()
        
        # Test 4: Model validation
        self.test_model_validation()
        
        # Test 5: File validation functions
        self.test_file_validation_functions()

    def test_password_hashing(self):
        """Unit test: Password hashing functions"""
        try:
            password = "TestPassword123!"
            hashed = make_password(password)
            
            # Test password was hashed
            assert hashed != password, "Password should be hashed"
            
            # Test password verification
            assert check_password(password, hashed), "Password verification should work"
            assert not check_password("wrong", hashed), "Wrong password should fail"
            
            self.log_result('unit_tests', 'Password Hashing', True, "Hash and verify working")
            
        except Exception as e:
            self.log_result('unit_tests', 'Password Hashing', False, str(e))

    def test_jwt_functions(self):
        """Unit test: JWT token generation and verification"""
        try:
            # Create a mock user object
            mock_user = Mock()
            mock_user.userID = 123
            mock_user.userName = "testuser"
            
            # Test token generation
            token = generate_jwt_token(mock_user)
            assert token is not None, "Token should be generated"
            assert isinstance(token, str), "Token should be string"
            
            # Test token verification
            payload = verify_jwt_token(token)
            assert payload['user_id'] == 123, "Payload should contain user ID"
            assert payload['username'] == "testuser", "Payload should contain username"
            
            self.log_result('unit_tests', 'JWT Functions', True, "Generate and verify working")
            
        except Exception as e:
            self.log_result('unit_tests', 'JWT Functions', False, str(e))

    def test_mastery_calculation(self):
        """Unit test: Mastery level calculation"""
        try:
            test_cases = [
                (95, "Expert"),
                (85, "Advanced"),
                (75, "Intermediate"),
                (65, "Beginner"),
                (45, "Needs Practice")
            ]
            
            for score, expected in test_cases:
                result = calculate_mastery_level(score)
                assert result == expected, f"Score {score} should give {expected}, got {result}"
            
            self.log_result('unit_tests', 'Mastery Calculation', True, "All score ranges correct")
            
        except Exception as e:
            self.log_result('unit_tests', 'Mastery Calculation', False, str(e))

    def test_model_validation(self):
        """Unit test: Model field validation"""
        try:
            # Test username length validation
            user_tests = UserRegistrationTests()
            
            # Test valid data
            result = user_tests.test_field_length_validation("testuser", "test@example.com", "password123")
            assert result['success'], "Valid data should pass validation"
            
            # Test invalid username (too long)
            result = user_tests.test_field_length_validation("this_username_is_too_long", "test@example.com", "password123")
            assert not result['success'], "Long username should fail validation"
            
            # Test invalid email (too long)
            long_email = "a" * 50 + "@example.com"
            result = user_tests.test_field_length_validation("testuser", long_email, "password123")
            assert not result['success'], "Long email should fail validation"
            
            self.log_result('unit_tests', 'Model Validation', True, "Field length validation working")
            
        except Exception as e:
            self.log_result('unit_tests', 'Model Validation', False, str(e))

    def test_file_validation_functions(self):
        """Unit test: File validation functions"""
        try:
            file_tests = FileUploadTests()
            
            # Test CSV format validation
            valid_csv = 'question,option_a,option_b,option_c,option_d,correct_answer,section\n"Test?","A","B","C","D","B","Math"'
            result = file_tests.test_csv_format_validation(valid_csv)
            assert result['success'], "Valid CSV should pass validation"
            
            # Test invalid CSV
            invalid_csv = 'invalid,csv,format'
            result = file_tests.test_csv_format_validation(invalid_csv)
            assert not result['success'], "Invalid CSV should fail validation"
            
            # Test JSON format validation
            valid_json = '{"quiz_title": "Test", "sections": []}'
            result = file_tests.test_json_format_validation(valid_json)
            assert result['success'], "Valid JSON should pass validation"
            
            # Test invalid JSON
            invalid_json = '{"invalid": json}'
            result = file_tests.test_json_format_validation(invalid_json)
            assert not result['success'], "Invalid JSON should fail validation"
            
            self.log_result('unit_tests', 'File Validation Functions', True, "CSV and JSON validation working")
            
        except Exception as e:
            self.log_result('unit_tests', 'File Validation Functions', False, str(e))

    # =====================================
    # INTEGRATION TESTS - Test API Endpoints
    # =====================================
    
    def run_integration_tests(self):
        """Run integration tests for API endpoints"""
        print("\n Integration Tests - Testing API Endpoints")
        print("=" * 60)
        
        # Test complete user workflow
        token = self.test_user_registration_integration()
        if token:
            quiz_id = self.test_file_upload_integration(token)
            if quiz_id:
                attempt_id = self.test_quiz_flow_integration(token, quiz_id)
                if attempt_id:
                    self.test_progress_integration(token)

    def test_user_registration_integration(self):
        """Integration test: Complete user registration flow"""
        try:
            timestamp = int(time.time())
            user_data = {
                "username": f"usr{str(timestamp)[-6:]}",
                "email": f"test{timestamp}@example.com",
                "password": "TestPass123!"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/register/",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                data = response.json()
                token = data['data']['token']
                self.session.headers.update({'Authorization': f'Bearer {token}'})
                self.log_result('integration_tests', 'User Registration API', True, f"User: {user_data['username']}")
                return token
            else:
                self.log_result('integration_tests', 'User Registration API', False, f"Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_result('integration_tests', 'User Registration API', False, str(e))
            return None

    def test_file_upload_integration(self, token):
        """Integration test: File upload and processing"""
        try:
            csv_content = '''question,option_a,option_b,option_c,option_d,correct_answer,section
"What is 2+2?","3","4","5","6","B","Math"
"What is 3+3?","5","6","7","8","B","Math"
"Capital of France?","London","Paris","Berlin","Madrid","B","Geography"'''
            
            files = {'file': ('test_quiz.csv', csv_content, 'text/csv')}
            data = {'quiz_title': 'Integration Test Quiz'}
            
            response = self.session.post(
                f"{self.base_url}/api/files/upload/",
                files=files,
                data=data
            )
            
            if response.status_code == 201:
                data = response.json()
                quiz_id = data['data']['quiz_id']
                self.log_result('integration_tests', 'File Upload API', True, f"Quiz ID: {quiz_id}")
                return quiz_id
            else:
                self.log_result('integration_tests', 'File Upload API', False, f"Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_result('integration_tests', 'File Upload API', False, str(e))
            return None

    def test_quiz_flow_integration(self, token, quiz_id):
        """Integration test: Complete quiz taking flow"""
        try:
            # Start quiz attempt
            response = self.session.post(f"{self.base_url}/api/quizzes/{quiz_id}/start/")
            
            if response.status_code != 201:
                self.log_result('integration_tests', 'Quiz Flow API', False, "Failed to start quiz")
                return None
            
            data = response.json()
            attempt_id = data['data']['attempt_id']
            first_question = data['data']['first_question']
            
            # Submit answer
            answer_response = self.session.post(
                f"{self.base_url}/api/attempts/{attempt_id}/answer/{first_question['question_id']}/",
                json={"selected_option": 1, "response_time": 5000},
                headers={"Content-Type": "application/json"}
            )
            
            if answer_response.status_code != 200:
                self.log_result('integration_tests', 'Quiz Flow API', False, "Failed to submit answer")
                return None
            
            # Complete quiz
            complete_response = self.session.post(f"{self.base_url}/api/attempts/{attempt_id}/complete/")
            
            if complete_response.status_code == 200:
                result_data = complete_response.json()
                score = result_data['data']['score']
                self.log_result('integration_tests', 'Quiz Flow API', True, f"Score: {score}%")
                return attempt_id
            else:
                self.log_result('integration_tests', 'Quiz Flow API', False, "Failed to complete quiz")
                return None
                
        except Exception as e:
            self.log_result('integration_tests', 'Quiz Flow API', False, str(e))
            return None

    def test_progress_integration(self, token):
        """Integration test: Progress tracking API"""
        try:
            response = self.session.get(f"{self.base_url}/api/progress/")
            
            if response.status_code == 200:
                data = response.json()
                has_progress = data['data'].get('has_progress', False)
                self.log_result('integration_tests', 'Progress Tracking API', True, 
                              "Progress data available" if has_progress else "Empty state handled")
            else:
                self.log_result('integration_tests', 'Progress Tracking API', False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result('integration_tests', 'Progress Tracking API', False, str(e))

    # =====================================
    # SYSTEM TESTS - Test Infrastructure
    # =====================================
    
    def run_system_tests(self):
        """Run system-level tests"""
        print("\n System Tests - Testing Infrastructure")
        print("=" * 60)
        
        self.test_database_health()
        self.test_s3_connectivity()
        self.test_api_response_times()
        self.test_error_handling()

    def test_database_health(self):
        """System test: Database connectivity and operations"""
        try:
            response = self.session.get(f"{self.base_url}/api/health/")
            
            if response.status_code == 200:
                data = response.json()
                db_status = data.get('database', {}).get('connection')
                if db_status == 'ok':
                    self.log_result('system_tests', 'Database Health', True, "Connection OK")
                else:
                    self.log_result('system_tests', 'Database Health', False, f"Status: {db_status}")
            else:
                self.log_result('system_tests', 'Database Health', False, f"Health check failed: {response.status_code}")
                
        except Exception as e:
            self.log_result('system_tests', 'Database Health', False, str(e))

    def test_s3_connectivity(self):
        """System test: S3 service connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/api/system/connections/")
            
            if response.status_code == 200:
                data = response.json()
                s3_status = data['data']['systems']['s3']['healthy']
                overall_status = data['data']['overall_status']
                
                if s3_status and overall_status == 'healthy':
                    self.log_result('system_tests', 'S3 Connectivity', True, "S3 healthy")
                else:
                    self.log_result('system_tests', 'S3 Connectivity', False, f"S3: {s3_status}, Overall: {overall_status}")
            else:
                self.log_result('system_tests', 'S3 Connectivity', False, f"Connection check failed: {response.status_code}")
                
        except Exception as e:
            self.log_result('system_tests', 'S3 Connectivity', False, str(e))

    def test_api_response_times(self):
        """System test: API response time performance"""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/health/")
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if response.status_code == 200 and response_time < 1000:  # Less than 1 second
                self.log_result('system_tests', 'API Response Time', True, f"{response_time:.0f}ms")
            else:
                self.log_result('system_tests', 'API Response Time', False, 
                              f"Slow response: {response_time:.0f}ms" if response.status_code == 200 else f"Failed: {response.status_code}")
                
        except Exception as e:
            self.log_result('system_tests', 'API Response Time', False, str(e))

    def test_error_handling(self):
        """System test: Error handling and validation"""
        try:
            # Test invalid endpoint
            response = self.session.get(f"{self.base_url}/api/invalid-endpoint/")
            
            if response.status_code == 404:
                self.log_result('system_tests', 'Error Handling', True, "404 errors handled correctly")
            else:
                self.log_result('system_tests', 'Error Handling', False, f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_result('system_tests', 'Error Handling', False, str(e))

    # =====================================
    # MAIN TEST RUN
    # =====================================
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("QuizCanvas Comprehensive Backend Test Suite")
        print("=" * 70)
        
        # Check if server is reachable
        try:
            response = requests.get(f"{self.base_url}/api/health/", timeout=5)
            print("Server is reachable")
        except requests.exceptions.RequestException:
            print("Cannot reach Django server")
            print("Make sure to run: python manage.py runserver")
            return
        
        # Run all test categories
        self.run_unit_tests()
        self.run_integration_tests()
        self.run_system_tests()
        
        # Calculate totals
        self.results['total_passed'] = sum(category['passed'] for category in self.results.values() if isinstance(category, dict) and 'passed' in category)
        self.results['total_failed'] = sum(category['failed'] for category in self.results.values() if isinstance(category, dict) and 'failed' in category)
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("COMPREHENSIVE TEST RESULTS")
        print("=" * 70)
        
        categories = ['unit_tests', 'integration_tests', 'system_tests']
        category_names = ['Unit Tests', 'Integration Tests', 'System Tests']
        
        for cat, name in zip(categories, category_names):
            passed = self.results[cat]['passed']
            failed = self.results[cat]['failed']
            total = passed + failed
            print(f"{name:20} | {passed:2}/{total:2} passed | {'PASS' if failed == 0 else 'FAIL'}")
        
        print("-" * 70)
        total_passed = self.results['total_passed']
        total_failed = self.results['total_failed']
        total_tests = total_passed + total_failed
        
        print(f"{'TOTAL':20} | {total_passed:2}/{total_tests:2} passed | {'🎉' if total_failed == 0 else '⚠️'}")
        
        if total_failed == 0:
            print(f"\nALL {total_tests} TESTS PASSED! Backend is fully operational!")
        else:
            print(f"\n {total_failed} tests failed out of {total_tests}")
        
        print("\n Test Categories Explained:")
        print("• Unit Tests: Individual functions and methods")
        print("• Integration Tests: API endpoints and workflows") 
        print("• System Tests: Infrastructure and performance")

def main():
    """Main test execution"""
    suite = QuizCanvasTestSuite()
    suite.run_all_tests()

if __name__ == "__main__":
    main()