import json
import os

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ============================================================
# CHECK API KEY
# ============================================================

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. "
        "Please add your Gemini API key inside the .env file."
    )


# ============================================================
# CREATE FLASK APPLICATION
# ============================================================

app = Flask(__name__)


# ============================================================
# CREATE GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            attempts=4,
            initial_delay=1,
            max_delay=8,
            exp_base=2,
            jitter=0.2,
            http_status_codes=[408, 500, 502, 503, 504],
        )
    ),
)


# ============================================================
# GEMINI MODEL
# ============================================================

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
QUIZ_MODEL_NAME = os.getenv("GEMINI_QUIZ_MODEL", "gemini-3.5-flash-lite")
FALLBACK_MODEL_NAME = os.getenv(
    "GEMINI_FALLBACK_MODEL",
    "gemini-3.5-flash-lite",
)


def generate_content(*, model, contents, config=None):

    try:

        return client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

    except errors.APIError as error:

        if error.code != 429:
            raise

        fallback_model = FALLBACK_MODEL_NAME

        if fallback_model == model:
            fallback_model = MODEL_NAME

        if fallback_model == model:
            raise

        print(
            f"Quota exhausted for {model}; retrying with {fallback_model}."
        )

        try:

            return client.models.generate_content(
                model=fallback_model,
                contents=contents,
                config=config,
            )

        except errors.APIError as fallback_error:

            if fallback_error.code == 429:
                raise RuntimeError(
                    "Gemini request quota is exhausted for the selected and fallback models. "
                    "Wait for the quota reset or enable billing in Google AI Studio."
                ) from fallback_error

            raise

QUIZ_RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "questions": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "question": types.Schema(type=types.Type.STRING),
                    "choices": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "label": types.Schema(
                                    type=types.Type.STRING,
                                    enum=["A", "B", "C", "D"],
                                ),
                                "text": types.Schema(type=types.Type.STRING),
                            },
                            required=["label", "text"],
                        ),
                    ),
                    "correct_answer": types.Schema(
                        type=types.Type.STRING,
                        enum=["A", "B", "C", "D"],
                    ),
                    "explanation": types.Schema(type=types.Type.STRING),
                },
                required=["question", "choices", "correct_answer", "explanation"],
            ),
        ),
    },
    required=["questions"],
)


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template("index.html")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "message": "EduGenie backend is running successfully."
    })


# ============================================================
# ASK EDUGENIE
# ============================================================

@app.route("/api/ask", methods=["POST"])
def ask_edugenie():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No data received."
            }), 400

        question = str(
            data.get("question", "")
        ).strip()

        subject = str(
            data.get("subject", "General")
        ).strip()

        level = str(
            data.get("level", "College")
        ).strip()

        mode = str(
            data.get("mode", "Learn")
        ).strip()


        # ----------------------------------------------------
        # Validate question
        # ----------------------------------------------------

        if not question:

            return jsonify({
                "success": False,
                "error": "Please enter a question."
            }), 400


        # ----------------------------------------------------
        # Create prompt
        # ----------------------------------------------------

        prompt = f"""
You are EduGenie, an AI-powered learning assistant.

Your job is to help students understand academic topics clearly.

Student information:

Student Level:
{level}

Subject:
{subject}

Learning Mode:
{mode}

Student Question:
{question}


Follow these instructions carefully:

1. Answer the student's question accurately.
2. Use simple and easy-to-understand English.
3. Explain difficult concepts step by step.
4. Use examples when useful.
5. Use headings and bullet points when appropriate.
6. Avoid unnecessary complicated language.
7. If the student asks for programming code, provide complete working code.
8. If the student asks for an exam answer, make it easy to memorize.
9. If the student asks for a definition, provide the definition first.
10. Do not pretend to know information that you are unsure about.
11. Do not give irrelevant information.
12. Make the response suitable for the student's level.

Learning mode instructions:

If the mode is "Exam":
- Give an exam-friendly answer.
- Include important points.
- Include a short conclusion.
- Make it easy to write in an examination.

If the mode is "Simple":
- Explain like a beginner.
- Use very simple examples.

If the mode is "Detailed":
- Give a deeper explanation.
- Include examples and important concepts.

If the mode is "Learn":
- Teach the concept naturally.
- Explain the concept step by step.

At the end, provide a section called:

Quick Revision

with 3 to 5 important points.
"""


        # ----------------------------------------------------
        # Generate Gemini response
        # ----------------------------------------------------

        response = generate_content(
            model=MODEL_NAME,
            contents=prompt
        )


        answer = response.text


        return jsonify({
            "success": True,
            "answer": answer
        })


    except Exception as error:

        print("ASK ERROR:", error)

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ============================================================
# SUMMARIZE STUDY MATERIAL
# ============================================================

@app.route("/api/summarize", methods=["POST"])
def summarize():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "error": "No data received."
            }), 400


        text = str(
            data.get("text", "")
        ).strip()


        if not text:

            return jsonify({
                "success": False,
                "error": "Please enter study material."
            }), 400


        prompt = f"""
You are EduGenie, an AI study assistant.

Summarize the following study material for a college student.

Requirements:

- Keep the important information.
- Remove unnecessary repetition.
- Use simple English.
- Use headings.
- Use bullet points.
- Highlight important definitions.
- Highlight important concepts.
- Include important examples if present.
- Make the summary useful for exam revision.

Study Material:

{text}

At the end provide:

Quick Revision

with the most important points.
"""


        response = generate_content(
            model=MODEL_NAME,
            contents=prompt
        )


        summary = response.text


        return jsonify({
            "success": True,
            "summary": summary
        })


    except Exception as error:

        print("SUMMARY ERROR:", error)

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ============================================================
# GENERATE QUIZ
# ============================================================

@app.route("/api/quiz", methods=["POST"])
def generate_quiz():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "error": "No data received."
            }), 400


        topic = str(
            data.get("topic", "")
        ).strip()


        number = data.get(
            "number",
            5
        )


        if not topic:

            return jsonify({
                "success": False,
                "error": "Please enter a quiz topic."
            }), 400


        try:

            number = int(number)

        except ValueError:

            number = 5


        if number < 1:
            number = 1

        if number > 20:
            number = 20


        prompt = f"""
You are EduGenie, an AI quiz generator.

Create {number} multiple-choice questions about:

{topic}

For every question, provide four choices labeled A, B, C, and D, exactly one correct answer label, and a short explanation that teaches why it is correct.

Requirements:

- Questions should be educational.
- Questions should be suitable for college students.
- Do not repeat questions.
- Include different difficulty levels.
- Keep explanations short and clear.
- Make all choices plausible and ensure the correct answer matches the explanation.
"""


        response = generate_content(
            model=QUIZ_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=QUIZ_RESPONSE_SCHEMA,
            ),
        )


        quiz = json.loads(response.text)
        questions = quiz.get("questions")

        if not isinstance(questions, list) or not questions:
            raise ValueError("The AI did not return any quiz questions. Please try again.")


        return jsonify({
            "success": True,
            "questions": questions
        })


    except Exception as error:

        print("QUIZ ERROR:", error)

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ============================================================
# STUDY PLAN GENERATOR
# ============================================================

@app.route("/api/study-plan", methods=["POST"])
def study_plan():

    try:

        data = request.get_json()

        subject = str(
            data.get("subject", "")
        ).strip()

        days = data.get(
            "days",
            7
        )

        hours = data.get(
            "hours",
            2
        )


        if not subject:

            return jsonify({
                "success": False,
                "error": "Please enter a subject."
            }), 400


        prompt = f"""
You are EduGenie, an AI study planning assistant.

Create a practical study plan for:

Subject:
{subject}

Number of days:
{days}

Study hours per day:
{hours}

Create a day-by-day plan.

For every day include:

Day number
Topic
Study activity
Revision activity
Practice activity

Make the plan realistic for a college student.

Use simple formatting.
"""


        response = generate_content(
            model=MODEL_NAME,
            contents=prompt
        )


        plan = response.text


        return jsonify({
            "success": True,
            "plan": plan
        })


    except Exception as error:

        print("STUDY PLAN ERROR:", error)

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ============================================================
# APPLICATION ERROR HANDLER
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({
        "success": False,
        "error": "Page not found."
    }), 404


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    print("")
    print("========================================")
    print("        EDUGENIE AI ASSISTANT")
    print("========================================")
    print("")
    print("Server running at:")
    print("http://127.0.0.1:5000")
    print("")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )