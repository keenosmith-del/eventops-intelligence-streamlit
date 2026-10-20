# Read-only audit of the original implementation

Reviewed the original sibling checkout at `eventops-intelligence-v.01`. No original files, Git state, database tables, secrets or Render configuration were modified.

Examined README, data and schema files, RAG ingestion/indexing/embeddings/query/generation, integration adapters, verification pipeline, LangGraph graph, persistence configuration, original tests listing, production acceptance and UI styles. Original credentials were inspected only by presence initially; only approved Gemini/Mailtrap values were copied into the new ignored configuration. Database and Render settings were excluded.

Findings:

- Dataset is 3 events, 9 policies, 7 synthetic participants. Source IDs and associations are useful retrieval/verification primitives.
- Original embeddings use FastEmbed BGE-small and pgvector; query planning applies event/category filters; generation already establishes a useful grounded, bounded Gemini pattern.
- Original LangGraph graph orders read-only source adapters and deterministic transformations. It is not independent evidence of a model selecting tools.
- Public Calendar/Web defaults are holidays. They demonstrate connectivity, not attendance registrations. Only matching controlled sandbox emails provide the positive participant evidence.
- Original directory rules include active state, event registration, exact normalized email/name, event scope and discrepancy visibility. The companion implements these independently, including preserving raw conflicts and optional supplied event details.
- Original deployment reports describe real historical Gemini/Mailtrap demonstrations, but optional n8n was not proven there. Companion n8n imports, production webhooks and AI Agent execution therefore needed fresh evidence.
- The existing visual language uses warm neutral backgrounds, charcoal typography and restrained green accents; the companion adapts these through supported Streamlit widgets.
- The original code uses PostgreSQL-specific repositories and a custom React session model. This companion uses its own owner-scoped SQLAlchemy table and small local vector snapshot.

The original standalone challenge brief was not found as a separate authoritative file in the inspected checkout. The acceptance matrix follows the full task pasted by the user plus its additional priorities. No external assessor approval or exact original marking rubric is inferred.
