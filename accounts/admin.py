from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Service, ServiceProvider,Profile

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'city', 'is_staff', 'date_joined', 'display_services')
    list_filter = ('user_type', 'city', 'is_staff', 'is_superuser', 'is_active')

    fieldsets = (
        ('Login Credentials', {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'email', 'phone',
                'profile_image', 'bio', 'location', 'city'
            )
        }),
        ('User Type & Services', {
            'fields': ('user_type', 'services')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        ('Create User', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'user_type', 'phone', 'password1', 'password2', 'services')
        }),
    )

    filter_horizontal = ('services', 'groups', 'user_permissions')

    def display_services(self, obj):
        return ", ".join([s.name for s in obj.services.all()])
    display_services.short_description = "Services"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'experience_years')
    search_fields = ('company_name', 'user__username')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'logo_tag']

    def logo_tag(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "-"
    logo_tag.short_description = 'Logo'
