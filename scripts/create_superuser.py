import os
import sys
from pathlib import Path
# ensure project root on path so HomeConnect.settings can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HomeConnect.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'changeme')
    print('Superuser created: username=admin password=changeme')
else:
    print('Superuser admin already exists')
