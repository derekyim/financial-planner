"""Multi-agent financial analysis system using LangGraph.

This module implements a supervisor pattern with specialist agents for:
- Information Recall: Understanding model structure and metrics
- Goal Seek: Finding optimal input values to achieve target outputs

Uses LangGraph for orchestration and all 5 memory types for context.
"""

import os
import uuid
from typing import Annotated, Literal, Optional, Any
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
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
    read_model_documentation,
    write_to_audit_log,
)
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
)
from agents.rag_pipeline import retrieve_context


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
    next: Literal["recall", "goal_seek", "strategic", "respond"]
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

def create_supervisor_node(llm: ChatOpenAI):
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
- 'respond': If you can answer directly without specialist help

Respond with the specialist name and your reasoning."""),
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

def model_doc_reader_node(state: FinancialAgentState) -> dict:
    """Read model documentation if not already cached.

    This node runs first to ensure we understand the model structure.
    """
    if state.get("model_documentation"):
        print("[Model Doc Reader] Documentation already cached, skipping.")
        return {}

    print("[Model Doc Reader] Reading model documentation...")
    try:
        doc_content = read_model_documentation.invoke({})
        print(f"[Model Doc Reader] Read {len(doc_content)} characters of documentation.")
        return {"model_documentation": doc_content}
    except Exception as e:
        print(f"[Model Doc Reader] Error reading documentation: {e}")
        return {"model_documentation": f"Error reading documentation: {str(e)}"}


# -----------------------------------------------------------------------------
# Information Recall Agent Node
# -----------------------------------------------------------------------------

def create_recall_agent_node(llm: ChatOpenAI):
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

def create_goal_seek_agent_node(llm: ChatOpenAI):
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

def create_respond_node(llm: ChatOpenAI):
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

Answer the user's question helpfully. If they need detailed analysis, suggest they ask about specific metrics."""

        messages = [SystemMessage(content=system_content)] + state["messages"]
        response = llm.invoke(messages)

        return {"messages": [response]}

    return respond_node


# -----------------------------------------------------------------------------
# Strategic Guidance Agent Node (RAG-powered)
# -----------------------------------------------------------------------------

def create_strategic_guidance_node(llm: ChatOpenAI):
    """Create the Strategic Guidance agent node with RAG.

    Args:
        llm: The LLM to use for the agent.

    Returns:
        The strategic guidance agent node function.
    """
    def strategic_guidance_node(state: FinancialAgentState) -> dict:
        """The strategic guidance agent provides RAG-powered business advice."""
        print("[Strategic Guidance Agent] Processing request...")

        # Get the user's question
        user_question = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_question = msg.content
                break

        # Retrieve relevant context from knowledge base
        print("[Strategic Guidance Agent] Retrieving context from knowledge base...")
        rag_context = retrieve_context(user_question, k=5)
        print(f"[Strategic Guidance Agent] Retrieved context ({len(rag_context)} chars)")

        # Build messages with system prompt, model context, and RAG context
        model_docs = state.get("model_documentation", "")
        system_content = f"""{STRATEGIC_GUIDANCE_PROMPT}

## Current Financial Model Context
{model_docs[:2000] if model_docs else "No financial model loaded."}

## Retrieved Business Knowledge
{rag_context}
"""

        messages = [SystemMessage(content=system_content)] + state["messages"]

        # Call the LLM
        response = llm.invoke(messages)

        print(f"[Strategic Guidance Agent] Generated response.")
        return {"messages": [response]}

    return strategic_guidance_node


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
            Keys: model_documentation, key_drivers_results, main_monthly, tasks, audit_log

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

    # Create LLMs
    supervisor_llm = ChatOpenAI(model=supervisor_model, temperature=0)
    agent_llm = ChatOpenAI(model=agent_model, temperature=0)

    # Create nodes
    supervisor_node = create_supervisor_node(supervisor_llm)
    recall_node = create_recall_agent_node(agent_llm)
    goal_seek_node = create_goal_seek_agent_node(agent_llm)
    strategic_node = create_strategic_guidance_node(agent_llm)
    respond_node = create_respond_node(agent_llm)

    # Create tool nodes
    recall_tool_node = ToolNode(READ_ONLY_TOOLS)
    goal_seek_tool_node = ToolNode(GOAL_SEEK_TOOLS)

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

    # Strategic guidance ends (no tools)
    builder.add_edge("strategic", END)

    # Direct response ends
    builder.add_edge("respond", END)

    # Compile with memory
    return builder.compile(checkpointer=checkpointer, store=store)


# -----------------------------------------------------------------------------
# Convenience Functions
# -----------------------------------------------------------------------------

_agent_instance = None
_current_config = None


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
            - key_drivers_results: Tab with KPIs  
            - main_monthly: Main operations tab (default: "M - Monthly")
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

    return result["messages"][-1].content


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
                    if hasattr(msg, "content") and msg.content:
                        yield msg.content
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        print(f"  Tool calls: {[tc['name'] for tc in msg.tool_calls]}")


# -----------------------------------------------------------------------------
# Main for Testing
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Get credentials path
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    spreadsheet_url = os.getenv(
        "SPREADSHEET_URL",
        "https://docs.google.com/spreadsheets/d/1yopikoACz8oY32Zv9FrGhb64_PlDwcO1e02WePBr4uM/edit"
    )

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
