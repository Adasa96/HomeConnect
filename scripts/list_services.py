import os
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HomeConnect.settings')
import django
django.setup()

from accounts.models import Service

print('Services in DB:')
for s in Service.objects.all():
    print('-', s.name)
