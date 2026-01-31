"""
Servidor MCP para Executor Agent.
Expone las herramientas de procesamiento de eventos y toma de decisiones.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from executor_tools import process_event, get_decision_history, calculate_risk_score, get_available_actions, get_decision_thresholds

logger = logging.getLogger(__name__)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s]: %(message)s"
)

# Crear servidor MCP
server = Server("executor-mcp-server")

@server.list_tools()
async def list_tools() -> List[Tool]:
    """
    Listar todas las herramientas disponibles en el servidor MCP.
    """
    return [
        Tool(
            name="process_event",
            description="Process an event and execute autonomous decisions based on risk assessment",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_data": {
                        "type": "string",
                        "description": "JSON string containing event data with structure: {event_type, severity, resource, time_to_impact, business_impact, confidence}"
                    }
                },
                "required": ["event_data"]
            }
        ),
        Tool(
            name="get_decision_history",
            description="Get decision history and audit trail from the executor agent",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of decisions to return (default: 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="calculate_risk_score",
            description="Calculate risk score for an event without executing actions",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_data": {
                        "type": "string",
                        "description": "JSON string containing event data with structure: {event_type, severity, resource, time_to_impact, business_impact, confidence}"
                    }
                },
                "required": ["event_data"]
            }
        ),
        Tool(
            name="get_available_actions",
            description="Get list of available actions in the executor system",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_decision_thresholds",
            description="Get current decision thresholds and configuration",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Ejecutar una herramienta específica.
    """
    try:
        logger.info(f"Tool called: {name} with arguments: {arguments}")
        
        if name == "process_event":
            event_data = arguments.get("event_data")
            if not event_data:
                return [TextContent(type="text", text=json.dumps({
                    "status": "error",
                    "message": "event_data is required"
                }, indent=2))]
            
            result = process_event(event_data)
            return [TextContent(type="text", text=result)]
            
        elif name == "get_decision_history":
            limit = arguments.get("limit", 10)
            result = get_decision_history(limit)
            return [TextContent(type="text", text=result)]
            
        elif name == "calculate_risk_score":
            event_data = arguments.get("event_data")
            if not event_data:
                return [TextContent(type="text", text=json.dumps({
                    "status": "error",
                    "message": "event_data is required"
                }, indent=2))]
            
            result = calculate_risk_score(event_data)
            return [TextContent(type="text", text=result)]
            
        elif name == "get_available_actions":
            result = get_available_actions()
            return [TextContent(type="text", text=result)]
            
        elif name == "get_decision_thresholds":
            result = get_decision_thresholds()
            return [TextContent(type="text", text=result)]
            
        else:
            return [TextContent(type="text", text=json.dumps({
                "status": "error",
                "message": f"Unknown tool: {name}"
            }, indent=2))]
            
    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}")
        error_result = {
            "status": "error",
            "message": f"Tool execution failed: {str(e)}"
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

async def main():
    """
    Función principal para ejecutar el servidor MCP.
    """
    logger.info("🚀 Starting Executor MCP Server...")
    
    # Ejecutar servidor con stdio
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="executor-mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
