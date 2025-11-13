"""
Email Service for OneClouds
Handles all email operations including password reset, email verification, and 2FA
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from backend.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service using Gmail SMTP with app password"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.frontend_url = settings.FRONTEND_URL
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email using Gmail SMTP with TLS encryption
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            plain_text_content: Plain text fallback (optional)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"OneClouds <{self.from_email}>"
            msg['To'] = to_email
            
            # Add plain text part if provided, otherwise create from HTML
            if plain_text_content:
                part1 = MIMEText(plain_text_content, 'plain')
                msg.attach(part1)
            
            # Add HTML part
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # Send email via Gmail SMTP with TLS
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Upgrade to TLS
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """
        Send password reset email with reset link
        
        Args:
            to_email: User's email address
            reset_token: JWT token for password reset
        
        Returns:
            bool: True if email sent successfully
        """
        reset_link = f"{self.frontend_url}/reset-password?token={reset_token}"
        
        subject = "Reset Your OneClouds Password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>We received a request to reset your OneClouds password. Click the button below to create a new password:</p>
                    <div style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </div>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #fff; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                        {reset_link}
                    </p>
                    <div class="warning">
                        ⚠️ <strong>This link will expire in 1 hour.</strong>
                    </div>
                    <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
                    <p>Best regards,<br>The OneClouds Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated email. Please do not reply.</p>
                    <p>© 2025 OneClouds. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_text = f"""
        Password Reset Request
        
        Hello,
        
        We received a request to reset your OneClouds password.
        
        Click the link below to reset your password:
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, you can safely ignore this email.
        
        Best regards,
        The OneClouds Team
        """
        
        return self._send_email(to_email, subject, html_content, plain_text)
    
    def send_email_verification_email(self, to_email: str, verification_token: str, new_email: str) -> bool:
        """
        Send email verification link for email change
        
        Args:
            to_email: New email address to verify
            verification_token: JWT token for email verification
            new_email: The new email being verified
        
        Returns:
            bool: True if email sent successfully
        """
        verification_link = f"{self.frontend_url}/verify-email?token={verification_token}"
        
        subject = "Verify Your New Email Address - OneClouds"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .info {{ background: #d1ecf1; border-left: 4px solid #0c5460; padding: 10px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✉️ Verify Your Email Address</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>You requested to change your email address to <strong>{new_email}</strong>.</p>
                    <p>Please verify this email address by clicking the button below:</p>
                    <div style="text-align: center;">
                        <a href="{verification_link}" class="button">Verify Email</a>
                    </div>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #fff; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                        {verification_link}
                    </p>
                    <div class="info">
                        ℹ️ <strong>This link will expire in 24 hours.</strong>
                    </div>
                    <p>After verification, you'll need to log in again with your new email address.</p>
                    <p>If you didn't request this change, please contact our support team immediately.</p>
                    <p>Best regards,<br>The OneClouds Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated email. Please do not reply.</p>
                    <p>© 2025 OneClouds. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_text = f"""
        Verify Your Email Address
        
        Hello,
        
        You requested to change your email address to {new_email}.
        
        Please verify this email address by clicking the link below:
        {verification_link}
        
        This link will expire in 24 hours.
        
        After verification, you'll need to log in again with your new email address.
        
        Best regards,
        The OneClouds Team
        """
        
        return self._send_email(new_email, subject, html_content, plain_text)
    
    def send_2fa_code_email(self, to_email: str, code: str) -> bool:
        """
        Send 2FA verification code email
        
        Args:
            to_email: User's email address
            code: 6-digit verification code
        
        Returns:
            bool: True if email sent successfully
        """
        subject = "Your OneClouds Verification Code"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .code {{ font-size: 32px; font-weight: bold; text-align: center; background: white; padding: 20px; border-radius: 10px; letter-spacing: 8px; margin: 20px 0; color: #667eea; border: 2px dashed #667eea; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Two-Factor Authentication</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>Here's your verification code for OneClouds:</p>
                    <div class="code">{code}</div>
                    <div class="warning">
                        ⚠️ <strong>This code will expire in 10 minutes.</strong>
                    </div>
                    <p>Enter this code in the OneClouds app to complete your login.</p>
                    <p>If you didn't request this code, please ignore this email and ensure your account is secure.</p>
                    <p>Best regards,<br>The OneClouds Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated email. Please do not reply.</p>
                    <p>© 2025 OneClouds. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_text = f"""
        Two-Factor Authentication Code
        
        Hello,
        
        Here's your verification code for OneClouds:
        
        {code}
        
        This code will expire in 10 minutes.
        
        Enter this code in the OneClouds app to complete your login.
        
        Best regards,
        The OneClouds Team
        """
        
        return self._send_email(to_email, subject, html_content, plain_text)
    
    def send_password_changed_notification(self, to_email: str) -> bool:
        """
        Send notification that password was changed
        
        Args:
            to_email: User's email address
        
        Returns:
            bool: True if email sent successfully
        """
        subject = "Your OneClouds Password Was Changed"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .alert {{ background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; }}
                .warning {{ background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Password Changed Successfully</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <div class="alert">
                        ✓ Your OneClouds password was successfully changed.
                    </div>
                    <p>For your security, you have been logged out of all devices. Please log in again with your new password.</p>
                    <div class="warning">
                        ⚠️ <strong>Didn't make this change?</strong><br>
                        If you did not change your password, please contact our support team immediately as your account may be compromised.
                    </div>
                    <p>Best regards,<br>The OneClouds Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated email. Please do not reply.</p>
                    <p>© 2025 OneClouds. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_text = """
        Password Changed Successfully
        
        Hello,
        
        Your OneClouds password was successfully changed.
        
        For your security, you have been logged out of all devices. Please log in again with your new password.
        
        If you did not make this change, please contact our support team immediately.
        
        Best regards,
        The OneClouds Team
        """
        
        return self._send_email(to_email, subject, html_content, plain_text)


# Global email service instance
email_service = EmailService()
