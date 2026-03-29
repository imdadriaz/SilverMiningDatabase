"""
This file is the command line tool that allows interaction with the project. Every django command goes through this file.

"""

import os
import sys

def main():
    #Tells django where settings.py is located and sets that as its settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'silver_mining.settings')
    #Attempt to import django
    try:
        from django.core.management import execute_from_command_line
    #If django not found catch error as exc and give an error message
    except ImportError as exc:
        raise ImportError("Couldnt import Django, make sure it isi installed and availabled") from exc
    #If django found succesfully run command
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()