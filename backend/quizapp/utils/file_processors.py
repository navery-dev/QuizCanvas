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
    # Data structure
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
            
            csv_reader = csv.DictReader(io.StringIO(content))
            
            # Check if fieldnames exist
            if csv_reader.fieldnames is None:
                raise ValidationError("CSV file has no headers or is empty")
            
            # Clean fieldnames (remove whitespace, convert to lowercase)
            fieldnames = [name.strip().lower() if name else '' for name in csv_reader.fieldnames]
            
            # Create a mapping from cleaned names to original names
            fieldname_mapping = {name.strip().lower(): name for name in csv_reader.fieldnames if name}
            
            # Check required columns using cleaned names
            required_lower = [col.lower() for col in cls.REQUIRED_COLUMNS]
            missing_columns = []
            
            for req_col in required_lower:
                if req_col not in fieldnames:
                    missing_columns.append(req_col)
            
            if missing_columns:
                raise ValidationError(f"CSV missing required columns: {', '.join(missing_columns)}")
            
            # Parse each row and validate data
            questions = []
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    question_data = cls._parse_csv_row(row, row_num, fieldname_mapping)
                    questions.append(question_data)
                except ValidationError as e:
                    raise ValidationError(f"Row {row_num}: {str(e)}")
                except AttributeError as e:
                    # Handle cases where CSV parsing results in None values
                    raise ValidationError(f"Row {row_num}: Malformed CSV data - {str(e)}")
            
            if not questions:
                raise ValidationError("CSV file contains no valid questions")
            
            return questions
            
        except UnicodeDecodeError:
            raise ValidationError("File encoding not supported. Please use UTF-8")
        except csv.Error as e:
            raise ValidationError(f"CSV parsing error: {str(e)}")
    
    @classmethod
    def _parse_csv_row(cls, row: Dict[str, str], row_num: int, fieldname_mapping: Dict[str, str]) -> Dict[str, Any]:
        # Helper function to get value from row using case-insensitive lookup
        def get_field_value(field_name):
            # Try original case first
            if field_name in row:
                return row[field_name]
            
            # Try case-insensitive lookup
            field_lower = field_name.lower()
            for original_name in fieldname_mapping.values():
                if original_name.lower() == field_lower:
                    return row[original_name]
            
            return None
        
        # Validate all required fields have values
        for field in cls.REQUIRED_COLUMNS:
            field_value = get_field_value(field)
            if field_value is None or not str(field_value).strip():
                raise ValidationError(f"Missing value for '{field}'")
        
        # Pull answer options into array, ensuring no None values
        options = []
        for option_key in ['option_a', 'option_b', 'option_c', 'option_d']:
            option_value = get_field_value(option_key)
            if option_value is None:
                raise ValidationError(f"Missing value for '{option_key}'")
            options.append(str(option_value).strip())
        
        # Validate correct answer format
        correct_answer = get_field_value('correct_answer')
        if correct_answer is None:
            raise ValidationError("Missing correct_answer value")
        
        correct_answer = str(correct_answer).strip().lower()
        if correct_answer not in ['a', 'b', 'c', 'd']:
            raise ValidationError("correct_answer must be a, b, c, or d")
        
        # Convert letter to array index
        answer_index = ord(correct_answer.upper()) - ord('A')
        
        # Handle optional fields safely
        section = get_field_value('section') or ''
        explanation = get_field_value('explanation') or ''
        
        return {
            'question_text': str(get_field_value('question')).strip(),
            'answer_options': options,
            'answer_index': answer_index,
            'section': str(section).strip() or 'General',
            'explanation': str(explanation).strip()
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
            
            data = json.loads(content)
            
            questions_data = []
            
            if isinstance(data, list):
                # Direct array of questions
                questions_data = data
            elif isinstance(data, dict):
                # Object with questions array
                if 'questions' not in data:
                    raise ValidationError("JSON object must contain 'questions' array")
                
                if not isinstance(data['questions'], list):
                    raise ValidationError("'questions' must be an array")
                
                questions_data = data['questions']
            else:
                raise ValidationError("JSON must be an array of questions or an object with 'questions' array")
            
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
            
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format: {str(e)}")
        except UnicodeDecodeError:
            raise ValidationError("File encoding not supported. Please use UTF-8")
    
    @classmethod
    def _parse_json_question(cls, question_data: Dict, idx: int) -> Dict[str, Any]:
        required_fields = ['question', 'options', 'correct_answer']
        
        # Validate fields
        for field in required_fields:
            if field not in question_data:
                raise ValidationError(f"Missing required field '{field}'")
        
        # Validate question text
        if not isinstance(question_data['question'], str) or not question_data['question'].strip():
            raise ValidationError("'question' must be a non-empty string")
        
        # Validate options array
        options = question_data['options']
        if not isinstance(options, list) or len(options) < 2:
            raise ValidationError("'options' must be an array with at least 2 items")
        
        if len(options) > 6:
            raise ValidationError("'options' cannot have more than 6 items")
        
        # Validate correct answer index
        correct_answer = question_data['correct_answer']
        if not isinstance(correct_answer, int):
            raise ValidationError("'correct_answer' must be an integer (0-based index)")
        
        if correct_answer < 0 or correct_answer >= len(options):
            raise ValidationError(f"'correct_answer' index {correct_answer} is out of range")
        
        return {
            'question_text': question_data['question'].strip(),
            'answer_options': [str(option).strip() for option in options],
            'answer_index': correct_answer,
            'section': question_data.get('section', '').strip() or 'General',
            'explanation': question_data.get('explanation', '').strip()
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
    filename = file.name.lower()
    
    if filename.endswith('.csv'):
        return CSVProcessor.process_file(file)
    elif filename.endswith('.json'):
        return JSONProcessor.process_file(file)
    else:
        raise ValidationError("Unsupported file type. Please upload CSV or JSON files only.")