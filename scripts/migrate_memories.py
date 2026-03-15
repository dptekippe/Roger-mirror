#!/usr/bin/env python3
"""
Migrate MEMORY.md into PostgreSQL vector memories table.

Parses MEMORY.md into discrete chunks, generates embeddings via
OpenAI text-embedding-3-small (1536 dims), and inserts them into
the `memories` table backed by pgvector.

Usage:
    export OPENAI_API_KEY="sk-..."
    python scripts/migrate_memories.py

Requires:
    pip install openai psycopg2-binary
"""

import os
import re
import sys
import time
import uuid
import json
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://dynastydroid_user:BKJZCv57P3sYpi5RGL3ciU9CylXsFRWv"
    "@dpg-d6g7g3pdrdic73d9jdrg-a.oregon-postgres.render.com/dynastydroid",
)

# Resolve MEMORY.md relative to repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
MEMORY_FILE = REPO_ROOT / "MEMORY.md"


def get_openai_client():
    """Return an OpenAI client or None if the API key is not set."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        import openai
        return openai.OpenAI(api_key=api_key)
    except ImportError:
        print("ERROR: openai package not installed. Run: pip install openai")
        sys.exit(1)


def get_embedding(client, text: str) -> list[float]:
    """Generate a 1536-dim embedding via text-embedding-3-small."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text.strip(),
    )
    return response.data[0].embedding


def parse_memory_md(filepath: Path) -> list[dict]:
    """Parse MEMORY.md into discrete memory chunks.

    Each top-level section (## heading) becomes one memory.  Within a
    section, sub-sections (### heading) are kept together with their
    parent.  Very large sections are further split at paragraph
    boundaries so no chunk exceeds ~1500 characters.
    """
    content = filepath.read_text(encoding="utf-8")
    chunks = []

    # Split on level-2 headings while keeping the heading with its body
    sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)

    for section in sections:
        section = section.strip()
        if not section or section.startswith("# ") and not section.startswith("## "):
            # Top-level title line – include as identity chunk
            if section.strip():
                chunks.append({
                    "content": section.strip(),
                    "memory_type": "identity",
                    "importance": 8.0,
                })
            continue

        # Determine memory_type from heading tags
        heading_line = section.split("\n")[0]
        memory_type = "general"
        importance = 5.0

        if "[CRITICAL]" in heading_line:
            memory_type = "identity"
            importance = 9.0
        elif "[INSIGHT]" in heading_line:
            memory_type = "insight"
            importance = 7.0
        elif "[FACT]" in heading_line:
            memory_type = "fact"
            importance = 6.0
        elif "[AUDIT]" in heading_line:
            memory_type = "audit"
            importance = 6.0
        elif "[PROACTIVE]" in heading_line:
            memory_type = "proactive"
            importance = 6.0

        # If the section is short enough, keep it whole
        if len(section) <= 1500:
            chunks.append({
                "content": section,
                "memory_type": memory_type,
                "importance": importance,
            })
        else:
            # Split into sub-sections (### headings) or paragraphs
            sub_parts = re.split(r"(?=^### )", section, flags=re.MULTILINE)
            for part in sub_parts:
                part = part.strip()
                if not part:
                    continue
                # Further split very long sub-parts by double newlines
                if len(part) > 1500:
                    paragraphs = re.split(r"\n\n+", part)
                    buffer = ""
                    for para in paragraphs:
                        if len(buffer) + len(para) > 1400 and buffer:
                            chunks.append({
                                "content": buffer.strip(),
                                "memory_type": memory_type,
                                "importance": importance,
                            })
                            buffer = para
                        else:
                            buffer = buffer + "\n\n" + para if buffer else para
                    if buffer.strip():
                        chunks.append({
                            "content": buffer.strip(),
                            "memory_type": memory_type,
                            "importance": importance,
                        })
                else:
                    chunks.append({
                        "content": part,
                        "memory_type": memory_type,
                        "importance": importance,
                    })

    return chunks


def get_bot_id(cur) -> str | None:
    """Get the first bot_id from the bots table."""
    try:
        cur.execute("SELECT id FROM bots LIMIT 1")
        row = cur.fetchone()
        return row[0] if row else None
    except Exception:
        return None


def migrate(dry_run: bool = False):
    """Run the migration."""
    print("=" * 60)
    print("MEMORY.MD → VECTOR MIGRATION")
    print("=" * 60)

    # Validate MEMORY.md exists
    if not MEMORY_FILE.exists():
        print(f"ERROR: {MEMORY_FILE} not found")
        sys.exit(1)

    # Parse chunks
    print(f"\n1. Parsing {MEMORY_FILE}...")
    chunks = parse_memory_md(MEMORY_FILE)
    print(f"   Parsed {len(chunks)} memory chunks")

    if dry_run:
        print("\n--- DRY RUN: showing parsed chunks ---")
        for i, chunk in enumerate(chunks):
            preview = chunk["content"][:80].replace("\n", " ")
            print(f"  [{i+1}] ({chunk['memory_type']}, imp={chunk['importance']}) {preview}...")
        return

    # OpenAI client
    client = get_openai_client()
    if not client:
        print("\nWARNING: OPENAI_API_KEY not set.")
        print("Inserting memories with NULL embeddings.")
        print("Re-run with OPENAI_API_KEY set to generate embeddings.\n")

    # Connect to DB
    print("\n2. Connecting to database...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    bot_id = get_bot_id(cur)
    print(f"   Bot ID: {bot_id}")

    # Clear existing rows in memories (fresh migration)
    cur.execute("DELETE FROM memories")
    conn.commit()
    print("   Cleared existing memories rows.")

    # Insert chunks
    print(f"\n3. Inserting {len(chunks)} memory chunks...")
    inserted = 0
    for i, chunk in enumerate(chunks):
        embedding = None
        if client:
            try:
                embedding = get_embedding(client, chunk["content"])
                time.sleep(0.5)  # Rate-limit courtesy
            except Exception as e:
                print(f"   WARNING: Embedding failed for chunk {i+1}: {e}")

        try:
            if embedding is not None:
                cur.execute(
                    """
                    INSERT INTO memories (content, embedding, bot_id, memory_type, importance, metadata)
                    VALUES (%s, %s::vector, %s, %s, %s, %s)
                    """,
                    (
                        chunk["content"],
                        embedding,
                        bot_id,
                        chunk["memory_type"],
                        chunk["importance"],
                        Json({"source": "MEMORY.md", "migrated": True}),
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO memories (content, bot_id, memory_type, importance, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        chunk["content"],
                        bot_id,
                        chunk["memory_type"],
                        chunk["importance"],
                        Json({"source": "MEMORY.md", "migrated": True, "needs_embedding": True}),
                    ),
                )
            inserted += 1
            preview = chunk["content"][:60].replace("\n", " ")
            emb_status = "with embedding" if embedding else "NULL embedding"
            print(f"   [{i+1}/{len(chunks)}] {emb_status} | {preview}...")
        except Exception as e:
            print(f"   ERROR inserting chunk {i+1}: {e}")
            conn.rollback()

    conn.commit()

    # VACUUM ANALYZE for IVFFlat index performance
    print("\n4. Running VACUUM ANALYZE...")
    conn.autocommit = True
    cur.execute("VACUUM ANALYZE memories")
    print("   Done.")

    # Verify
    print("\n5. Verification...")
    cur.execute("SELECT COUNT(*) FROM memories")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM memories WHERE embedding IS NOT NULL")
    with_emb = cur.fetchone()[0]
    cur.execute("SELECT AVG(importance) FROM memories")
    avg_imp = cur.fetchone()[0]

    print(f"   Total memories: {total}")
    print(f"   With embeddings: {with_emb}")
    print(f"   Average importance: {avg_imp:.1f}")

    # Test: search for "Byte Bowl" if embeddings exist
    if client and with_emb > 0:
        print("\n6. Test: Searching for 'Byte Bowl'...")
        try:
            query_emb = get_embedding(client, "Byte Bowl")
            cur.execute(
                """
                SELECT content, 1 - (embedding <=> %s::vector) AS similarity
                FROM memories
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT 5
                """,
                (query_emb, query_emb),
            )
            results = cur.fetchall()
            for content, sim in results:
                preview = content[:100].replace("\n", " ")
                print(f"   [{sim:.3f}] {preview}...")
        except Exception as e:
            print(f"   Test query error: {e}")

    conn.close()

    print("\n" + "=" * 60)
    print(f"MIGRATION COMPLETE: {inserted}/{len(chunks)} chunks inserted")
    print("=" * 60)


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    migrate(dry_run=dry)
