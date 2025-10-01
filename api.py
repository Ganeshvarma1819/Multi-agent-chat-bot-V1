import os
import random
import re
import asyncio
import shutil
import json
from dotenv import load_dotenv
from typing import List, cast
import time

# FastAPI Imports
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from fastapi.concurrency import run_in_threadpool

# LangChain & AI Model Imports
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.runnables import RunnableBranch, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Agent Imports
from langchain_tavily import TavilySearch

# Import Google Cloud Translate
from google.cloud import translate_v2 as translate

# Load environment variables
load_dotenv()

# --- GLOBAL VARIABLES & MODELS ---
vector_store_global = None
llm = None
translate_client = None
CHROMA_DB_PATH = "./chroma_db"

# --- PYDANTIC MODELS ---
class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    english: str
    telugu: str

# --- UTILITY FUNCTIONS ---
def deduplicate_docs(docs: List[Document]) -> List[Document]:
    seen_contents = set()
    unique_docs = []
    for doc in docs:
        normalized_content = re.sub(r'\s+', ' ', doc.page_content).strip()
        if normalized_content not in seen_contents:
            unique_docs.append(doc)
            seen_contents.add(normalized_content)
    return unique_docs

# --- FASTAPI APP ---
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost:3001"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup_event():
    global vector_store_global, llm, translate_client
    print("🚀 Server starting up...")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.1)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store_global = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embeddings)
    try:
        translate_client = translate.Client()
        print("✅ Google Translate client loaded.")
    except Exception as e:
        print(f"❌ Warning: Could not load Google Translate client. Translation will not work. Error: {e}")
        translate_client = None
    print("✅ All models and databases loaded. Server is ready!")

# --- CHAIN FACTORY ---
async def get_full_chain():
    assert llm is not None and vector_store_global is not None
    def format_docs(docs: List[Document]) -> str:
        return "\n\n".join(doc.page_content for doc in docs)

    # RAG Chain
    retriever = vector_store_global.as_retriever(search_kwargs={'k': 7})
    rag_prompt = PromptTemplate.from_template(
        """
        You are a precise building code assistant. Answer the user's QUESTION using ONLY the provided CONTEXT.
        Your answer must be grammatically perfect and professional.
        CRITICAL RULE: DO NOT repeat any information. Synthesize all related facts into a single, cohesive statement.
        Present your answer using markdown. Use bullet points for lists.
        CONTEXT: {context}
        ---
        QUESTION: {question}
        ANSWER:
        """
    )
    rag_chain = (
        {
            "context": RunnableLambda(lambda x: x["question"]) | retriever | RunnableLambda(deduplicate_docs) | RunnableLambda(format_docs),
            "question": RunnableLambda(lambda x: x["question"])
        }
        | rag_prompt | llm | StrOutputParser()
    )

    # Web Search Chain
    web_search_tool = TavilySearch(max_results=3)
    web_search_prompt = PromptTemplate.from_template(
        """You are an expert AI assistant. Answer the user's QUESTION based on the SEARCH RESULTS.
        Your answer must be a single, cohesive, and non-repetitive response.
        SEARCH RESULTS: {context}
        ---
        QUESTION: {question}
        ANSWER:"""
    )
    # ✅ FIXED: This chain now correctly extracts the 'question' and passes it to the search tool.
    web_search_chain = (
        {
            "context": RunnableLambda(lambda x: x["question"]) | web_search_tool,
            "question": RunnableLambda(lambda x: x["question"])
        }
        | web_search_prompt
        | llm
        | StrOutputParser()
    )


    # ROUTER
    router_prompt = PromptTemplate.from_template(
        """Classify the user's question into: 'knowledge_base' or 'web_search'.
        - Use 'knowledge_base' for questions about building rules, G.O. 168, setbacks, etc.
        - Use 'web_search' for all other general knowledge questions.
        USER QUESTION: {question}
        Classification:"""
    )
    router_chain = router_prompt | llm | StrOutputParser()
    branch = RunnableBranch(
        (lambda x: "web_search" in x["topic"].lower(), web_search_chain),
        rag_chain,
    )
    return {"topic": router_chain, "question": RunnablePassthrough()} | branch

# --- API ENDPOINT ---
@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    try:
        # 1. Get the full, clean English answer. No streaming.
        chain = await get_full_chain()
        print(f"Invoking chain for question: {request.question}")
        full_english_answer = await chain.ainvoke(request.question)
        print("Chain invoked successfully.")

        # 2. Translate the complete, clean answer using Google Translate.
        telugu_answer = "[Translator not available]"
        if translate_client:
            print("Translating to Telugu with Google Cloud API...")
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: translate_client.translate(full_english_answer, target_language='te')
            )
            telugu_answer = result['translatedText']
            print("Translation successful.")

        # 3. Return the complete, clean response object.
        return JSONResponse(content={"english": full_english_answer, "telugu": telugu_answer})

    except Exception as e:
        print(f"Error in ask_question endpoint: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

# ... other endpoints like /upload can remain ...
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # This endpoint is separate and doesn't need changes.
    # Note: You'll need to re-add the process_and_embed_documents function if you use this.
    pass