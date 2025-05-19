from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.vectorstores.base import VectorStoreRetriever


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

prompt_template = """You are a helpful and knowledgeable assistant. Use the context provided to give a detailed and comprehensive answer to the user's question below.
Your response should:
1. Be thorough
2. Be also concise and to the point, don't answer questions that are not related to the context
3. Provide examples or specific points when relevant
4. If you don't know the answer based on the context, clearly state that and explain why

context: {context}

question: {query}

answer: """

custom_rag_prompt = PromptTemplate.from_template(prompt_template)


class Utils:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm

    def query_rewrite(self, query: str):
        # Rewrite to optimize input query

        query_rewrite_prompt = f"""You are a helpful assistant that takes a
        user's query and turns it into a short statement or paragraph so that
        it can be used in a semantic similarity search on a vector database to
        return the most similar chunks of content based on the rewritten query.
        Please make no comments, just return the rewritten query.
        \n\nquery: {query}\n\nai: """

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
    ):
        self.llm = llm
        self.retriever = retriever
        self.prompt = prompt
        self.utils = Utils(llm)

    def invoke(self, query: str):

        retrieval_query = self.utils.query_rewrite(query)

        docs = self.retriever.invoke(retrieval_query.content)

        context = self.utils.format_docs(docs)

        final_prompt = self.prompt.format(context=context, query=query)

        return self.llm.invoke(final_prompt)

    def stream(self, query: str):

        retrieval_query = self.utils.query_rewrite(query)

        docs = self.retriever.invoke(retrieval_query.content)

        context = self.utils.format_docs(docs)

        final_prompt = self.prompt.format(context=context, query=query)

        for token in self.llm.stream(final_prompt):
            yield token


rag_chain = RAGChain(llm, retriever, custom_rag_prompt)
