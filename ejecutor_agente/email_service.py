"""
Servicio de correo electrónico para envío de alertas del Executor Agent.
Implementa envío SMTP SSL compatible con Gmail y otros proveedores.
"""

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class EmailConfig:
    """Configuración del servicio de correo."""
    smtp_server: str
    smtp_port: int
    email_from: str
    email_password: str
    use_tls: bool = True

@dataclass
class EmailResult:
    """Resultado del envío de correo."""
    success: bool
    message: str
    recipients: List[str]
    timestamp: float
    error_details: Optional[str] = None

class EmailService:
    """
    Servicio reutilizable para envío de correos electrónicos.
    Soporta SMTP SSL/TLS y configuración mediante variables de entorno.
    """
    
    def __init__(self):
        """Inicializar el servicio de correo con configuración desde entorno."""
        self.logger = logging.getLogger(f"{__name__}.EmailService")
        self.config = self._load_config()
        
    def _load_config(self) -> EmailConfig:
        """
        Cargar configuración desde variables de entorno.
        
        Returns:
            Configuración del servicio de correo
            
        Raises:
            ValueError: Si faltan variables de entorno requeridas
        """
        # Variables de entorno requeridas
        email_from = os.getenv("ALERT_EMAIL_FROM")
        email_password = os.getenv("ALERT_EMAIL_PASSWORD")
        
        if not email_from or not email_password:
            raise ValueError(
                "ALERT_EMAIL_FROM and ALERT_EMAIL_PASSWORD environment variables are required"
            )
        
        # Configuración SMTP con valores por defecto para Gmail
        smtp_server = os.getenv("ALERT_SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("ALERT_SMTP_PORT", "587"))
        use_tls = os.getenv("ALERT_USE_TLS", "true").lower() == "true"
        
        config = EmailConfig(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            email_from=email_from,
            email_password=email_password,
            use_tls=use_tls
        )
        
        self.logger.info(f"Email service configured for {config.email_from}")
        return config
    
    def _create_alert_email(self, 
                           to_emails: List[str], 
                           event_data: Dict[str, Any], 
                           decision_data: Dict[str, Any]) -> EmailMessage:
        """
        Crear mensaje de correo para alerta.
        
        Args:
            to_emails: Lista de destinatarios
            event_data: Datos del evento que generó la alerta
            decision_data: Datos de la decisión tomada
            
        Returns:
            Mensaje de correo configurado
        """
        msg = EmailMessage()
        
        # Configurar destinatarios
        msg["From"] = self.config.email_from
        msg["To"] = ", ".join(to_emails)
        
        # Asunto del correo
        severity = event_data.get("severity", "UNKNOWN")
        event_type = event_data.get("event_type", "UNKNOWN")
        resource = event_data.get("resource", "UNKNOWN")
        
        subject = f"[ALERT-{severity}] {event_type} on {resource}"
        msg["Subject"] = subject
        
        # Cuerpo del correo en formato HTML
        html_body = self._build_html_body(event_data, decision_data)
        msg.set_content(html_body, subtype='html')
        
        return msg
    
    def _build_html_body(self, event_data: Dict[str, Any], decision_data: Dict[str, Any]) -> str:
        """
        Construir cuerpo HTML del correo con formato profesional.
        
        Args:
            event_data: Datos del evento
            decision_data: Datos de la decisión
            
        Returns:
            Cuerpo HTML formateado
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .alert-critical {{ border-left: 5px solid #dc3545; }}
                .alert-high {{ border-left: 5px solid #fd7e14; }}
                .alert-medium {{ border-left: 5px solid #ffc107; }}
                .alert-low {{ border-left: 5px solid #28a745; }}
                .section {{ margin: 15px 0; }}
                .label {{ font-weight: bold; color: #495057; }}
                .value {{ margin-left: 10px; }}
                .decision {{ background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-top: 15px; }}
                .footer {{ font-size: 12px; color: #6c757d; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="header alert-{event_data.get('severity', 'unknown').lower()}">
                <h2>🚨 Executor Agent Alert</h2>
                <p><strong>Timestamp:</strong> {timestamp}</p>
            </div>
            
            <div class="section">
                <h3>📋 Event Details</h3>
                <p><span class="label">Event Type:</span> <span class="value">{event_data.get('event_type', 'N/A')}</span></p>
                <p><span class="label">Resource:</span> <span class="value">{event_data.get('resource', 'N/A')}</span></p>
                <p><span class="label">Severity:</span> <span class="value">{event_data.get('severity', 'N/A')}</span></p>
                <p><span class="label">Business Impact:</span> <span class="value">{event_data.get('business_impact', 'N/A')}</span></p>
                <p><span class="label">Time to Impact:</span> <span class="value">{event_data.get('time_to_impact', 'N/A')} minutes</span></p>
                <p><span class="label">Confidence:</span> <span class="value">{event_data.get('confidence', 'N/A')}</span></p>
            </div>
            
            <div class="decision">
                <h3>🤖 Decision Made</h3>
                <p><span class="label">Decision:</span> <span class="value">{decision_data.get('decision', 'N/A')}</span></p>
                <p><span class="label">Risk Score:</span> <span class="value">{decision_data.get('score', 'N/A')}</span></p>
                <p><span class="label">Actions Executed:</span> <span class="value">{', '.join(decision_data.get('actions_executed', []))}</span></p>
                <p><span class="label">Reasoning:</span> <span class="value">{decision_data.get('reasoning', 'N/A')}</span></p>
            </div>
            
            <div class="footer">
                <p>This alert was generated automatically by the Executor Agent.</p>
                <p>If you believe this is an error, please contact your system administrator.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_alert(self, 
                   to_emails: List[str], 
                   event_data: Dict[str, Any], 
                   decision_data: Dict[str, Any]) -> EmailResult:
        """
        Enviar alerta por correo electrónico.
        
        Args:
            to_emails: Lista de destinatarios
            event_data: Datos del evento
            decision_data: Datos de la decisión
            
        Returns:
            Resultado del envío
        """
        timestamp = datetime.now().timestamp()
        
        try:
            # Validar destinatarios
            if not to_emails:
                return EmailResult(
                    success=False,
                    message="No recipients specified",
                    recipients=[],
                    timestamp=timestamp,
                    error_details="Empty recipient list"
                )
            
            # Crear mensaje
            msg = self._create_alert_email(to_emails, event_data, decision_data)
            
            # Enviar correo
            self.logger.info(f"Sending alert email to {len(to_emails)} recipients")
            
            # Crear contexto SSL/TLS con verificación deshabilitada para Gmail
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Conectar y enviar
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls(context=context)
                
                server.login(self.config.email_from, self.config.email_password)
                server.send_message(msg)
            
            self.logger.info(f"Alert email sent successfully to {to_emails}")
            
            return EmailResult(
                success=True,
                message=f"Alert sent to {len(to_emails)} recipients",
                recipients=to_emails,
                timestamp=timestamp
            )
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {str(e)}"
            self.logger.error(error_msg)
            return EmailResult(
                success=False,
                message="Email authentication failed",
                recipients=to_emails,
                timestamp=timestamp,
                error_details=error_msg
            )
            
        except smtplib.SMTPRecipientsRefused as e:
            error_msg = f"All recipients refused: {str(e)}"
            self.logger.error(error_msg)
            return EmailResult(
                success=False,
                message="All recipients refused",
                recipients=to_emails,
                timestamp=timestamp,
                error_details=error_msg
            )
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error occurred: {str(e)}"
            self.logger.error(error_msg)
            return EmailResult(
                success=False,
                message="SMTP error",
                recipients=to_emails,
                timestamp=timestamp,
                error_details=error_msg
            )
            
        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            self.logger.error(error_msg)
            return EmailResult(
                success=False,
                message="Unexpected error",
                recipients=to_emails,
                timestamp=timestamp,
                error_details=error_msg
            )
    
    def test_connection(self) -> bool:
        """
        Probar la conexión con el servidor SMTP.
        
        Returns:
            True si la conexión es exitosa
        """
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls(context=context)
                
                server.login(self.config.email_from, self.config.email_password)
            
            self.logger.info("SMTP connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP connection test failed: {str(e)}")
            return False
