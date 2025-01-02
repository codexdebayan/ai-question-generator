from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
import os
import re
from pypdf import PdfReader
from flask_cors import CORS

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("No GEMINI_API_KEY found in .env file!")

genai.configure(api_key=api_key)
modal = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return render_template("index.html")


def get_gemini_response(input, prompt):
    response = modal.generate_content([input, prompt])
    return response.text


def extract_text_from_pdf(file):
    reader = PdfReader(file)
    print(file)
    no_of_pages = len(reader.pages)
    text_content = ""
    for i in range(no_of_pages):
        page = reader.pages[i]
        temp_text = page.extract_text()
        if temp_text:
            text_content += "\n" + temp_text  # Corrected concatenation
    return text_content


prompt_templates = {
    "MCQ": """
        You are a question generator. Create 10 multiple-choice questions based on the provided text.
        Format each question as follows:
        - Question number.
        - Four options (A, B, C, D).
        Ensure the questions are clear, concise, and relevant to the input text.
        
        Ensure the questions are different from previosuly generated questions.
    """,
    "MCQ with Answers": """
        You are a question generator. Create 10 multiple-choice questions with answers based on the provided text.
        Format each question as follows:
        - Question number.
        - Four options (A, B, C, D).
        - Provide the correct answer after each question.
        Ensure the questions are clear, concise, and relevant to the input text.
        
        Ensure the questions are different from previosuly generated questions.
    """,
    "Long Questions": """
        You are a question generator. Create 5 long-answer questions based on the provided text.
        Format each question with a question number and ensure it requires detailed responses.
        
        Ensure the questions are different from previosuly generated questions.
    """,
    "Long Questions with Answers": """
        You are a question generator. Create 5 long-answer questions with answers based on the provided text.
        Format each question with a question number followed by the answer.
        Ensure the questions and answers are clear, detailed, and relevant to the input text.
        
        Ensure the questions are different from previosuly generated questions.
    """,
}


@app.route("/generate", methods=["POST"])
def generate():
    try:
        input_text = request.form.get("inputText")
        option = request.form.get("option")
        pdf_file = request.files.get("pdfFile")

        if not input_text and not pdf_file:
            return jsonify({"msg": "Input text or PDF file is required!"}), 400

        if pdf_file:
            input_text = extract_text_from_pdf(pdf_file)

        prompt_template = prompt_templates.get(option)
        if not prompt_template:
            return jsonify({"message": "Invalid option selected"}), 400

        prompt = prompt_template

        response = get_gemini_response(input_text, prompt)

        # Make sentences starting with ** bold
        formatted_response = response.replace("\n", "<br>").replace(". ", ".<br><br>")

        # Find sentences starting with ** and ending with ** and wrap them in <strong> tags
        formatted_response = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", formatted_response)
        
        # Find sentences starting with * and ending with * and wrap them in <em> tags for semi-bold
        formatted_response = re.sub(r"\*(.*?)\*", r"<em>\1</em>", formatted_response)

        return jsonify({"message": formatted_response}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500




if __name__ == "__main__":
    app.run(host="0.0.0.0",port="5050",debug=True)
