"""
Authentication URL Configuration for CollabSpace AI.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    # Part 1 - Basic Auth
    RegisterView,
    CustomTokenObtainPairView,
    LogoutView,
    ProfileView,
    ChangePasswordView,
    VerifyEmailView,
    ResendVerificationEmailView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    DeleteAccountView,
    # Part 2 - Advanced Features
    Enable2FAView,
    Verify2FASetupView,
    Disable2FAView,
    ListSessionsView,
    RevokeSessionView,
    RevokeAllSessionsView,
    SearchUsersView,
    UserDetailView,
    UpdateActivityView,
    AccountStatsView,
    CheckAuthView,
)

app_name = 'authentication'

urlpatterns = [
    # Registration & Login
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # User Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Email Verification
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend-verification'),
    
    # Password Reset
    path('reset-password/', PasswordResetRequestView.as_view(), name='reset-password'),
    path('reset-password-confirm/', PasswordResetConfirmView.as_view(), name='reset-password-confirm'),
    
    # Two-Factor Authentication
    path('2fa/enable/', Enable2FAView.as_view(), name='2fa-enable'),
    path('2fa/verify-setup/', Verify2FASetupView.as_view(), name='2fa-verify-setup'),
    path('2fa/disable/', Disable2FAView.as_view(), name='2fa-disable'),
    
    # Session Management
    path('sessions/', ListSessionsView.as_view(), name='list-sessions'),
    path('sessions/<int:session_id>/', RevokeSessionView.as_view(), name='revoke-session'),
    path('sessions/revoke-all/', RevokeAllSessionsView.as_view(), name='revoke-all-sessions'),
    
    # User Search & Discovery
    path('users/search/', SearchUsersView.as_view(), name='search-users'),
    path('users/<uuid:user_id>/', UserDetailView.as_view(), name='user-detail'),
    
    # User Activity
    path('activity/update/', UpdateActivityView.as_view(), name='update-activity'),
    
    # Account Statistics
    path('stats/', AccountStatsView.as_view(), name='account-stats'),
    
    # Account Management
    path('account/', DeleteAccountView.as_view(), name='delete-account'),
    
    # Debug/Check Endpoint
    path('check/', CheckAuthView.as_view(), name='check-auth'),
]