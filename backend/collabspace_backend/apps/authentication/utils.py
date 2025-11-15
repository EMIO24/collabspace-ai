"""
Authentication utility functions for CollabSpace AI.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import pyotp
import qrcode
from io import BytesIO
import base64


def send_verification_email(user, token):
    """
    Send email verification link to user.
    
    Args:
        user: User instance
        token: Verification token
    """
    # In production, this should be your frontend URL
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    
    subject = 'Verify your CollabSpace AI email'
    
    # HTML email content
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Welcome to CollabSpace AI!</h2>
            <p>Hello {user.get_full_name()},</p>
            <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
            <p style="margin: 30px 0;">
                <a href="{verification_url}" 
                   style="background-color: #4F46E5; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    Verify Email Address
                </a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p><a href="{verification_url}">{verification_url}</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account with CollabSpace AI, please ignore this email.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
            <p style="color: #666; font-size: 12px;">
                CollabSpace AI - AI-Powered Team Collaboration Platform
            </p>
        </body>
    </html>
    """
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_password_reset_email(user, token):
    """
    Send password reset link to user.
    
    Args:
        user: User instance
        token: Reset token
    """
    # In production, this should be your frontend URL
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    subject = 'Reset your CollabSpace AI password'
    
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Password Reset Request</h2>
            <p>Hello {user.get_full_name()},</p>
            <p>We received a request to reset your password. Click the button below to reset it:</p>
            <p style="margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background-color: #4F46E5; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    Reset Password
                </a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request a password reset, please ignore this email or contact support if you have concerns.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
            <p style="color: #666; font-size: 12px;">
                CollabSpace AI - AI-Powered Team Collaboration Platform
            </p>
        </body>
    </html>
    """
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_welcome_email(user):
    """
    Send welcome email to new user after email verification.
    
    Args:
        user: User instance
    """
    subject = 'Welcome to CollabSpace AI!'
    
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Welcome to CollabSpace AI! 🎉</h2>
            <p>Hello {user.get_full_name()},</p>
            <p>Your email has been verified successfully. You're all set to start collaborating!</p>
            <h3>Getting Started:</h3>
            <ul>
                <li>Create your first workspace</li>
                <li>Invite team members</li>
                <li>Start organizing projects and tasks</li>
                <li>Try our AI-powered features</li>
            </ul>
            <p style="margin: 30px 0;">
                <a href="{settings.FRONTEND_URL}/dashboard" 
                   style="background-color: #4F46E5; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    Go to Dashboard
                </a>
            </p>
            <p>Need help? Check out our <a href="{settings.FRONTEND_URL}/docs">documentation</a> 
               or contact our support team.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
            <p style="color: #666; font-size: 12px;">
                CollabSpace AI - AI-Powered Team Collaboration Platform
            </p>
        </body>
    </html>
    """
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


# ==============================================================================
# TWO-FACTOR AUTHENTICATION HELPERS
# ==============================================================================

def generate_2fa_secret():
    """
    Generate a new TOTP secret for 2FA.
    
    Returns:
        str: Base32 encoded secret
    """
    return pyotp.random_base32()


def generate_2fa_qr_code(user, secret):
    """
    Generate QR code for 2FA setup.
    
    Args:
        user: User instance
        secret: TOTP secret
        
    Returns:
        str: Base64 encoded QR code image
    """
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email,
        issuer_name='CollabSpace AI'
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{qr_code_base64}"


def verify_2fa_code(secret, code):
    """
    Verify a TOTP code.
    
    Args:
        secret: TOTP secret
        code: 6-digit code from authenticator app
        
    Returns:
        bool: True if code is valid, False otherwise
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)  # Allow 30 seconds drift


# ==============================================================================
# JWT TOKEN HELPERS
# ==============================================================================

def get_tokens_for_user(user):
    """
    Generate JWT tokens for user.
    
    Args:
        user: User instance
        
    Returns:
        dict: Dictionary containing refresh and access tokens
    """
    from rest_framework_simplejwt.tokens import RefreshToken
    
    refresh = RefreshToken.for_user(user)
    
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# ==============================================================================
# VALIDATION HELPERS
# ==============================================================================

def is_valid_username(username):
    """
    Check if username meets requirements.
    
    Args:
        username: Username string
        
    Returns:
        bool: True if valid, False otherwise
    """
    if len(username) < 3 or len(username) > 150:
        return False
    
    # Check alphanumeric with underscores and hyphens
    return username.replace('_', '').replace('-', '').isalnum()


def is_password_strong(password):
    """
    Check if password is strong enough.
    
    Args:
        password: Password string
        
    Returns:
        tuple: (bool, list) - (is_valid, list of errors)
    """
    errors = []
    
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    
    if not any(char.isdigit() for char in password):
        errors.append('Password must contain at least one digit')
    
    if not any(char.isupper() for char in password):
        errors.append('Password must contain at least one uppercase letter')
    
    if not any(char.islower() for char in password):
        errors.append('Password must contain at least one lowercase letter')
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(char in special_chars for char in password):
        errors.append('Password must contain at least one special character')
    
    return (len(errors) == 0, errors)