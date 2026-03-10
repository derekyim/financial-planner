"""Multi-agent financial analysis system using LangGraph.

This module implements a supervisor pattern with specialist agents for:
- Information Recall: Understanding model structure and metrics
- Goal Seek: Finding optimal input values to achieve target outputs

Uses LangGraph for orchestration and all 5 memory types for context.
"""

import os
import uuid
import warnings
from typing import Annotated, Literal, Optional, Any
from typing_extensions import TypedDict

warnings.filterwarnings("ignore", message="Pydantic serializer warnings")

from langchain_openai import OpenAIEmbeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

from agents.tools import (
    initialize_tools,
    READ_ONLY_TOOLS,
    GOAL_SEEK_TOOLS,
    ALL_TOOLS,
    VARIANCE_TOOLS,
    read_model_documentation,
    write_to_audit_log,
)
from agents.strategic_tools import STRATEGIC_TOOLS
from agents.presentation_tools import PRESENTATION_TOOLS, initialize_presentation_tools
from agents.memory_types import (
    ShortTermMemory,
    LongTermMemory,
    SemanticMemory,
    EpisodicMemory,
    ProceduralMemory,
)
from agents.playbooks import (
    PLANNER_SYSTEM_PROMPT,
    RECALL_AGENT_PROMPT,
    GOAL_SEEK_AGENT_PROMPT,
    STRATEGIC_GUIDANCE_PROMPT,
    PRESENTATION_AGENT_PROMPT,
    VARIANCE_AGENT_PROMPT,
)
from agents.rag_pipeline import retrieve_context
from agents.llm_factory import create_llm


# -----------------------------------------------------------------------------
# State Definition
# -----------------------------------------------------------------------------

class FinancialAgentState(TypedDict):
    """State for the financial analysis multi-agent system.

    Attributes:
        messages: Conversation history (short-term memory via checkpointer).
        user_id: Unique identifier for the user.
        model_url: URL of the Google Sheet financial model.
        next: The next agent to route to.
        model_documentation: Cached model documentation (read once).
    """
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    model_url: str
    next: str
    model_documentation: str


# -----------------------------------------------------------------------------
# Router Output (Structured Output for Supervisor)
# -----------------------------------------------------------------------------

class RouterOutput(BaseModel):
    """The supervisor's routing decision."""
    next: Literal["recall", "goal_seek", "strategic", "presentation", "variance", "respond"]
    reasoning: str


# -----------------------------------------------------------------------------
# Memory Store Setup
# -----------------------------------------------------------------------------

def create_memory_store(with_embeddings: bool = True) -> InMemoryStore:
    """Create a memory store for the agent.

    Args:
        with_embeddings: Whether to enable embedding-based search.

    Returns:
        Configured InMemoryStore instance.
    """
    if with_embeddings:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        return InMemoryStore(
            index={
                "dims": 1536,
                "embed": embeddings,
            }
        )
    return InMemoryStore()


def initialize_memory_store(store: BaseStore) -> None:
    """Initialize memory store with default data.

    Args:
        store: The memory store to initialize.
    """
    # Initialize procedural memory with default playbooks
    procedural = ProceduralMemory(store)
    procedural.initialize_default_playbooks()


# -----------------------------------------------------------------------------
# Supervisor/Planner Node
# -----------------------------------------------------------------------------

def create_supervisor_node(llm: BaseChatModel):
    """Create the supervisor node that routes to specialist agents.

    Args:
        llm: The LLM to use for routing decisions.

    Returns:
        The supervisor node function.
    """
    supervisor_prompt = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM_PROMPT),
        ("human", """User question: {question}

Current model documentation has been read: {has_docs}

Based on this question, which specialist should handle it?
- 'recall': For questions about metrics, formulas, model structure
- 'goal_seek': For optimization, achieving targets, finding solutions
- 'strategic': For business strategy advice, industry best practices, how to improve operations
- 'presentation': For creating slide decks and presentations
- 'variance': For variance analysis comparing the current model against another model
- 'respond': If you can answer directly without specialist help

DO NOT RESPOND WITH ANYTHING OTHER THAN THE SPECIALIST NAME AND YOUR REASONING."""),
    ])

    routing_llm = llm.with_structured_output(RouterOutput)

    def supervisor_node(state: FinancialAgentState) -> dict:
        """The supervisor decides which agent to route to."""
        # Get the user's question from the last human message
        user_question = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_question = msg.content
                break

        has_docs = bool(state.get("model_documentation"))

        # Get routing decision
        prompt_value = supervisor_prompt.invoke({
            "question": user_question,
            "has_docs": "Yes" if has_docs else "No",
        })
        result = routing_llm.invoke(prompt_value)

        print(f"[Supervisor] Routing to: {result.next}")
        print(f"  Reason: {result.reasoning}")

        return {"next": result.next}

    return supervisor_node


# -----------------------------------------------------------------------------
# Model Documentation Reader Node
# -----------------------------------------------------------------------------

_model_doc_cache: dict = {"url": None, "content": None}


def model_doc_reader_node(state: FinancialAgentState) -> dict:
    """Read model documentation, using a module-level cache per spreadsheet URL.

    The LangGraph initial state always sends model_documentation="" which
    overwrites the checkpointed value, so we cache at the module level instead.
    """
    from agents.tools import get_spreadsheet_url
    try:
        current_url = get_spreadsheet_url()
    except RuntimeError:
        current_url = None

    if (_model_doc_cache["content"]
            and _model_doc_cache["url"] == current_url):
        print("[Model Doc Reader] Using cached documentation (no API call).")
        return {"model_documentation": _model_doc_cache["content"]}

    print("[Model Doc Reader] Reading model documentation...")
    try:
        doc_content = read_model_documentation.invoke({})
        print(f"[Model Doc Reader] Read {len(doc_content)} characters of documentation.")
        _model_doc_cache["url"] = current_url
        _model_doc_cache["content"] = doc_content
        return {"model_documentation": doc_content}
    except Exception as e:
        print(f"[Model Doc Reader] Error reading documentation: {e}")
        return {"model_documentation": f"Error reading documentation: {str(e)}"}


# -----------------------------------------------------------------------------
# Information Recall Agent Node
# -----------------------------------------------------------------------------

def create_recall_agent_node(llm: BaseChatModel):
    """Create the Information Recall agent node.

    Args:
        llm: The LLM to use for the agent.

    Returns:
        The recall agent node function.
    """
    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(READ_ONLY_TOOLS)

    def recall_agent_node(state: FinancialAgentState) -> dict:
        """The recall agent answers questions about the model."""
        print("[Recall Agent] Processing request...")

        # Build messages with system prompt and model context
        model_docs = state.get("model_documentation", "")
        system_content = f"""{RECALL_AGENT_PROMPT}

## Current Model Documentation
{model_docs[:4000]}  # Truncate if too long
"""

        messages = [SystemMessage(content=system_content)] + state["messages"]

        # Call the LLM
        response = llm_with_tools.invoke(messages)

        print(f"[Recall Agent] Generated response.")
        return {"messages": [response]}

    return recall_agent_node


# -----------------------------------------------------------------------------
# Goal Seek Agent Node
# -----------------------------------------------------------------------------

def create_goal_seek_agent_node(llm: BaseChatModel):
    """Create the Goal Seek agent node.

    Args:
        llm: The LLM to use for the agent.

    Returns:
        The goal seek agent node function.
    """
    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(GOAL_SEEK_TOOLS)

    def goal_seek_agent_node(state: FinancialAgentState) -> dict:
        """The goal seek agent finds optimal input values."""
        print("[Goal Seek Agent] Processing optimization request...")

        # Build messages with system prompt and model context
        model_docs = state.get("model_documentation", "")
        system_content = f"""{GOAL_SEEK_AGENT_PROMPT}

## Current Model Documentation
{model_docs[:4000]}  # Truncate if too long
"""

        messages = [SystemMessage(content=system_content)] + state["messages"]

        # Call the LLM
        response = llm_with_tools.invoke(messages)

        print(f"[Goal Seek Agent] Generated response.")
        return {"messages": [response]}

    return goal_seek_agent_node


# -----------------------------------------------------------------------------
# Direct Response Node (for simple queries)
# -----------------------------------------------------------------------------

def create_respond_node(llm: BaseChatModel):
    """Create a direct response node for simple queries.

    Args:
        llm: The LLM to use.

    Returns:
        The respond node function.
    """
    def respond_node(state: FinancialAgentState) -> dict:
        """Respond directly without specialist agents."""
        print("[Respond] Generating direct response...")

        model_docs = state.get("model_documentation", "")
        system_content = f"""You are a helpful financial analysis assistant.

## Model Context
{model_docs[:2000] if model_docs else "No model documentation loaded yet."}

Answer the user's question helpfully. If they need detailed analysis, suggest they ask about specific metrics.

Never include raw tool output, column letters, row numbers, cell references, or pipe-delimited data in your response. Present insights in plain business language."""

        messages = [SystemMessage(content=system_content)] + state["messages"]
        response = llm.invoke(messages)

        return {"messages": [response]}

    return respond_node


# -----------------------------------------------------------------------------
# Strategic Guidance Agent Node (RAG-powered)
# -----------------------------------------------------------------------------

def create_strategic_guidance_node(llm: BaseChatModel, tools: list):
    """Create the Strategic Guidance agent node with RAG + web search.

    Args:
        llm: The LLM to use for the agent.
        tools: Tools available to this agent (includes Tavily web search).

    Returns:
        The strategic guidance agent node function.
    """
    llm_with_tools = llm.bind_tools(tools)

    def strategic_guidance_node(state: FinancialAgentState) -> dict:
        """The strategic guidance agent provides RAG-powered business advice."""
        print("[Strategic Guidance Agent] Processing request...")

        user_question = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_question = msg.content
                break

        print("[Strategic Guidance Agent] Retrieving context from knowledge base...")
        rag_context = retrieve_context(user_question, k=5)
        print(f"[Strategic Guidance Agent] Retrieved context ({len(rag_context)} chars)")

        from datetime import date
        today = date.today().isoformat()

        model_docs = state.get("model_documentation", "")
        system_content = f"""{STRATEGIC_GUIDANCE_PROMPT}

## Current Financial Model Context
{model_docs[:2000] if model_docs else "No financial model loaded."}

## Retrieved Business Knowledge
{rag_context}

## IMPORTANT: Today's date is {today}.
Your training data is outdated. For ANY question about recent events, trends, or current practices, you MUST call the web_search tool FIRST before responding. The tool automatically restricts to the last 90 days. Do not answer from memory when current data is available.

DO NOT RESPOND WITH ANYTHING OTHER THAN THE STRATEGIC GUIDANCE AND YOUR REASONING.
DO NOT RESPOND WITH IF YOU ARE SEARCHING THE LAST 90 DAYS OF DATA.
"""

        messages = [SystemMessage(content=system_content)] + state["messages"]
        response = llm_with_tools.invoke(messages)

        print(f"[Strategic Guidance Agent] Generated response.")
        return {"messages": [response]}

    return strategic_guidance_node


# -----------------------------------------------------------------------------
# Presentation Agent Node
# -----------------------------------------------------------------------------

def create_presentation_node(llm: BaseChatModel, tools: list):
    """Create the Presentation agent node.

    Args:
        llm: The LLM to use for the agent.
        tools: Presentation tools (add_title_slide, add_content_slide, etc.).

    Returns:
        The presentation agent node function.
    """
    llm_with_tools = llm.bind_tools(tools)

    def presentation_node(state: FinancialAgentState) -> dict:
        """The presentation agent creates slides from conversation insights."""
        print("[Presentation Agent] Processing request...")

        model_docs = state.get("model_documentation", "")

        conversation_summary = []
        for msg in state["messages"]:
            if isinstance(msg, HumanMessage):
                conversation_summary.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage) and msg.content:
                text = _extract_text(msg.content)
                if text and not (hasattr(msg, "tool_calls") and msg.tool_calls):
                    conversation_summary.append(f"Assistant: {text[:500]}")

        conv_text = "\n".join(conversation_summary[-10:])

        system_content = f"""{PRESENTATION_AGENT_PROMPT}

## Current Model Documentation
{model_docs[:2000] if model_docs else "No model documentation loaded."}

## Conversation Context
{conv_text}
"""

        messages = [SystemMessage(content=system_content)] + state["messages"]
        response = llm_with_tools.invoke(messages)

        print("[Presentation Agent] Generated response.")
        return {"messages": [response]}

    return presentation_node


# -----------------------------------------------------------------------------
# Variance Analysis Agent Node
# -----------------------------------------------------------------------------

def create_variance_agent_node(llm: BaseChatModel, tools: list):
    """Create the Variance Analysis agent node.

    Args:
        llm: The LLM to use for the agent.
        tools: Variance analysis tools (read, write, switch_model, etc.).

    Returns:
        The variance agent node function.
    """
    llm_with_tools = llm.bind_tools(tools)

    def variance_agent_node(state: FinancialAgentState) -> dict:
        """The variance agent compares models and populates the Variance tab."""
        print("[Variance Agent] Processing request...")

        model_docs = state.get("model_documentation", "")
        system_content = f"""{VARIANCE_AGENT_PROMPT}

## Current Model Documentation
{model_docs[:2000] if model_docs else "No model documentation loaded."}
"""

        messages = [SystemMessage(content=system_content)] + state["messages"]
        response = llm_with_tools.invoke(messages)

        print("[Variance Agent] Generated response.")
        return {"messages": [response]}

    return variance_agent_node


# -----------------------------------------------------------------------------
# Routing Logic
# -----------------------------------------------------------------------------

def should_continue_after_agent(state: FinancialAgentState) -> Literal["tools", "end"]:
    """Determine if we need to execute tools or end."""
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"


def route_after_supervisor(state: FinancialAgentState) -> str:
    """Route based on supervisor decision."""
    next_agent = state.get("next", "")
    return next_agent if next_agent else "respond"


# -----------------------------------------------------------------------------
# Build the Graph
# -----------------------------------------------------------------------------

def create_financial_agent(
    credentials_path: str,
    spreadsheet_url: str,
    store: Optional[BaseStore] = None,
    checkpointer: Optional[MemorySaver] = None,
    supervisor_model: str = "gpt-4o",
    agent_model: str = "gpt-4o-mini",
    tab_names: Optional[dict] = None,
) -> StateGraph:
    """Create the financial analysis multi-agent system.

    Args:
        credentials_path: Path to Google service account JSON.
        spreadsheet_url: URL of the Google Sheet to analyze.
        store: Optional memory store. Creates one if not provided.
        checkpointer: Optional checkpointer. Creates one if not provided.
        supervisor_model: Model to use for supervisor (default: gpt-4o).
        agent_model: Model to use for specialist agents (default: gpt-4o-mini).
        tab_names: Optional dict to configure tab names for the spreadsheet.
            Keys: model_documentation, business_levers_outcomes, main_monthly, tasks, audit_log

    Returns:
        Compiled LangGraph for the financial agent.
    """
    # Initialize tools with credentials and tab configuration
    initialize_tools(credentials_path, spreadsheet_url, tab_names=tab_names)

    # Create memory components
    if store is None:
        store = create_memory_store(with_embeddings=True)
        initialize_memory_store(store)

    if checkpointer is None:
        checkpointer = MemorySaver()

    # Create LLMs via factory (resolves provider from model name prefix)
    supervisor_llm = create_llm(supervisor_model, temperature=0)
    agent_llm = create_llm(agent_model, temperature=0)

    # Create nodes
    supervisor_node = create_supervisor_node(supervisor_llm)
    recall_node = create_recall_agent_node(agent_llm)
    goal_seek_node = create_goal_seek_agent_node(agent_llm)
    strategic_node = create_strategic_guidance_node(agent_llm, STRATEGIC_TOOLS)
    presentation_node = create_presentation_node(agent_llm, PRESENTATION_TOOLS)
    variance_node = create_variance_agent_node(agent_llm, VARIANCE_TOOLS)
    respond_node = create_respond_node(agent_llm)

    # Create tool nodes
    recall_tool_node = ToolNode(READ_ONLY_TOOLS)
    goal_seek_tool_node = ToolNode(GOAL_SEEK_TOOLS)
    strategic_tool_node = ToolNode(STRATEGIC_TOOLS)
    presentation_tool_node = ToolNode(PRESENTATION_TOOLS)
    variance_tool_node = ToolNode(VARIANCE_TOOLS)

    # Build the graph
    builder = StateGraph(FinancialAgentState)

    # Add nodes
    builder.add_node("read_model_docs", model_doc_reader_node)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("recall", recall_node)
    builder.add_node("recall_tools", recall_tool_node)
    builder.add_node("goal_seek", goal_seek_node)
    builder.add_node("goal_seek_tools", goal_seek_tool_node)
    builder.add_node("strategic", strategic_node)
    builder.add_node("strategic_tools", strategic_tool_node)
    builder.add_node("presentation", presentation_node)
    builder.add_node("presentation_tools", presentation_tool_node)
    builder.add_node("variance", variance_node)
    builder.add_node("variance_tools", variance_tool_node)
    builder.add_node("respond", respond_node)

    # Add edges
    # Start by reading model documentation
    builder.add_edge(START, "read_model_docs")
    builder.add_edge("read_model_docs", "supervisor")

    # Supervisor routes to specialists
    builder.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "recall": "recall",
            "goal_seek": "goal_seek",
            "strategic": "strategic",
            "presentation": "presentation",
            "variance": "variance",
            "respond": "respond",
        },
    )

    # Recall agent -> tools -> recall (loop) or end
    builder.add_conditional_edges(
        "recall",
        should_continue_after_agent,
        {"tools": "recall_tools", "end": END},
    )
    builder.add_edge("recall_tools", "recall")

    # Goal seek agent -> tools -> goal_seek (loop) or end
    builder.add_conditional_edges(
        "goal_seek",
        should_continue_after_agent,
        {"tools": "goal_seek_tools", "end": END},
    )
    builder.add_edge("goal_seek_tools", "goal_seek")

    # Strategic guidance agent -> tools -> strategic (loop) or end
    builder.add_conditional_edges(
        "strategic",
        should_continue_after_agent,
        {"tools": "strategic_tools", "end": END},
    )
    builder.add_edge("strategic_tools", "strategic")

    # Presentation agent -> tools -> presentation (loop) or end
    builder.add_conditional_edges(
        "presentation",
        should_continue_after_agent,
        {"tools": "presentation_tools", "end": END},
    )
    builder.add_edge("presentation_tools", "presentation")

    # Variance agent -> tools -> variance (loop) or end
    builder.add_conditional_edges(
        "variance",
        should_continue_after_agent,
        {"tools": "variance_tools", "end": END},
    )
    builder.add_edge("variance_tools", "variance")

    # Direct response ends
    builder.add_edge("respond", END)

    # Compile with memory
    return builder.compile(checkpointer=checkpointer, store=store)


# -----------------------------------------------------------------------------
# Convenience Functions
# -----------------------------------------------------------------------------

_agent_instance = None
_current_config = None


def _extract_text(content) -> str:
    """Normalize message content to a plain string.

    OpenAI returns content as a str, but Anthropic returns a list of
    content blocks like [{"type": "text", "text": "..."}].
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content) if content else ""


def setup_agent(
    credentials_path: str,
    spreadsheet_url: str,
    supervisor_model: str = "gpt-4o",
    agent_model: str = "gpt-4o-mini",
    tab_names: Optional[dict] = None,
) -> None:
    """Set up the global agent instance.

    Args:
        credentials_path: Path to Google service account JSON.
        spreadsheet_url: URL of the Google Sheet to analyze.
        supervisor_model: Model to use for supervisor.
        agent_model: Model to use for specialist agents.
        tab_names: Optional dict to configure tab names. Keys:
            - model_documentation: Tab with model docs
            - business_levers_outcomes: Tab with KPIs  
            - main_monthly: Main operations tab (default: "operations")
            - tasks: Tasks tab
            - audit_log: Audit log tab
    """
    global _agent_instance, _current_config
    _agent_instance = create_financial_agent(
        credentials_path=credentials_path,
        spreadsheet_url=spreadsheet_url,
        supervisor_model=supervisor_model,
        agent_model=agent_model,
        tab_names=tab_names,
    )
    _current_config = {
        "spreadsheet_url": spreadsheet_url,
    }
    print("Financial agent initialized successfully!")

    try:
        initialize_presentation_tools(credentials_path)
        print("[Presentation] Slides tools initialized.")
    except Exception as e:
        print(f"[Presentation] Failed to initialize slides: {e}")

    _load_calc_engine(credentials_path, spreadsheet_url)


def _load_calc_engine(credentials_path: str, spreadsheet_url: str) -> None:
    """Export the operations tab and load it into the HyperFormula calc engine."""
    from agents import calc_client
    from agents.tools import get_tab_name

    if not calc_client.is_available():
        print("[CalcEngine] Service not running — skipping model load. "
              "Goal Seek will fall back to live spreadsheet writes.")
        return

    try:
        from shared.sheets_utilities import SheetsUtilities
        sheets = SheetsUtilities(credentials_path)
        main_tab = get_tab_name("main_monthly")
        print(f"[CalcEngine] Exporting '{main_tab}' tab with formulas...")
        sid = sheets._extract_spreadsheet_id(spreadsheet_url)
        wb = sheets.client.open_by_key(sid)
        ws = wb.worksheet(main_tab)
        formulas = ws.get_all_values(value_render_option='FORMULA')
        tab_data = [{"name": main_tab, "data": formulas}]
        print(f"[CalcEngine] Exported 1 tab ({len(formulas)} rows), sending to calc engine...")
        result = calc_client.load_model(tab_data)
        print(f"[CalcEngine] Loaded: {result.get('sheets')} sheets, "
              f"{result.get('cells')} cells")
    except Exception as e:
        print(f"[CalcEngine] Failed to load model: {e}. "
              "Goal Seek will fall back to live spreadsheet writes.")


def chat(
    message: str,
    user_id: str = "default_user",
    thread_id: Optional[str] = None,
) -> str:
    """Chat with the financial analysis agent.

    Args:
        message: The user's message.
        user_id: User identifier for memory.
        thread_id: Conversation thread ID. Auto-generated if not provided.

    Returns:
        The agent's response.
    """
    if _agent_instance is None:
        raise RuntimeError("Agent not initialized. Call setup_agent() first.")

    if thread_id is None:
        thread_id = str(uuid.uuid4())

    config = {"configurable": {"thread_id": thread_id}}

    result = _agent_instance.invoke(
        {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "model_url": _current_config.get("spreadsheet_url", ""),
            "next": "",
            "model_documentation": "",
        },
        config,
    )

    return _extract_text(result["messages"][-1].content)


def chat_stream(
    message: str,
    user_id: str = "default_user",
    thread_id: Optional[str] = None,
):
    """Stream chat with the financial analysis agent.

    Args:
        message: The user's message.
        user_id: User identifier for memory.
        thread_id: Conversation thread ID.

    Yields:
        Chunks of the agent's response.
    """
    if _agent_instance is None:
        raise RuntimeError("Agent not initialized. Call setup_agent() first.")

    if thread_id is None:
        thread_id = str(uuid.uuid4())

    config = {"configurable": {"thread_id": thread_id}}

    for chunk in _agent_instance.stream(
        {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "model_url": _current_config.get("spreadsheet_url", ""),
            "next": "",
            "model_documentation": "",
        },
        config,
        stream_mode="updates",
    ):
        for node_name, values in chunk.items():
            print(f"\n[{node_name}]")
            if "messages" in values:
                for msg in values["messages"]:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        print(f"  Tool calls: {[tc['name'] for tc in msg.tool_calls]}")
                        continue
                    if not isinstance(msg, AIMessage):
                        continue
                    if hasattr(msg, "content") and msg.content:
                        yield _extract_text(msg.content)


# -----------------------------------------------------------------------------
# Main for Testing
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Get credentials path
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    spreadsheet_url = os.getenv("SPREADSHEET_URL", "")

    print("Financial Analysis Agent")
    print("=" * 50)

    # Initialize
    setup_agent(creds_path, spreadsheet_url)

    # Test recall
    print("\n--- Test 1: Information Recall ---")
    response = chat("What is EBITDA and how is it calculated?")
    print(f"Response: {response}")

    # Test goal seek
    print("\n--- Test 2: Goal Seek ---")
    response = chat("I want to increase EBITDA by 10% while maintaining cash above $1M. What should I do?")
    print(f"Response: {response}")
