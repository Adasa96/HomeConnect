from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# ---------------------------------------------------------
# SERVICE MODEL
# ---------------------------------------------------------
class Service(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# ---------------------------------------------------------
# CUSTOM USER MODEL
# ---------------------------------------------------------
class User(AbstractUser):
    USER_TYPES = [
        ('homeowner', 'Homeowner'),
        ('service_provider', 'Service Provider'),
    ]

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default='homeowner'
    )

    bio = models.TextField(blank=True, null=True)

    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True
    )

    phone = models.CharField(max_length=30, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)

    # Homeowners = services they want
    # Service providers = services they offer
    services = models.ManyToManyField(
        Service,
        related_name='users',
        blank=True
    )

    def __str__(self):
        return self.username


# ---------------------------------------------------------
# EXTENDED SERVICE PROVIDER PROFILE
# ---------------------------------------------------------
class ServiceProvider(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provider_profile"
    )

    company_name = models.CharField(max_length=150, blank=True)

    skills = models.TextField(
        blank=True,
        help_text="Describe your skills, experience, or services you provide."
    )

    experience_years = models.PositiveIntegerField(default=0)

    portfolio_image = models.ImageField(
        upload_to="provider_portfolio/",
        blank=True,
        null=True
    )

    # Services the provider specializes in
    services = models.ManyToManyField(
        Service,
        blank=True,
        related_name='providers'
    )

    def __str__(self):
        return self.company_name or self.user.username
