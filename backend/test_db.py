"""Test database connection and similarity search."""
import asyncio
import numpy as np
from src.db.postgres.driver import PostgresDriver
from src.db.postgres.operations import PostgresOperations
from src.rag.embeddings import EmbeddingsService
from src.core.config import get_settings


async def test():
    settings = get_settings()
    print("RAG Similarity Threshold:", settings.rag_similarity_threshold)
    print(f"Embedding Model: {settings.gemini_model_embedding}")
    
    driver = PostgresDriver()
    await driver.connect()
    pool = driver.pool
    
    # Get Frank's user_id
    async with pool.acquire() as conn:
        frank = await conn.fetchrow(
            "SELECT id, email FROM auth.users WHERE email LIKE '%frank%'"
        )
        print(f"Frank: {frank['email']} ({frank['id']})")
    
    # Get an exact memory content
    async with pool.acquire() as conn:
        mem = await conn.fetchrow(
            """SELECT id, content FROM memory.embeddings 
               WHERE user_id = $1 AND layer = 'personal' LIMIT 1""",
            frank["id"]
        )
        exact_content = mem['content']
        print(f"\nExact memory content: {exact_content[:60]}...")
    
    # Generate embedding for exact content
    emb_service = EmbeddingsService()
    exact_embedding = await emb_service.embed_text(exact_content, task_type="RETRIEVAL_QUERY")
    print(f"Generated embedding shape: {exact_embedding.shape}")
    
    # Test similarity for exact match
    ops = PostgresOperations(driver)
    results = await ops.similarity_search(
        query_embedding=exact_embedding,
        layer="personal",
        user_id=frank["id"],
        min_confidence=0.0,
        threshold=0.0,
        limit=5
    )
    print(f"\nSimilarity results for exact content:")
    for r in results[:3]:
        print(f"  [{r['similarity']:.4f}] {r['content'][:50]}...")
    
    # Also test a different query
    print("\n--- Testing with related query ---")
    query = "Frank likes to learn"
    query_embedding = await emb_service.embed_query(query)
    
    results2 = await ops.similarity_search(
        query_embedding=query_embedding,
        layer="personal",
        user_id=frank["id"],
        min_confidence=0.0,
        threshold=0.0,
        limit=5
    )
    print(f"Similarity results for '{query}':")
    for r in results2[:3]:
        print(f"  [{r['similarity']:.4f}] {r['content'][:50]}...")


if __name__ == "__main__":
    asyncio.run(test())


if __name__ == "__main__":
    asyncio.run(test())


if __name__ == "__main__":
    asyncio.run(test())


if __name__ == "__main__":
    asyncio.run(test())


if __name__ == "__main__":
    asyncio.run(test())
