from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
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

# Text splitter
text_splitter = CharacterTextSplitter(
    chunk_size=600, chunk_overlap=120, length_function=len
)

vector_store = Chroma(
    collection_name="test_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_db",  # This will create a persistent database
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

    def measure_difficulty(self, query: str):
        difficulty_prompt = f"""You are a helpful assistant. Your task is to measure the difficulty of a user's query.
         - The difficulty is measured on a scale of 1 to 10, where 1 is the easiest and 10 is the hardest.
         - Make no comments, just return the difficulty score.
         - The difficulty score should be an integer between 1 and 10.
         - This difficulty score is used to determine the number of documents to retrieve from the vector database, so make sure to return a difficulty score that is realistic.
         - The difficulty score should be based on the complexity of the query, the length of the query, and the number of documents to retrieve.

        User's Query: {query}
        """

        difficulty_score = self.llm.invoke(difficulty_prompt)

        return difficulty_score

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

    def get_retrieved_documents(self, query: str, history_str: str = ""):
        print(f"RAGChain - Input User Query: '{query}'")

        retrieval_query_result = self.utils.query_rewrite(query, history_str)
        retrieval_query_content = getattr(
            retrieval_query_result, "content", str(retrieval_query_result)
        )

        difficulty_score_result = self.utils.measure_difficulty(query)
        difficulty_score_str = getattr(
            difficulty_score_result, "content", str(difficulty_score_result)
        ).strip()
        print(f"RAGChain - Measured Difficulty (raw): '{difficulty_score_str}'")

        num_docs_to_retrieve = 3  # Default k
        try:
            difficulty = int(difficulty_score_str)
            if 1 <= difficulty <= 10:
                num_docs_to_retrieve = difficulty
            else:
                print(
                    f"RAGChain - Difficulty score {difficulty} out of range (1-10). Defaulting to k={num_docs_to_retrieve}"
                )
        except ValueError:
            print(
                f"RAGChain - Could not parse difficulty '{difficulty_score_str}'. Defaulting to k={num_docs_to_retrieve}"
            )
        num_docs_to_retrieve = max(num_docs_to_retrieve, 3)

        print(f"RAGChain - Number of docs to retrieve (k): {num_docs_to_retrieve}")
        print(f"RAGChain - Query rewrite: {retrieval_query_content}")

        # First, let's try with the where clause
        try:
            docs = self.retriever.invoke(
                retrieval_query_content,
                config={
                    "configurable": {
                        "search_kwargs": {
                            "k": num_docs_to_retrieve
                            * 3,  # Get more docs to filter from
                            "where": {
                                "is_active": True
                            },  # Only search active documents
                        }
                    }
                },
            )
            print(f"RAGChain - Retrieved {len(docs)} documents using where clause")
        except Exception as e:
            print(f"RAGChain - Where clause failed: {e}")
            # Fallback: get all documents and filter manually
            docs = self.retriever.invoke(
                retrieval_query_content,
                config={
                    "configurable": {
                        "search_kwargs": {
                            "k": num_docs_to_retrieve
                            * 3,  # Get more docs to filter from
                        }
                    }
                },
            )
            print(f"RAGChain - Retrieved {len(docs)} documents without filtering")

        # Manual filtering to ensure we only get active documents
        active_docs = []
        for doc in docs:
            print(f"RAGChain - Document metadata: {doc.metadata}")
            if doc.metadata and doc.metadata.get("is_active", False):
                active_docs.append(doc)

        # Limit to requested number of documents
        active_docs = active_docs[:num_docs_to_retrieve]

        print(f"RAGChain - Final active documents: {len(active_docs)}")

        # If no active documents found, return empty list
        if not active_docs:
            print("RAGChain - WARNING: No active documents found!")

        return active_docs

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

        return final_prompt_str, query

    def process_query(self, query: str, stream_response: bool = True):
        final_prompt_str, original_query = self._prepare_rag_inputs(query)

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
        else:
            full_response = self.llm.invoke(final_prompt_str)
            full_response_content = getattr(
                full_response, "content", str(full_response)
            )

            self.chat_memory.save_context(
                {"question": original_query}, {"answer": full_response_content}
            )
            print(f"RAGChain - LLM Answer (invoked): '{full_response_content}'")
            return full_response_content

    def clear_memory(self):
        """Clear the chat memory to reset the conversation history."""
        self.chat_memory.clear()
        print("RAGChain - Memory cleared successfully")


rag_chain = RAGChain(llm, retriever, custom_rag_prompt)
