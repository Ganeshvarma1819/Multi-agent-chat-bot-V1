
I've also included a `requirements.txt` file that you'll need for the Python backend setup.

-----

### **Instructions**

1.  **Create `requirements.txt`:** In the root folder of your project (e.g., `Chat_bot_2/`), create a new file named `requirements.txt` and paste the content from the first code block below.
2.  **Create `README.md`:** In the same root folder, create a new file named `README.md` and paste the content from the second code block.

-----

### 1\. `requirements.txt`

```txt
# Main web framework
fastapi
uvicorn[standard]

# Environment variables
python-dotenv

# Core LangChain and Google integration
langchain
langchain-google-genai
langchain-community

# Vector Database
chromadb

# PDF Loading
pypdfium2

# Web Search Tool
langchain-tavily

# Google Cloud Translation API
google-cloud-translate

# Fallback Local Translator (and its dependencies)
transformers
torch
sentencepiece
```

-----

### 2\. `README.md`

```markdown
# Advanced Bilingual RAG Chatbot

This repository contains the complete source code for an advanced, bilingual (English/Telugu) chatbot system built with FastAPI and React. The chatbot leverages a Retrieval-Augmented Generation (RAG) architecture to answer questions from a private knowledge base of PDF documents, and can fall back to a web search for general knowledge questions.

This project is the culmination of several iterations, resulting in a robust, non-streaming backend that prioritizes answer correctness and quality, paired with a clean, user-friendly frontend.

---

## ✨ Features

* **🧠 Retrieval-Augmented Generation (RAG):** Answers questions based on a custom knowledge base of PDF documents.
* **🌐 Dynamic Router:** Intelligently decides whether to answer from the local knowledge base (for specific topics) or perform a web search (for general questions).
* **🗣️ Bilingual Support:** Automatically provides high-quality translations of answers from English to Telugu using the Google Cloud Translation API.
* **☁️ Powered by Google Gemini:** Uses the powerful `gemini-1.5-pro-latest` model for high-quality reasoning and answer synthesis.
* **🚀 Modern Tech Stack:** Built with Python, FastAPI, LangChain, React, and ChromaDB.
* **📄 PDF Data Ingestion:** Includes a script to automatically process, clean, and embed PDF documents into a vector database.
* **✅ Error-Resistant:** The final version uses a non-streaming approach to guarantee clean, non-repetitive answers.

---

## 📂 Project Structure

```

.
├── /data/                  \# Folder to store your source PDF documents

├── /frontend/              \# Contains the React frontend application

│   ├── /src/

│   │   ├── App.css         \# Styles for the application

│   │   ├── App.js          \# Main React component

│   │   └── Api.js          \# Handles API calls to the backend

│   └── package.json

├── .env                    \# Environment variables (you must create this)

├── api.py                  \# The main FastAPI backend server

├── main.py                 \# Script for data ingestion (processing PDFs)

├── requirements.txt        \# Python dependencies for the backend

└── README.md               \# This file

````

---

## 🛠️ Technology Stack

**Backend:**
* Python 3.10+
* FastAPI
* LangChain
* Google Gemini Pro
* Google Cloud Translation API
* ChromaDB (Vector Store)
* Tavily (Web Search)

**Frontend:**
* React
* JavaScript (ES6+)
* CSS3

---

## ⚙️ Setup and Installation

Follow these steps to get the chatbot running on your local machine.

### Prerequisites

* Python 3.10 or higher
* Node.js and npm
* Access to Google Cloud Platform to enable APIs

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <your-project-folder>
````

### 2\. Backend Setup

**a. Create and Activate a Virtual Environment:**

```bash
# For Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# For macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

**b. Install Python Dependencies:**

```bash
pip install -r requirements.txt
```

**c. Set up Google Cloud APIs:**

1.  Go to your [Google Cloud Console](https://console.cloud.google.com/).
2.  Ensure your project is selected.
3.  Enable the **"Vertex AI API"** (or "Generative Language API").
4.  Enable the **"Cloud Translation API"**.
5.  Ensure you have authenticated your local environment (e.g., by running `gcloud auth application-default login`).

**d. Create the Environment File:**
Create a file named `.env` in the root of your project and add your API keys:

```env
# Get from Google AI Studio or Google Cloud Console
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"

# Get from [https://tavily.com/](https://tavily.com/)
TAVILY_API_KEY="YOUR_TAVILY_API_KEY"
```

**e. Prepare Your Data:**

1.  Place all the PDF documents you want the chatbot to learn from inside the `/data` folder.

**f. Run the Data Ingestion Script:**
This script will process the PDFs in the `/data` folder and create your vector database (`chroma_db`).

```bash
python main.py
```

You only need to run this script once, or again whenever you add new documents to the `/data` folder.

### 3\. Frontend Setup

**a. Navigate to the Frontend Directory:**

```bash
cd frontend
```

**b. Install npm Dependencies:**

```bash
npm install
```

### 4\. Running the Application

You need to run the backend and frontend servers in two separate terminals.

**a. Start the Backend Server:**
*Make sure you are in the root project directory and your Python virtual environment is active.*

```bash
uvicorn api:app --reload
```

The backend will be running at `http://localhost:8000`.

**b. Start the Frontend Development Server:**
*Make sure you are in the `/frontend` directory.*

```bash
npm start
```

Your application will open in your browser, usually at `http://localhost:3000`.

-----

## 🤖 How It Works (Architecture)

1.  **User Question:** The React frontend sends a question to the FastAPI `/ask` endpoint.
2.  **Router:** A LangChain router first classifies the question as either `knowledge_base` (for specific rules) or `web_search` (for general knowledge).
3.  **Branching:**
      * If `knowledge_base`, the RAG chain is triggered. It retrieves relevant text chunks from the ChromaDB vector store.
      * If `web_search`, the Web Search chain is triggered. It uses the Tavily API to get search results.
4.  **Synthesis:** The retrieved context (from either RAG or web search) is combined with the user's question in a detailed prompt and sent to the **Google Gemini Pro** model.
5.  **Answer Generation:** Gemini generates a high-quality, non-repetitive English answer. The backend waits for this complete answer.
6.  **Translation:** The complete English answer is sent to the **Google Cloud Translation API** to get a high-quality Telugu translation.
7.  **Response:** The backend sends a single JSON object containing both the final English and Telugu answers back to the React frontend, which then displays them.

-----

## 🔌 API Endpoints

  * `POST /ask`: The main endpoint for asking questions.
      * **Request Body:** `{ "question": "Your question here" }`
      * **Response Body:** `{ "english": "...", "telugu": "..." }`
  * `POST /upload`: Endpoint for uploading new PDF files to the `/data` directory and triggering the ingestion script.

-----

## 🔧 Customization

  * **Knowledge Base:** To change the chatbot's knowledge, simply change the PDF files in the `/data` folder and re-run `python main.py`.
  * **Prompts:** The core "personality" and instructions for the chatbot can be modified by editing the `rag_prompt` and `web_search_prompt` variables in `api.py`.
  * **Model:** You can easily switch the language model by changing the `model` parameter in the `ChatGoogleGenerativeAI` initialization in `api.py`.

<!-- end list -->

```
```
