"""
Docker-specific DMOJ configuration - extends base DMOJ settings
"""

import os
from dmoj.settings import *

# Force PyMySQL as MySQLdb replacement (must be before any DB access)
import pymysql
pymysql.install_as_MySQLdb()

# Patch PyMySQL for compatibility with Django
from pymysql.constants import ER
if not hasattr(ER, 'CONSTRAINT_FAILED'):
    ER.CONSTRAINT_FAILED = 2067

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE', 'dmoj'),
        'USER': os.getenv('MYSQL_USER', 'dmoj'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD', 'dmoj_password'),
        'HOST': os.getenv('MYSQL_HOST', 'db'),
        'PORT': os.getenv('MYSQL_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
            'use_unicode': True,
        },
    }
}

# Redis / Cache
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/1',
    }
}

# Celery
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'

# Static / Media
STATIC_ROOT = '/site/static/'
MEDIA_ROOT = '/site/media/'

# Session
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Site
SECRET_KEY = os.getenv('SECRET_KEY', 'change_this_secret_key_in_production')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
SITE_URL = os.getenv('SITE_URL', 'http://localhost:8080')
SITE_NAME = 'DMOJ'
SITE_LONG_NAME = 'Don Mills Online Judge'
SITE_ID = 1

# Time zone
TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')

# Debug
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Compression
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = False

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

# Bridge (judge communication) -- bridged runs as separate container
BRIDGED_JUDGE_ADDRESS = [('bridged', 9999)]
BRIDGED_DJANGO_ADDRESS = [('bridged', 9998)]
BRIDGED_DJANGO_CONNECT = None
BRIDGED_JUDGE_KEY = os.getenv('BRIDGE_API_KEY', 'change_this_bridge_api_key')

# Problem data
DMOJ_PROBLEM_DATA_ROOT = '/site/problems/'

# URLs
ROOT_URLCONF = 'dmoj_urls'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/site/log/dmoj.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'dmoj': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Silence MariaDB-specific warnings about conditional unique constraints
SILENCED_SYSTEM_CHECKS = ['models.W036']

# --- Custom extensions --------------------------------------------------------

INSTALLED_APPS = list(INSTALLED_APPS) + [
    'rest_framework',
    'custom_commands',
]

# Admin API key for bulk-load endpoints (Authorization: Bearer <key>)
ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', '')

# Django REST Framework -- only allow explicit authentication, no browsable API
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}
