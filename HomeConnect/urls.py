"""



















































URL configuration for HomeConnect project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Redirect root URL to admin for now
    path('accounts/', include('accounts.urls')),
    path('services/', include('services.urls')),
    path('mpesa/', include('connectmpesa.urls')),
    path('booking/', include('booking.urls')),
        # Redirect root URL to services dashboard for now
    path('', RedirectView.as_view(pattern_name='services:dashboard', permanent=False)),
    # 'services' app URL include removed because the app isn't present in the project.
    # Add it back when you create a `services` app with a `urls.py` module.

]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
