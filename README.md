# Silver Mining Database

The Silver Mining Database is a website that ranks companies based on mining and financial indicators. This repository stores the SQL schema and starter data for the project.

## Requirements
- MySQL 8.0 or compatible
- MySQL Workbench or MySQL CLI

## Installation

Clone the repository and install dependencies:
```bash
git clone https://github.com/imdadriaz/SilverMiningDatabase.git
cd SilverMiningDatabase
pip install -r requirements.txt
```

## Setup

In `silver_mining/settings.py`, set the default database password to your own MySQL password on line 77:
```bash
'PASSWORD': 'Local1234', #Set to your own password
```

Run the SQL script using one of the following methods.

1. **Run in MySQL Workbench:** Open `db/SilverMiningDatabase.sql` and run the script.

2. **Run in terminal:**
```bash
mysql -u root -p < db/SilverMiningDatabase.sql
```

This creates the database and inserts starter data. Next, make migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Run

Use the command:
```bash
python manage.py runserver
```
To open the website, follow the link:
http://127.0.0.1:8000/

To sign in with a starter account, use one of the following:
1. maad@email.com, password1
2. slee@email.com, password2
3. jsmith@emaul.com, password3
