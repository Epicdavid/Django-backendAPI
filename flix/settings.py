from corsheaders.defaults import default_headers
from decouple import config

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_HOSTS = []

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'mu%1hlw9$6+5!v5cw5skvx=&=z+za^gqizc2ykm_t_#$@6(22q'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'flix.backends.CustomerBackend',
]


# Application definition

INSTALLED_APPS = [
    "bootstrap_admin",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'simple_history',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'corsheaders',
    'rest_auth',
    'rest_auth.registration',
    'rest_framework',
    'rest_framework.authtoken',
    'flix',
    "pinax.referrals",
    "mptt",
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'pinax.referrals.middleware.SessionJumpingMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'flix.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'buildx'),
             os.path.join(BASE_DIR, 'build'),
            os.path.join(BASE_DIR, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'flix.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases


PINAX_REFERRALS_IP_ADDRESS_META_FIELD = True


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators




# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'



ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_REQUIRED = True
AUTH_USER_MODEL = 'flix.User'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_UNIQUE_USERNAME = False
ACCOUNT_USERNAME_VALIDATORS = 'home.settings.validator.custom_usename_validator'

REST_AUTH_SERIALIZERS = {
    'USER_DETAILS_SERIALIZER':'flix.serializers.UserSerializer',
    'TOKEN_SERIALIZER':'flix.serializers.TokenSerializer',
    'LOGIN_SERIALIZER': 'flix.serializers.Login'
    
}

REST_AUTH_REGISTER_SERIALIZERS = {
    'REGISTER_SERIALIZER':'flix.serializers.SignupSerializer'
}
CORS_ALLOW_HEADERS = list(default_headers) + [
    'X-CSRFTOKEN',
]

OLD_PASSWORD_FIELD_ENABLED = True
SIMPLE_HISTORY_HISTORY_CHANGE_REASON_USE_TEXT_FIELD=True