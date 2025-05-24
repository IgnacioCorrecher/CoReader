import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from langchain_text_splitters import RecursiveCharacterTextSplitter

# from langchain_experimental.text_splitter import SemanticChunker
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.vectorstores.base import VectorStoreRetriever
from langchain.memory import ConversationBufferWindowMemory

# Load env variables (GOOGLE API KEY)
load_dotenv()
# Instance the llm chat
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite")

# Load embeddings model
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Text splitter - Using RecursiveCharacterTextSplitter for better chunking
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    separators=[
        "\n\n",
        "\n",
        ".",
        "!",
        "?",
    ],
    keep_separator=True,  # Keep separators to maintain context
)

vector_store = Chroma(
    collection_name="test_collection",
    embedding_function=embeddings,
    persist_directory=os.path.join(os.path.dirname(__file__), "chroma_db"),
)

retriever = vector_store.as_retriever()

prompt_template = """You are a helpful and knowledgeable assistant, and an expert content writer. Use the context provided to give a detailed and comprehensive answer to the user's question below. You also need to look at the chat history to give a more accurate answer, and if the user's question is related to the chat history, you should use the chat history to think how the chat history can be used to answer the user's question.
Your response should:
1. Be thorough
2. Be also concise and to the point, don't answer questions that are not related to the context
3. Provide examples or specific points when relevant
4. If you don't know the answer based on the context, clearly state that and explain why
5. The response should be in the same language as the question.
6. The final answer should be in markdown format, use bold, italic.
7. Don't abuse the use of markdown formatting, use it when it makes sense.
8. Never reference the speaker, instead use the name of the person that is being talked about.
9. If the context is in a different language than the question, translate the context to the language of the question.
10. Don't abuse of bullet points, use them when it makes sense.

Banned words and sentences:
1. "Here is the answer to your question:"
2. "Based on the provided context, here's the answer to your question:"
3. "Based on the provided context"
4. "Según el contexto proporcionado"
5. "En el contexto proporcionado"
6. "En el contexto proporcionado, la respuesta a la pregunta es:"

Current context for the question:
{context}

User's question: {query}

Answer: """

custom_rag_prompt = PromptTemplate.from_template(prompt_template)


class Utils:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm

    def query_rewrite(self, query: str, history: str):
        # Rewrite to optimize input query

        query_rewrite_prompt = f"""You are a helpful assistant. Your task is to understand a user's query in the context of the provided chat history.
        First, identify if the query contains pronouns or needs clarification based on the history.
        Then, rephrase the user's query into a concise statement or paragraph suitable for a semantic similarity search on a vector database.
        This rewritten query should incorporate resolved pronouns or context from the chat history to be self-contained and specific.
        Make no comments, just return the rewritten query.
        The rewritten query should:
        1. Be in the same language as the question.
        2. Be concise and to the point.
        3. Be specific and not too general.
        4. Be clear and not too vague.
        5. Be easy to understand and not too complex.

        Chat History:
        {history}

        User's Current Query: {query}

        Rewritten Query for Semantic Search:"""

        retrieval_query = self.llm.invoke(query_rewrite_prompt)

        return retrieval_query

    def format_docs(self, docs):
        # Document parse to string concat
        return "\n\n".join(doc.page_content for doc in docs)


class RAGChain:
    def __init__(
        self,
        llm: ChatGoogleGenerativeAI,
        retriever: VectorStoreRetriever,
        prompt: PromptTemplate,
        memory_window_k: int = 3,  # Number of interactions to keep in memory
    ):
        self.llm = llm
        self.retriever = retriever
        self.prompt = prompt
        self.utils = Utils(llm)
        self.chat_memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=False,
            output_key="answer",
            input_key="question",
            k=memory_window_k,
        )

    def rank_documents(self, docs_with_scores, query: str, max_docs: int = 5):
        """
        Rank documents based on similarity scores and other factors.
        Returns the top-ranked documents up to max_docs limit.
        """
        if not docs_with_scores:
            return []

        # Extract query keywords for relevance scoring
        query_keywords = set(query.lower().split())

        ranked_docs = []
        for doc, score in docs_with_scores:
            # Base similarity score (lower is better for distance, so invert it)
            similarity_score = 1.0 / (1.0 + score) if score > 0 else 1.0

            # Content relevance score based on keyword matching
            doc_text = doc.page_content.lower()
            keyword_matches = sum(
                1 for keyword in query_keywords if keyword in doc_text
            )
            keyword_score = (
                keyword_matches / len(query_keywords) if query_keywords else 0
            )

            # Document length score (normalized, prefer medium-length docs)
            doc_length = len(doc.page_content)
            # Optimal length around 800-1200 characters, score decreases for very short or very long
            if doc_length < 100:
                length_score = 0.3  # Too short
            elif 800 <= doc_length <= 1200:
                length_score = 1.0  # Optimal
            elif doc_length > 2000:
                length_score = 0.7  # Too long
            else:
                length_score = 0.8  # Decent length

            # Combined ranking score (weighted combination)
            final_score = (
                0.6 * similarity_score  # Primary factor: similarity
                + 0.3 * keyword_score  # Secondary: keyword relevance
                + 0.1 * length_score  # Tertiary: document length
            )

            ranked_docs.append(
                (
                    doc,
                    final_score,
                    {
                        "similarity_score": similarity_score,
                        "keyword_score": keyword_score,
                        "length_score": length_score,
                        "final_score": final_score,
                        "original_distance": score,
                    },
                )
            )

        # Sort by final score (descending - higher is better)
        ranked_docs.sort(key=lambda x: x[1], reverse=True)

        # Log ranking information
        print("RAGChain - Document ranking results:")
        for i, (doc, final_score, scores) in enumerate(ranked_docs[:max_docs]):
            print(
                f"  Rank {i + 1}: Score={final_score:.3f} "
                f"(sim={scores['similarity_score']:.3f}, "
                f"kw={scores['keyword_score']:.3f}, "
                f"len={scores['length_score']:.3f}) "
                f"Content preview: {doc.page_content[:100]}..."
            )

        # Return top documents only
        return [doc for doc, _, _ in ranked_docs[:max_docs]]

    def get_retrieved_documents(self, query: str, history_str: str = ""):
        print(f"RAGChain - Input User Query: '{query}'")

        retrieval_query_result = self.utils.query_rewrite(query, history_str)
        retrieval_query_content = getattr(
            retrieval_query_result, "content", str(retrieval_query_result)
        )

        print(f"RAGChain - Query rewrite: {retrieval_query_content}")

        # Get more documents for ranking (up to 15 to have good selection)
        initial_k = 15

        # Try to get documents with similarity scores for better ranking
        try:
            # Use similarity_search_with_score to get both documents and scores
            docs_with_scores = vector_store.similarity_search_with_score(
                retrieval_query_content,
                k=initial_k,
                filter={"is_active": True},  # Filter for active documents
            )
            print(
                f"RAGChain - Retrieved {len(docs_with_scores)} documents with scores using filter"
            )
        except Exception as e:
            print(f"RAGChain - Filtered search failed: {e}")
            # Fallback: get all documents and filter manually
            try:
                docs_with_scores = vector_store.similarity_search_with_score(
                    retrieval_query_content, k=initial_k
                )
                print(
                    f"RAGChain - Retrieved {len(docs_with_scores)} documents with scores (no filter)"
                )

                # Manual filtering to ensure we only get active documents
                filtered_docs_with_scores = []
                for doc, score in docs_with_scores:
                    if doc.metadata and doc.metadata.get("is_active", False):
                        filtered_docs_with_scores.append((doc, score))
                docs_with_scores = filtered_docs_with_scores
                print(
                    f"RAGChain - After manual filtering: {len(docs_with_scores)} active documents"
                )
            except Exception as e2:
                print(f"RAGChain - Similarity search with scores failed: {e2}")
                # Final fallback: use regular retriever
                docs = self.retriever.invoke(
                    retrieval_query_content,
                    config={"configurable": {"search_kwargs": {"k": initial_k}}},
                )
                # Convert to docs_with_scores format (use dummy scores)
                docs_with_scores = [
                    (doc, 0.5)
                    for doc in docs
                    if doc.metadata and doc.metadata.get("is_active", False)
                ]
                print(
                    f"RAGChain - Using fallback retriever: {len(docs_with_scores)} documents"
                )

        # If no active documents found, return empty list
        if not docs_with_scores:
            print("RAGChain - WARNING: No active documents found!")
            return []

        # Rank documents and return top ones
        ranked_docs = self.rank_documents(
            docs_with_scores, retrieval_query_content, max_docs=5
        )

        print(f"RAGChain - Final ranked documents: {len(ranked_docs)}")
        return ranked_docs

    def _prepare_rag_inputs(self, query: str):
        loaded_memory_vars = self.chat_memory.load_memory_variables({})
        history_str = loaded_memory_vars.get("chat_history", "")

        docs = self.get_retrieved_documents(query, history_str)

        context = self.utils.format_docs(docs)

        prompt_inputs = {
            "context": context,
            "query": query,
        }
        final_prompt_str = self.prompt.format(**prompt_inputs)

        return final_prompt_str, query, docs

    def process_query(self, query: str, stream_response: bool = True):
        final_prompt_str, original_query, retrieved_docs = self._prepare_rag_inputs(
            query
        )

        if stream_response:
            response_parts = []
            for token in self.llm.stream(final_prompt_str):
                response_parts.append(token.content)
                yield token

            full_response_content = "".join(response_parts)
            self.chat_memory.save_context(
                {"question": original_query}, {"answer": full_response_content}
            )
            print(f"RAGChain - LLM Answer (streamed): '{full_response_content}'")
            return retrieved_docs  # Return docs for citations when streaming
        else:
            full_response = self.llm.invoke(final_prompt_str)
            full_response_content = getattr(
                full_response, "content", str(full_response)
            )

            self.chat_memory.save_context(
                {"question": original_query}, {"answer": full_response_content}
            )
            print(f"RAGChain - LLM Answer (invoked): '{full_response_content}'")
            return full_response_content, retrieved_docs

    def get_citations_for_query(self, query: str):
        """Get citations for a given query without generating a response"""
        loaded_memory_vars = self.chat_memory.load_memory_variables({})
        history_str = loaded_memory_vars.get("chat_history", "")
        docs = self.get_retrieved_documents(query, history_str)
        return docs

    def clear_memory(self):
        """Clear the chat memory to reset the conversation history."""
        self.chat_memory.clear()
        print("RAGChain - Memory cleared successfully")


rag_chain = RAGChain(llm, retriever, custom_rag_prompt)
