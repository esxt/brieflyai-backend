import os
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import docx
import spacy

app = Flask(__name__)
CORS(app)
# Load spaCy for text cleaning
nlp = spacy.load("en_core_web_sm")

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Fine-tuned GPT-3.5 model ID (disabled for now, will most likely be used for final submission)
# FINE_TUNED_MODEL = "ft:gpt-3.5-turbo:my-org-id:my-finetuned-model-id"

def preprocess_text(text):
    """Cleans text while keeping full sentence structure."""
    doc = nlp(text)
    cleaned_text = " ".join([token.text for token in doc if not token.is_punct])
    return cleaned_text.strip()

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text.strip()

def extract_text_from_docx(file_path):
    """Extracts text from a DOCX file."""
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def chunk_text(text, chunk_size=800):
    """Splits text into smaller chunks while keeping full sentences."""
    sentences = text.split(". ")
    chunks = []
    current_chunk = []

    for sentence in sentences:
        if sum(len(s.split()) for s in current_chunk) + len(sentence.split()) <= chunk_size:
            current_chunk.append(sentence)
        else:
            chunks.append(". ".join(current_chunk) + ".")
            current_chunk = [sentence]

    if current_chunk:
        chunks.append(". ".join(current_chunk) + ".")

    return chunks

def generate_summary(text, fine_tuned=False, temperature=1, max_tokens=200):
    """Generates a summary using OpenAI's GPT-4o."""
    
    # Use GPT-4o instead of fine-tuned GPT-3.5
    # model = FINE_TUNED_MODEL if fine_tuned else "gpt-4o"
    model = "gpt-4o"  # Since fine-tuning is not being used

    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an AI that summarizes text concisely while preserving key details."},
            {"role": "user", "content": text}
        ],
        temperature=temperature,  # Controls randomness (Anything above 2 and the model starts hallucinating)
        max_tokens=max_tokens,  # Summary length limit
        top_p=0.9,  # Alternative sampling strategy
        frequency_penalty=0.2,  # Reduce repetition
        presence_penalty=0.1  # Encourage new information
    )

    summary = response.choices[0].message.content
    return summary

def summarise_large_text(text, fine_tuned=False):
    """Handles large text by summarizing smaller chunks separately."""
    chunks = chunk_text(text)
    
    # Always use GPT-4o, fine-tuning is currently not in use
    # summaries = [generate_summary(chunk, fine_tuned=fine_tuned) for chunk in chunks]
    summaries = [generate_summary(chunk, fine_tuned=False) for chunk in chunks]
    
    return " ".join(summaries)

@app.route("/summarise", methods=["POST"])
def summarise():
    """API endpoint to summarise text input."""
    data = request.json
    text = data.get("text", "")
    
    # fine_tuned = data.get("fine_tuned", False)  # Fine-tuning is disabled
    fine_tuned = False  # Always use GPT-4o

    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    # Preprocess text
    cleaned_text = preprocess_text(text)
    
    # Generate summary
    summary = summarise_large_text(cleaned_text, fine_tuned=fine_tuned)
    
    return jsonify({"summary": summary})

@app.route("/upload", methods=["POST"])
def upload_file():
    """API endpoint to upload and summarise documents."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    file_ext = os.path.splitext(file.filename)[-1].lower()
    
    if file_ext not in [".pdf", ".docx", ".txt"]:
        return jsonify({"error": "Unsupported file format"}), 400
    
    file_path = "uploads/" + file.filename
    file.save(file_path)
    
    # Extract text
    if file_ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif file_ext == ".docx":
        text = extract_text_from_docx(file_path)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    
    os.remove(file_path)  # Delete file after processing
    
    # Preprocess text
    cleaned_text = preprocess_text(text)
    
    # Generate summary
    summary = summarise_large_text(cleaned_text)
    
    return jsonify({"summary": summary})

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to the GPT-4o Text Summarization API!"})

if __name__ == "__main__":
    app.run(debug=True)
