# hr.py
import os
import asyncio
import dotenv

from google import genai
from google.genai import types
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage

# --- RAG Imports (LlamaIndex + Qdrant) ---
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from qdrant_client import QdrantClient

dotenv.load_dotenv()

# =================================================================================
# --- CONFIGURATION ---
# =================================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not all([GEMINI_API_KEY, QDRANT_URL, QDRANT_API_KEY]):
    raise ValueError("Missing required environment variables: GEMINI_API_KEY / QDRANT_URL / QDRANT_API_KEY")

DEFAULT_LLM_MODEL = "models/gemini-2.5-flash"
COLLECTION_NAME = "HR-POLICIES"
EMBEDDING_MODEL_NAME = "models/text-embedding-004"

INSTRUCTIONS = """
You are the official HR Assistant for the University of Management and Technology.
Your primary responsibility is to provide accurate, formal, and professional guidance 
based on the following sources:

1. HR Policy Documents (via the RAG system).
2. The Google Search Tool for relevant institutional information from 'https://www.umt.edu.pk/' site. Go and search from it when a query is asked for relevant information.

Guidelines:
- Always prioritize information from the HR policy documents. 
- If the required information is not available in the policy documents, consult the Google Search Tool.
do not mention the name of tool or document used.
- If neither source provides an answer, politely respond with:
  "I'm sorry, I couldn't find information on that topic. 
   This platform is under development, and more information will be available soon."
- Maintain a professional, educational, and supportive tone in all responses.
- Only include the 'platform under development' note when a query cannot be answered from the HR policy documents or the Search Tool.
"""

# =================================================================================
# --- MEMORY STORE ---
# =================================================================================
session_memories = {}

search_tool = types.Tool(
    google_search=types.GoogleSearch()
)

# =================================================================================
# --- MAIN CLASS ---
# =================================================================================
class HR_AI:
    def __init__(self, model_name: str = DEFAULT_LLM_MODEL):
        self.model_name = model_name
        self.client_genai = self._get_genai_client()

        # --- Setup RAG (Embeddings + Qdrant Index) ---
        Settings.embed_model = GoogleGenAIEmbedding(model_name=EMBEDDING_MODEL_NAME, api_key=GEMINI_API_KEY)
        Settings.llm= None
        qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        vector_store = QdrantVectorStore(client=qdrant_client, collection_name=COLLECTION_NAME)
        self.index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        self.query_engine = self.index.as_query_engine()

    def _get_genai_client(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set.")
        return genai.Client(api_key=GEMINI_API_KEY)

    def _get_memory(self, session_id: str):
        if session_id not in session_memories:
            session_memories[session_id] = ConversationBufferMemory(return_messages=True)
        return session_memories[session_id]

    async def generate(self, user_message: str, session_id: str = "default"):
        print(f"\n[Session: {session_id}] User: {user_message}")
        memory = self._get_memory(session_id)
        history = memory.chat_memory.messages

        # =====================================================
        # Step 1: Retrieve Context using RAG
        # =====================================================
        print(f"[Session: {session_id}] Retrieving context from RAG...")
        retrieval_response = await asyncio.to_thread(self.query_engine.query, user_message)
        context = retrieval_response.response or ""
        print(f"[Session: {session_id}] Context: {context[:200]}...")

        # =====================================================
        # Step 2: Build conversation contents for Gemini
        # =====================================================
        contents = []
        for msg in history:
            if isinstance(msg, HumanMessage):
                contents.append(types.Content(role="user", parts=[types.Part.from_text(text=msg.content)]))
            elif isinstance(msg, AIMessage):
                contents.append(types.Content(role="model", parts=[types.Part.from_text(text=msg.content)]))

        # Build final prompt dynamically
        if context.strip():
            context_prompt = f"""{INSTRUCTIONS}

    CONTEXT FROM HR DOCUMENTS:
    ---
    {context}
    ---

    CURRENT QUESTION:
    {user_message}
    """
        else:
            context_prompt = f"""{INSTRUCTIONS}

    (No relevant HR policy context was found.)

    CURRENT QUESTION:
    {user_message}
    """

        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=context_prompt)]))

        config = types.GenerateContentConfig(system_instruction=INSTRUCTIONS)

        # =====================================================
        # Step 3: Generate response from Gemini
        # =====================================================
        full_response = ""
        try:
            loop = asyncio.get_event_loop()
            response_stream = await loop.run_in_executor(
                None,
                lambda: self.client_genai.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=config
                )
            )
            for chunk in response_stream:
                full_response += chunk.text
                print(chunk.text, end="")
            print()

        except Exception as e:
            print(f"Error: {e}")
            return "An error occurred."

        # =====================================================
        # Step 4: Save messages to memory
        # =====================================================
        memory.chat_memory.add_user_message(user_message)
        memory.chat_memory.add_ai_message(full_response)

        return full_response
