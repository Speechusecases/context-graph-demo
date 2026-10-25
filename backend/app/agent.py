"""
Strands Agents integration with Context Graph tools.

This module replaces the previous Claude Agent SDK implementation with the
open-source Strands Agents SDK. The agent talks to Anthropic directly through
Strands' Anthropic model provider and exposes the same context-graph tools.

The public interface (``ContextGraphAgent`` with ``query`` / ``query_stream``)
and the streaming event contract consumed by the frontend are kept identical,
so no changes to ``main.py`` or the UI are required.
"""

import json
from typing import Any, Optional

from strands import Agent, tool
from strands.models.anthropic import AnthropicModel

from .config import config
from .context_graph_client import context_graph_client
from .gds_client import gds_client
from .vector_client import vector_client

# Model used by the agent. Kept as a module constant so get_agent_context()
# and the model provider stay in sync.
AGENT_MODEL_ID = "claude-sonnet-4-20250514"
AGENT_MAX_TOKENS = 4096

# The frontend displays tool names with this prefix stripped and matches
# tool_use/tool_result events by name. Strands tool names are bare function
# names, so we re-attach this prefix when emitting stream events to preserve
# the existing frontend contract.
TOOL_NAME_PREFIX = "mcp__graph__"


def slim_properties(props: dict) -> dict:
    """Remove large properties to reduce response size."""
    slim = {}
    for key, value in props.items():
        # Skip embedding vectors
        if key in ("fast_rp_embedding", "reasoning_embedding", "embedding"):
            continue
        # Truncate long strings
        if isinstance(value, str) and len(value) > 200:
            slim[key] = value[:200] + "..."
        # Limit list sizes
        elif isinstance(value, list) and len(value) > 10:
            slim[key] = value[:10]
        else:
            slim[key] = value
    return slim


def get_graph_data_for_entity(entity_id: str, depth: int = 2, limit: int = 30) -> dict:
    """Get graph visualization data centered on an entity."""
    try:
        graph_data = context_graph_client.get_graph_data(
            center_node_id=entity_id, depth=depth, limit=limit
        )
        # Build nodes list first
        nodes = [
            {
                "id": node.id,
                "labels": node.labels,
                "properties": slim_properties(node.properties),
            }
            for node in graph_data.nodes
        ]

        # Create set of node IDs for filtering relationships
        node_ids = {node["id"] for node in nodes}

        # Only include relationships where both nodes exist
        relationships = [
            {
                "id": rel.id,
                "type": rel.type,
                "startNodeId": rel.start_node_id,
                "endNodeId": rel.end_node_id,
                "properties": slim_properties(rel.properties),
            }
            for rel in graph_data.relationships
            if rel.start_node_id in node_ids and rel.end_node_id in node_ids
        ]

        return {
            "nodes": nodes,
            "relationships": relationships,
        }
    except Exception as e:
        print(f"Error getting graph data for entity {entity_id}: {e}")
        return {"nodes": [], "relationships": []}


# ============================================
# SYSTEM PROMPT
# ============================================

CONTEXT_GRAPH_SYSTEM_PROMPT = """You are an AI assistant for a financial institution with access to a Context Graph.

The Context Graph stores decision traces - the reasoning, context, and causal relationships behind every significant decision made in the organization. This enables you to:

1. **Find Precedents**: Search for similar past decisions to inform current recommendations
2. **Trace Causality**: Understand how past decisions influenced subsequent outcomes
3. **Record Decisions**: Create new decision traces with full reasoning context
4. **Detect Patterns**: Identify fraud patterns and entity duplicates using graph structure

## Key Concepts

**Event Clock vs State Clock**:
- Traditional systems store the "state clock" - what is true right now
- The Context Graph stores the "event clock" - what happened, when, and with what reasoning

**Decision Traces**:
- Every significant decision is recorded with full reasoning
- Risk factors, confidence scores, and applied policies are captured
- Causal chains show how decisions influenced each other

## Guidelines

When helping users:
1. **Always search for precedents** before making recommendations
2. **Explain your reasoning thoroughly** - this becomes part of the decision trace
3. **Cite specific past decisions** when they inform your recommendation
4. **Flag exceptions or escalations** that may be needed
5. **Consider both structural and semantic similarity** when finding related cases

You have access to tools that leverage both:
- **Semantic similarity** (text embeddings) - for matching by meaning
- **Structural similarity** (FastRP graph embeddings) - for matching by relationship patterns

This combination provides insights that are impossible with traditional databases."""


# ============================================
# TOOL RESULT HELPERS
# ============================================


def _ok(payload: Any) -> dict[str, Any]:
    """Build a successful Strands ToolResult carrying a JSON payload."""
    return {
        "status": "success",
        "content": [{"text": json.dumps(payload, indent=2, default=str)}],
    }


def _error(message: str) -> dict[str, Any]:
    """Build an error Strands ToolResult."""
    return {"status": "error", "content": [{"text": message}]}


def merge_graph_data(graphs: list[dict], max_nodes: int = 50, max_rels: int = 75) -> dict:
    """Merge multiple graph data objects, removing duplicates and limiting size."""
    all_nodes = {}
    all_relationships = {}

    for graph in graphs:
        if not graph:
            continue
        for node in graph.get("nodes", []):
            if len(all_nodes) < max_nodes:
                all_nodes[node["id"]] = node
        for rel in graph.get("relationships", []):
            # Only include relationships where both nodes are in the graph
            if rel.get("startNodeId") in all_nodes and rel.get("endNodeId") in all_nodes:
                if len(all_relationships) < max_rels:
                    all_relationships[rel["id"]] = rel

    return {
        "nodes": list(all_nodes.values()),
        "relationships": list(all_relationships.values()),
    }


# ============================================
# TOOLS
# ============================================


@tool
async def search_customer(query: str, limit: int = 10) -> dict[str, Any]:
    """Search for customers by name, email, or account number. Returns customer
    profiles with risk scores and related account counts.

    Args:
        query: Name, email, or account number to search for.
        limit: Maximum number of customers to return.
    """
    try:
        results = context_graph_client.search_customers(query=query, limit=limit)
        # Include graph data for top customers (1 hop from each)
        graphs = []
        for customer in results[:3]:  # Limit to first 3 customers
            customer_id = customer.get("id")
            if customer_id:
                customer_graph = get_graph_data_for_entity(customer_id, depth=1)
                graphs.append(customer_graph)

        # Merge all graph data with size limits
        graph_data = merge_graph_data(graphs) if graphs else {"nodes": [], "relationships": []}

        return _ok({"customers": results, "graph_data": graph_data})
    except Exception as e:
        return _error(f"Error searching customers: {str(e)}")


@tool
async def get_customer_decisions(
    customer_id: str, decision_type: Optional[str] = None, limit: int = 20
) -> dict[str, Any]:
    """Get all decisions made about a specific customer, including approvals,
    rejections, escalations, and exceptions.

    Args:
        customer_id: The internal customer ID (person.id).
        decision_type: Optional decision type filter (e.g. approval, rejection).
        limit: Maximum number of decisions to return.
    """
    try:
        results = context_graph_client.get_customer_decisions(
            customer_id=customer_id,
            decision_type=decision_type,
            limit=limit,
        )
        # Include graph data centered on the customer
        graph_data = get_graph_data_for_entity(customer_id, depth=2)

        return _ok({"decisions": results, "graph_data": graph_data})
    except Exception as e:
        return _error(f"Error getting decisions: {str(e)}")


@tool
async def find_similar_decisions(decision_id: str, limit: int = 5) -> dict[str, Any]:
    """Find structurally similar past decisions using FastRP graph embeddings.
    Returns decisions with similar influences, causes, and precedents as well as
    decisions about related accounts.

    Args:
        decision_id: The internal decision ID (decision.id).
        limit: Number of similar decisions to return.
    """
    try:
        similar_decisions = gds_client.find_similar_decisions(decision_id, limit=int(limit))

        # Include graph data centered on the decision
        graph_data = get_graph_data_for_entity(decision_id, depth=2)

        return _ok({"similar_decisions": similar_decisions, "graph_data": graph_data})
    except Exception as e:
        return _error(f"Error finding similar decisions: {str(e)}")


@tool
async def find_precedents(
    scenario: str, category: Optional[str] = None, limit: int = 5
) -> dict[str, Any]:
    """Find precedent decisions that could inform the current decision. Uses both
    semantic similarity (meaning) and structural similarity (graph patterns).

    Args:
        scenario: Natural-language description of the current scenario.
        category: Optional decision category to constrain the search.
        limit: Number of precedents to return.
    """
    try:
        results = vector_client.find_precedents_hybrid(
            scenario=scenario, category=category, limit=limit
        )
        # Include graph data for the first precedent found
        graph_data = None
        if results and len(results) > 0:
            first_id = results[0].get("id") if isinstance(results[0], dict) else None
            if first_id:
                graph_data = get_graph_data_for_entity(first_id, depth=2)

        return _ok({"precedents": results, "graph_data": graph_data})
    except Exception as e:
        return _error(f"Error finding precedents: {str(e)}")


@tool
async def get_causal_chain(
    decision_id: str, direction: str = "both", depth: int = 3
) -> dict[str, Any]:
    """Trace the causal chain of a decision - what caused it and what it led to.
    Useful for understanding decision impact and history.

    Args:
        decision_id: The internal decision ID (decision.id).
        direction: One of "causes", "effects", or "both".
        depth: How many hops to traverse along the causal chain.
    """
    try:
        results = context_graph_client.get_causal_chain(
            decision_id=decision_id,
            direction=direction,
            depth=depth,
        )
        # Include graph data centered on the decision
        graph_data = get_graph_data_for_entity(decision_id, depth=3)

        return _ok({"causal_chain": results, "graph_data": graph_data})
    except Exception as e:
        return _error(f"Error getting causal chain: {str(e)}")


@tool
async def record_decision(
    decision_type: str,
    category: str,
    reasoning: str,
    customer_id: Optional[str] = None,
    account_id: Optional[str] = None,
    risk_factors: Optional[list] = None,
    precedent_ids: Optional[list] = None,
    confidence_score: float = 0.8,
) -> dict[str, Any]:
    """Record a new decision with full reasoning context. Creates a decision trace
    in the context graph that can be referenced by future decisions.

    Args:
        decision_type: The type of decision (e.g. approval, rejection, escalation).
        category: The decision category (e.g. credit, wire_transfer, trading).
        reasoning: Full reasoning text behind the decision.
        customer_id: Optional related customer ID (person.id).
        account_id: Optional related account ID (account.id).
        risk_factors: Optional list of risk factors considered.
        precedent_ids: Optional list of precedent decision IDs cited.
        confidence_score: Confidence score for the decision (0.0 - 1.0).
    """
    try:
        # Generate embedding for the reasoning
        reasoning_embedding = None
        try:
            reasoning_embedding = vector_client.generate_embedding(reasoning)
        except Exception:
            pass  # Continue without embedding if it fails

        decision_id = context_graph_client.record_decision(
            decision_type=decision_type,
            category=category,
            reasoning=reasoning,
            customer_id=customer_id,
            account_id=account_id,
            risk_factors=risk_factors or [],
            precedent_ids=precedent_ids or [],
            confidence_score=confidence_score,
            reasoning_embedding=reasoning_embedding,
        )

        return _ok(
            {
                "success": True,
                "decision_id": decision_id,
                "message": f"Decision recorded successfully with ID {decision_id}",
            }
        )
    except Exception as e:
        return _error(f"Error recording decision: {str(e)}")


@tool
async def detect_fraud_patterns(
    account_id: Optional[str] = None, neighbor_count: int = 5
) -> dict[str, Any]:
    """Analyze accounts or transactions for potential fraud patterns using graph
    structure analysis. Checks an account's proximity to flagged transactions as
    well as the prevalence of flagged transactions in the community of related
    accounts.

    Args:
        account_id: The internal account ID (account.id), not the customer-facing
            account number (account.account_number).
        neighbor_count: Number of example decisions to return from the community.
    """
    try:
        results = gds_client.detect_fraud_patterns(
            account_id=account_id,
            neighbor_count=int(neighbor_count),
        )
        return _ok(results)
    except Exception as e:
        return _error(f"Error detecting fraud patterns: {str(e)}")


@tool
async def find_decision_community(
    decision_id: str, example_count: int = 5
) -> dict[str, Any]:
    """Find decisions in the same community using Leiden community detection.
    Returns decisions that are structurally related through causal chains and
    precedent relationships.

    Args:
        decision_id: The internal decision ID (decision.id).
        example_count: Number of example decisions to return from the community.
    """
    try:
        results = gds_client.get_decision_community(
            decision_id=decision_id, example_count=int(example_count)
        )

        # Include graph data centered on the decision
        graph_data = get_graph_data_for_entity(decision_id, depth=2)

        return _ok({"community_decisions": results, "graph_data": graph_data})
    except Exception as e:
        return _error(f"Error finding community: {str(e)}")


@tool
async def find_accounts_with_high_shared_transaction_volume(
    account_id: str,
) -> dict[str, Any]:
    """Find accounts that share high transaction volumes with a given account.

    Args:
        account_id: The internal account ID (account.id), not the customer-facing
            account number (account.account_number).
    """
    try:
        results = gds_client.find_accounts_with_high_shared_transaction_volume(
            account_id=account_id
        )
        return _ok(results)
    except Exception as e:
        return _error(
            f"Error finding accounts with high shared transaction volume: {str(e)}"
        )


@tool
async def get_policy(
    category: Optional[str] = None, policy_name: Optional[str] = None
) -> dict[str, Any]:
    """Get the current policy rules for a specific category. Returns policy details
    including thresholds and requirements. If policy_name is provided, returns
    policies matching any words in the name.

    Args:
        category: The policy category to retrieve.
        policy_name: Optional policy name to fuzzy-match against.
    """
    try:
        # Get all policies for the category
        policies = context_graph_client.get_policies(category=category)

        if policy_name:
            # Extract meaningful words from the search query (skip common words)
            stop_words = {"the", "a", "an", "for", "and", "or", "of", "in", "to", "with"}
            search_words = [
                word.lower()
                for word in policy_name.split()
                if word.lower() not in stop_words and len(word) > 2
            ]

            # Score each policy by how many search words match
            scored_policies = []
            for policy in policies:
                policy_name_lower = policy.get("name", "").lower()
                # Count how many search words appear in the policy name
                matches = sum(1 for word in search_words if word in policy_name_lower)
                if matches > 0:
                    scored_policies.append({"policy": policy, "relevance_score": matches})

            # Sort by relevance score (highest first)
            scored_policies.sort(key=lambda x: x["relevance_score"], reverse=True)

            if scored_policies:
                # Return all matching policies with relevance info
                results = {
                    "matching_policies": [
                        {**sp["policy"], "relevance_score": sp["relevance_score"]}
                        for sp in scored_policies
                    ],
                    "search_terms": search_words,
                    "total_matches": len(scored_policies),
                }
            else:
                # No matches found - return all policies in category as fallback
                results = {
                    "matching_policies": [],
                    "search_terms": search_words,
                    "total_matches": 0,
                    "all_policies_in_category": policies,
                    "note": f"No policies matched '{policy_name}'. Showing all policies in category.",
                }
        else:
            results = policies

        return _ok(results)
    except Exception as e:
        return _error(f"Error getting policy: {str(e)}")


@tool
async def execute_cypher(cypher: str) -> dict[str, Any]:
    """Execute a read-only Cypher query against the context graph for custom
    analysis. Only SELECT/MATCH queries are allowed.

    Args:
        cypher: The read-only Cypher query to execute.
    """
    try:
        results = context_graph_client.execute_cypher(cypher=cypher)
        return _ok(results)
    except ValueError as e:
        return _error(f"Query not allowed: {str(e)}")
    except Exception as e:
        return _error(f"Error executing query: {str(e)}")


@tool
async def get_schema() -> dict[str, Any]:
    """Get the graph database schema including node labels, relationship types,
    property keys, indexes, and constraints. Also returns counts for each node
    label and relationship type.
    """
    try:
        schema = context_graph_client.get_schema()
        return _ok(schema)
    except Exception as e:
        return _error(f"Error getting schema: {str(e)}")


# Ordered list of tools registered with the agent.
CONTEXT_GRAPH_TOOLS = [
    search_customer,
    get_customer_decisions,
    find_similar_decisions,
    find_precedents,
    get_causal_chain,
    record_decision,
    detect_fraud_patterns,
    find_decision_community,
    find_accounts_with_high_shared_transaction_volume,
    get_policy,
    execute_cypher,
    get_schema,
]


# ============================================
# MODEL / AGENT CONSTRUCTION
# ============================================


def _build_model() -> AnthropicModel:
    """Create the Strands Anthropic model provider from app config."""
    return AnthropicModel(
        client_args={"api_key": config.anthropic.api_key},
        model_id=AGENT_MODEL_ID,
        max_tokens=AGENT_MAX_TOKENS,
    )


# ============================================
# AGENT CONTEXT
# ============================================

AVAILABLE_TOOLS = [
    "search_customer",
    "get_customer_decisions",
    "find_similar_decisions",
    "find_precedents",
    "get_causal_chain",
    "record_decision",
    "detect_fraud_patterns",
    "find_decision_community",
    "find_accounts_with_high_shared_transaction_volume",
    "get_policy",
    "execute_cypher",
    "get_schema",
]


def get_agent_context() -> dict[str, Any]:
    """Get agent context information for transparency/debugging."""
    return {
        "system_prompt": CONTEXT_GRAPH_SYSTEM_PROMPT,
        "model": AGENT_MODEL_ID,
        "available_tools": AVAILABLE_TOOLS,
        "mcp_server": "context-graph",
    }


# ============================================
# STREAM EVENT HELPERS
# ============================================


def _display_tool_name(raw_name: str) -> str:
    """Re-attach the frontend-expected prefix to a bare Strands tool name."""
    if not raw_name:
        return raw_name
    return raw_name if raw_name.startswith(TOOL_NAME_PREFIX) else TOOL_NAME_PREFIX + raw_name


def _parse_tool_result_content(content: Any) -> Any:
    """Parse the content of a Strands toolResult block back into a Python object.

    Tools return their payload as a JSON string inside a ``{"text": ...}`` block,
    so we parse it so the frontend receives a structured object (with graph_data).
    """
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and "text" in item:
                try:
                    return json.loads(item["text"])
                except (json.JSONDecodeError, TypeError):
                    return item["text"]
            if isinstance(item, dict) and "json" in item:
                return item["json"]
    elif isinstance(content, str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content
    return content


# ============================================
# AGENT SESSION MANAGEMENT
# ============================================


class ContextGraphAgent:
    """Wrapper for managing a Strands Agents session.

    Keeps the same async-context-manager + query/query_stream interface the rest
    of the application expects, so swapping SDKs is transparent to callers.
    """

    def __init__(self):
        self.agent: Agent | None = None

    async def __aenter__(self):
        # A fresh Agent per request keeps requests stateless; conversation
        # history is injected into the prompt (see _build_full_message).
        self.agent = Agent(
            model=_build_model(),
            system_prompt=CONTEXT_GRAPH_SYSTEM_PROMPT,
            tools=CONTEXT_GRAPH_TOOLS,
            # We consume stream_async ourselves; disable the default stdout handler.
            callback_handler=None,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.agent = None

    @staticmethod
    def _build_full_message(
        message: str, conversation_history: list[dict[str, str]] | None
    ) -> str:
        """Fold recent conversation history into the prompt text."""
        if conversation_history and len(conversation_history) > 0:
            history_text = "\n".join(
                [
                    f"{msg['role'].upper()}: {msg['content']}"
                    for msg in conversation_history[-6:]
                ]  # Last 6 messages
            )
            return f"""Previous conversation:
{history_text}

Current message from USER: {message}

Please respond to the current message, taking the conversation history into account."""
        return message

    async def query(
        self, message: str, conversation_history: list[dict[str, str]] | None = None
    ) -> dict[str, Any]:
        """Send a query to the agent and get the full (non-streaming) response."""
        if not self.agent:
            raise RuntimeError("Agent not connected. Use 'async with' context manager.")

        full_message = self._build_full_message(message, conversation_history)

        response_text = ""
        tool_calls: list[dict[str, Any]] = []

        async for event in self.agent.stream_async(full_message):
            msg = event.get("message")
            if not msg:
                continue
            for block in msg.get("content", []) or []:
                if "text" in block:
                    response_text += block["text"]
                elif "toolUse" in block:
                    tool_use = block["toolUse"]
                    tool_calls.append(
                        {
                            "name": _display_tool_name(tool_use.get("name", "")),
                            "input": tool_use.get("input") or {},
                        }
                    )

        return {
            "response": response_text,
            "tool_calls": tool_calls,
            "decisions_made": [],
        }

    async def query_stream(
        self, message: str, conversation_history: list[dict[str, str]] | None = None
    ):
        """Send a query to the agent and stream the response.

        Yields the same event shapes the frontend already consumes:
        ``agent_context``, ``text``, ``tool_use``, ``tool_result``, ``done``.
        """
        if not self.agent:
            raise RuntimeError("Agent not connected. Use 'async with' context manager.")

        full_message = self._build_full_message(message, conversation_history)

        # Emit agent context first
        yield {"type": "agent_context", "context": get_agent_context()}

        tool_calls: list[dict[str, Any]] = []
        tool_id_to_name: dict[str, str] = {}  # Map toolUseId -> display name

        async for event in self.agent.stream_async(full_message):
            # Strands emits complete messages for both assistant turns (text +
            # toolUse blocks) and tool-result turns (toolResult blocks). Token
            # deltas (event["data"]) are intentionally ignored so text arrives as
            # whole blocks, matching the previous SDK's behavior.
            msg = event.get("message")
            if not msg:
                continue

            for block in msg.get("content", []) or []:
                if "text" in block:
                    yield {"type": "text", "content": block["text"]}

                elif "toolUse" in block:
                    tool_use = block["toolUse"]
                    tool_id = tool_use.get("toolUseId")
                    display_name = _display_tool_name(tool_use.get("name", ""))
                    tool_input = tool_use.get("input") or {}

                    if tool_id:
                        tool_id_to_name[tool_id] = display_name

                    tool_call = {"name": display_name, "input": tool_input}
                    tool_calls.append(tool_call)
                    yield {"type": "tool_use", **tool_call}

                elif "toolResult" in block:
                    tool_result = block["toolResult"]
                    tool_id = tool_result.get("toolUseId")
                    name = tool_id_to_name.get(tool_id, "unknown")
                    output = _parse_tool_result_content(tool_result.get("content"))
                    yield {"type": "tool_result", "name": name, "output": output}

        # Final event with summary
        yield {
            "type": "done",
            "tool_calls": tool_calls,
            "decisions_made": [],
        }
