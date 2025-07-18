﻿from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class MediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_S3_BUCKET_NAME
    location = 'media'
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False
