"""
This file is the main configuration file for django for this project. Tells django things like which database to use, what apps are installed etc.

"""




from pathlib import Path

#Finds root folder of project
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-change-this-in-production'

#Set to False once complete
DEBUG = True

#Which web addresses are allowed to access the site
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

#Every app django needs to know about
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'mining',
]

MIDDLEWARE = [
    #Basic security protections on every request
    'django.middleware.security.SecurityMiddleware',
    #Checks if user is logged in
    'django.contrib.sessions.middleware.SessionMiddleware',
    #Cleans up URLs
    'django.middleware.common.CommonMiddleware',
    #Protects POST rquests from being faked by other websites
    'django.middleware.csrf.CsrfViewMiddleware',
    #Enables flash messages
    'django.contrib.messages.middleware.MessageMiddleware',
    #Security layer prevents site from being embedded inside another site
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


#Tells django where to find main url
ROOT_URLCONF = 'silver_mining.urls'


#How django handles HTML templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

#How django connects to web server
WSGI_APPLICATION = 'silver_mining.wsgi.application'


#My SQL connection details
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'SilverMiningDatabase',
        'USER': 'root',
        'PASSWORD': 'Local1234',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'unix_socket': '/tmp/mysql.sock',
        },
    }
}

#Stores login sessions in the database
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

#Stores flash messages in the session (i.e "login successful")
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Denver'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'