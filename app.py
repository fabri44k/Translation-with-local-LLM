from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import json
from llm.llm_manager import LLMManager 
import re



MAX_WORD_DEFAULT = 200
MODEL_CONFIG_FILE_PATH = "./config.json"
SUPPORTED_FILE_EXTENSIONS = ['.txt', '.md']

app = Flask(__name__)
CORS(app)

# get the list of available models (for select in html)
def get_models_name_list(config_file_path):
    try:
        with open(config_file_path, 'r') as file:
            config = json.load(file)
        return [n["name"] for n in config.get("models", []) if "name" in n]
    except Exception as e:
        raise RuntimeError(f"Error reading model list from {config_file_path}: {str(e)}")

# get the model configuration for the requested model
def get_model_config(config_file_path, model_name):
    try:
        with open(config_file_path, 'r') as file:
            config = json.load(file)
        return next((m for m in config.get("models", []) if m.get("name") == model_name), None)
    except Exception as e:
        raise RuntimeError(f"Error reading model list from {config_file_path}: {str(e)}")

# get the llm prompt from the config file
def get_llm_prompt(config_file_path):
    try:
        with open(config_file_path, 'r') as file:
            config = json.load(file)
        return config.get("prompt", "Translate the following text to {language}: {text}")
    except Exception as e:
        raise RuntimeError(f"Error reading model list from {config_file_path}: {str(e)}")



def get_word_count(text):
    return len(text.split())



# apply chunking for the llm input
def split_text(text, max_chunk_size=100):
    if not text:
        return []

    paragraphs = re.split(r'\n\s*\n', text.strip())
    chunks = []
    for paragraph in paragraphs:
        clean_para = ' '.join(paragraph.split())
        if not clean_para:
            continue
        if len(clean_para.split()) <= max_chunk_size:
            chunks.append(clean_para)
            continue

        current_chunk = ""
        sentences = re.split(r'(?<=[.!?])\s+', clean_para)
        for sentence in sentences:
            if len(current_chunk.split()) + len(sentence.split()) <= max_chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        if current_chunk:
            chunks.append(current_chunk.strip())
    return chunks


def translate_text(chunk_mode, llm: LLMManager, input_text, language):
    if not chunk_mode:
        print("chunking disabled")
        dict_for_template = {
            "language": language,
            "text": input_text
        }
        result = llm.answer_query(dict_for_template)
        return result
    else:
        print("chunking enabled")
        chunks = split_text(input_text)
        translated_chunks = []
        for chunk in chunks:
            dict_for_template = {
                "language": language,
                "text": chunk
            }
            translated_chunk = llm.answer_query(dict_for_template)
            translated_chunks.append(translated_chunk + "\n\n")
        
        # final string with all translated chunks
        translated_chunks_final = ''.join(translated_chunks).strip()

        return translated_chunks_final

        



# === Flask Endpoints ===
@app.route("/translate", methods=["POST"])
def translate():
    try:
        data = request.get_json()
        print(data)
        text = data.get("text", "")
        requested_model = data.get("model", "")
        language = data.get("language", "English")
        

        if not text:
            return jsonify({"response": False, "message": "No text provided."})

        model_info = get_model_config(MODEL_CONFIG_FILE_PATH, requested_model)
        if not model_info:
            return jsonify({"response": False, "message": f"Model {requested_model} not found in config.json !"})

        max_word_count = model_info.get("max_word_for_prompt", MAX_WORD_DEFAULT)
        thinking_enabled = model_info.get("thinking_enabled", False)
        temperature = model_info.get("temperature", 0.4)
        template = get_llm_prompt(MODEL_CONFIG_FILE_PATH)

        word_count = get_word_count(text)
        chunk_mode = word_count > max_word_count
        
        llm = LLMManager("ollama", requested_model, temperature, template, thinking_enabled)

        translation = translate_text(chunk_mode, llm, text, language)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        response = jsonify({
            "response": True,
            "translation": translation,
            "timestamp": timestamp,
            "chunk_mode": chunk_mode
        })
        print(response.get_json())
        return response
    
    except Exception as e:
        return jsonify({"response": False, "message": f"Error: {str(e)}"})



@app.route("/llmList", methods=["POST"])
def get_llm_list():
    try:
        response = jsonify({"response": True, "models": get_models_name_list(MODEL_CONFIG_FILE_PATH)})
        print(response.get_json())
        return response
    except Exception as e:
        return jsonify({"response": False, "message": f"Error: {str(e)}"})


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# === END Flask Endpoints ===


if __name__ == "__main__":
    app.run(debug=True)
