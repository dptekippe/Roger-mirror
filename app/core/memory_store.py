"""
Vector-based semantic memory store backed by PostgreSQL + pgvector.

Provides search_memories(), write_memory(), and get_context_for_prompt()
for semantic retrieval of Roger's long-term memories using
OpenAI text-embedding-3-small (1536 dims) and cosine similarity.
"""

import os
import logging
from typing import Optional, List, Dict

import psycopg2
from psycopg2.extras import RealDictCursor, Json

logger = logging.getLogger(__name__)

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://dynastydroid_user:BKJZCv57P3sYpi5RGL3ciU9CylXsFRWv"
    "@dpg-d6g7g3pdrdic73d9jdrg-a.oregon-postgres.render.com/dynastydroid",
)


def _get_openai_client():
    """Lazily create and return an OpenAI client."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")
    import openai
    return openai.OpenAI(api_key=api_key)


def get_embedding(text: str) -> List[float]:
    """Generate a 1536-dim embedding via text-embedding-3-small."""
    client = _get_openai_client()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text.strip(),
    )
    return response.data[0].embedding


def search_memories(
    query: str,
    threshold: float = 0.8,
    limit: int = 10,
    bot_id: Optional[str] = None,
) -> List[Dict]:
    """Semantic search over memories using cosine similarity.

    Returns a list of dicts with keys: id, content, memory_type,
    importance, timestamp, similarity.
    """
    try:
        query_embedding = get_embedding(query)
    except Exception as e:
        logger.error("Failed to generate query embedding: %s", e)
        return []

    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if bot_id:
                    cur.execute(
                        """
                        SELECT id, content, memory_type, importance, timestamp,
                               1 - (embedding <=> %s::vector) AS similarity
                        FROM memories
                        WHERE bot_id = %s
                          AND embedding IS NOT NULL
                          AND 1 - (embedding <=> %s::vector) >= %s
                        ORDER BY similarity DESC
                        LIMIT %s
                        """,
                        (query_embedding, bot_id, query_embedding, threshold, limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, content, memory_type, importance, timestamp,
                               1 - (embedding <=> %s::vector) AS similarity
                        FROM memories
                        WHERE embedding IS NOT NULL
                          AND 1 - (embedding <=> %s::vector) >= %s
                        ORDER BY similarity DESC
                        LIMIT %s
                        """,
                        (query_embedding, query_embedding, threshold, limit),
                    )
                return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error("Memory search failed: %s", e)
        return []


def write_memory(
    content: str,
    bot_id: Optional[str] = None,
    memory_type: str = "general",
    importance: float = 5.0,
    metadata: Optional[dict] = None,
) -> Optional[str]:
    """Embed and insert a new memory. Returns the new memory id or None on failure."""
    try:
        embedding = get_embedding(content)
    except Exception as e:
        logger.error("Failed to generate embedding for write_memory: %s", e)
        return None

    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO memories (content, embedding, bot_id, memory_type, importance, metadata)
                    VALUES (%s, %s::vector, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        content,
                        embedding,
                        bot_id,
                        memory_type,
                        importance,
                        Json(metadata or {}),
                    ),
                )
                conn.commit()
                row = cur.fetchone()
                return str(row[0]) if row else None
    except Exception as e:
        logger.error("write_memory failed: %s", e)
        return None


def get_context_for_prompt(
    query: str,
    bot_id: Optional[str] = None,
    threshold: float = 0.8,
    max_tokens: int = 2000,
) -> str:
    """Retrieve relevant memories formatted as a context block for LLM prompts.

    Returns an empty string if no memories match or if the vector store
    is unavailable (allowing callers to fall back to MEMORY.md).
    """
    memories = search_memories(query, threshold=threshold, bot_id=bot_id)
    if not memories:
        return ""

    lines = ["## Relevant Memories"]
    total_chars = 0
    for m in memories:
        line = f"- [{m['memory_type']}] {m['content']} (similarity: {m['similarity']:.2f})"
        total_chars += len(line)
        if total_chars > max_tokens * 4:  # rough char-to-token estimate
            break
        lines.append(line)

    return "\n".join(lines)


def load_memory_context(query: str, bot_id: Optional[str] = None) -> str:
    """High-level helper: try vector memory, fall back to MEMORY.md.

    This is the primary entry point for main.py / roger_subconscious.py.
    """
    try:
        context = get_context_for_prompt(query, bot_id=bot_id)
        if context:
            return context
    except Exception as e:
        logger.warning("Vector memory unavailable, falling back to MEMORY.md: %s", e)

    # Fallback: read MEMORY.md directly
    from pathlib import Path

    memory_file = Path(__file__).resolve().parent.parent.parent / "MEMORY.md"
    if memory_file.exists():
        try:
            return memory_file.read_text(encoding="utf-8")[:8000]
        except Exception as e:
            logger.error("Failed to read MEMORY.md fallback: %s", e)

    return ""
