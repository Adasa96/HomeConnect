from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Service, ServiceProvider, Profile


# Inline admin for Profile to display/edit inside UserAdmin
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = ('profile_image', 'bio', 'location', 'city')
    readonly_fields = ('profile_image_preview',)

    def profile_image_preview(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" width="60" height="60" />', obj.profile_image.url)
        return "-"
    profile_image_preview.short_description = "Profile Image Preview"


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]

    list_display = ('username', 'email', 'user_type', 'city', 'is_staff', 'date_joined', 'display_services')
    list_filter = ('user_type', 'city', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'profile__bio')

    fieldsets = (
        ('Login Credentials', {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('User Type & Services', {'fields': ('user_type', 'services')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        ('Create User', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'user_type', 'phone', 'password1', 'password2', 'services')
        }),
    )

    filter_horizontal = ('services', 'groups', 'user_permissions')

    def display_services(self, obj):
        services = obj.services.all()
        return ", ".join([s.name for s in services]) if services else "-"
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
    list_display = ('user', 'profile_image_tag', 'location')
    search_fields = ('user__username', 'user__email','location')
    list_filter = ('location',)

    readonly_fields = ('profile_image_tag',)

    def profile_image_tag(self, obj):
        if obj.profile_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius:6px;" />',
                obj.profile_image.url
            )
        return "-"
    profile_image_tag.short_description = 'Profile Image'
