import os
import sys
import sqlite3
from pathlib import Path

# ensure project root is on sys.path so `HomeConnect` package can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HomeConnect.settings')
import django
django.setup()

from accounts.models import Service, User

print('TABLES:')
conn = sqlite3.connect('db.sqlite3')
for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(' -', row[0])

print('\nMODEL TABLES:')
print(' - Service ->', Service._meta.db_table)
print(' - User ->', User._meta.db_table)
field = User._meta.get_field('services')
print(' - User.services through ->', field.remote_field.through._meta.db_table)
