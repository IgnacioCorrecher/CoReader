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
    chunk_size=1000, chunk_overlap=200, length_function=len
)

vector_store = Chroma(collection_name="test_collection", embedding_function=embeddings)

retriever = vector_store.as_retriever()

prompt_template = """You are a helpful and knowledgeable assistant, and an expert content writer. Use the context provided to give a detailed and comprehensive answer to the user's question below. You also need to look at the chat history to give a more accurate answer, and if the user's question is related to the chat history, you should use the chat history to think how the chat history can be used to answer the user's question.
Your response should:
1. Be thorough
2. Be also concise and to the point, don't answer questions that are not related to the context
3. Provide examples or specific points when relevant
4. If you don't know the answer based on the context, clearly state that and explain why
5. The response should be in the same language as the question.

Chat History:
{chat_history}

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

    def stream(self, query: str):
        # Load chat history
        loaded_memory_vars = self.chat_memory.load_memory_variables({})
        history_str = loaded_memory_vars.get("chat_history", "")

        # Rewrite query for retrieval, now history-aware
        retrieval_query = self.utils.query_rewrite(query, history_str)

        # Measure difficulty
        difficulty_score_result = self.utils.measure_difficulty(query)
        difficulty_score_str = getattr(
            difficulty_score_result, "content", str(difficulty_score_result)
        ).strip()

        num_docs_to_retrieve = 3  # Default k

        try:
            difficulty = int(difficulty_score_str)
            if 1 <= difficulty <= 10:
                num_docs_to_retrieve = difficulty
            else:
                print(
                    f"Warning: Difficulty score {difficulty} out of expected range 1-10. Using default k={num_docs_to_retrieve}"
                )
        except ValueError:
            print(
                f"Warning: Could not parse difficulty score '{difficulty_score_str}' as an integer. Using default k={num_docs_to_retrieve}"
            )

        print(f"Dynamic k for retrieval: {num_docs_to_retrieve}")

        docs = self.retriever.invoke(
            retrieval_query.content,
            config={"configurable": {"search_kwargs": {"k": num_docs_to_retrieve}}},
        )
        context = self.utils.format_docs(docs)

        # Prepare inputs for the prompt
        prompt_inputs = {
            "chat_history": history_str,
            "context": context,
            "query": query,
        }
        final_prompt_str = self.prompt.format(**prompt_inputs)

        print(final_prompt_str)

        response_parts = []

        # Stream each generated token in real time and append token to answer for history
        for token in self.llm.stream(final_prompt_str):
            response_parts.append(token.content)
            yield token

        full_response_content = "".join(response_parts)

        # Save the full interaction to memory after streaming is complete
        self.chat_memory.save_context(
            {"question": query}, {"answer": full_response_content}
        )


rag_chain = RAGChain(llm, retriever, custom_rag_prompt)
