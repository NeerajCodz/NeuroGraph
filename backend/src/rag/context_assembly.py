"""Context assembly for LLM generation with token budget management."""

from dataclasses import dataclass
from typing import Any

from src.core.config import get_settings
from src.core.logging import get_logger
from src.memory.scoring import ScoredNode

logger = get_logger(__name__)


@dataclass
class TokenBudget:
    """Token budget allocation for context sections."""
    total: int = 4000
    graph: int = 2000
    assets: int = 800
    integrations: int = 600
    web: int = 400
    system: int = 200


class ContextAssembler:
    """Assembles LLM context from scored results with token budgeting."""

    def __init__(self, budget: TokenBudget | None = None) -> None:
        self._settings = get_settings()
        self._budget = budget or TokenBudget(
            total=self._settings.rag_max_context_tokens,
            graph=self._settings.rag_graph_budget_tokens,
            assets=self._settings.rag_asset_budget_tokens,
            integrations=self._settings.rag_integration_budget_tokens,
        )
        # Approximate tokens per character (conservative estimate)
        self._chars_per_token = 4

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return len(text) // self._chars_per_token + 1

    def assemble(
        self,
        scored_nodes: list[ScoredNode],
        reasoning_paths: list[str] | None = None,
        assets: list[dict[str, Any]] | None = None,
        integrations: dict[str, Any] | None = None,
        web_context: str | None = None,
    ) -> str:
        """Assemble context from all sources with token budgeting.
        
        Args:
            scored_nodes: Scored and ranked memory nodes
            reasoning_paths: Extracted reasoning paths from graph
            assets: Related file/document summaries
            integrations: Recent integration activity (Slack, etc.)
            web_context: External web search context
            
        Returns:
            Assembled context string for LLM
        """
        sections: list[str] = []
        tokens_used = 0
        
        # Section 1: Memory (core facts from graph + vector)
        memory_lines = []
        for node in scored_nodes:
            if tokens_used >= self._budget.graph:
                break
            
            # Format: [score] entity1 → relation → entity2
            line = f"[{node.final_score:.2f}] {node.content}"
            
            # Add confidence warning if low
            if node.confidence < 0.5:
                line += f" ⚠️ low confidence ({node.confidence:.2f})"
            
            # Add age warning if old
            if node.age_days > 30:
                line += f" (⏳ {int(node.age_days)}d ago)"
            
            memory_lines.append(line)
            tokens_used += self.estimate_tokens(line)
        
        if memory_lines:
            sections.append("## Memory\n" + "\n".join(memory_lines))
        
        # Section 2: Reasoning paths
        if reasoning_paths:
            path_lines = [f"  {path}" for path in reasoning_paths[:3]]
            path_section = "## Reasoning path\n" + "\n".join(path_lines)
            path_tokens = self.estimate_tokens(path_section)
            
            if tokens_used + path_tokens < self._budget.total:
                sections.append(path_section)
                tokens_used += path_tokens
        
        # Section 3: Related assets (summaries only)
        if assets and tokens_used < self._budget.graph + self._budget.assets:
            asset_lines = []
            for asset in assets[:3]:
                line = f"- {asset.get('name', 'Unknown')}: {asset.get('summary', '')[:100]}"
                if tokens_used + self.estimate_tokens(line) < self._budget.graph + self._budget.assets:
                    asset_lines.append(line)
                    tokens_used += self.estimate_tokens(line)
            
            if asset_lines:
                sections.append("## Related files\n" + "\n".join(asset_lines))
        
        # Section 4: Integration activity
        if integrations and tokens_used < self._budget.total - self._budget.web:
            latest = integrations.get("latest", "")
            if latest:
                int_section = f"## Recent activity\n{latest}"
                int_tokens = self.estimate_tokens(int_section)
                
                if tokens_used + int_tokens < self._budget.total - self._budget.web:
                    sections.append(int_section)
                    tokens_used += int_tokens
        
        # Section 5: Web context (only if low graph confidence)
        avg_confidence = 0.0
        if scored_nodes:
            avg_confidence = sum(n.confidence for n in scored_nodes[:10]) / min(10, len(scored_nodes))
        
        if web_context and avg_confidence < 0.6:
            web_section = f"## External context\n{web_context[:500]}"
            web_tokens = self.estimate_tokens(web_section)
            
            if tokens_used + web_tokens < self._budget.total:
                sections.append(web_section)
                tokens_used += web_tokens
        
        # Section 6: Trust signal
        low_conf_count = sum(1 for n in scored_nodes if n.confidence < 0.5)
        trust_section = (
            f"## Trust signal\n"
            f"Overall confidence: {avg_confidence:.0%}. "
            f"{low_conf_count} nodes below 0.5 — treat cautiously."
        )
        sections.append(trust_section)
        
        # Assemble final context
        context = "\n\n".join(sections)
        
        logger.info(
            "context_assembled",
            sections_count=len(sections),
            nodes_included=len(memory_lines),
            tokens_estimated=tokens_used,
        )
        
        return context

    def build_prompt(
        self,
        query: str,
        context: str,
        system_instruction: str | None = None,
    ) -> str:
        """Build the final LLM prompt with context.
        
        Args:
            query: User query
            context: Assembled context
            system_instruction: Optional custom system instruction
            
        Returns:
            Complete prompt for LLM
        """
        default_system = """You are NeuroGraph, an AI with structured memory.
Use ONLY the context below to answer.
If confidence is low, say so explicitly."""

        return f"""{system_instruction or default_system}

{context}

---

User question: {query}

Answer with reasoning. Cite which memory nodes led to your conclusion."""

    def extract_reasoning_paths(
        self,
        scored_nodes: list[ScoredNode],
        graph_paths: list[dict[str, Any]] | None = None,
    ) -> list[str]:
        """Extract human-readable reasoning paths.
        
        Args:
            scored_nodes: Scored nodes
            graph_paths: Raw graph traversal paths
            
        Returns:
            List of formatted reasoning path strings
        """
        paths: list[str] = []
        
        if graph_paths:
            for path in graph_paths[:5]:
                nodes = path.get("nodes", [])
                rels = path.get("relationships", [])
                
                if len(nodes) < 2:
                    continue
                
                path_parts = []
                for i, node in enumerate(nodes):
                    path_parts.append(node.get("name", "?"))
                    if i < len(rels):
                        rel_type = rels[i].get("type", "→")
                        path_parts.append(f" → {rel_type} → ")
                
                paths.append("".join(path_parts))
        
        return paths
