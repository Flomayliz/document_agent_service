from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain.tools import tool
from app.db.factory import get_database
from app.db.user_handler import UserDbHandler
from datetime import datetime
import os
import re
from collections import Counter


class IngestInput(BaseModel):
    """Input for the ingest_local tool."""

    file_path: str = Field(description="Path to the document file")


class SummaryInput(BaseModel):
    """Input for the summary tool."""

    doc_id: str = Field(description="Document ID")
    length: int = Field(default=150, description="Desired summary length in words")


class TopicsInput(BaseModel):
    """Input for the get_topics tool."""

    doc_id: str = Field(description="Document ID")


class AggregateInput(BaseModel):
    """Input for the aggregate tool."""

    topic: Optional[str] = Field(default=None, description="Topic to filter by")
    keyword: Optional[str] = Field(default=None, description="Keyword to filter by")


class AnswerInput(BaseModel):
    """Input for the answer tool."""

    doc_id: str = Field(description="Document ID")
    question: str = Field(description="Question to answer")


class GetDocumentInput(BaseModel):
    """Input for the get_document tool."""

    doc_id: str = Field(description="Document ID to retrieve")


class DocumentStatsInput(BaseModel):
    """Input for the document_stats tool."""

    doc_id: str = Field(description="Document ID")


class CompareDocumentsInput(BaseModel):
    """Input for the compare_documents tool."""

    doc_id_1: str = Field(description="First document ID")
    doc_id_2: str = Field(description="Second document ID")


class SearchInput(BaseModel):
    """Input for the search tool."""

    query: str = Field(description="Search query text")
    limit: int = Field(default=5, description="Maximum number of results to return")


class UserHistoryInput(BaseModel):
    """Input for the get_user_history tool."""

    user_id: str = Field(description="User ID to retrieve history for")


@tool
async def list_docs() -> List[Dict[str, Any]]:
    """List all documents in the database.

    ACTION GUIDE: Use this as your FIRST STEP when asked about documents but NOT given a specific document ID.
    NO PARAMETERS NEEDED: This tool requires no input parameters.

    Returns:
        List of document metadata including document IDs, which are needed for other tools.
    """
    try:
        repo = get_database()
        docs = []

        # Process documents from list_meta()
        async for doc in repo.list_meta():
            # Convert to dict representation for the agent
            doc_dict = {
                "id": doc.id,
                "filename": doc.filename,
                "keywords": doc.keywords,
                "topics": doc.topics,
                "summary": doc.summary or "",
                "file_size": doc.metadata.size_bytes,
            }

            # Add created date if available
            if doc.metadata.created:
                doc_dict["created_at"] = doc.metadata.created.isoformat()
            elif doc.metadata.modified:
                doc_dict["created_at"] = doc.metadata.modified.isoformat()
            else:
                doc_dict["created_at"] = datetime.now().isoformat()

            docs.append(doc_dict)

        return docs if docs else [{"message": "No documents found"}]
    except Exception as e:
        return [{"error": f"Error listing documents: {str(e)}"}]


@tool(args_schema=TopicsInput)
async def get_topics(doc_id: str) -> List[str]:
    """Get topics for a document.

    ACTION GUIDE: Use ONLY when specifically asked about topics, themes, or categories of a document.
    REQUIRED INPUT: doc_id - You MUST provide a valid document ID.

    Args:
        doc_id: Document ID

    Returns:
        List of topics
    """
    try:
        repo = get_database()
        doc = await repo.get(doc_id)

        if not doc:
            return [f"Error: Document with ID {doc_id} not found"]

        return doc.topics if hasattr(doc, "topics") else []
    except Exception as e:
        return [f"Error getting topics: {str(e)}"]


@tool(args_schema=GetDocumentInput)
async def get_document(doc_id: str) -> Dict[str, Any]:
    """Retrieve a complete document by its ID.

    ACTION GUIDE: Use when you need to see the FULL content of a specific document. Use this tool when the user asks for
    "the complete text", "the entire document", "the full content" or wants to "read" a document. This tool returns
    EVERYTHING including all content and metadata.
    REQUIRED INPUT: doc_id - You MUST provide a valid document ID.

    Args:
        doc_id: Document ID

    Returns:
        Complete document with all metadata and full text content
    """
    try:
        repo = get_database()
        doc = await repo.get(doc_id)

        if not doc:
            return {"error": f"Document with ID {doc_id} not found"}

        # Convert document to dictionary with all content
        doc_dict = {
            "id": doc.id,
            "filename": doc.filename,
            "path": doc.path,
            "content": doc.text,  # Full document text
            "keywords": doc.keywords,
            "topics": doc.topics,
            "summary": doc.summary or "",
            "metadata": {
                "file_size": doc.metadata.size_bytes,
                "mime_type": doc.metadata.mime,
                "author": doc.metadata.author,
                "title": doc.metadata.title,
                "pages": doc.metadata.pages,
                "lines": doc.metadata.lines,
                "paragraphs": doc.metadata.paragraphs,
                "tables": doc.metadata.tables,
                "creator": doc.metadata.creator,
            },
        }

        # Add created/modified dates if available
        if doc.metadata.created:
            doc_dict["metadata"]["created"] = doc.metadata.created.isoformat()
        if doc.metadata.modified:
            doc_dict["metadata"]["modified"] = doc.metadata.modified.isoformat()

        return doc_dict
    except Exception as e:
        return {"error": f"Error retrieving document: {str(e)}"}


@tool(args_schema=DocumentStatsInput)
async def document_stats(doc_id: str) -> Dict[str, Any]:
    """Get detailed statistics about a document.

    ACTION GUIDE: Use when asked for analytical information about a document like word count, reading time,
    complexity metrics, or general statistics about the document's content.
    REQUIRED INPUT: doc_id - Document ID

    Args:
        doc_id: Document ID

    Returns:
        Dictionary of document statistics
    """
    try:
        repo = get_database()
        doc = await repo.get(doc_id)

        if not doc:
            return {"error": f"Document with ID {doc_id} not found"}

        # Calculate basic statistics
        text = doc.text
        word_count = len(re.findall(r"\b\w+\b", text))
        char_count = len(text)
        sentence_count = len(re.findall(r"[.!?]+", text)) or 1  # Avoid division by zero
        paragraph_count = len(re.split(r"\n\s*\n", text))

        # Calculate advanced metrics
        avg_word_length = char_count / max(1, word_count)
        avg_sentence_length = word_count / max(1, sentence_count)
        avg_paragraph_length = word_count / max(1, paragraph_count)

        # Reading time estimation (average reading speed: 200-250 words per minute)
        reading_time_minutes = word_count / 225

        # Most common words (excluding stop words)
        stop_words = {
            "the",
            "a",
            "an",
            "in",
            "on",
            "at",
            "of",
            "for",
            "to",
            "and",
            "or",
            "but",
            "is",
            "are",
            "was",
            "were",
        }
        words = re.findall(r"\b[a-z]{3,}\b", text.lower())
        filtered_words = [word for word in words if word not in stop_words]
        most_common_words = Counter(filtered_words).most_common(10)

        # Complexity metrics
        unique_words = len(set(words))
        vocabulary_richness = unique_words / max(1, word_count)  # Type-token ratio

        # Flesch Reading Ease score (rough approximation)
        if sentence_count > 0 and word_count > 0:
            flesch_score = (
                206.835
                - (1.015 * (word_count / sentence_count))
                - (84.6 * (sum(len(word) for word in words) / word_count))
            )
        else:
            flesch_score = 0

        # Prepare statistics dictionary
        stats = {
            "basic_stats": {
                "word_count": word_count,
                "character_count": char_count,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count,
                "file_size_bytes": doc.metadata.size_bytes,
            },
            "readability": {
                "average_word_length": round(avg_word_length, 2),
                "average_sentence_length": round(avg_sentence_length, 2),
                "average_paragraph_length": round(avg_paragraph_length, 2),
                "estimated_reading_time_minutes": round(reading_time_minutes, 2),
                "flesch_reading_ease": round(flesch_score, 2),
            },
            "vocabulary": {
                "unique_word_count": unique_words,
                "vocabulary_richness": round(vocabulary_richness, 4),
                "most_common_words": most_common_words,
            },
            "metadata": {
                "filename": doc.filename,
                "mime_type": doc.metadata.mime,
                "author": doc.metadata.author,
                "title": doc.metadata.title,
                "pages": doc.metadata.pages,
                "created": doc.metadata.created.isoformat() if doc.metadata.created else None,
                "modified": doc.metadata.modified.isoformat() if doc.metadata.modified else None,
            },
        }

        return stats
    except Exception as e:
        return {"error": f"Error analyzing document statistics: {str(e)}"}


@tool(args_schema=CompareDocumentsInput)
async def compare_documents(doc_id_1: str, doc_id_2: str) -> Dict[str, Any]:
    """Compare two documents and identify similarities and differences.

    ACTION GUIDE: Use when asked to compare, contrast, or find similarities between two specific documents.
    REQUIRED INPUT: Two different document IDs to compare

    Args:
        doc_id_1: First document ID
        doc_id_2: Second document ID

    Returns:
        Comparison results including similarities, differences, and unique content
    """
    try:
        repo = get_database()
        doc1 = await repo.get(doc_id_1)
        doc2 = await repo.get(doc_id_2)

        if not doc1:
            return {"error": f"Document with ID {doc_id_1} not found"}
        if not doc2:
            return {"error": f"Document with ID {doc_id_2} not found"}

        # Get basic information about both documents
        doc1_info = {
            "id": doc1.id,
            "filename": doc1.filename,
            "size_bytes": doc1.metadata.size_bytes,
            "word_count": len(re.findall(r"\b\w+\b", doc1.text)),
            "topics": doc1.topics,
            "keywords": doc1.keywords,
        }

        doc2_info = {
            "id": doc2.id,
            "filename": doc2.filename,
            "size_bytes": doc2.metadata.size_bytes,
            "word_count": len(re.findall(r"\b\w+\b", doc2.text)),
            "topics": doc2.topics,
            "keywords": doc2.keywords,
        }

        # Compare metadata
        metadata_comparison = {
            "size_difference": doc1.metadata.size_bytes - doc2.metadata.size_bytes,
            "word_count_difference": doc1_info["word_count"] - doc2_info["word_count"],
        }

        # Compare content (shared topics and keywords)
        shared_topics = list(set(doc1.topics) & set(doc2.topics))
        unique_topics_doc1 = list(set(doc1.topics) - set(doc2.topics))
        unique_topics_doc2 = list(set(doc2.topics) - set(doc1.topics))

        shared_keywords = list(set(doc1.keywords) & set(doc2.keywords))
        unique_keywords_doc1 = list(set(doc1.keywords) - set(doc2.keywords))
        unique_keywords_doc2 = list(set(doc2.keywords) - set(doc1.keywords))

        # Text similarity (simple approach using common sentences)
        doc1_sentences = set(re.split(r"[.!?]+", doc1.text))
        doc2_sentences = set(re.split(r"[.!?]+", doc2.text))
        common_sentences = doc1_sentences & doc2_sentences
        similarity_ratio = len(common_sentences) / max(
            1, (len(doc1_sentences) + len(doc2_sentences)) / 2
        )

        # Compile results
        comparison = {
            "documents": {"document1": doc1_info, "document2": doc2_info},
            "metadata_comparison": metadata_comparison,
            "content_comparison": {
                "similarity_ratio": round(similarity_ratio, 2),
                "shared_topics": shared_topics,
                "unique_topics_doc1": unique_topics_doc1,
                "unique_topics_doc2": unique_topics_doc2,
                "shared_keywords": shared_keywords,
                "unique_keywords_doc1": unique_keywords_doc1,
                "unique_keywords_doc2": unique_keywords_doc2,
                "common_sentences_count": len(common_sentences),
            },
        }

        return comparison
    except Exception as e:
        return {"error": f"Error comparing documents: {str(e)}"}


@tool(args_schema=SearchInput)
async def search(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search across all documents for specific content.

    ACTION GUIDE: Use when a user wants to find documents containing specific words, phrases, or concepts.
    This tool searches the CONTENT of documents, not just metadata or topics.
    REQUIRED INPUT: query - The search text to look for across all documents
    OPTIONAL INPUT: limit - Maximum number of results to return (default: 5)

    Args:
        query: Search query text
        limit: Maximum number of results to return

    Returns:
        List of matching document summaries with relevance scores
    """
    try:
        if not query or len(query.strip()) == 0:
            return [{"error": "Search query cannot be empty"}]

        repo = get_database()
        search_results = []

        # Get all documents
        documents = []
        async for doc in repo.list_meta():
            # Get the full document for searching
            full_doc = await repo.get(doc.id)
            if full_doc:
                documents.append(full_doc)

        # Simple relevance scoring
        def calculate_relevance(doc, query):
            # Count occurrences of query terms in document text
            query_terms = re.findall(r"\b\w+\b", query.lower())
            text_lower = doc.text.lower()
            title_lower = (doc.metadata.title or "").lower()

            # Boost scores for exact phrase match
            exact_phrase_matches = text_lower.count(query.lower()) * 3

            # Count term occurrences (with higher weight for title matches)
            term_scores = sum(text_lower.count(term) for term in query_terms)
            title_scores = sum(title_lower.count(term) for term in query_terms) * 2

            # Check if query terms appear in keywords or topics
            keyword_topic_matches = sum(
                1 for term in query_terms if any(term in kw.lower() for kw in doc.keywords)
            )
            keyword_topic_matches += sum(
                1 for term in query_terms if any(term in topic.lower() for topic in doc.topics)
            )
            keyword_topic_matches *= 1.5  # Higher weight for metadata matches

            # Combine scores
            score = term_scores + title_scores + exact_phrase_matches + keyword_topic_matches

            # Normalize by document length
            word_count = len(re.findall(r"\b\w+\b", doc.text))
            if word_count > 0:
                score = score / (word_count**0.5)  # Using square root for softer normalization

            return score

        # Calculate relevance for each document
        scored_docs = []
        for doc in documents:
            relevance = calculate_relevance(doc, query)
            if relevance > 0:  # Only include documents with some relevance
                scored_docs.append((doc, relevance))

        # Sort by relevance score (descending)
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Take top results up to limit
        for doc, score in scored_docs[:limit]:
            # Create snippet with context around query terms
            snippet = ""
            query_terms = re.findall(r"\b\w+\b", query.lower())

            # Find a relevant excerpt
            for term in query_terms:
                match = re.search(f"\\b{re.escape(term)}\\b", doc.text, re.IGNORECASE)
                if match:
                    start = max(0, match.start() - 50)
                    end = min(len(doc.text), match.end() + 50)
                    context = doc.text[start:end].strip()
                    if context:
                        snippet = f"...{context}..."
                        break

            if not snippet and doc.text:
                # Fallback to first part of the document
                snippet = doc.text[:100] + "..."

            # Add to results
            search_results.append(
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "title": doc.metadata.title or doc.filename,
                    "relevance_score": round(score, 2),
                    "snippet": snippet,
                    "keywords": doc.keywords[:5] if doc.keywords else [],
                    "topics": doc.topics[:3] if doc.topics else [],
                }
            )

        if not search_results:
            return [{"message": f"No documents found matching query: '{query}'"}]

        return search_results
    except Exception as e:
        return [{"error": f"Error searching documents: {str(e)}"}]


@tool
def about_leslie() -> Dict[str, Any]:
    """Get information about Leslie, the creator of this agent.

    ACTION GUIDE: Use when asked about Leslie, her background, skills, experience, or any personal/professional information about the creator of this system.
    NO PARAMETERS NEEDED: This tool requires no input parameters.

    Returns:
        Dict[str, Any]: A dictionary containing Leslie's information from the CV file.
        If an error occurs, returns a dictionary with an 'error' key explaining the issue.
    """
    # read json file with Leslie's info from cv_data/cv.json
    try:
        import json

        cv_path = os.path.join(os.path.dirname(__file__), "cv_data", "cv.json")
        with open(cv_path, "r") as f:
            leslie_info = json.load(f)

        return leslie_info
    except Exception as e:
        return {"error": f"Error retrieving Leslie's information: {str(e)}"}


@tool(args_schema=UserHistoryInput)
async def get_user_history(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve the Q&A history for a specific user.

    ACTION GUIDE: Use when asked about a user's previous questions, conversation history,
    or past interactions. This shows all the questions a user has asked and the answers they received.
    REQUIRED INPUT: user_id - You MUST provide a valid user ID.

    Args:
        user_id: User ID to retrieve history for

    Returns:
        List of Q&A pairs from the user's history, or error if user not found
    """
    try:
        user_service = UserDbHandler()
        history = await user_service.get_user_history(user_id)

        if history is None:
            return [{"error": f"User with ID {user_id} not found"}]

        if not history:
            return [{"message": f"No history found for user {user_id}"}]

        # Convert QA objects to dictionaries for the agent
        history_dicts = []
        for qa in history:
            qa_dict = {
                "question": qa.question,
                "answer": qa.answer,
                "timestamp": qa.timestamp.isoformat(),
            }
            history_dicts.append(qa_dict)

        return history_dicts
    except Exception as e:
        return [{"error": f"Error retrieving user history: {str(e)}"}]
