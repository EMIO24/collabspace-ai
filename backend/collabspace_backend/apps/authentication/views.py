"""
Authentication views for CollabSpace AI.

API endpoints for user authentication and profile management.
"""

from rest_framework import status, generics, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from django.utils import timezone
from datetime import timedelta
import secrets

from .models import User, PasswordResetToken, UserSession
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    CustomTokenObtainPairSerializer, ChangePasswordSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    EmailVerificationSerializer, UserUpdateSerializer,
    Enable2FASerializer, Verify2FASerializer, PublicUserSerializer
)
from .utils import (
    send_verification_email, send_password_reset_email,
    generate_2fa_secret, generate_2fa_qr_code, verify_2fa_code
)


# ==============================================================================
# REGISTRATION & LOGIN
# ==============================================================================

class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    
    POST /api/auth/register/
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate email verification token
        verification_token = secrets.token_urlsafe(32)
        user.email_verification_token = verification_token
        user.email_verification_sent_at = timezone.now()
        user.save()
        
        # Send verification email
        send_verification_email(user, verification_token)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Registration successful. Please check your email to verify your account.',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view with user data.
    
    POST /api/auth/login/
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Update last login
            user = User.objects.get(email=request.data.get('email').lower())
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
        
        return response


class LogoutView(views.APIView):
    """
    Logout endpoint - blacklists the refresh token.
    
    POST /api/auth/logout/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            logout(request)
            
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ==============================================================================
# USER PROFILE
# ==============================================================================

class ProfileView(views.APIView):
    """
    Get and update user profile.
    
    GET /api/auth/profile/
    PUT /api/auth/profile/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user profile."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update current user profile."""
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Profile updated successfully',
            'user': UserSerializer(request.user).data
        })


class ChangePasswordView(views.APIView):
    """
    Change user password.
    
    POST /api/auth/change-password/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


# ==============================================================================
# EMAIL VERIFICATION
# ==============================================================================

class VerifyEmailView(views.APIView):
    """
    Verify user email with token.
    
    POST /api/auth/verify-email/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        
        try:
            user = User.objects.get(email_verification_token=token)
            
            # Check if token is expired (24 hours)
            if user.email_verification_sent_at:
                expiry_time = user.email_verification_sent_at + timedelta(hours=24)
                if timezone.now() > expiry_time:
                    return Response(
                        {'error': 'Verification token has expired'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Verify email
            user.is_email_verified = True
            user.email_verification_token = None
            user.email_verification_sent_at = None
            user.save()
            
            return Response({
                'message': 'Email verified successfully'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid verification token'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ResendVerificationEmailView(views.APIView):
    """
    Resend email verification link.
    
    POST /api/auth/resend-verification/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        if user.is_email_verified:
            return Response(
                {'error': 'Email is already verified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate new token
        verification_token = secrets.token_urlsafe(32)
        user.email_verification_token = verification_token
        user.email_verification_sent_at = timezone.now()
        user.save()
        
        # Send verification email
        send_verification_email(user, verification_token)
        
        return Response({
            'message': 'Verification email sent successfully'
        }, status=status.HTTP_200_OK)


# ==============================================================================
# PASSWORD RESET
# ==============================================================================

class PasswordResetRequestView(views.APIView):
    """
    Request password reset email.
    
    POST /api/auth/reset-password/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(hours=1)
            
            PasswordResetToken.objects.create(
                user=user,
                token=reset_token,
                expires_at=expires_at
            )
            
            # Send password reset email
            send_password_reset_email(user, reset_token)
            
        except User.DoesNotExist:
            # Don't reveal if email exists (security)
            pass
        
        # Always return success to prevent email enumeration
        return Response({
            'message': 'If an account exists with that email, a password reset link has been sent.'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(views.APIView):
    """
    Confirm password reset with token.
    
    POST /api/auth/reset-password-confirm/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            
            if not reset_token.is_valid():
                return Response(
                    {'error': 'Invalid or expired reset token'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Reset password
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            
            # Mark token as used
            reset_token.mark_as_used()
            
            return Response({
                'message': 'Password reset successfully'
            }, status=status.HTTP_200_OK)
            
        except PasswordResetToken.DoesNotExist:
            return Response(
                {'error': 'Invalid reset token'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ==============================================================================
# ACCOUNT MANAGEMENT
# ==============================================================================

class DeleteAccountView(views.APIView):
    """
    Delete user account (soft delete).
    
    DELETE /api/auth/account/
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        user = request.user
        
        # Soft delete user
        user.is_active = False
        user.save()
        
        # Logout user
        logout(request)
        
        return Response({
            'message': 'Account deleted successfully'
        }, status=status.HTTP_200_OK)


# ==============================================================================
# TWO-FACTOR AUTHENTICATION
# ==============================================================================

class Enable2FAView(views.APIView):
    """
    Enable two-factor authentication for user.
    
    POST /api/auth/2fa/enable/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = Enable2FASerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Check if 2FA is already enabled
        if user.two_factor_enabled:
            return Response(
                {'error': 'Two-factor authentication is already enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate 2FA secret
        secret = generate_2fa_secret()
        user.two_factor_secret = secret
        user.save(update_fields=['two_factor_secret'])
        
        # Generate QR code
        qr_code = generate_2fa_qr_code(user, secret)
        
        return Response({
            'message': 'Scan the QR code with your authenticator app',
            'secret': secret,
            'qr_code': qr_code,
            'instructions': 'After scanning, verify with a 6-digit code from your app'
        }, status=status.HTTP_200_OK)


class Verify2FASetupView(views.APIView):
    """
    Verify 2FA setup with a code from authenticator app.
    
    POST /api/auth/2fa/verify-setup/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = Verify2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        code = serializer.validated_data['code']
        
        if not user.two_factor_secret:
            return Response(
                {'error': 'Two-factor authentication is not set up. Enable it first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify the code
        if verify_2fa_code(user.two_factor_secret, code):
            user.two_factor_enabled = True
            user.save(update_fields=['two_factor_enabled'])
            
            return Response({
                'message': 'Two-factor authentication enabled successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Invalid verification code'},
                status=status.HTTP_400_BAD_REQUEST
            )


class Disable2FAView(views.APIView):
    """
    Disable two-factor authentication.
    
    POST /api/auth/2fa/disable/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = Verify2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        code = serializer.validated_data['code']
        
        if not user.two_factor_enabled:
            return Response(
                {'error': 'Two-factor authentication is not enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify the code before disabling
        if verify_2fa_code(user.two_factor_secret, code):
            user.two_factor_enabled = False
            user.two_factor_secret = None
            user.save(update_fields=['two_factor_enabled', 'two_factor_secret'])
            
            return Response({
                'message': 'Two-factor authentication disabled successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Invalid verification code'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ==============================================================================
# SESSION MANAGEMENT
# ==============================================================================

class ListSessionsView(views.APIView):
    """
    List all active sessions for the user.
    
    GET /api/auth/sessions/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        sessions = UserSession.objects.filter(
            user=request.user,
            is_active=True,
            expires_at__gt=timezone.now()
        ).order_by('-last_activity')
        
        session_data = []
        for session in sessions:
            session_data.append({
                'id': session.id,
                'ip_address': session.ip_address,
                'user_agent': session.user_agent,
                'device_info': session.device_info,
                'created_at': session.created_at,
                'last_activity': session.last_activity,
                'expires_at': session.expires_at
            })
        
        return Response({
            'count': len(session_data),
            'sessions': session_data
        })


class RevokeSessionView(views.APIView):
    """
    Revoke a specific session.
    
    DELETE /api/auth/sessions/{session_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, session_id):
        try:
            session = UserSession.objects.get(
                id=session_id,
                user=request.user
            )
            session.deactivate()
            
            return Response({
                'message': 'Session revoked successfully'
            }, status=status.HTTP_200_OK)
            
        except UserSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class RevokeAllSessionsView(views.APIView):
    """
    Revoke all sessions except the current one.
    
    POST /api/auth/sessions/revoke-all/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Get current session key from request
        current_session_key = request.session.session_key
        
        # Deactivate all other sessions
        sessions = UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).exclude(session_key=current_session_key)
        
        count = sessions.count()
        sessions.update(is_active=False)
        
        return Response({
            'message': f'Successfully revoked {count} session(s)'
        }, status=status.HTTP_200_OK)


# ==============================================================================
# USER SEARCH & DISCOVERY
# ==============================================================================

class SearchUsersView(views.APIView):
    """
    Search for users by username or email.
    
    GET /api/auth/users/search/?q=john
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        if len(query) < 2:
            return Response(
                {'error': 'Search query must be at least 2 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Search users (limit to 20 results)
        users = User.objects.filter(
            is_active=True
        ).filter(
            username__icontains=query
        ) | User.objects.filter(
            email__icontains=query
        )
        
        users = users.exclude(id=request.user.id)[:20]
        
        serializer = PublicUserSerializer(users, many=True)
        
        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        })


class UserDetailView(views.APIView):
    """
    Get public information about a specific user.
    
    GET /api/auth/users/{user_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, is_active=True)
            serializer = PublicUserSerializer(user)
            
            return Response(serializer.data)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# ==============================================================================
# USER ACTIVITY
# ==============================================================================

class UpdateActivityView(views.APIView):
    """
    Update user's last activity timestamp.
    
    POST /api/auth/activity/update/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        request.user.update_last_activity()
        
        return Response({
            'message': 'Activity updated',
            'last_activity': request.user.last_activity
        })


# ==============================================================================
# ACCOUNT STATISTICS
# ==============================================================================

class AccountStatsView(views.APIView):
    """
    Get user account statistics.
    
    GET /api/auth/stats/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Calculate days since joining
        days_since_joining = (timezone.now() - user.date_joined).days
        
        # Get active sessions count
        active_sessions = UserSession.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now()
        ).count()
        
        stats = {
            'user_id': str(user.id),
            'account_age_days': days_since_joining,
            'email_verified': user.is_email_verified,
            'two_factor_enabled': user.two_factor_enabled,
            'plan_type': user.plan_type,
            'active_sessions': active_sessions,
            'last_login': user.last_login,
            'last_activity': user.last_activity,
            'date_joined': user.date_joined,
        }
        
        return Response(stats)


# ==============================================================================
# DEVELOPER / DEBUG ENDPOINTS (Remove in production)
# ==============================================================================

class CheckAuthView(views.APIView):
    """
    Check if user is authenticated and return user info.
    Useful for debugging authentication issues.
    
    GET /api/auth/check/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'authenticated': True,
            'user': UserSerializer(request.user).data,
            'auth_header': request.META.get('HTTP_AUTHORIZATION', 'Not provided')
        })