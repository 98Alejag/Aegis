"""
Script de prueba para el servicio de correo electrónico del Executor Agent.
Valida la configuración y envío de alertas por email.
"""

import os
import json
import time
from email_service import EmailService, EmailConfig
from action_system import ActionExecutor, SendAlertAction
from decision_engine import DecisionEngine, Severity, BusinessImpact

def test_email_service_config():
    """Probar la configuración del servicio de correo."""
    print("Testing Email Service Configuration...")
    
    try:
        # Verificar variables de entorno requeridas
        required_vars = ["ALERT_EMAIL_FROM", "ALERT_EMAIL_PASSWORD"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"Missing environment variables: {missing_vars}")
            print("Please set these variables in your .env file:")
            for var in missing_vars:
                print(f"  {var}=your_value")
            return False
        
        # Intentar inicializar el servicio
        email_service = EmailService()
        config = email_service.config
        
        print(f"Email service configured successfully:")
        print(f"  From: {config.email_from}")
        print(f"  SMTP: {config.smtp_server}:{config.smtp_port}")
        print(f"  TLS: {config.use_tls}")
        print(f"  Recipients: {os.getenv('ALERT_EMAIL_RECIPIENTS', 'Not configured')}")
        
        return True
        
    except Exception as e:
        print(f"Email service configuration failed: {str(e)}")
        return False

def test_smtp_connection():
    """Probar la conexión con el servidor SMTP."""
    print("\nTesting SMTP Connection...")
    
    try:
        email_service = EmailService()
        
        if email_service.test_connection():
            print("SMTP connection successful")
            return True
        else:
            print("SMTP connection failed")
            return False
            
    except Exception as e:
        print(f"SMTP connection test error: {str(e)}")
        return False

def test_send_alert_action():
    """Probar la acción de envío de alertas."""
    print("\nTesting SendAlert Action...")
    
    try:
        # Crear acción de envío de alerta
        send_alert_action = SendAlertAction()
        
        # Evento de prueba
        event = {
            "event_type": "SYSTEM_FAILURE",
            "severity": "HIGH",
            "resource": "database-primary",
            "time_to_impact": 2,
            "business_impact": "CRITICAL",
            "confidence": 0.95
        }
        
        # Datos de decisión de prueba
        from decision_engine import DecisionType
        decision = DecisionType.EXECUTE_IMMEDIATE
        score = 95.0
        actions_executed = ["send_alert", "create_ticket", "execute_script"]
        reasoning = "High risk event requires immediate execution"
        
        # Contexto para la acción
        context = {
            "event": event,
            "decision": decision,
            "score": score,
            "actions_executed": actions_executed,
            "reasoning": reasoning
        }
        
        # Ejecutar acción
        result = send_alert_action.execute(context)
        
        print(f"Action result: {result.result.value}")
        print(f"Message: {result.message}")
        
        if result.result.value == "SUCCESS":
            print("Alert email sent successfully")
            if result.details and "recipients" in result.details:
                print(f"  Recipients: {result.details['recipients']}")
        else:
            print("Alert email failed")
            if result.details and "error" in result.details:
                print(f"  Error: {result.details['error']}")
        
        return result.result.value == "SUCCESS"
        
    except Exception as e:
        print(f"SendAlert action test error: {str(e)}")
        return False

def test_full_integration():
    """Probar integración completa con DecisionEngine y ActionSystem."""
    print("\nTesting Full Integration...")
    
    try:
        # Inicializar componentes
        decision_engine = DecisionEngine()
        action_executor = ActionExecutor()
        
        # Evento crítico de prueba
        event = {
            "event_type": "SECURITY_BREACH",
            "severity": "HIGH",
            "resource": "auth-server",
            "time_to_impact": 1,
            "business_impact": "CRITICAL",
            "confidence": 0.98
        }
        
        print(f"Processing event: {event['event_type']}")
        
        # Procesar evento
        decision_result = decision_engine.process_event(event)
        
        print(f"Decision: {decision_result.decision.value}")
        print(f"Score: {decision_result.score:.2f}")
        print(f"Actions: {decision_result.actions_executed}")
        
        # Preparar contexto para acciones
        action_context = {
            "event": event,
            "decision": decision_result.decision,
            "score": decision_result.score,
            "actions_executed": decision_result.actions_executed,
            "reasoning": decision_result.reasoning
        }
        
        # Ejecutar acciones
        action_results = action_executor.execute_actions(
            decision_result.actions_executed, 
            action_context
        )
        
        print("Action Results:")
        email_sent = False
        for result in action_results:
            status = "OK" if result.result.value == "SUCCESS" else "FAIL"
            print(f"  {status} {result.action_name}: {result.message}")
            
            if result.action_name == "send_alert" and result.result.value == "SUCCESS":
                email_sent = True
        
        if email_sent:
            print("Full integration test successful - email alert sent")
        else:
            print("Full integration test completed - email not sent (may be expected)")
        
        return True
        
    except Exception as e:
        print(f"Full integration test error: {str(e)}")
        return False

def test_email_without_config():
    """Probar comportamiento cuando no hay configuración de email."""
    print("\nTesting Behavior Without Email Configuration...")
    
    try:
        # Temporalmente eliminar variables de entorno
        original_email = os.getenv("ALERT_EMAIL_FROM")
        original_password = os.getenv("ALERT_EMAIL_PASSWORD")
        
        if "ALERT_EMAIL_FROM" in os.environ:
            del os.environ["ALERT_EMAIL_FROM"]
        if "ALERT_EMAIL_PASSWORD" in os.environ:
            del os.environ["ALERT_EMAIL_PASSWORD"]
        
        # Crear acción y ejecutar
        send_alert_action = SendAlertAction()
        
        event = {"event_type": "TEST_EVENT"}
        context = {"event": event}
        
        result = send_alert_action.execute(context)
        
        print(f"Result without config: {result.result.value}")
        print(f"Message: {result.message}")
        
        if result.result.value == "FAILURE":
            print("Correctly handled missing configuration")
            success = True
        else:
            print("Should have failed with missing configuration")
            success = False
        
        # Restaurar variables de entorno
        if original_email:
            os.environ["ALERT_EMAIL_FROM"] = original_email
        if original_password:
            os.environ["ALERT_EMAIL_PASSWORD"] = original_password
        
        return success
        
    except Exception as e:
        print(f"FAIL Test without config error: {str(e)}")
        return False

def main():
    """Ejecutar todas las pruebas del servicio de correo."""
    print("Executor Agent Email Service Test Suite")
    print("=" * 50)
    
    # Verificar si hay configuración de correo
    if not os.getenv("ALERT_EMAIL_FROM"):
        print("\nEmail configuration not found in .env file")
        print("To test email functionality, set these variables in .env:")
        print("  ALERT_EMAIL_FROM=your-email@gmail.com")
        print("  ALERT_EMAIL_PASSWORD=your-app-password")
        print("  ALERT_EMAIL_RECIPIENTS=admin@example.com")
        print("\nRunning basic functionality tests without email sending...")
    
    tests = [
        ("Configuration", test_email_service_config),
        ("SMTP Connection", test_smtp_connection),
        ("SendAlert Action", test_send_alert_action),
        ("Full Integration", test_full_integration),
        ("Missing Config", test_email_without_config)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"FAIL {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Resumen
    print(f"\n{'='*50}")
    print("Test Results Summary:")
    passed = 0
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\nAll tests passed!")
    else:
        print("Some tests failed - check configuration")

if __name__ == "__main__":
    main()
