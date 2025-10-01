import os
from dotenv import load_dotenv
from tqdm import tqdm
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_experimental.text_splitter import SemanticChunker

load_dotenv()

RULES_DATA_PATH = "./rules_data"
RULES_CHROMA_PATH = "./chroma_db_rules"
PROCESSED_LOG_FILE = "./processed_rules.log"

def populate_rules_incrementally():
    print("🚀 Starting rules database population...")
    try:
        with open(PROCESSED_LOG_FILE, 'r') as f:
            processed_files = set(f.read().splitlines())
    except FileNotFoundError:
        processed_files = set()
    
    if not os.path.exists(RULES_DATA_PATH): os.makedirs(RULES_DATA_PATH)
    current_files = set(f for f in os.listdir(RULES_DATA_PATH) if f.lower().endswith('.pdf'))
    new_files_to_process = current_files - processed_files

    if not new_files_to_process:
        print("✅ Database is up-to-date. No new rulebooks to add.")
        return
    
    print(f"📄 Found {len(new_files_to_process)} new rulebook(s): {', '.join(new_files_to_process)}")
    all_new_chunks, embeddings = [], GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    text_splitter = SemanticChunker(embeddings)

    for file_name in new_files_to_process:
        file_path = os.path.join(RULES_DATA_PATH, file_name)
        try:
            loader = PyPDFLoader(file_path)
            chunks = text_splitter.split_documents(loader.load())
            all_new_chunks.extend(chunks)
            print(f"   -> Processed {file_name}, split into {len(chunks)} semantic chunks.")
        except Exception as e:
            print(f"   -> ❌ Error processing {file_name}: {e}")

    if all_new_chunks:
        print(f"\n   -> Adding {len(all_new_chunks)} new chunks to the database...")
        vector_store = Chroma(persist_directory=RULES_CHROMA_PATH, embedding_function=embeddings)
        batch_size = 100
        batches = [all_new_chunks[i:i + batch_size] for i in range(0, len(all_new_chunks), batch_size)]
        for batch in tqdm(batches, desc="Embedding and adding batches"):
            vector_store.add_documents(batch)
        print("\n   -> ✅ Successfully populated rules database.")
        with open(PROCESSED_LOG_FILE, 'a') as f:
            for file_name in new_files_to_process: f.write(f"{file_name}\n")
        print("   -> Updated processed files log.")

if __name__ == "__main__":
    populate_rules_incrementally()