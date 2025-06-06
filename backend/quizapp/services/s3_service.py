import boto3
import logging
import uuid
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            self.bucket_name = settings.AWS_S3_BUCKET_NAME
            self._verify_bucket_access()
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise Exception("AWS credentials not configured")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def _verify_bucket_access(self):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Successfully connected to S3 bucket: {self.bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise Exception(f"S3 bucket '{self.bucket_name}' not found")
            elif error_code == '403':
                raise Exception(f"Access denied to S3 bucket '{self.bucket_name}'")
            else:
                raise Exception(f"Error accessing S3 bucket: {e}")
    
    def upload_quiz_file(self, file, user_id: int, original_filename: str) -> Dict[str, Any]:
        try:
            # Generate unique filename to prevent conflicts
            file_extension = original_filename.split('.')[-1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            
            # Create organized S3 key structure
            timestamp = datetime.now().strftime('%Y/%m/%d')
            s3_key = f"quiz-files/{user_id}/{timestamp}/{unique_filename}"
            
            # Metadata for the file
            metadata = {
                'original-filename': original_filename,
                'user-id': str(user_id),
                'upload-timestamp': datetime.now().isoformat(),
                'file-type': file_extension
            }
            
            # Upload file to S3
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'Metadata': metadata,
                    'ContentType': file.content_type or 'application/octet-stream',
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            logger.info(f"Successfully uploaded file to S3: {s3_key}")
            
            return {
                's3_key': s3_key,
                's3_url': f"https://{self.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}",
                'original_filename': original_filename,
                'file_size': file.size,
                'content_type': file.content_type
            }
            
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise Exception(f"S3 upload failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {e}")
            raise
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            logger.info(f"Generated presigned URL for {s3_key}")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise Exception(f"Failed to generate download URL: {e}")
    
    def delete_file(self, s3_key: str) -> bool:
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Successfully deleted file from S3: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False

def test_connection(self):
    """
    Test S3 connection for health checks
    Returns True if connection is healthy, False otherwise
    """
    try:
        from django.conf import settings
        
        # Test basic bucket access
        response = self.s3_client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        
        return True
        
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"S3 health check failed: {str(e)}")
        return False

_s3_service = None

def get_s3_service() -> S3Service:
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service