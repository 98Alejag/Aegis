import logging
import os
import json
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

from a2a.types import AgentSkill, AgentCard, AgentCapabilities
from decision_engine import DecisionEngine, Event, DecisionResult
from action_system import ActionExecutor
from executor_tools import initialize_tools, process_event, get_decision_history, calculate_risk_score, get_available_actions, get_decision_thresholds

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# A2A configuration
host = os.getenv("A2A_HOST", "localhost")
port = int(os.getenv("A2A_PORT_ASSISTANT", "10002"))

load_dotenv()

SYSTEM_INSTRUCTION = (
    "You are the Executor Agent, an autonomous decision-making system that processes events "
    "from other agents and executes appropriate actions based on risk assessment. "
    ""
    "Your core responsibilities include: "
    "- Receiving events with severity, impact, urgency, and confidence metrics "
    "- Calculating risk scores using a weighted algorithm "
    "- Making decisions based on configurable thresholds "
    "- Executing appropriate actions (alerts, tickets, scripts, logging) "
    "- Providing structured responses with decision reasoning "
    ""
    "Event structure you expect: "
    "{"
    "  'event_type': string,"
    "  'severity': 'LOW' | 'MEDIUM' | 'HIGH',"
    "  'resource': string,"
    "  'time_to_impact': number (minutes),"
    "  'business_impact': 'LOW' | 'MEDIUM' | 'CRITICAL',"
    "  'confidence': number (0.0-1.0)"
    "}"
    ""
    "Decision thresholds: "
    "- Score >= 80: EXECUTE_IMMEDIATE (alert + ticket + script) "
    "- Score >= 50: ALERT_AND_TICKET (alert + ticket) "
    "- Score < 50: LOG_ONLY (log event) "
    "- Confidence < 0.7: REQUIRES_HUMAN_REVIEW (flag for review) "
    ""
    "Always provide structured responses with: decision, score, actions_executed, status, and reasoning. "
    "Be precise, autonomous, and maintain clear audit trails of all decisions."
)

logger.info("--- ⚡ Loading Decision Engine and Action System... ---")
logger.info("--- 🤖 Creating ADK Executor Agent... ---")

# Initialize decision engine and action executor
decision_engine = DecisionEngine()
action_executor = ActionExecutor()

# Initialize tools with the engine instances
initialize_tools(decision_engine, action_executor)

root = LlmAgent(
    model="gemini-2.5-flash",
    name="executor_agent",
    description="Autonomous decision-making agent that processes events and executes actions based on risk assessment",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=os.getenv("EXECUTOR_MCP_SERVER_URL", "http://localhost:8082/mcp")
            )
        )
    ],
)

# Define executor-focused skills
process_event_skill = AgentSkill(
    id='process_event',
    name='Event Processing and Decision Making',
    description='Process incoming events, calculate risk scores, and execute appropriate actions based on decision thresholds',
    tags=['event processing', 'decision making', 'risk assessment', 'autonomous actions'],
    examples=[
        'Process this event: {"event_type": "CPU_HIGH", "severity": "HIGH", "resource": "server-01", "time_to_impact": 5, "business_impact": "CRITICAL", "confidence": 0.9}',
        'Handle security alert with medium severity and 30 minutes to impact',
        'Evaluate system failure event with low confidence'
    ],
)

decision_history_skill = AgentSkill(
    id='decision_history',
    name='Decision History and Audit Trail',
    description='Retrieve decision history and audit trails for compliance and analysis',
    tags=['audit trail', 'decision history', 'compliance', 'monitoring'],
    examples=[
        'Show me the last 10 decisions made',
        'Get decision history for critical events',
        'What decisions were made in the last hour?'
    ],
)

risk_assessment_skill = AgentSkill(
    id='risk_assessment',
    name='Risk Assessment and Scoring',
    description='Calculate and explain risk scores for events with detailed breakdown',
    tags=['risk scoring', 'assessment', 'analysis', 'metrics'],
    examples=[
        'Calculate risk score for this event',
        'Explain how risk scores are calculated',
        'What factors influence the decision thresholds?'
    ],
)

# A2A Agent Card definition for Executor Agent
assistant_agent_card = AgentCard(
    name='Executor Agent',
    description='Autonomous decision-making agent that processes events from other agents, calculates risk scores, and executes appropriate actions based on configurable thresholds and business rules',
    url=f'http://{host}:{port}/',
    version='1.0.0',
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[process_event_skill, decision_history_skill, risk_assessment_skill],
)

# Make the agent A2A-compatible
a2a_app = to_a2a(root, port=port)

# ADK expects a variable named 'root_agent'
root_agent = root