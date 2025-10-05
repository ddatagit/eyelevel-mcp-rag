import os
from dotenv import load_dotenv
from groundx import GroundX, Document
from mcp.server.fastmcp import FastMCP

load_dotenv()

PORT: int = int(os.getenv("PORT") or 8000)

mcp = FastMCP(name="eyelevel-rag", host="0.0.0.0", port=PORT)
client = GroundX(api_key=os.getenv("GROUNDX_API_KEY") or "")

@mcp.tool()
def search_doc_for_rag_context(query: str) -> str:
    """
    Searches and retrieves relevant context from a knowledge base,
    based on the user's query. Automatically searches across all available buckets.
    Args:
        query: The search query supplied by the user.
    Returns:
        str: Relevant text content that can be used by the LLM to answer the query.
    """
    # Get all available buckets
    buckets_response = client.buckets.list()

    if not buckets_response.buckets:
        return "No buckets available to search."

    # Search each bucket and combine results
    all_results = []
    for bucket in buckets_response.buckets:
        try:
            response = client.search.content(
                id=bucket.bucket_id,
                query=query,
                n=10,
            )
            if response.search.text:
                all_results.append(f"[From {bucket.name}]\n{response.search.text}")
        except Exception as e:
            continue

    return "\n\n".join(all_results) if all_results else "No relevant results found."

@mcp.tool()
def ingest_documents(local_file_path: str, bucket_name: str) -> str:
    """
    Ingest documents from a local file into the knowledge base.
    Args:
        local_file_path: The path to the local file containing the documents to ingest.
        bucket_name: The name of the bucket to create and use for ingestion.
    Returns:
        str: A message indicating the documents have been ingested.
    """
    # Check if bucket exists, create if not
    bucket_id = None

    if bucket_id is None:
        bucket_response = client.buckets.create(name=bucket_name)
        bucket_id = bucket_response.bucket.bucket_id

    file_name = os.path.basename(local_file_path)
    client.ingest(
        documents=[
            Document(
            bucket_id=bucket_id,
            file_name=file_name,
            file_path=local_file_path,
            file_type="pdf",
            search_data=dict(
                key = "value",
            ),
            )
        ]
    )
    return f"""Ingested {file_name} into the knowledge base (bucket: {bucket_name}, bucket_id: {bucket_id}).
               It should be available in a few minutes"""

if __name__ == "__main__":
    mcp.run(transport="streamable-http")