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
        
        # Expose budget properties for tests
        self.total_budget = self._budget.total
        self.graph_budget = self._budget.graph
        self.asset_budget = self._budget.assets
        self.integration_budget = self._budget.integrations
        self.web_budget = self._budget.web

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return len(text) // self._chars_per_token + 1

    def _build_memory_section(self, scored_nodes: list[ScoredNode]) -> str:
        """Build memory section from scored nodes."""
        memory_lines = []
        tokens_used = 0
        
        for node in scored_nodes:
            if tokens_used >= self._budget.graph:
                break
            
            line = f"[{node.final_score:.2f}] {node.content}"
            
            if node.confidence < 0.5:
                line += f" ⚠️ low confidence ({node.confidence:.2f})"
            
            if node.age_days > 30:
                line += f" (⏳ {int(node.age_days)}d ago)"
            
            memory_lines.append(line)
            tokens_used += self.estimate_tokens(line)
        
        if memory_lines:
            return "## Memory\n" + "\n".join(memory_lines)
        return ""

    def _build_reasoning_section(self, paths: list[str]) -> str:
        """Build reasoning path section."""
        if not paths:
            return ""
        path_lines = [f"  {path}" for path in paths[:3]]
        return "## Reasoning path\n" + "\n".join(path_lines)

    def _build_assets_section(self, assets: list[dict[str, Any]]) -> str:
        """Build related files section."""
        if not assets:
            return ""
        asset_lines = []
        for asset in assets[:3]:
            line = f"- {asset.get('name', 'Unknown')}: {asset.get('summary', '')[:100]}"
            asset_lines.append(line)
        
        if asset_lines:
            return "## Related files\n" + "\n".join(asset_lines)
        return ""

    def _build_trust_section(self, scored_nodes: list[ScoredNode]) -> str:
        """Build trust signal section."""
        avg_confidence = 0.0
        if scored_nodes:
            avg_confidence = sum(n.confidence for n in scored_nodes[:10]) / min(10, len(scored_nodes))
        
        low_conf_count = sum(1 for n in scored_nodes if n.confidence < 0.5)
        return (
            f"## Trust signal\n"
            f"Overall confidence: {avg_confidence:.0%}. "
            f"{low_conf_count} nodes below 0.5 — treat cautiously."
        )

    def assemble(
        self,
        scored_nodes: list[ScoredNode],
        reasoning_paths: list[str] | None = None,
        assets: list[dict[str, Any]] | None = None,
        integrations: dict[str, Any] | None = None,
        web_context: dict[str, Any] | str | None = None,
    ) -> str:
        """Assemble context from all sources with token budgeting.
        
        Args:
            scored_nodes: Scored and ranked memory nodes
            reasoning_paths: Extracted reasoning paths from graph
            assets: Related file/document summaries
            integrations: Recent integration activity (Slack, etc.)
            web_context: External web search context (dict or str)
            
        Returns:
            Assembled context string for LLM
        """
        sections: list[str] = []
        tokens_used = 0
        
        # Section 1: Memory (core facts from graph + vector)
        memory_section = self._build_memory_section(scored_nodes)
        if memory_section:
            sections.append(memory_section)
            tokens_used += self.estimate_tokens(memory_section)
        
        # Section 2: Reasoning paths
        if reasoning_paths:
            reasoning_section = self._build_reasoning_section(reasoning_paths)
            if reasoning_section:
                sections.append(reasoning_section)
                tokens_used += self.estimate_tokens(reasoning_section)
        
        # Section 3: Related assets
        if assets:
            assets_section = self._build_assets_section(assets)
            if assets_section:
                sections.append(assets_section)
                tokens_used += self.estimate_tokens(assets_section)
        
        # Section 4: Integration activity
        if integrations:
            latest = integrations.get("latest", "")
            if latest:
                int_section = f"## Recent activity\n{latest}"
                sections.append(int_section)
                tokens_used += self.estimate_tokens(int_section)
        
        # Section 5: Web context (only if low graph confidence)
        avg_confidence = 0.0
        if scored_nodes:
            avg_confidence = sum(n.confidence for n in scored_nodes[:10]) / min(10, len(scored_nodes))
        
        if web_context and avg_confidence < 0.6:
            # Handle both dict and str formats
            if isinstance(web_context, dict):
                web_text = web_context.get("summary", str(web_context))
            else:
                web_text = web_context
            
            web_section = f"## External context\n{web_text[:500]}"
            sections.append(web_section)
            tokens_used += self.estimate_tokens(web_section)
        
        # Section 6: Trust signal
        trust_section = self._build_trust_section(scored_nodes)
        sections.append(trust_section)
        
        # Assemble final context
        context = "\n\n".join(sections)
        
        logger.info(
            "context_assembled",
            sections_count=len(sections),
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
