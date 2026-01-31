"""
Herramientas MCP para Executor Agent.
Implementa las funciones que el agente puede usar para procesar eventos y tomar decisiones.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from decision_engine import DecisionEngine, Event, DecisionResult
from action_system import ActionExecutor

logger = logging.getLogger(__name__)

# Instancias globales (se inicializan en agent.py)
decision_engine: Optional[DecisionEngine] = None
action_executor: Optional[ActionExecutor] = None

def initialize_tools(dec_engine: DecisionEngine, act_executor: ActionExecutor):
    """
    Inicializar las herramientas con las instancias del DecisionEngine y ActionExecutor.
    
    Args:
        dec_engine: Instancia del DecisionEngine
        act_executor: Instancia del ActionExecutor
    """
    global decision_engine, action_executor
    decision_engine = dec_engine
    action_executor = act_executor
    logger.info("Executor tools initialized successfully")

def process_event(event_data: str) -> str:
    """
    Procesar un evento y ejecutar acciones basadas en decisión autónoma.
    
    Args:
        event_data: JSON string con datos del evento
        
    Returns:
        JSON string con resultado estructurado de la decisión
    """
    try:
        if not decision_engine or not action_executor:
            return json.dumps({
                "status": "error",
                "message": "Decision engine or action executor not initialized",
                "decision": "LOG_ONLY",
                "score": 0.0,
                "actions_executed": [],
                "reasoning": "System not properly initialized"
            })
        
        # Parsear evento
        event_dict = json.loads(event_data)
        
        # Procesar evento con DecisionEngine
        decision_result = decision_engine.process_event(event_dict)
        
        # Preparar contexto para acciones
        action_context = {
            "event": event_dict,
            "decision": decision_result.decision,
            "score": decision_result.score,
            "reasoning": decision_result.reasoning
        }
        
        # Ejecutar acciones
        action_executions = action_executor.execute_actions(
            decision_result.actions_executed, 
            action_context
        )
        
        # Construir respuesta estructurada
        response = {
            "decision": decision_result.decision.value,
            "score": decision_result.score,
            "actions_executed": [ae.action_name for ae in action_executions],
            "action_results": [
                {
                    "action": ae.action_name,
                    "result": ae.result.value,
                    "message": ae.message,
                    "timestamp": ae.timestamp
                }
                for ae in action_executions
            ],
            "status": decision_result.status,
            "reasoning": decision_result.reasoning,
            "timestamp": decision_result.timestamp
        }
        
        logger.info(f"Event processed: {event_dict.get('event_type')} -> {decision_result.decision.value}")
        return json.dumps(response, indent=2)
        
    except json.JSONDecodeError as e:
        error_response = {
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}",
            "decision": "LOG_ONLY",
            "score": 0.0,
            "actions_executed": ["log_error"],
            "reasoning": f"JSON parsing error: {str(e)}"
        }
        return json.dumps(error_response, indent=2)
        
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
        error_response = {
            "status": "error",
            "message": f"Processing error: {str(e)}",
            "decision": "LOG_ONLY",
            "score": 0.0,
            "actions_executed": ["log_error"],
            "reasoning": f"Unexpected error: {str(e)}"
        }
        return json.dumps(error_response, indent=2)

def get_decision_history(limit: int = 10) -> str:
    """
    Obtener historial de decisiones tomadas por el motor.
    
    Args:
        limit: Número máximo de decisiones a retornar
        
    Returns:
        JSON string con historial de decisiones
    """
    try:
        if not decision_engine:
            return json.dumps({
                "status": "error",
                "message": "Decision engine not initialized",
                "history": []
            })
        
        history = decision_engine.get_decision_history(limit)
        
        # Convertir a formato serializable
        history_data = [
            {
                "decision": dr.decision.value,
                "score": dr.score,
                "actions_executed": dr.actions_executed,
                "status": dr.status,
                "reasoning": dr.reasoning,
                "timestamp": dr.timestamp
            }
            for dr in history
        ]
        
        response = {
            "status": "success",
            "count": len(history_data),
            "history": history_data
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting decision history: {str(e)}")
        error_response = {
            "status": "error",
            "message": f"Failed to get history: {str(e)}",
            "history": []
        }
        return json.dumps(error_response, indent=2)

def calculate_risk_score(event_data: str) -> str:
    """
    Calcular score de riesgo para un evento sin ejecutar acciones.
    
    Args:
        event_data: JSON string con datos del evento
        
    Returns:
        JSON string con desglose del score de riesgo
    """
    try:
        if not decision_engine:
            return json.dumps({
                "status": "error",
                "message": "Decision engine not initialized",
                "score": 0.0
            })
        
        # Parsear evento
        event_dict = json.loads(event_data)
        
        # Crear objeto Event
        from decision_engine import Severity, BusinessImpact
        event = Event(
            event_type=event_dict["event_type"],
            severity=Severity(event_dict["severity"]),
            resource=event_dict["resource"],
            time_to_impact=float(event_dict["time_to_impact"]),
            business_impact=BusinessImpact(event_dict["business_impact"]),
            confidence=float(event_dict["confidence"])
        )
        
        # Calcular score
        score = decision_engine.calculate_risk_score(event)
        
        # Obtener decisión esperada
        decision = decision_engine.make_decision(event)
        
        # Desglose del cálculo
        breakdown = {
            "severity_weight": decision_engine.SEVERITY_WEIGHTS[event.severity],
            "impact_weight": decision_engine.IMPACT_WEIGHTS[event.business_impact],
            "urgency_weight": decision_engine.URGENCY_WEIGHT,
            "confidence_factor": event.confidence,
            "thresholds": {
                "immediate": decision_engine.IMMEDIATE_THRESHOLD,
                "alert": decision_engine.ALERT_THRESHOLD,
                "confidence": decision_engine.CONFIDENCE_THRESHOLD
            }
        }
        
        response = {
            "status": "success",
            "score": score,
            "expected_decision": decision.value,
            "breakdown": breakdown,
            "event": event_dict
        }
        
        return json.dumps(response, indent=2)
        
    except json.JSONDecodeError as e:
        error_response = {
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}",
            "score": 0.0
        }
        return json.dumps(error_response, indent=2)
        
    except KeyError as e:
        error_response = {
            "status": "error",
            "message": f"Missing required field: {str(e)}",
            "score": 0.0
        }
        return json.dumps(error_response, indent=2)
        
    except Exception as e:
        logger.error(f"Error calculating risk score: {str(e)}")
        error_response = {
            "status": "error",
            "message": f"Calculation error: {str(e)}",
            "score": 0.0
        }
        return json.dumps(error_response, indent=2)

def get_available_actions() -> str:
    """
    Obtener lista de acciones disponibles en el sistema.
    
    Returns:
        JSON string con lista de acciones disponibles
    """
    try:
        if not action_executor:
            return json.dumps({
                "status": "error",
                "message": "Action executor not initialized",
                "actions": []
            })
        
        actions = action_executor.get_available_actions()
        
        response = {
            "status": "success",
            "count": len(actions),
            "actions": actions
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting available actions: {str(e)}")
        error_response = {
            "status": "error",
            "message": f"Failed to get actions: {str(e)}",
            "actions": []
        }
        return json.dumps(error_response, indent=2)

def get_decision_thresholds() -> str:
    """
    Obtener umbrales de decisión configurados.
    
    Returns:
        JSON string con umbrales actuales
    """
    try:
        if not decision_engine:
            return json.dumps({
                "status": "error",
                "message": "Decision engine not initialized",
                "thresholds": {}
            })
        
        thresholds = {
            "immediate_threshold": decision_engine.IMMEDIATE_THRESHOLD,
            "alert_threshold": decision_engine.ALERT_THRESHOLD,
            "confidence_threshold": decision_engine.CONFIDENCE_THRESHOLD,
            "severity_weights": {k.value: v for k, v in decision_engine.SEVERITY_WEIGHTS.items()},
            "impact_weights": {k.value: v for k, v in decision_engine.IMPACT_WEIGHTS.items()},
            "urgency_weight": decision_engine.URGENCY_WEIGHT
        }
        
        response = {
            "status": "success",
            "thresholds": thresholds
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting thresholds: {str(e)}")
        error_response = {
            "status": "error",
            "message": f"Failed to get thresholds: {str(e)}",
            "thresholds": {}
        }
        return json.dumps(error_response, indent=2)
