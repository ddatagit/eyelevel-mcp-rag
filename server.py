import os
from typing import Optional
from dotenv import load_dotenv
from groundx import GroundX, Document
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP(name="eyelevel-rag", stateless_http=True)
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
def ingest_documents(source: str, bucket_name: str, file_type: str = "pdf") -> str:
    """
    Ingest documents from a local file path or remote URL into the knowledge base.
    Args:
        source: The local file path or remote URL (starting with http:// or https://) to ingest.
        bucket_name: The name of the bucket to create and use for ingestion.
        file_type: The type of file being ingested (default: pdf).
    Returns:
        str: A message indicating the documents have been ingested.
    """
    # Create bucket
    bucket_response = client.buckets.create(name=bucket_name)
    bucket_id = bucket_response.bucket.bucket_id

    # Determine file name
    file_name = source.split("/")[-1] if "/" in source else os.path.basename(source)

    # Ingest document (works for both local files and remote URLs)
    client.ingest(
        documents=[
            Document(
                bucket_id=bucket_id,
                file_name=file_name,
                file_path=source,
                file_type=file_type,
                search_data={"key": "value"}
            )
        ]
    )

    return f"Ingested {file_name} into bucket '{bucket_name}' (ID: {bucket_id}). Available in a few minutes."