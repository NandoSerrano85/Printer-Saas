import os
import logging
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from .models import (
    EmailRequest, EmailVerificationRequest, PasswordResetRequest,
    EmailResponse, EmailTemplate, EmailPriority, EmailStatus
)

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for sending transactional emails"""
    
    def __init__(self):
        # Email configuration from environment
        self.smtp_server = os.getenv("SMTP_SERVER", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        self.from_email = os.getenv("FROM_EMAIL", "noreply@printer-saas.com")
        self.from_name = os.getenv("FROM_NAME", "Printer SaaS")
        self.reply_to = os.getenv("REPLY_TO_EMAIL", "support@printer-saas.com")
        
        # App configuration
        self.app_name = os.getenv("APP_NAME", "Printer SaaS")
        self.app_url = os.getenv("APP_URL", "https://app.printer-saas.com")
        self.support_email = os.getenv("SUPPORT_EMAIL", "support@printer-saas.com")
        
        # Template configuration
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
        
        # Test mode - if true, emails are logged instead of sent
        self.test_mode = os.getenv("EMAIL_TEST_MODE", "false").lower() == "true"
        
    def _get_smtp_connection(self):
        """Get SMTP connection"""
        try:
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            return server
        except Exception as e:
            logger.error(f"SMTP connection error: {str(e)}")
            raise e
    
    def _render_template(self, template_name: str, template_data: Dict[str, Any]) -> tuple[str, str]:
        """Render email template (HTML and text versions)"""
        try:
            # Add common template variables
            common_data = {
                "app_name": self.app_name,
                "app_url": self.app_url,
                "support_email": self.support_email,
                "current_year": datetime.now().year,
                **template_data
            }
            
            # Render HTML template
            html_template = self.jinja_env.get_template(f"{template_name}.html")
            html_content = html_template.render(**common_data)
            
            # Render text template (fallback to simple text if not found)
            try:
                text_template = self.jinja_env.get_template(f"{template_name}.txt")
                text_content = text_template.render(**common_data)
            except TemplateNotFound:
                # Generate simple text version from HTML (basic fallback)
                import re
                text_content = re.sub(r'<[^>]+>', '', html_content)
                text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            return html_content, text_content
            
        except TemplateNotFound:
            logger.error(f"Email template not found: {template_name}")
            raise ValueError(f"Email template not found: {template_name}")
        except Exception as e:
            logger.error(f"Template rendering error: {str(e)}")
            raise e
    
    def _get_template_subject(self, template: EmailTemplate, template_data: Dict[str, Any]) -> str:
        """Get email subject based on template"""
        subjects = {
            EmailTemplate.EMAIL_VERIFICATION: f"Verify your {self.app_name} email address",
            EmailTemplate.PASSWORD_RESET: f"Reset your {self.app_name} password",
            EmailTemplate.WELCOME: f"Welcome to {self.app_name}!",
            EmailTemplate.ACCOUNT_LOCKED: f"Your {self.app_name} account has been locked",
            EmailTemplate.PASSWORD_CHANGED: f"Your {self.app_name} password was changed",
            EmailTemplate.TWO_FACTOR_ENABLED: f"Two-factor authentication enabled on {self.app_name}",
            EmailTemplate.TWO_FACTOR_DISABLED: f"Two-factor authentication disabled on {self.app_name}",
            EmailTemplate.LOGIN_ALERT: f"New login to your {self.app_name} account",
        }
        
        base_subject = subjects.get(template, f"{self.app_name} Notification")
        
        # Add user-specific data if available
        if 'user_name' in template_data:
            return f"{base_subject} - {template_data['user_name']}"
        
        return base_subject
    
    def send_email(self, email_request: EmailRequest) -> EmailResponse:
        """Send email using configured SMTP server"""
        try:
            # Generate email ID for tracking
            email_id = str(uuid4())
            
            # Get template subject
            subject = self._get_template_subject(email_request.template, email_request.template_data)
            
            # Render email content
            html_content, text_content = self._render_template(
                email_request.template.value, 
                email_request.template_data
            )
            
            if self.test_mode:
                # In test mode, just log the email
                logger.info(f"TEST EMAIL - ID: {email_id}")
                logger.info(f"To: {email_request.to_email}")
                logger.info(f"Subject: {subject}")
                logger.info(f"Template: {email_request.template.value}")
                logger.info(f"Content: {text_content[:200]}...")
                
                return EmailResponse(
                    success=True,
                    message="Email sent (test mode)",
                    email_id=email_id
                )
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = f"{email_request.to_name or ''} <{email_request.to_email}>".strip()
            msg['Reply-To'] = self.reply_to
            msg['Message-ID'] = f"<{email_id}@{self.smtp_server}>"
            
            # Attach text and HTML parts
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with self._get_smtp_connection() as server:
                server.send_message(msg)
            
            logger.info(f"Email sent successfully - ID: {email_id}, To: {email_request.to_email}")
            
            return EmailResponse(
                success=True,
                message="Email sent successfully",
                email_id=email_id
            )
            
        except Exception as e:
            logger.error(f"Email send error: {str(e)}")
            return EmailResponse(
                success=False,
                message="Failed to send email",
                error=str(e)
            )
    
    def send_verification_email(self, verification_request: EmailVerificationRequest) -> EmailResponse:
        """Send email verification email"""
        template_data = {
            "verification_url": verification_request.verification_url,
            "verification_token": verification_request.verification_token,
            "expires_at": verification_request.expires_at.strftime("%B %d, %Y at %H:%M UTC"),
            "user_email": verification_request.email
        }
        
        email_request = EmailRequest(
            to_email=verification_request.email,
            template=EmailTemplate.EMAIL_VERIFICATION,
            template_data=template_data,
            priority=EmailPriority.HIGH,
            tenant_id="system",  # Email verification is system-wide
            user_id=verification_request.user_id
        )
        
        return self.send_email(email_request)
    
    def send_password_reset_email(self, reset_request: PasswordResetRequest) -> EmailResponse:
        """Send password reset email"""
        template_data = {
            "reset_url": reset_request.reset_url,
            "reset_token": reset_request.reset_token,
            "expires_at": reset_request.expires_at.strftime("%B %d, %Y at %H:%M UTC"),
            "user_email": reset_request.email
        }
        
        email_request = EmailRequest(
            to_email=reset_request.email,
            template=EmailTemplate.PASSWORD_RESET,
            template_data=template_data,
            priority=EmailPriority.HIGH,
            tenant_id="system",  # Password reset is system-wide
            user_id=reset_request.user_id
        )
        
        return self.send_email(email_request)
    
    def send_welcome_email(self, user_email: str, user_name: str, tenant_id: str, user_id: UUID) -> EmailResponse:
        """Send welcome email to new user"""
        template_data = {
            "user_name": user_name,
            "login_url": f"{self.app_url}/login",
            "dashboard_url": f"{self.app_url}/dashboard"
        }
        
        email_request = EmailRequest(
            to_email=user_email,
            to_name=user_name,
            template=EmailTemplate.WELCOME,
            template_data=template_data,
            priority=EmailPriority.NORMAL,
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        return self.send_email(email_request)
    
    def send_password_changed_email(self, user_email: str, user_name: str, tenant_id: str, user_id: UUID) -> EmailResponse:
        """Send password changed notification email"""
        template_data = {
            "user_name": user_name,
            "changed_at": datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC"),
            "security_url": f"{self.app_url}/security"
        }
        
        email_request = EmailRequest(
            to_email=user_email,
            to_name=user_name,
            template=EmailTemplate.PASSWORD_CHANGED,
            template_data=template_data,
            priority=EmailPriority.HIGH,
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        return self.send_email(email_request)
    
    def send_two_factor_enabled_email(self, user_email: str, user_name: str, tenant_id: str, user_id: UUID) -> EmailResponse:
        """Send 2FA enabled notification email"""
        template_data = {
            "user_name": user_name,
            "enabled_at": datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC"),
            "security_url": f"{self.app_url}/security"
        }
        
        email_request = EmailRequest(
            to_email=user_email,
            to_name=user_name,
            template=EmailTemplate.TWO_FACTOR_ENABLED,
            template_data=template_data,
            priority=EmailPriority.NORMAL,
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        return self.send_email(email_request)
    
    def send_account_locked_email(self, user_email: str, user_name: str, locked_until: datetime, tenant_id: str, user_id: UUID) -> EmailResponse:
        """Send account locked notification email"""
        template_data = {
            "user_name": user_name,
            "locked_until": locked_until.strftime("%B %d, %Y at %H:%M UTC"),
            "unlock_url": f"{self.app_url}/unlock-account",
            "security_url": f"{self.app_url}/security"
        }
        
        email_request = EmailRequest(
            to_email=user_email,
            to_name=user_name,
            template=EmailTemplate.ACCOUNT_LOCKED,
            template_data=template_data,
            priority=EmailPriority.URGENT,
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        return self.send_email(email_request)
    
    def test_email_connection(self) -> bool:
        """Test email server connection"""
        try:
            with self._get_smtp_connection() as server:
                server.noop()  # Test connection
            return True
        except Exception as e:
            logger.error(f"Email connection test failed: {str(e)}")
            return False

# Global email service instance
email_service = EmailService()