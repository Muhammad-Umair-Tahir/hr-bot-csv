# track_bot.py - Track Selection AI Assistant
import os
import asyncio
import dotenv

from google import genai
from google.genai import types

# --- RAG Imports (LlamaIndex + Qdrant) ---
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from qdrant_client import QdrantClient

# --- Local Imports ---
from .fetch_data import fetch_faculty_and_track_data
from utils.research_portal import fetch_research_portal_data

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

TRACK_SELECTION_INSTRUCTIONS = """
Role:
You are a strict policy compliance engine for the University of Management and Technology. Your only job is to decide faculty track eligibility using the official Faculty Track Assignment Policy (provided via RAG).

Rules:

Use only the policy document as your source of rules.

For each faculty input (designation, PhD status, publications, funded projects, industry experience, etc.), check track eligibility step by step against the policy.

Never guess. If required data is missing or unclear, respond with:

“Eligibility cannot be determined due to missing or incomplete data.”

Always return one of three outcomes:

✅ Approved (with reason based on policy)

❌ Not Approved (with reason based on policy)

⚠️ Insufficient Data (explain which data is missing)

Be explicit about conditions. Always mention why a faculty member is eligible or not (e.g., “PhD holder → auto-eligible for Research Track” or “Funding < Rs. 5M → not eligible for SIT”).

Do not invent new rules. If the policy is silent on a case, clearly state:

“The policy document does not define eligibility for this case.”

When multiple tracks are possible, list all valid options as per the rules.

Ensure numerical thresholds, publication counts, and course requirements are applied exactly as written (do not approximate).
"""

# =================================================================================
# --- MAIN CLASS ---
# =================================================================================
class TrackSelectionAI:
    def __init__(self, model_name: str = DEFAULT_LLM_MODEL):
        self.model_name = model_name
        self.client_genai = self._get_genai_client()

        # --- Setup RAG (Embeddings + Qdrant Index) ---
        Settings.embed_model = GoogleGenAIEmbedding(model_name=EMBEDDING_MODEL_NAME, api_key=GEMINI_API_KEY)
        Settings.llm = None
        qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        vector_store = QdrantVectorStore(client=qdrant_client, collection_name=COLLECTION_NAME)
        self.index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        self.query_engine = self.index.as_query_engine()

    def _get_genai_client(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set.")
        return genai.Client(api_key=GEMINI_API_KEY)

    async def evaluate_track_eligibility(self, faculty_id: int, track_id: int):
        """
        Evaluate faculty eligibility for a specific track using RAG-based policy analysis.
        Includes both database information and research portal data.
        
        Data Flow:
        1. Use faculty_id to fetch faculty data from database (including faculty_code)
        2. Use faculty_code to fetch research portal data
        3. Combine both data sources for comprehensive evaluation
        
        Args:
            faculty_id (int): Database ID of the faculty member
            track_id (int): Database ID of the track to evaluate
            
        Returns:
            dict: Contains 'decision' and 'remarks'
        """
        try:
            # =====================================================
            # Step 1: Fetch Faculty and Track Data from Database
            # =====================================================
            data = await fetch_faculty_and_track_data(faculty_id, track_id)
            
            if not data:
                return {
                    "decision": "NOT APPROVED",
                    "remarks": "Error: Faculty or track not found in database. Please verify the provided IDs."
                }
            
            faculty_info = data["faculty_data"]
            track_info = data["track_data"]
            
            # =====================================================
            # Step 2: Fetch Research Portal Data using Faculty Code
            # =====================================================
            faculty_code = faculty_info['code']  # Extract faculty code from database data
            if not faculty_code:
                research_profile = "No faculty code available to fetch research portal data."
            else:
                print(f"Fetching research portal data for faculty code: {faculty_code}")
                research_data = await asyncio.to_thread(fetch_research_portal_data, faculty_code)
                
                # Build research profile summary
                research_profile = "No research profile data available."
                if research_data:
                    profile = research_data['profile_data']
                    articles = research_data['articles']
                    
                    research_profile = f"""
                Research Profile:
                - Username: {profile['username'] or 'Not available'}
                - Full Name: {profile['full_name'] or 'Not available'}
                - ResearchGate Profile: {profile['researchgate_url'] or 'Not available'}
                - Google Scholar Profile: {profile['google_scholar_url'] or 'Not available'}
                
                Publications Summary:
                - Total Publications: {len(articles)}
                """
                    
                    if articles:
                        research_profile += "\n                Publications List:\n"
                        for i, article in enumerate(articles[:10], 1):  # Limit to first 10 articles
                            research_profile += f"""                {i}. {article['articleName'] or 'Untitled'}
                   Year: {article['yearofPublication'] or 'N/A'}, Status: {article['status'] or 'Unknown'}
"""
                        if len(articles) > 10:
                            research_profile += f"                ... and {len(articles) - 10} more publications\n"
                    else:
                        research_profile += "\n                No publications found in research portal.\n"
                else:
                    research_profile += "\n                Could not retrieve research portal data for this faculty member.\n"
            
            # =====================================================
            # Step 3: Build comprehensive evaluation query for RAG
            # =====================================================
            evaluation_query = f"""
            TRACK SELECTION ELIGIBILITY EVALUATION REQUEST:
            
            FACULTY PROFILE:
            - Full Name: {faculty_info['name']}
            - Academic Title: {faculty_info['title']} (NOTE: If "Dr", indicates PhD qualification)
            - Faculty Code: {faculty_info['code']}
            - Academic Designation: {faculty_info['academic_designation']}
            - Administrative Designation: {faculty_info['administrative_designation']}
            - Teaching Experience: {faculty_info['teaching_experience']} years
            - Professional Experience: {faculty_info['professional_experience']} years
            - University Email: {faculty_info['university_email']}
            - Employment Status: {faculty_info['status']}
            - System Role: {faculty_info['role']}
            - Account Active: {faculty_info['is_active']}
            
            TARGET TRACK DETAILS:
            - Track Name: {track_info['name']}
            - Track Code: {track_info['code']}
            - Track Type: {track_info['type']}
            
            RESEARCH PROFILE:
            {research_profile}
            
            EVALUATION QUESTION:
            Based on UMT's track selection policies, determine if this faculty member is eligible for the specified track.
            
            KEY CONSIDERATIONS:
            1. For Research Track: If title is "Dr", this indicates PhD qualification and grants AUTOMATIC ELIGIBILITY
            2. Evaluate how well the faculty's qualifications, experience, and research profile align with track requirements
            3. Consider both academic credentials and practical experience
            4. Assess research output quality and quantity for research-oriented tracks
            5. Review teaching/professional experience relevance to the track type
            
            Provide a comprehensive eligibility assessment with clear reasoning.
            """
            
            # =====================================================
            # Step 4: Retrieve Context using RAG
            # =====================================================
            print("Retrieving track selection policies from RAG system...")
            retrieval_response = await asyncio.to_thread(self.query_engine.query, evaluation_query)
            context = retrieval_response.response or ""
            
            # =====================================================
            # Step 5: Build evaluation prompt
            # =====================================================
            evaluation_prompt = f"""{TRACK_SELECTION_INSTRUCTIONS}
            
            TRACK SELECTION POLICY CONTEXT:
            ---
            {context}
            ---
            
            COMPREHENSIVE FACULTY EVALUATION REQUEST:
            {evaluation_query}
            
            SPECIAL ATTENTION REQUIRED:
            - For Research Track: Check if faculty title is "Dr" (indicates PhD qualification = automatic eligibility)
            - Evaluate experience alignment with track requirements
            - Assess research/publications for research-oriented tracks
            - Consider teaching load and professional background
            
            Based on the above policy context and faculty information, provide your eligibility assessment
            STRICTLY using the defined output format. Output ONLY:
            1) The DECISION line, and 2) the REMARKS with exactly 3–4 one-line bullets.
            Do NOT include any additional sections, explanations, or pre/post text.
            """
            
            # =====================================================
            # Step 6: Generate evaluation from Gemini
            # =====================================================
            contents = [types.Content(role="user", parts=[types.Part.from_text(text=evaluation_prompt)])]
            config = types.GenerateContentConfig(system_instruction=TRACK_SELECTION_INSTRUCTIONS)
            
            full_response = ""
            try:
                print("Generating AI evaluation...")
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
                
            except Exception as e:
                return {
                    "decision": "NOT APPROVED",
                    "remarks": f"System error occurred during AI evaluation: {str(e)}"
                }
            
            # =====================================================
            # Step 7: Parse response and extract decision
            # =====================================================
            decision = "NOT APPROVED"  # Default
            
            # Try to extract structured decision
            if "DECISION:" in full_response:
                lines = full_response.split('\n')
                for line in lines:
                    if line.strip().startswith("DECISION:"):
                        decision_part = line.split("DECISION:")[-1].strip()
                        if "APPROVED" in decision_part.upper():
                            decision = "APPROVED" if "NOT APPROVED" not in decision_part.upper() else "NOT APPROVED"
                        break
            
            print(f"Evaluation complete. Decision: {decision}")
            return {
                "decision": decision,
                "remarks": full_response
            }
            
        except Exception as e:
            return {
                "decision": "NOT APPROVED",
                "remarks": f"System error: {str(e)}"
            }


# =================================================================================
# --- TESTING FUNCTION ---
# =================================================================================
async def test_track_selection():
    """Test the track selection functionality."""
    ai = TrackSelectionAI()
    
    print("=== Testing Track Selection AI ===")
    
    # Test track eligibility evaluation
    # Note: Using faculty_id (database ID), not faculty_code
    result = await ai.evaluate_track_eligibility(faculty_id=4, track_id=2)
    
    print("\n=== EVALUATION RESULT ===")
    print(f"Decision: {result['decision']}")
    print(f"Remarks: {result['remarks']}")


if __name__ == "__main__":
    asyncio.run(test_track_selection())
