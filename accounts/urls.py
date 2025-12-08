from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # User profile
    path('profile/', views.profile_view, name='profile'),

    # PASSWORD RESET WORKFLOW
    # Step 1: User enters email
    path('password-reset/', 
         views.CustomPasswordResetView.as_view(), 
         name='password_reset'),

    # Step 2: Email sent confirmation
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),

    # Step 3: User opens link from email
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        views.CustomPasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),

    # Step 4: Password reset complete
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
    path('provider/dashboard/', views.provider_dashboard_view, name='provider_dashboard'),
    path('homeowner/dashboard/', views.homeowner_dashboard, name='homeowner_dashboard'),
    path('provider/showcase/', views.provider_showcase_view, name='provider_showcase'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/delete/', views.delete_profile, name='delete_profile'),
    path("delete/", views.delete_account, name="delete_account"),

]
