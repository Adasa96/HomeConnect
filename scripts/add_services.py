import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so Django settings can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HomeConnect.settings')
import django
django.setup()

from accounts.models import Service


def add_services(names):
	created = []
	exists = []
	for name in names:
		svc, was_created = Service.objects.get_or_create(
			name=name,
			defaults={'description': f'{name} services'}
		)
		if was_created:
			created.append(svc)
		else:
			exists.append(svc)
	return created, exists


def main():
	names = ['Cleaning', 'Babysitting']
	created, exists = add_services(names)

	for s in created:
		print(f"Created: {s.name} (id={s.id})")
	for s in exists:
		print(f"Exists: {s.name} (id={s.id})")

	print('\nAll services in DB:')
	for s in Service.objects.order_by('name'):
		print('-', s.name)


if __name__ == '__main__':
	main()

