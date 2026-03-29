"""
This file is the bridge between the web server and the django application.

"""


import os
from django.core.wsgi import get_wsgi_application

#Tells django where settings.py is located and sets that as its settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'silver_mining.settings')

#Creates WSGI application that web server talks to
application = get_wsgi_application() 