#!/usr/bin/env python3
"""
Enhanced QuizCanvas Development Test Suite
Tests all major functionality with detailed debugging
"""

import requests
import json
import io
import time
import sys
from pathlib import Path

class QuizCanvasTestSuite:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.user_token = None
        self.quiz_id = None
        self.attempt_id = None
        
        # Test results tracking
        self.results = {
            'passed': 0,
            'failed': 0,
            'details': []
        }

    def log_test(self, test_name, passed, details="", response=None):
        """Log test results with detailed information"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        
        if not passed or response:
            if response:
                print(f"   └─ Status: {response.status_code}")
                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        print(f"   └─ Error: {error_data.get('error', 'Unknown error')}")
                        if 'details' in error_data:
                            print(f"   └─ Details: {error_data['details']}")
                    except:
                        print(f"   └─ Response: {response.text[:100]}...")
            if details:
                print(f"   └─ {details}")
        
        if passed:
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1
            
        self.results['details'].append({
            'test': test_name,
            'passed': passed,
            'details': details,
            'status_code': response.status_code if response else None
        })

    def test_user_registration(self):
        """Test user registration with unique credentials"""
        timestamp = int(time.time())
        # Keep username under 10 characters - use last 6 digits of timestamp
        short_id = str(timestamp)[-6:]
        test_data = {
            "username": f"usr{short_id}",
            "email": f"test{timestamp}@example.com",
            "password": "TestPass123!"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/register/",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                data = response.json()
                self.user_token = data['data']['token']
                self.session.headers.update({'Authorization': f'Bearer {self.user_token}'})
                self.log_test("User Registration", True, f"User: {test_data['username']}", response)
                return True
            else:
                self.log_test("User Registration", False, "Registration failed", response)
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
            return False

    def create_test_csv_content(self):
        """Create valid CSV content for testing"""
        csv_content = '''question,option_a,option_b,option_c,option_d,correct_answer,section
"What is 2+2?","3","4","5","6","B","Math Basics"
"What is the capital of France?","London","Berlin","Paris","Madrid","C","Geography"
"Which planet is closest to the sun?","Venus","Mercury","Earth","Mars","B","Science"
"What is the largest ocean?","Atlantic","Pacific","Indian","Arctic","B","Geography"
"What is 5*3?","12","15","18","20","B","Math Basics"'''
        return csv_content

    def test_file_upload(self):
        """Test file upload with proper CSV format"""
        if not self.user_token:
            self.log_test("File Upload & Processing", False, "No auth token available")
            return False

        try:
            # Create test CSV file
            csv_content = self.create_test_csv_content()
            csv_file = io.StringIO(csv_content)
            
            files = {
                'file': ('test_quiz.csv', csv_content, 'text/csv')
            }
            
            data = {
                'quiz_title': 'Test Quiz Upload'
            }
            
            response = self.session.post(
                f"{self.base_url}/api/files/upload/",
                files=files,
                data=data
            )
            
            if response.status_code == 201:
                data = response.json()
                self.quiz_id = data['data']['quiz_id']
                self.log_test("File Upload & Processing", True, 
                            f"Quiz ID: {self.quiz_id}, Questions: {data['data']['total_questions']}", 
                            response)
                return True
            else:
                self.log_test("File Upload & Processing", False, "Upload failed", response)
                return False
                
        except Exception as e:
            self.log_test("File Upload & Processing", False, f"Exception: {str(e)}")
            return False

    def test_quiz_attempt_flow(self):
        """Test complete quiz attempt flow"""
        if not self.quiz_id:
            self.log_test("Quiz Attempt Flow", False, "No quiz ID available")
            return False

        try:
            # Start quiz attempt
            response = self.session.post(f"{self.base_url}/api/quizzes/{self.quiz_id}/start/")
            
            if response.status_code != 201:
                self.log_test("Quiz Attempt Flow", False, "Failed to start quiz", response)
                return False
            
            data = response.json()
            self.attempt_id = data['data']['attempt_id']
            
            # Answer first question
            first_question = data['data']['first_question']
            answer_response = self.session.post(
                f"{self.base_url}/api/attempts/{self.attempt_id}/answer/{first_question['question_id']}/",
                json={
                    "selected_option": 1,  # Choose option B
                    "response_time": 5000
                },
                headers={"Content-Type": "application/json"}
            )
            
            if answer_response.status_code != 200:
                self.log_test("Quiz Attempt Flow", False, "Failed to submit answer", answer_response)
                return False
            
            # Complete quiz attempt
            complete_response = self.session.post(
                f"{self.base_url}/api/attempts/{self.attempt_id}/complete/"
            )
            
            if complete_response.status_code == 200:
                complete_data = complete_response.json()
                self.log_test("Quiz Attempt Flow", True, 
                            f"Score: {complete_data['data']['score']}%", 
                            complete_response)
                return True
            else:
                self.log_test("Quiz Attempt Flow", False, "Failed to complete quiz", complete_response)
                return False
                
        except Exception as e:
            self.log_test("Quiz Attempt Flow", False, f"Exception: {str(e)}")
            return False

    def test_progress_tracking(self):
        """Test progress tracking functionality"""
        if not self.user_token:
            self.log_test("Progress Tracking", False, "No auth token available")
            return False

        try:
            response = self.session.get(f"{self.base_url}/api/progress/")
            
            if response.status_code == 200:
                data = response.json()
                has_progress = data['data'].get('has_progress', False)
                
                if has_progress:
                    progress_count = len(data['data'].get('progress', []))
                    self.log_test("Progress Tracking", True, 
                                f"Found {progress_count} progress records", response)
                else:
                    # Empty state is also valid
                    self.log_test("Progress Tracking", True, 
                                "Empty state (no progress data yet)", response)
                return True
            else:
                self.log_test("Progress Tracking", False, "Failed to get progress", response)
                return False
                
        except Exception as e:
            self.log_test("Progress Tracking", False, f"Exception: {str(e)}")
            return False

    def test_database_health(self):
        """Test database connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/api/health/")
            
            if response.status_code == 200:
                data = response.json()
                db_status = data.get('database', {}).get('connection', 'unknown')
                self.log_test("Database Health", db_status == 'ok', 
                            f"DB Status: {db_status}", response)
                return db_status == 'ok'
            else:
                self.log_test("Database Health", False, "Health check failed", response)
                return False
                
        except Exception as e:
            self.log_test("Database Health", False, f"Exception: {str(e)}")
            return False

    def test_system_connections(self):
        """Test system connections (S3, EC2)"""
        try:
            response = self.session.get(f"{self.base_url}/api/system/connections/")
            
            if response.status_code == 200:
                data = response.json()
                overall_status = data['data']['overall_status']
                self.log_test("System Connections", overall_status == 'healthy', 
                            f"Status: {overall_status}", response)
                return overall_status == 'healthy'
            else:
                self.log_test("System Connections", False, "Connection check failed", response)
                return False
                
        except Exception as e:
            self.log_test("System Connections", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 Running Enhanced QuizCanvas Test Suite")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("User Registration", self.test_user_registration),
            ("File Upload & Processing", self.test_file_upload),
            ("Quiz Attempt Flow", self.test_quiz_attempt_flow),
            ("Progress Tracking", self.test_progress_tracking),
            ("Database Health", self.test_database_health),
            ("System Connections", self.test_system_connections)
        ]
        
        for test_name, test_func in tests:
            test_func()
            time.sleep(0.5)  # Brief pause between tests
        
        # Summary
        print("=" * 60)
        print(f"📊 Results: {self.results['passed']}/{len(tests)} tests passed")
        
        if self.results['failed'] == 0:
            print("🎉 All tests PASSED! QuizCanvas is fully operational!")
        else:
            print(f"⚠️  {self.results['failed']} tests FAILED - see details above")
            
        print("\n📋 Detailed Summary:")
        print("-" * 30)
        for detail in self.results['details']:
            status = "PASS" if detail['passed'] else "FAIL"
            print(f"{detail['test']}: {status}")
            if detail['status_code']:
                print(f"   └─ Status: {detail['status_code']}")
        
        # Recommendations
        if self.results['failed'] > 0:
            print(f"\n🔧 Troubleshooting Steps:")
            print("1. Ensure Django server is running: python manage.py runserver")
            print("2. Check database migrations: python manage.py migrate")
            print("3. Verify environment variables are set")
            print("4. Check the CSV format matches requirements exactly")
            print("5. Review Django logs for specific error details")

def main():
    """Main test execution"""
    # Check if server is reachable
    try:
        response = requests.get("http://127.0.0.1:8000/api/health/", timeout=5)
        print("✅ Server is reachable")
    except requests.exceptions.RequestException:
        print("❌ Cannot reach Django server at http://127.0.0.1:8000")
        print("💡 Make sure to run: python manage.py runserver")
        sys.exit(1)
    
    # Run tests
    suite = QuizCanvasTestSuite()
    suite.run_all_tests()

if __name__ == "__main__":
    main()