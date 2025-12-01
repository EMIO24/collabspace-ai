"""
Authentication views for CollabSpace AI.

API endpoints for user authentication and profile management.
"""

from rest_framework import status, generics, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import logout
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from datetime import timedelta
import secrets

from .models import User, PasswordResetToken, UserSession
from .serializers import (
    UserSerializer, RegisterSerializer, 
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
        
        # Atomic transaction: If email sending fails, user creation is rolled back
        try:
            with transaction.atomic():
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
                
        except Exception as e:
            return Response(
                {'error': 'Registration failed. Please try again later.', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view with user data.
    POST /api/auth/login/
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # 1. Standard authentication
        response = super().post(request, *args, **kwargs)
        
        # 2. If successful, update last_login safely
        if response.status_code == 200:
            try:
                # Handle login via Email OR Username safely
                login_identifier = request.data.get('email') or request.data.get('username')
                
                if login_identifier:
                    User.objects.filter(
                        Q(email__iexact=login_identifier) | Q(username__iexact=login_identifier)
                    ).update(last_login=timezone.now())
                    
            except Exception:
                # Do not crash the login response if stats update fails
                pass
        
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
                return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            logout(request)
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
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
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)


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
                    return Response({'error': 'Verification token has expired'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify email
            user.is_email_verified = True
            user.email_verification_token = None
            user.email_verification_sent_at = None
            user.save()
            
            return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({'error': 'Invalid verification token'}, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailView(views.APIView):
    """
    Resend email verification link.
    POST /api/auth/resend-verification/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        if user.is_email_verified:
            return Response({'error': 'Email is already verified'}, status=status.HTTP_400_BAD_REQUEST)
        
        verification_token = secrets.token_urlsafe(32)
        user.email_verification_token = verification_token
        user.email_verification_sent_at = timezone.now()
        user.save()
        
        send_verification_email(user, verification_token)
        return Response({'message': 'Verification email sent successfully'}, status=status.HTTP_200_OK)


# ==============================================================================
# PASSWORD RESET
# ==============================================================================

class PasswordResetRequestView(views.APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        print(f"🔍 DEBUG: Searching for user with email: '{email}'") # DEBUG PRINT
        
        try:
            # Try to get the user
            user = User.objects.get(email__iexact=email)
            print(f"✅ DEBUG: User found: {user.username} (ID: {user.id})") # DEBUG PRINT
            
            reset_token = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(hours=1)
            
            PasswordResetToken.objects.create(
                user=user,
                token=reset_token,
                expires_at=expires_at
            )
            
            print("📨 DEBUG: Attempting to send email now...") # DEBUG PRINT
            send_password_reset_email(user, reset_token)
            print("🚀 DEBUG: Email function called.") # DEBUG PRINT
            
        except User.DoesNotExist:
            print("❌ DEBUG: User.DoesNotExist triggered! No user found with that email.") # DEBUG PRINT
            # Gracefully handle non-existent users
            pass
        except Exception as e:
            print(f"💥 DEBUG: Other error occurred: {e}") # DEBUG PRINT
        
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
                return Response({'error': 'Invalid or expired reset token'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            
            reset_token.mark_as_used()
            
            return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
            
        except PasswordResetToken.DoesNotExist:
            return Response({'error': 'Invalid reset token'}, status=status.HTTP_400_BAD_REQUEST)


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
        user.is_active = False
        user.save()
        logout(request)
        return Response({'message': 'Account deleted successfully'}, status=status.HTTP_200_OK)


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
        if user.two_factor_enabled:
            return Response({'error': 'Two-factor authentication is already enabled'}, status=status.HTTP_400_BAD_REQUEST)
        
        secret = generate_2fa_secret()
        user.two_factor_secret = secret
        user.save(update_fields=['two_factor_secret'])
        
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
            return Response({'error': 'Two-factor authentication is not set up. Enable it first.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if verify_2fa_code(user.two_factor_secret, code):
            user.two_factor_enabled = True
            user.save(update_fields=['two_factor_enabled'])
            return Response({'message': 'Two-factor authentication enabled successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid verification code'}, status=status.HTTP_400_BAD_REQUEST)


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
            return Response({'error': 'Two-factor authentication is not enabled'}, status=status.HTTP_400_BAD_REQUEST)
        
        if verify_2fa_code(user.two_factor_secret, code):
            user.two_factor_enabled = False
            user.two_factor_secret = None
            user.save(update_fields=['two_factor_enabled', 'two_factor_secret'])
            return Response({'message': 'Two-factor authentication disabled successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid verification code'}, status=status.HTTP_400_BAD_REQUEST)


# ==============================================================================
# SESSION MANAGEMENT (Simplified for clarity)
# ==============================================================================

class ListSessionsView(views.APIView):
    """GET /api/auth/sessions/"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        sessions = UserSession.objects.filter(
            user=request.user, is_active=True, expires_at__gt=timezone.now()
        ).order_by('-last_activity')
        
        session_data = [{
            'id': s.id, 'ip_address': s.ip_address, 'user_agent': s.user_agent,
            'device_info': s.device_info, 'created_at': s.created_at,
            'last_activity': s.last_activity, 'expires_at': s.expires_at
        } for s in sessions]
        
        return Response({'count': len(session_data), 'sessions': session_data})

class RevokeSessionView(views.APIView):
    """DELETE /api/auth/sessions/{session_id}/"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, session_id):
        try:
            session = UserSession.objects.get(id=session_id, user=request.user)
            session.deactivate()
            return Response({'message': 'Session revoked successfully'}, status=status.HTTP_200_OK)
        except UserSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

class RevokeAllSessionsView(views.APIView):
    """POST /api/auth/sessions/revoke-all/"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        current_session_key = request.session.session_key
        sessions = UserSession.objects.filter(user=request.user, is_active=True).exclude(session_key=current_session_key)
        count = sessions.count()
        sessions.update(is_active=False)
        return Response({'message': f'Successfully revoked {count} session(s)'}, status=status.HTTP_200_OK)


# ==============================================================================
# USER SEARCH & DISCOVERY
# ==============================================================================

class SearchUsersView(views.APIView):
    """GET /api/auth/users/search/?q=john"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if len(query) < 2:
            return Response({'error': 'Search query must be at least 2 characters'}, status=status.HTTP_400_BAD_REQUEST)
        
        users = User.objects.filter(is_active=True).filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        ).exclude(id=request.user.id)[:20]
        
        return Response({'count': len(users), 'results': PublicUserSerializer(users, many=True).data})

class UserDetailView(views.APIView):
    """GET /api/auth/users/{user_id}/"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, is_active=True)
            return Response(PublicUserSerializer(user).data)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


# ==============================================================================
# DEBUG / STATS
# ==============================================================================

class UpdateActivityView(views.APIView):
    """POST /api/auth/activity/update/"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        request.user.update_last_activity()
        return Response({'message': 'Activity updated', 'last_activity': request.user.last_activity})

class AccountStatsView(views.APIView):
    """GET /api/auth/stats/"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        days_since_joining = (timezone.now() - user.date_joined).days
        active_sessions = UserSession.objects.filter(user=user, is_active=True, expires_at__gt=timezone.now()).count()
        
        stats = {
            'user_id': str(user.id), 'account_age_days': days_since_joining,
            'email_verified': user.is_email_verified, 'two_factor_enabled': user.two_factor_enabled,
            'plan_type': user.plan_type, 'active_sessions': active_sessions,
            'last_login': user.last_login, 'last_activity': user.last_activity, 'date_joined': user.date_joined,
        }
        return Response(stats)

class CheckAuthView(views.APIView):
    """GET /api/auth/check/"""
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({'authenticated': True, 'user': UserSerializer(request.user).data})