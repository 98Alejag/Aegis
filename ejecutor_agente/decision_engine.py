"""
Decision Engine para Executor Agent.
Motor de decisión autónomo basado en score de riesgo.
"""

import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

class DecisionType(Enum):
    """Tipos de decisiones que puede tomar el motor."""
    EXECUTE_IMMEDIATE = "EXECUTE_IMMEDIATE"
    ALERT_AND_TICKET = "ALERT_AND_TICKET"
    LOG_ONLY = "LOG_ONLY"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"

class Severity(Enum):
    """Niveles de severidad de eventos."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class BusinessImpact(Enum):
    """Niveles de impacto de negocio."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    CRITICAL = "CRITICAL"

@dataclass
class Event:
    """Estructura de eventos recibidos por el executor_agent."""
    event_type: str
    severity: Severity
    resource: str
    time_to_impact: float  # en minutos
    business_impact: BusinessImpact
    confidence: float  # 0.0 a 1.0

@dataclass
class DecisionResult:
    """Resultado estructurado de una decisión."""
    decision: DecisionType
    score: float
    actions_executed: List[str]
    status: str
    reasoning: str
    timestamp: float

class DecisionEngine:
    """
    Motor de decisión desacoplado que calcula scores de riesgo
    y toma decisiones basadas en contexto.
    """
    
    # Umbrales de decisión
    IMMEDIATE_THRESHOLD = 80.0
    ALERT_THRESHOLD = 50.0
    CONFIDENCE_THRESHOLD = 0.7
    
    # Pesos para cálculo de score
    SEVERITY_WEIGHTS = {
        Severity.LOW: 10,
        Severity.MEDIUM: 25,
        Severity.HIGH: 40
    }
    
    IMPACT_WEIGHTS = {
        BusinessImpact.LOW: 10,
        BusinessImpact.MEDIUM: 25,
        BusinessImpact.CRITICAL: 40
    }
    
    URGENCY_WEIGHT = 20  # Peso máximo para urgencia
    
    def __init__(self):
        """Inicializar el motor de decisión."""
        self.logger = logging.getLogger(f"{__name__}.DecisionEngine")
        self.decision_history: List[DecisionResult] = []
        
    def calculate_risk_score(self, event: Event) -> float:
        """
        Calcular score de riesgo basado en severidad, impacto y urgencia.
        
        Args:
            event: Evento a evaluar
            
        Returns:
            Score de riesgo (0-100)
        """
        # Puntaje base por severidad
        severity_score = self.SEVERITY_WEIGHTS[event.severity]
        
        # Puntaje base por impacto de negocio
        impact_score = self.IMPACT_WEIGHTS[event.business_impact]
        
        # Puntaje de urgencia basado en tiempo hasta impacto
        # Menos tiempo = más urgente
        if event.time_to_impact <= 5:  # 5 minutos o menos
            urgency_score = self.URGENCY_WEIGHT
        elif event.time_to_impact <= 30:  # 30 minutos
            urgency_score = self.URGENCY_WEIGHT * 0.7
        elif event.time_to_impact <= 120:  # 2 horas
            urgency_score = self.URGENCY_WEIGHT * 0.4
        else:  # más de 2 horas
            urgency_score = self.URGENCY_WEIGHT * 0.1
            
        # Calcular score total (normalizado a 0-100)
        total_score = severity_score + impact_score + urgency_score
        
        # Ajustar por confianza
        adjusted_score = total_score * event.confidence
        
        # Asegurar que esté en rango 0-100
        final_score = max(0, min(100, adjusted_score))
        
        self.logger.info(
            f"Score calculation - Severity: {severity_score}, "
            f"Impact: {impact_score}, Urgency: {urgency_score}, "
            f"Confidence: {event.confidence}, Final: {final_score:.2f}"
        )
        
        return final_score
    
    def make_decision(self, event: Event) -> DecisionType:
        """
        Tomar decisión basada en el score y confianza.
        
        Args:
            event: Evento a evaluar
            
        Returns:
            Tipo de decisión a tomar
        """
        # Verificar confianza primero
        if event.confidence < self.CONFIDENCE_THRESHOLD:
            self.logger.warning(
                f"Low confidence ({event.confidence:.2f}) requires human review"
            )
            return DecisionType.REQUIRES_HUMAN_REVIEW
        
        # Calcular score de riesgo
        score = self.calculate_risk_score(event)
        
        # Tomar decisión basada en umbrales
        if score >= self.IMMEDIATE_THRESHOLD:
            decision = DecisionType.EXECUTE_IMMEDIATE
        elif score >= self.ALERT_THRESHOLD:
            decision = DecisionType.ALERT_AND_TICKET
        else:
            decision = DecisionType.LOG_ONLY
            
        self.logger.info(f"Decision made: {decision.value} (score: {score:.2f})")
        return decision
    
    def get_actions_for_decision(self, decision: DecisionType) -> List[str]:
        """
        Mapear decisión a acciones específicas.
        
        Args:
            decision: Tipo de decisión
            
        Returns:
            Lista de acciones a ejecutar
        """
        action_map = {
            DecisionType.EXECUTE_IMMEDIATE: [
                "send_alert",
                "create_ticket", 
                "execute_script"
            ],
            DecisionType.ALERT_AND_TICKET: [
                "send_alert",
                "create_ticket"
            ],
            DecisionType.LOG_ONLY: [
                "log_event"
            ],
            DecisionType.REQUIRES_HUMAN_REVIEW: [
                "log_event",
                "flag_for_review"
            ]
        }
        
        return action_map.get(decision, [])
    
    def generate_reasoning(self, event: Event, score: float, decision: DecisionType) -> str:
        """
        Generar explicación de la decisión tomada.
        
        Args:
            event: Evento evaluado
            score: Score calculado
            decision: Decisión tomada
            
        Returns:
            Explicación en texto plano
        """
        reasoning_parts = [
            f"Event: {event.event_type} on {event.resource}",
            f"Severity: {event.severity.value}, Impact: {event.business_impact.value}",
            f"Time to impact: {event.time_to_impact}min, Confidence: {event.confidence:.2f}",
            f"Risk score: {score:.2f}"
        ]
        
        if decision == DecisionType.REQUIRES_HUMAN_REVIEW:
            reasoning_parts.append("Low confidence triggered human review requirement")
        elif decision == DecisionType.EXECUTE_IMMEDIATE:
            reasoning_parts.append(f"High score ({score:.2f} >= {self.IMMEDIATE_THRESHOLD}) requires immediate execution")
        elif decision == DecisionType.ALERT_AND_TICKET:
            reasoning_parts.append(f"Medium score ({score:.2f} >= {self.ALERT_THRESHOLD}) requires alert and ticket")
        else:
            reasoning_parts.append(f"Low score ({score:.2f} < {self.ALERT_THRESHOLD}) only requires logging")
            
        return " | ".join(reasoning_parts)
    
    def process_event(self, event_data: Dict[str, Any]) -> DecisionResult:
        """
        Procesar un evento y retornar resultado estructurado.
        
        Args:
            event_data: Diccionario con datos del evento
            
        Returns:
            Resultado estructurado de la decisión
        """
        try:
            # Parsear evento
            event = Event(
                event_type=event_data["event_type"],
                severity=Severity(event_data["severity"]),
                resource=event_data["resource"],
                time_to_impact=float(event_data["time_to_impact"]),
                business_impact=BusinessImpact(event_data["business_impact"]),
                confidence=float(event_data["confidence"])
            )
            
            # Tomar decisión
            decision = self.make_decision(event)
            score = self.calculate_risk_score(event)
            
            # Obtener acciones
            actions = self.get_actions_for_decision(decision)
            
            # Generar explicación
            reasoning = self.generate_reasoning(event, score, decision)
            
            # Crear resultado
            result = DecisionResult(
                decision=decision,
                score=score,
                actions_executed=actions,
                status="completed",
                reasoning=reasoning,
                timestamp=time.time()
            )
            
            # Guardar en historial
            self.decision_history.append(result)
            
            self.logger.info(f"Event processed successfully: {event.event_type}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing event: {str(e)}")
            # Retornar resultado de error
            return DecisionResult(
                decision=DecisionType.LOG_ONLY,
                score=0.0,
                actions_executed=["log_error"],
                status="error",
                reasoning=f"Processing error: {str(e)}",
                timestamp=time.time()
            )
    
    def get_decision_history(self, limit: int = 10) -> List[DecisionResult]:
        """
        Obtener historial de decisiones.
        
        Args:
            limit: Número máximo de decisiones a retornar
            
        Returns:
            Lista de decisiones recientes
        """
        return self.decision_history[-limit:]
