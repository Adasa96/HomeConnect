from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from cloudinary.models import CloudinaryField


# -------------------------------------------------------
# CUSTOM USER MODEL
# -------------------------------------------------------
class User(AbstractUser):
    USER_TYPES = (
        ('homeowner', 'Homeowner'),
        ('service_provider', 'Service Provider'),
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='homeowner')
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)

    services = models.ManyToManyField('services.Service', blank=True, related_name='users')
    def __str__(self):
        return self.username


# -------------------------------------------------------
# NORMAL PROFILE (For ALL USERS)
# -------------------------------------------------------
class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(
        upload_to="profile_images/",
        blank=True,
        null=True
    )

    location = models.CharField(max_length=150, blank=True)
    city = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"


# -------------------------------------------------------
# SERVICE MODEL
# -------------------------------------------------------
class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# -------------------------------------------------------
# SERVICE PROVIDER MODEL
# -------------------------------------------------------
class ServiceProvider(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provider_profile"
    )

    company_name = models.CharField(max_length=150, blank=True)
    skills = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)

    portfolio_image = models.ImageField(
        upload_to="provider_portfolio/",
        blank=True,
        null=True
    )

    services = models.ManyToManyField(
        Service,
        blank=True,
        related_name='providers'
    )

    def __str__(self):
        return self.company_name or self.user.username


# -------------------------------------------------------
# AUTO-CREATE PROFILES (NORMAL + PROVIDER)
# -------------------------------------------------------
@receiver(post_save, sender=User)
def create_user_related_profiles(sender, instance, created, **kwargs):
    """
    Create:
    - Normal Profile for all users
    - ServiceProvider profile ONLY for service providers
    """
    if created:
        Profile.objects.create(user=instance)

        if instance.user_type == 'service_provider':
            ServiceProvider.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_related_profiles(sender, instance, **kwargs):
    """
    Save linked profiles whenever User is saved.
    """
    instance.profile.save()

    if instance.user_type == 'service_provider':
        instance.provider_profile.save()
