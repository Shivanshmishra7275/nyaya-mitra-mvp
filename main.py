# main.py
# =========
# Nyaya Mitra - Legal AI | Phase 4: Real RAG Pipeline with Gemini

import os
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
from rank_bm25 import BM25Okapi

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please create one!")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for in-memory DB
VECTOR_STORE = []
BM25_INDEX = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load JSON and build search index on startup
    global VECTOR_STORE, BM25_INDEX
    try:
        with open("vector_store_mock.json", "r", encoding="utf-8") as f:
            VECTOR_STORE = json.load(f)
            
        # Build BM25 Index for fast keyword search
        corpus = [chunk["text"].lower().split() for chunk in VECTOR_STORE]
        BM25_INDEX = BM25Okapi(corpus)
        logger.info(f"Real Vector store loaded & BM25 index built: {len(VECTOR_STORE)} chunks.")
    except Exception as e:
        logger.error(f"Failed to load vector store: {e}")
    yield

app = FastAPI(title="Nyaya Mitra API", lifespan=lifespan)

# CORS for React Native Web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    user_query: str

class QueryResponse(BaseModel):
    explanation: str
    citations: list[str]
    suggested_next_steps: list[str]

def retrieve_context(query: str, top_k: int = 15):
    """Real BM25 search over the JSON chunks."""
    tokenized_query = query.lower().split()
    top_chunks = BM25_INDEX.get_top_n(tokenized_query, VECTOR_STORE, n=top_k)
    return top_chunks

def generate_legal_response(query: str, chunks: list):
    """Real Gemini 1.5 Flash generation strictly outputting JSON."""
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Combine chunks into context string
    context_text = "\n\n".join([f"Source: {c['metadata']['source']} (Page {c['metadata']['page']})\nText: {c['text']}" for c in chunks])
    
    prompt = f"""You are Nyaya Mitra, an AI legal guide for Indian law. 
Use the following legal context to answer the user's query. 

CONTEXT:
{context_text}

USER QUERY: {query}

INSTRUCTIONS:
1. Base your answer strictly on the provided context.
2. Output your response as a valid, raw JSON object exactly matching this schema:
{{
    "explanation": "Clear, plain-language explanation of the law based on context.",
    "citations": ["List of sources (e.g., 'BNS Page 14')"],
    "suggested_next_steps": ["Actionable advice 1", "Actionable advice 2"]
}}
3. DO NOT wrap the JSON in markdown. Return ONLY the raw JSON string.
"""
    
    response = model.generate_content(prompt, generation_config={"temperature": 0.2})
    raw_text = response.text.strip()
    
    # Clean up markdown if Gemini adds it accidentally
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
        
    return json.loads(raw_text.strip())

@app.post("/api/v1/legal-query", response_model=QueryResponse)
async def legal_query(request: QueryRequest):
    logger.info(f"Real Query received: {request.user_query}")
    try:
        # Retrieve real context
        relevant_chunks = retrieve_context(request.user_query)
        
        if not relevant_chunks:
            raise HTTPException(status_code=404, detail="No relevant legal text found.")
            
        # Generate real answer with Gemini
        response_data = generate_legal_response(request.user_query, relevant_chunks)
        
        return response_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Gemini output invalid JSON: {e}")
        raise HTTPException(status_code=502, detail="AI generated an invalid response format.")
    except Exception as e:
        logger.error(f"Error during query processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))