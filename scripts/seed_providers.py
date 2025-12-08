import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HomeConnect.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Service
from services.models import ServiceProvider, ServiceRequest

User = get_user_model()

# Create sample services
svc_names = ['Plumbing', 'Electrical', 'Landscaping','Cleaning','Painting','Babysitting']
services = []
for name in svc_names:
    s, _ = Service.objects.get_or_create(name=name, defaults={'description': f'{name} services'})
    services.append(s)

# Create a service provider user
prov_username = 'svc_provider'
if not User.objects.filter(username=prov_username).exists():
    provider_user = User.objects.create_user(prov_username, email='provider@example.com', password='providerpass')
    provider_user.user_type = 'service_provider'
    provider_user.save()
else:
    provider_user = User.objects.get(username=prov_username)

# Create provider profile
provider_profile, created = ServiceProvider.objects.get_or_create(user=provider_user, defaults={'company_name': 'Account Services', 'phone': '0799053832', 'bio': 'We provide excellent services.'})
if created:
    provider_profile.services.set(services)
else:
    # ensure services attached
    for s in services:
        provider_profile.services.add(s)

# Create a homeowner user
home_username = 'home_user'
if not User.objects.filter(username=home_username).exists():
    home_user = User.objects.create_user(home_username, email='home@example.com', password='homepass')
    home_user.user_type = 'homeowner'
    home_user.save()
else:
    home_user = User.objects.get(username=home_username)

# Create a sample service request
sr, created = ServiceRequest.objects.get_or_create(homeowner=home_user, provider=provider_profile, service=services[0], defaults={'details': 'Leaky faucet needs repair.'})

print('Seed complete:')
print(' Services:', [s.name for s in services])
print(' Provider:', provider_user.username, 'profile id', provider_profile.id)
print(' Homeowner:', home_user.username)
print(' Sample request id:', sr.id)
