"""
Script de prueba para Executor Agent.
Valida el funcionamiento del motor de decisión y sistema de acciones.
"""

import json
import time
import asyncio
from decision_engine import DecisionEngine, Event, Severity, BusinessImpact
from action_system import ActionExecutor
from executor_tools import initialize_tools, process_event, get_decision_history, calculate_risk_score

def test_decision_engine():
    """Probar el motor de decisión con diferentes escenarios."""
    print("Testing Decision Engine...")
    
    engine = DecisionEngine()
    
    # Casos de prueba
    test_cases = [
        {
            "name": "Critical Event - High Confidence",
            "event": {
                "event_type": "SYSTEM_FAILURE",
                "severity": "HIGH",
                "resource": "database-primary",
                "time_to_impact": 2,
                "business_impact": "CRITICAL",
                "confidence": 0.95
            },
            "expected_decision": "EXECUTE_IMMEDIATE"
        },
        {
            "name": "Medium Event - Medium Confidence",
            "event": {
                "event_type": "CPU_HIGH",
                "severity": "MEDIUM",
                "resource": "web-server-01",
                "time_to_impact": 25,
                "business_impact": "MEDIUM",
                "confidence": 0.8
            },
            "expected_decision": "ALERT_AND_TICKET"
        },
        {
            "name": "Low Event - Low Confidence",
            "event": {
                "event_type": "MEMORY_WARNING",
                "severity": "LOW",
                "resource": "cache-server",
                "time_to_impact": 180,
                "business_impact": "LOW",
                "confidence": 0.4
            },
            "expected_decision": "REQUIRES_HUMAN_REVIEW"
        },
        {
            "name": "Low Priority Event",
            "event": {
                "event_type": "LOG_ROTATION",
                "severity": "LOW",
                "resource": "backup-server",
                "time_to_impact": 300,
                "business_impact": "LOW",
                "confidence": 0.9
            },
            "expected_decision": "LOG_ONLY"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        
        # Procesar evento
        result = engine.process_event(test_case["event"])
        
        print(f"Event: {test_case['event']['event_type']}")
        print(f"Decision: {result.decision.value}")
        print(f"Score: {result.score:.2f}")
        print(f"Actions: {result.actions_executed}")
        print(f"Expected: {test_case['expected_decision']}")
        
        # Validar resultado
        if result.decision.value == test_case["expected_decision"]:
            print("PASS")
        else:
            print("FAIL")
        
        print(f"Reasoning: {result.reasoning}")

def test_action_system():
    """Probar el sistema de acciones."""
    print("\nTesting Action System...")
    
    executor = ActionExecutor()
    
    # Evento de prueba
    event = {
        "event_type": "SYSTEM_FAILURE",
        "severity": "HIGH",
        "resource": "database-primary",
        "time_to_impact": 2,
        "business_impact": "CRITICAL",
        "confidence": 0.95
    }
    
    # Contexto de prueba
    context = {
        "event": event,
        "decision": "EXECUTE_IMMEDIATE",
        "score": 95.0,
        "reasoning": "High risk event requires immediate action"
    }
    
    # Probar diferentes acciones
    action_sets = [
        ["send_alert"],
        ["create_ticket"],
        ["execute_script"],
        ["log_event"],
        ["send_alert", "create_ticket", "execute_script"],
        ["log_event", "flag_for_review"]
    ]
    
    for actions in action_sets:
        print(f"\n--- Testing actions: {actions} ---")
        results = executor.execute_actions(actions, context)
        
        for result in results:
            status = "OK" if result.result.value == "SUCCESS" else "ERROR"
            print(f"{status} {result.action_name}: {result.message}")

def test_integration():
    """Probar integración completa del sistema."""
    print("\nTesting Full Integration...")
    
    # Inicializar componentes
    engine = DecisionEngine()
    executor = ActionExecutor()
    initialize_tools(engine, executor)
    
    # Eventos de prueba para integración
    events = [
        {
            "event_type": "SECURITY_BREACH",
            "severity": "HIGH",
            "resource": "auth-server",
            "time_to_impact": 1,
            "business_impact": "CRITICAL",
            "confidence": 0.98
        },
        {
            "event_type": "DISK_SPACE_LOW",
            "severity": "MEDIUM",
            "resource": "file-server-02",
            "time_to_impact": 45,
            "business_impact": "MEDIUM",
            "confidence": 0.85
        },
        {
            "event_type": "SERVICE_DEGRADED",
            "severity": "LOW",
            "resource": "api-gateway",
            "time_to_impact": 200,
            "business_impact": "LOW",
            "confidence": 0.6
        }
    ]
    
    for i, event in enumerate(events, 1):
        print(f"\n--- Integration Test {i}: {event['event_type']} ---")
        
        # Procesar evento usando herramientas
        event_json = json.dumps(event)
        result_json = process_event(event_json)
        result = json.loads(result_json)
        
        print(f"Decision: {result['decision']}")
        print(f"Score: {result['score']:.2f}")
        print(f"Status: {result['status']}")
        print(f"Actions executed: {result['actions_executed']}")
        
        # Mostrar resultados de acciones
        if 'action_results' in result:
            for action_result in result['action_results']:
                status = "OK" if action_result['result'] == 'SUCCESS' else "ERROR"
                print(f"  {status} {action_result['action']}: {action_result['message']}")

def test_decision_history():
    """Probar funcionalidad de historial de decisiones."""
    print("\nTesting Decision History...")
    
    # Inicializar componentes
    engine = DecisionEngine()
    executor = ActionExecutor()
    initialize_tools(engine, executor)
    
    # Procesar varios eventos
    events = [
        {
            "event_type": "EVENT_1",
            "severity": "HIGH",
            "resource": "resource-1",
            "time_to_impact": 5,
            "business_impact": "CRITICAL",
            "confidence": 0.9
        },
        {
            "event_type": "EVENT_2",
            "severity": "MEDIUM",
            "resource": "resource-2",
            "time_to_impact": 30,
            "business_impact": "MEDIUM",
            "confidence": 0.8
        },
        {
            "event_type": "EVENT_3",
            "severity": "LOW",
            "resource": "resource-3",
            "time_to_impact": 120,
            "business_impact": "LOW",
            "confidence": 0.7
        }
    ]
    
    # Procesar eventos
    for event in events:
        event_json = json.dumps(event)
        process_event(event_json)
    
    # Obtener historial
    history_json = get_decision_history(5)
    history = json.loads(history_json)
    
    print(f"History entries: {history['count']}")
    for entry in history['history']:
        print(f"  - {entry['decision']} (score: {entry['score']:.2f}): {entry['reasoning']}")

def test_risk_calculation():
    """Probar cálculo de riesgo con desglose."""
    print("\nTesting Risk Calculation...")
    
    # Inicializar componentes
    engine = DecisionEngine()
    executor = ActionExecutor()
    initialize_tools(engine, executor)
    
    # Evento de prueba
    event = {
        "event_type": "COMPLEX_EVENT",
        "severity": "HIGH",
        "resource": "critical-resource",
        "time_to_impact": 10,
        "business_impact": "CRITICAL",
        "confidence": 0.85
    }
    
    # Calcular riesgo
    event_json = json.dumps(event)
    risk_json = calculate_risk_score(event_json)
    risk_result = json.loads(risk_json)
    
    print(f"Full response: {json.dumps(risk_result, indent=2)}")
    print(f"Risk Score: {risk_result['score']:.2f}")
    if 'expected_decision' in risk_result:
        print(f"Expected Decision: {risk_result['expected_decision']}")
    else:
        print("Expected Decision: Not available in response")
    if 'breakdown' in risk_result:
        print(f"Breakdown:")
        breakdown = risk_result['breakdown']
        print(f"  - Severity Weight: {breakdown['severity_weight']}")
        print(f"  - Impact Weight: {breakdown['impact_weight']}")
        print(f"  - Urgency Weight: {breakdown['urgency_weight']}")
        print(f"  - Confidence Factor: {breakdown['confidence_factor']}")
        print(f"  - Thresholds: {breakdown['thresholds']}")
    else:
        print("Breakdown: Not available in response")

def main():
    """Ejecutar todas las pruebas."""
    print("Executor Agent Test Suite")
    print("=" * 50)
    
    try:
        # Ejecutar pruebas
        test_decision_engine()
        test_action_system()
        test_integration()
        test_decision_history()
        test_risk_calculation()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        
    except Exception as e:
        print(f"\nTest failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
