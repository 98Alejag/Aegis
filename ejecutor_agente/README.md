# Executor Agent

Agente autónomo de toma de decisiones que procesa eventos desde otros agentes y ejecuta acciones basadas en evaluación de riesgo.

## Arquitectura

El executor_agent sigue una arquitectura desacoplada con los siguientes componentes:

### 1. Decision Engine (`decision_engine.py`)
Motor de decisión autónomo que:
- Calcula scores de riesgo basados en severidad, impacto y urgencia
- Toma decisiones usando umbrales configurables
- Maneja baja confianza con revisión humana
- Proporciona trazabilidad completa de decisiones

**Umbrales de Decisión:**
- `score >= 80`: EXECUTE_IMMEDIATE
- `score >= 50`: ALERT_AND_TICKET  
- `score < 50`: LOG_ONLY
- `confidence < 0.7`: REQUIRES_HUMAN_REVIEW

### 2. Action System (`action_system.py`)
Sistema de acciones desacoplado que implementa:
- **SendAlertAction**: Envío de alertas
- **CreateTicketAction**: Creación de tickets
- **ExecuteScriptAction**: Ejecución de scripts de remediación
- **LogEventAction**: Registro de eventos
- **FlagForReviewAction**: Marcado para revisión humana
- **LogErrorAction**: Registro de errores

### 3. Executor Tools (`executor_tools.py`)
Herramientas MCP que exponen la funcionalidad:
- `process_event()`: Procesa eventos y ejecuta decisiones
- `get_decision_history()`: Obtiene historial de decisiones
- `calculate_risk_score()`: Calcula score sin ejecutar acciones
- `get_available_actions()`: Lista acciones disponibles
- `get_decision_thresholds()`: Muestra umbrales configurados

### 4. MCP Server (`mcp_server.py`)
Servidor MCP que expone las herramientas al agente ADK.

## Estructura de Eventos

El executor_agent espera eventos con esta estructura:

```json
{
  "event_type": "string",
  "severity": "LOW" | "MEDIUM" | "HIGH",
  "resource": "string", 
  "time_to_impact": number,
  "business_impact": "LOW" | "MEDIUM" | "CRITICAL",
  "confidence": number
}
```

## Cálculo de Score de Riesgo

El score se calcula usando una fórmula ponderada:

```
score = (severity_weight + impact_weight + urgency_weight) * confidence
```

**Pesos configurables:**
- Severidad: LOW=10, MEDIUM=25, HIGH=40
- Impacto: LOW=10, MEDIUM=25, CRITICAL=40
- Urgencia: Máximo 20 (basado en tiempo hasta impacto)

## Flujo de Decisión

1. **Validación**: Verificar confianza mínima (0.7)
2. **Cálculo**: Calcular score de riesgo
3. **Decisión**: Aplicar umbrales configurados
4. **Acciones**: Ejecutar acciones correspondientes
5. **Registro**: Guardar decisión y resultados

## Respuesta Estructurada

El executor_agent siempre devuelve respuestas con esta estructura:

```json
{
  "decision": "EXECUTE_IMMEDIATE | ALERT_AND_TICKET | LOG_ONLY | REQUIRES_HUMAN_REVIEW",
  "score": number,
  "actions_executed": ["action1", "action2"],
  "action_results": [
    {
      "action": "string",
      "result": "SUCCESS | FAILURE | PARTIAL | SKIPPED",
      "message": "string",
      "timestamp": number
    }
  ],
  "status": "completed | error",
  "reasoning": "string",
  "timestamp": number
}
```

## Ejemplos de Uso

### Evento Crítico
```json
{
  "event_type": "SYSTEM_FAILURE",
  "severity": "HIGH",
  "resource": "database-primary", 
  "time_to_impact": 2,
  "business_impact": "CRITICAL",
  "confidence": 0.95
}
```
**Resultado**: EXECUTE_IMMEDIATE (score: 95.0)
**Acciones**: send_alert, create_ticket, execute_script

### Evento Medio
```json
{
  "event_type": "CPU_HIGH",
  "severity": "MEDIUM", 
  "resource": "web-server-01",
  "time_to_impact": 25,
  "business_impact": "MEDIUM",
  "confidence": 0.8
}
```
**Resultado**: ALERT_AND_TICKET (score: 51.2)
**Acciones**: send_alert, create_ticket

### Baja Confianza
```json
{
  "event_type": "MEMORY_WARNING",
  "severity": "LOW",
  "resource": "cache-server",
  "time_to_impact": 180, 
  "business_impact": "LOW",
  "confidence": 0.4
}
```
**Resultado**: REQUIRES_HUMAN_REVIEW (score: 8.8)
**Acciones**: log_event, flag_for_review

## Configuración

### Variables de Entorno
- `EXECUTOR_MCP_SERVER_URL`: URL del servidor MCP (default: http://localhost:8082/mcp)
- `A2A_HOST`: Host para agente A2A (default: localhost)
- `A2A_PORT_ASSISTANT`: Puerto para agente A2A (default: 10002)

### Umbrales Configurables
Se pueden modificar en `decision_engine.py`:
- `IMMEDIATE_THRESHOLD`: Umbral para ejecución inmediata (default: 80.0)
- `ALERT_THRESHOLD`: Umbral para alerta y ticket (default: 50.0)
- `CONFIDENCE_THRESHOLD`: Umbral de confianza mínima (default: 0.7)

## Pruebas

Ejecutar el suite de pruebas completo:

```bash
cd ejecutor_agente
python test_executor.py
```

Las pruebas validan:
- Motor de decisión con diferentes escenarios
- Sistema de acciones individual y combinado
- Integración completa del flujo
- Historial de decisiones
- Cálculo de riesgo con desglose

## Integración A2A

El executor_agent mantiene la compatibilidad con la arquitectura A2A existente:

- Se expone como agente A2A en el puerto configurado
- Define skills específicas para procesamiento de eventos
- Interactúa con otros agentes a través del protocolo A2A
- Proporciona respuestas estructuradas al orquestador

## Características Clave

✅ **Autonomía**: Toma decisiones sin intervención humana  
✅ **Trazabilidad**: Registra cada decisión con razonamiento completo  
✅ **Configurabilidad**: Umbrales y pesos ajustables  
✅ **Desacoplamiento**: Componentes independientes y reutilizables  
✅ **Escalabilidad**: Arquitectura modular para fácil extensión  
✅ **Seguridad**: Manejo de baja confianza con revisión humana  
✅ **Auditabilidad**: Historial completo para cumplimiento  

## Uso en Demostraciones

El executor_agent está diseñado para ser fácil de demostrar:

1. **Eventos Simples**: Probar con diferentes tipos de eventos
2. **Decisiones Explicables**: Cada decisión incluye razonamiento claro
3. **Acciones Visibles**: Las acciones se registran con resultados detallados
4. **Configuración Dinámica**: Los umbrales pueden ajustarse en tiempo real
5. **Historial Completo**: Se puede consultar el historial de decisiones recientes
