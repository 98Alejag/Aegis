"""
Sistema de Acciones para Executor Agent.
Implementa acciones desacopladas para cada tipo de decisión.
"""

import logging
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ActionResult(Enum):
    """Resultados posibles de una acción."""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"
    SKIPPED = "SKIPPED"

@dataclass
class ActionExecution:
    """Resultado de ejecución de una acción."""
    action_name: str
    result: ActionResult
    message: str
    timestamp: float
    details: Optional[Dict[str, Any]] = None

class Action(ABC):
    """
    Clase base abstracta para todas las acciones.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> ActionExecution:
        """
        Ejecutar la acción con el contexto proporcionado.
        
        Args:
            context: Contexto de ejecución (evento, decisión, etc.)
            
        Returns:
            Resultado de la ejecución
        """
        pass
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        Validar que el contexto tenga los datos necesarios.
        
        Args:
            context: Contexto a validar
            
        Returns:
            True si el contexto es válido
        """
        return True

class SendAlertAction(Action):
    """Acción para enviar alertas."""
    
    def __init__(self):
        super().__init__("send_alert")
    
    def execute(self, context: Dict[str, Any]) -> ActionExecution:
        """Enviar alerta basada en el evento."""
        try:
            event = context.get("event", {})
            decision = context.get("decision", {})
            score = context.get("score", 0)
            
            # Simular envío de alerta
            alert_data = {
                "alert_type": "SYSTEM_ALERT",
                "event_type": event.get("event_type", "UNKNOWN"),
                "resource": event.get("resource", "UNKNOWN"),
                "severity": event.get("severity", "UNKNOWN"),
                "decision": decision.value if hasattr(decision, 'value') else str(decision),
                "risk_score": score,
                "timestamp": time.time(),
                "message": f"Alert: {event.get('event_type')} detected on {event.get('resource')}"
            }
            
            # Simular llamada a sistema de alertas
            self.logger.info(f"🚨 ALERT SENT: {json.dumps(alert_data, indent=2)}")
            
            return ActionExecution(
                action_name=self.name,
                result=ActionResult.SUCCESS,
                message=f"Alert sent for {event.get('event_type')} on {event.get('resource')}",
                timestamp=time.time(),
                details={"alert_data": alert_data}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send alert: {str(e)}")
            return ActionExecution(
                action_name=self.name,
                result=ActionResult.FAILURE,
                message=f"Alert failed: {str(e)}",
                timestamp=time.time()
            )

class CreateTicketAction(Action):
    """Acción para crear tickets de incidencia."""
    
    def __init__(self):
        super().__init__("create_ticket")
    
    def execute(self, context: Dict[str, Any]) -> ActionExecution:
        """Crear ticket basado en el evento."""
        try:
            event = context.get("event", {})
            decision = context.get("decision", {})
            score = context.get("score", 0)
            
            # Simular creación de ticket
            ticket_data = {
                "ticket_id": f"TK-{int(time.time())}",
                "title": f"Incident: {event.get('event_type')} on {event.get('resource')}",
                "description": f"Event detected with risk score {score:.2f}. Decision: {decision.value if hasattr(decision, 'value') else str(decision)}",
                "severity": event.get("severity", "UNKNOWN"),
                "business_impact": event.get("business_impact", "UNKNOWN"),
                "resource": event.get("resource", "UNKNOWN"),
                "status": "OPEN",
                "created_at": time.time(),
                "priority": self._calculate_priority(score)
            }
            
            # Simular llamada a sistema de tickets
            self.logger.info(f"🎫 TICKET CREATED: {json.dumps(ticket_data, indent=2)}")
            
            return ActionExecution(
                action_name=self.name,
                result=ActionResult.SUCCESS,
                message=f"Ticket {ticket_data['ticket_id']} created successfully",
                timestamp=time.time(),
                details={"ticket_data": ticket_data}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create ticket: {str(e)}")
            return ActionExecution(
                action_name=self.name,
                result=ActionResult.FAILURE,
                message=f"Ticket creation failed: {str(e)}",
                timestamp=time.time()
            )
    
    def _calculate_priority(self, score: float) -> str:
        """Calcular prioridad del ticket basada en score."""
        if score >= 80:
            return "CRITICAL"
        elif score >= 50:
            return "HIGH"
        else:
            return "MEDIUM"

class ExecuteScriptAction(Action):
    """Acción para ejecutar scripts de remediación."""
    
    def __init__(self):
        super().__init__("execute_script")
    
    def execute(self, context: Dict[str, Any]) -> ActionExecution:
        """Ejecutar script de remediación."""
        try:
            event = context.get("event", {})
            
            # Simular ejecución de script
            script_data = {
                "script_name": f"remediate_{event.get('event_type', 'unknown').lower()}",
                "target_resource": event.get("resource", "UNKNOWN"),
                "parameters": {
                    "severity": event.get("severity", "UNKNOWN"),
                    "confidence": event.get("confidence", 0.0)
                },
                "execution_id": f"EXEC-{int(time.time())}",
                "started_at": time.time()
            }
            
            # Simular ejecución
            self.logger.info(f"⚡ SCRIPT EXECUTED: {json.dumps(script_data, indent=2)}")
            
            return ActionExecution(
                action_name=self.name,
                result=ActionResult.SUCCESS,
                message=f"Script {script_data['script_name']} executed on {event.get('resource')}",
                timestamp=time.time(),
                details={"script_data": script_data}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to execute script: {str(e)}")
            return ActionExecution(
                action_name=self.name,
                result=ActionResult.FAILURE,
                message=f"Script execution failed: {str(e)}",
                timestamp=time.time()
            )

class LogEventAction(Action):
    """Acción para registrar eventos."""
    
    def __init__(self):
        super().__init__("log_event")
    
    def execute(self, context: Dict[str, Any]) -> ActionExecution:
        """Registrar evento en logs."""
        try:
            event = context.get("event", {})
            decision = context.get("decision", {})
            score = context.get("score", 0)
            
            log_entry = {
                "timestamp": time.time(),
                "event_type": event.get("event_type", "UNKNOWN"),
                "resource": event.get("resource", "UNKNOWN"),
                "severity": event.get("severity", "UNKNOWN"),
                "business_impact": event.get("business_impact", "UNKNOWN"),
                "decision": decision.value if hasattr(decision, 'value') else str(decision),
                "risk_score": score,
                "confidence": event.get("confidence", 0.0)
            }
            
            self.logger.info(f"📋 EVENT LOGGED: {json.dumps(log_entry, indent=2)}")
            
            return ActionExecution(
                action_name=self.name,
                result=ActionResult.SUCCESS,
                message=f"Event logged: {event.get('event_type')} on {event.get('resource')}",
                timestamp=time.time(),
                details={"log_entry": log_entry}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log event: {str(e)}")
            return ActionExecution(
                action_name=self.name,
                result=ActionResult.FAILURE,
                message=f"Event logging failed: {str(e)}",
                timestamp=time.time()
            )

class FlagForReviewAction(Action):
    """Acción para marcar eventos para revisión humana."""
    
    def __init__(self):
        super().__init__("flag_for_review")
    
    def execute(self, context: Dict[str, Any]) -> ActionExecution:
        """Marcar evento para revisión humana."""
        try:
            event = context.get("event", {})
            decision = context.get("decision", {})
            score = context.get("score", 0)
            
            review_data = {
                "review_id": f"RV-{int(time.time())}",
                "event_type": event.get("event_type", "UNKNOWN"),
                "resource": event.get("resource", "UNKNOWN"),
                "reason": "Low confidence",
                "confidence": event.get("confidence", 0.0),
                "risk_score": score,
                "decision": decision.value if hasattr(decision, 'value') else str(decision),
                "status": "PENDING_REVIEW",
                "created_at": time.time()
            }
            
            self.logger.info(f"👁️ FLAGGED FOR REVIEW: {json.dumps(review_data, indent=2)}")
            
            return ActionExecution(
                action_name=self.name,
                result=ActionResult.SUCCESS,
                message=f"Event flagged for human review: {event.get('event_type')}",
                timestamp=time.time(),
                details={"review_data": review_data}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to flag for review: {str(e)}")
            return ActionExecution(
                action_name=self.name,
                result=ActionResult.FAILURE,
                message=f"Review flagging failed: {str(e)}",
                timestamp=time.time()
            )

class LogErrorAction(Action):
    """Acción para registrar errores."""
    
    def __init__(self):
        super().__init__("log_error")
    
    def execute(self, context: Dict[str, Any]) -> ActionExecution:
        """Registrar error en logs."""
        try:
            error_message = context.get("error", "Unknown error")
            event_data = context.get("event", {})
            
            error_entry = {
                "timestamp": time.time(),
                "error_type": "PROCESSING_ERROR",
                "message": error_message,
                "event_data": event_data,
                "severity": "HIGH"
            }
            
            self.logger.error(f"❌ ERROR LOGGED: {json.dumps(error_entry, indent=2)}")
            
            return ActionExecution(
                action_name=self.name,
                result=ActionResult.SUCCESS,
                message=f"Error logged: {error_message}",
                timestamp=time.time(),
                details={"error_entry": error_entry}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log error: {str(e)}")
            return ActionExecution(
                action_name=self.name,
                result=ActionResult.FAILURE,
                message=f"Error logging failed: {str(e)}",
                timestamp=time.time()
            )

class ActionExecutor:
    """
    Ejecutor de acciones que coordina la ejecución de múltiples acciones.
    """
    
    def __init__(self):
        """Inicializar el ejecutor con todas las acciones disponibles."""
        self.logger = logging.getLogger(f"{__name__}.ActionExecutor")
        self.actions: Dict[str, Action] = {
            "send_alert": SendAlertAction(),
            "create_ticket": CreateTicketAction(),
            "execute_script": ExecuteScriptAction(),
            "log_event": LogEventAction(),
            "flag_for_review": FlagForReviewAction(),
            "log_error": LogErrorAction()
        }
    
    def execute_actions(self, action_names: List[str], context: Dict[str, Any]) -> List[ActionExecution]:
        """
        Ejecutar una lista de acciones en orden.
        
        Args:
            action_names: Nombres de acciones a ejecutar
            context: Contexto de ejecución
            
        Returns:
            Lista de resultados de ejecución
        """
        results = []
        
        for action_name in action_names:
            action = self.actions.get(action_name)
            if not action:
                self.logger.warning(f"Action '{action_name}' not found, skipping")
                results.append(ActionExecution(
                    action_name=action_name,
                    result=ActionResult.SKIPPED,
                    message=f"Action '{action_name}' not found",
                    timestamp=time.time()
                ))
                continue
            
            try:
                self.logger.info(f"Executing action: {action_name}")
                result = action.execute(context)
                results.append(result)
                
                if result.result == ActionResult.FAILURE:
                    self.logger.warning(f"Action '{action_name}' failed: {result.message}")
                
            except Exception as e:
                self.logger.error(f"Unexpected error executing '{action_name}': {str(e)}")
                results.append(ActionExecution(
                    action_name=action_name,
                    result=ActionResult.FAILURE,
                    message=f"Unexpected error: {str(e)}",
                    timestamp=time.time()
                ))
        
        return results
    
    def get_available_actions(self) -> List[str]:
        """
        Obtener lista de acciones disponibles.
        
        Returns:
            Lista de nombres de acciones
        """
        return list(self.actions.keys())
