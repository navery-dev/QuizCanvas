import csv
import json
import io
from typing import Dict, List, Any, Tuple
from django.core.exceptions import ValidationError

class FileProcessor:
    @staticmethod
    def validate_file_size(file, max_size_mb=10):
        if file.size > max_size_mb * 1024 * 1024:
            raise ValidationError(f"File size exceeds {max_size_mb}MB limit")
    
    @staticmethod
    def validate_file_type(file, allowed_types):
        if not file.name.lower().endswith(tuple(allowed_types)):
            raise ValidationError(f"File type not supported. Allowed: {', '.join(allowed_types)}")

class CSVProcessor(FileProcessor):
    # Updated to match your actual CSV structure
    REQUIRED_COLUMNS = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']
    OPTIONAL_COLUMNS = ['section', 'explanation']
    
    @classmethod
    def validate_csv_structure(cls, file) -> List[Dict[str, Any]]:
        try:
            file.seek(0)
            content = file.read().decode('utf-8')
            
            # Check if file is empty
            if not content.strip():
                raise ValidationError("File is empty")
            
            # Parse CSV with better error handling
            try:
                csv_reader = csv.DictReader(io.StringIO(content))
            except Exception as e:
                raise ValidationError(f"Failed to parse CSV: {str(e)}")
            
            # Check if fieldnames exist
            if csv_reader.fieldnames is None:
                raise ValidationError("CSV file has no headers or is empty")
            
            # Clean fieldnames (remove whitespace, handle BOM)
            cleaned_fieldnames = []
            for name in csv_reader.fieldnames:
                if name:
                    # Remove BOM and whitespace
                    cleaned_name = name.strip().replace('\ufeff', '').lower()
                    cleaned_fieldnames.append(cleaned_name)
            
            print(f"DEBUG: Found CSV columns: {cleaned_fieldnames}")
            
            # Check required columns using cleaned names
            required_lower = [col.lower() for col in cls.REQUIRED_COLUMNS]
            missing_columns = []
            
            for req_col in required_lower:
                if req_col not in cleaned_fieldnames:
                    missing_columns.append(req_col)
            
            if missing_columns:
                raise ValidationError(f"CSV missing required columns: {', '.join(missing_columns)}. Found columns: {', '.join(cleaned_fieldnames)}")
            
            # Parse each row and validate data
            questions = []
            file.seek(0)  # Reset file pointer
            csv_reader = csv.DictReader(io.StringIO(file.read().decode('utf-8')))
            
            for row_num, row in enumerate(csv_reader, start=2):
                if not row or all(not str(v).strip() for v in row.values() if v is not None):
                    continue  # Skip empty rows
                
                try:
                    question_data = cls._parse_csv_row(row, row_num)
                    questions.append(question_data)
                except ValidationError as e:
                    raise ValidationError(f"Row {row_num}: {str(e)}")
                except Exception as e:
                    raise ValidationError(f"Row {row_num}: Unexpected error - {str(e)}")
            
            if not questions:
                raise ValidationError("CSV file contains no valid questions")
            
            return questions
            
        except UnicodeDecodeError:
            raise ValidationError("File encoding not supported. Please use UTF-8")
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"CSV parsing error: {str(e)}")
    
    @classmethod
    def _parse_csv_row(cls, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
        def get_field_value(field_name):
            # Try exact match first
            if field_name in row:
                return row[field_name]
            
            # Try case-insensitive lookup
            field_lower = field_name.lower()
            for key, value in row.items():
                if key and key.strip().replace('\ufeff', '').lower() == field_lower:
                    return value
            
            return None
        
        # Extract and validate required fields
        question_text = get_field_value('question')
        if not question_text or not str(question_text).strip():
            raise ValidationError("Missing or empty question text")
        
        # Extract options
        options = []
        for option_key in ['option_a', 'option_b', 'option_c', 'option_d']:
            option_value = get_field_value(option_key)
            if option_value is None or not str(option_value).strip():
                raise ValidationError(f"Missing or empty value for '{option_key}'")
            options.append(str(option_value).strip())
        
        # Validate correct answer
        correct_answer = get_field_value('correct_answer')
        if not correct_answer:
            raise ValidationError("Missing correct_answer value")
        
        correct_answer = str(correct_answer).strip().lower()
        if correct_answer not in ['a', 'b', 'c', 'd']:
            raise ValidationError(f"correct_answer must be a, b, c, or d. Got: '{correct_answer}'")
        
        # Convert letter to array index
        answer_index = ord(correct_answer.upper()) - ord('A')
        
        # Handle optional fields
        section = get_field_value('section')
        section = str(section).strip() if section else 'General'
        
        explanation = get_field_value('explanation')
        explanation = str(explanation).strip() if explanation else ''
        
        return {
            'question_text': str(question_text).strip(),
            'answer_options': options,
            'answer_index': answer_index,
            'section': section,
            'explanation': explanation
        }
    
    @classmethod
    def process_file(cls, file) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        cls.validate_file_size(file)
        cls.validate_file_type(file, ['.csv'])
        questions = cls.validate_csv_structure(file)
        
        # Generate metadata
        sections = list(set(q['section'] for q in questions))
        metadata = {
            'total_questions': len(questions),
            'sections': sections,
            'section_counts': {section: sum(1 for q in questions if q['section'] == section) 
                             for section in sections}
        }
        
        return questions, metadata

class JSONProcessor(FileProcessor):
    
    @classmethod
    def validate_json_structure(cls, file) -> List[Dict[str, Any]]:
        try:
            file.seek(0)
            content = file.read().decode('utf-8')
            
            # Check if file is empty
            if not content.strip():
                raise ValidationError("File is empty")
            
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON format: {str(e)}")
            
            questions_data = []
            
            if isinstance(data, list):
                # Direct array of questions (this is what your test.json uses)
                questions_data = data
            elif isinstance(data, dict):
                # Object with questions array
                if 'questions' in data:
                    if not isinstance(data['questions'], list):
                        raise ValidationError("'questions' must be an array")
                    questions_data = data['questions']
                else:
                    # Single question object - convert to array
                    if cls._is_question_object(data):
                        questions_data = [data]
                    else:
                        raise ValidationError("JSON object must contain 'questions' array or be a single question object")
            else:
                raise ValidationError("JSON must be an array of questions, a single question object, or an object with 'questions' array")
            
            if not questions_data:
                raise ValidationError("No questions found in JSON file")
            
            # Parse each question
            questions = []
            for idx, question_data in enumerate(questions_data):
                try:
                    parsed_question = cls._parse_json_question(question_data, idx)
                    questions.append(parsed_question)
                except ValidationError as e:
                    raise ValidationError(f"Question {idx + 1}: {str(e)}")
            
            if not questions:
                raise ValidationError("JSON file contains no valid questions")
            
            return questions
            
        except UnicodeDecodeError:
            raise ValidationError("File encoding not supported. Please use UTF-8")
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"JSON processing error: {str(e)}")
    
    @classmethod
    def _is_question_object(cls, obj: Dict) -> bool:
        """Check if an object looks like a single question"""
        required_fields = ['question', 'options', 'correct_answer']
        return all(field in obj for field in required_fields)
    
    @classmethod
    def _parse_json_question(cls, question_data: Dict, idx: int) -> Dict[str, Any]:
        if not isinstance(question_data, dict):
            raise ValidationError("Each question must be an object")
        
        required_fields = ['question', 'options', 'correct_answer']
        
        # Validate required fields exist
        for field in required_fields:
            if field not in question_data:
                raise ValidationError(f"Missing required field '{field}'")
        
        # Validate question text
        question_text = question_data['question']
        if not isinstance(question_text, str) or not question_text.strip():
            raise ValidationError("'question' must be a non-empty string")
        
        # Validate options array
        options = question_data['options']
        if not isinstance(options, list) or len(options) < 2:
            raise ValidationError("'options' must be an array with at least 2 items")
        
        if len(options) > 6:
            raise ValidationError("'options' cannot have more than 6 items")
        
        # Ensure all options are strings
        cleaned_options = []
        for i, option in enumerate(options):
            if option is None or str(option).strip() == '':
                raise ValidationError(f"Option {i + 1} cannot be empty")
            cleaned_options.append(str(option).strip())
        
        # Validate correct answer index
        correct_answer = question_data['correct_answer']
        if not isinstance(correct_answer, int):
            raise ValidationError("'correct_answer' must be an integer (0-based index)")
        
        if correct_answer < 0 or correct_answer >= len(options):
            raise ValidationError(f"'correct_answer' index {correct_answer} is out of range for {len(options)} options")
        
        # Handle optional fields
        section = question_data.get('section', '')
        section = str(section).strip() if section else 'General'
        
        explanation = question_data.get('explanation', '')
        explanation = str(explanation).strip() if explanation else ''
        
        return {
            'question_text': question_text.strip(),
            'answer_options': cleaned_options,
            'answer_index': correct_answer,
            'section': section,
            'explanation': explanation
        }
    
    @classmethod
    def process_file(cls, file) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        cls.validate_file_size(file)
        cls.validate_file_type(file, ['.json'])
        questions = cls.validate_json_structure(file)
        
        sections = list(set(q['section'] for q in questions))
        metadata = {
            'total_questions': len(questions),
            'sections': sections,
            'section_counts': {section: sum(1 for q in questions if q['section'] == section) 
                             for section in sections}
        }
        
        return questions, metadata

def process_quiz_file(file) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Main entry point for processing uploaded quiz files"""
    if not file:
        raise ValidationError("No file provided")
    
    filename = file.name.lower()
    
    if filename.endswith('.csv'):
        return CSVProcessor.process_file(file)
    elif filename.endswith('.json'):
        return JSONProcessor.process_file(file)
    else:
        raise ValidationError("Unsupported file type. Please upload CSV or JSON files only.")