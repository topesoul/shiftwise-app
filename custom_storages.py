# /workspace/shiftwise/custom_storages.py

from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class StaticStorage(S3Boto3Storage):
    location = settings.STATICFILES_LOCATION
    default_acl = None  # Disable ACLs
    file_overwrite = True  # Allow overwriting of static files

class MediaStorage(S3Boto3Storage):
    location = settings.MEDIAFILES_LOCATION
    default_acl = None  # Disable ACLs
    file_overwrite = False  # Prevent overwriting of media files