from django.contrib import admin
from .models import ServiceProvider, ServiceRequest


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'homeowner', 'provider', 'service', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('homeowner__username', 'provider__company_name', 'service__name')
