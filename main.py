import os
import re
import warnings
from dotenv import load_dotenv

# Use the more robust PyPDFium2Loader
from langchain_community.document_loaders import PyPDFium2Loader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

# --- Global constants for paths ---
CHROMA_DB_PATH = "./chroma_db"
DATA_PATH = "./data"
PROCESSED_LOG_FILE = "./processed_files.log"

# Suppress a common warning from the PDF loader
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="pypdfium2._helpers.textpage"
)

def clean_pdf_text(text: str) -> str:
    """A cleaning function to remove headers, footers, and other noise."""
    # Normalize whitespace and split into lines
    lines = text.split('\n')
    cleaned_lines = []

    # Patterns for lines to be REMOVED
    header_footer_patterns = [
        r'^\s*Page\s*\d+\s*(of\s*\d+)?\s*$',
        r'^\s*Confidential\s*$',
        r'(?i)government\s+of\s+telangana',
    ]

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue
        if any(re.search(pattern, stripped_line, re.IGNORECASE) for pattern in header_footer_patterns):
            continue
        cleaned_lines.append(stripped_line)

    return " ".join(cleaned_lines)

def update_and_load_vector_db():
    """Checks for new PDFs, cleans them, and loads them into ChromaDB."""
    print("🚀 Starting database update process...")
    try:
        with open(PROCESSED_LOG_FILE, 'r') as f:
            processed_files = set(f.read().splitlines())
    except FileNotFoundError:
        processed_files = set()
    print(f"   -> Found {len(processed_files)} previously processed file(s).")

    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
    
    current_files = set(f for f in os.listdir(DATA_PATH) if f.endswith('.pdf'))
    new_files_to_process = current_files - processed_files

    if not new_files_to_process:
        print("✅ Database is up-to-date.")
    else:
        print(f"📄 Found {len(new_files_to_process)} new document(s) to process.")
        
        all_chunks = []
        for file_name in new_files_to_process:
            file_path = os.path.join(DATA_PATH, file_name)
            print(f"   -> Processing '{file_name}'...")
            try:
                # Use the better loader
                loader = PyPDFium2Loader(file_path)
                documents = loader.load()
                
                # Clean the text before splitting
                for doc in documents:
                    doc.page_content = clean_pdf_text(doc.page_content)

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
                chunks = text_splitter.split_documents(documents)
                all_chunks.extend(chunks)
                print(f"   -> Split '{file_name}' into {len(chunks)} clean chunks.")
            except Exception as e:
                print(f"   -> ❌ Failed to process '{file_name}': {e}")

        if all_chunks:
            vector_store = Chroma(
                persist_directory=CHROMA_DB_PATH,
                embedding_function=GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            )
            print(f"   -> Adding {len(all_chunks)} new chunks to the database...")
            vector_store.add_documents(all_chunks)
            print("   -> ✅ Successfully added documents.")

            with open(PROCESSED_LOG_FILE, 'a') as f:
                for file_name in new_files_to_process:
                    f.write(f"{file_name}\n")

    print("🏁 Database update process finished.")

if __name__ == "__main__":
    update_and_load_vector_db()