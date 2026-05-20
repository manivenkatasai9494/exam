# app.py

import streamlit as st
import json
import os
import re
from dotenv import load_dotenv
from groq import Groq

# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="AI Quiz Generator",
    page_icon="🧠",
    layout="wide"
)

# ==========================================
# CHECK API KEY
# ==========================================
if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY not found in environment variables.")
    st.info("Create a .env file and add:\n\nGROQ_API_KEY=gsk_your_actual_api_key")
    st.stop()

# ==========================================
# GROQ CLIENT
# ==========================================
client = Groq(api_key=GROQ_API_KEY)

# ==========================================
# GENERATE QUIZ FUNCTION
# ==========================================
def generate_quiz(topic, difficulty="Medium", num_questions=10):
    prompt = f"""
Generate exactly {num_questions} multiple-choice questions on the topic: {topic}.
Difficulty Level: {difficulty}.

Return ONLY valid JSON in this format:
[
  {{
    "question": "What is Python?",
    "options": {{
      "A": "A programming language",
      "B": "A snake",
      "C": "A database",
      "D": "An operating system"
    }},
    "correct_answer": "A",
    "explanation": "Python is a programming language."
  }}
]

Rules:
- Generate exactly {num_questions} questions.
- Difficulty should be {difficulty}.
- Each question must have 4 options: A, B, C, D.
- correct_answer must be one of A, B, C, or D.
- explanation should be short and clear.
- Return only JSON.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a quiz generator. Return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    content = response.choices[0].message.content.strip()

    # Remove markdown code blocks if present
    content = content.replace("```json", "").replace("```", "").strip()

    # Extract JSON array safely
    match = re.search(r"\[.*\]", content, re.DOTALL)
    if match:
        content = match.group(0)

    return json.loads(content)

# ==========================================
# INITIALIZE SESSION STATE
# ==========================================
def init_state():
    defaults = {
        "quiz_generated": False,
        "quiz": [],
        "topic": "",
        "difficulty": "Medium",
        "num_questions": 10,
        "submitted": False,
        "results": [],
        "score": 0
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

# ==========================================
# HEADER
# ==========================================
st.title("🧠 AI Quiz Generator")
st.write("Generate AI-powered quizzes on any topic.")

# ==========================================
# HOME PAGE
# ==========================================
if not st.session_state.quiz_generated:

    topic = st.text_input(
        "📘 Enter Topic",
        placeholder="Python Basics"
    )

    col1, col2 = st.columns(2)

    with col1:
        difficulty = st.selectbox(
            "🎯 Difficulty Level",
            ["Easy", "Medium", "Hard"],
            index=1
        )

    with col2:
        num_questions = st.selectbox(
            "🔢 Number of Questions",
            [5, 10, 15, 20],
            index=1
        )

    if st.button("🚀 Generate Quiz", use_container_width=True):
        if not topic.strip():
            st.warning("Please enter a topic.")
        else:
            with st.spinner("Generating quiz..."):
                try:
                    quiz = generate_quiz(
                        topic=topic,
                        difficulty=difficulty,
                        num_questions=num_questions
                    )

                    if len(quiz) != num_questions:
                        st.error(
                            f"AI generated {len(quiz)} questions instead of "
                            f"{num_questions}. Please try again."
                        )
                    else:
                        st.session_state.quiz = quiz
                        st.session_state.topic = topic
                        st.session_state.difficulty = difficulty
                        st.session_state.num_questions = num_questions
                        st.session_state.quiz_generated = True
                        st.session_state.submitted = False
                        st.rerun()

                except Exception as e:
                    st.error(f"Error generating quiz: {e}")

# ==========================================
# QUIZ PAGE
# ==========================================
elif not st.session_state.submitted:

    st.header(f"📘 Topic: {st.session_state.topic}")

    col1, col2 = st.columns(2)

    with col1:
        st.info(f"🎯 Difficulty: {st.session_state.difficulty}")

    with col2:
        st.info(f"🔢 Questions: {st.session_state.num_questions}")

    with st.form("quiz_form"):
        for i, q in enumerate(st.session_state.quiz):
            st.subheader(f"Q{i+1}. {q['question']}")

            st.radio(
                "Select your answer:",
                ["A", "B", "C", "D"],
                format_func=lambda x, opts=q["options"]: f"{x}. {opts[x]}",
                key=f"q_{i}"
            )

            st.divider()

        submitted = st.form_submit_button(
            "✅ Submit Quiz",
            use_container_width=True
        )

    if submitted:
        correct = 0
        results = []

        for i, q in enumerate(st.session_state.quiz):
            user_answer = st.session_state[f"q_{i}"]
            correct_answer = q["correct_answer"]
            is_correct = user_answer == correct_answer

            if is_correct:
                correct += 1

            results.append({
                "question": q["question"],
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "explanation": q["explanation"],
                "is_correct": is_correct
            })

        st.session_state.results = results
        st.session_state.score = correct
        st.session_state.submitted = True
        st.rerun()

# ==========================================
# RESULTS PAGE
# ==========================================
if st.session_state.submitted:

    total = len(st.session_state.quiz)
    correct = st.session_state.score
    wrong = total - correct
    percentage = (correct / total) * 100

    if percentage >= 90:
        rating = "🏆 Excellent"
    elif percentage >= 75:
        rating = "🌟 Very Good"
    elif percentage >= 60:
        rating = "👍 Good"
    elif percentage >= 40:
        rating = "🙂 Average"
    else:
        rating = "📘 Needs Improvement"

    st.title("📊 Quiz Report")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Score", f"{correct}/{total}")
    col2.metric("Correct", correct)
    col3.metric("Wrong", wrong)
    col4.metric("Percentage", f"{percentage:.1f}%")

    st.success(f"Rating: {rating}")

    st.subheader("📝 Detailed Review")

    for i, result in enumerate(st.session_state.results):
        icon = "✅" if result["is_correct"] else "❌"

        with st.expander(f"{icon} Q{i+1}: {result['question']}"):
            st.write(f"**Your Answer:** {result['user_answer']}")
            st.write(f"**Correct Answer:** {result['correct_answer']}")
            st.write(f"**Explanation:** {result['explanation']}")

    # Download report
    report = {
        "topic": st.session_state.topic,
        "difficulty": st.session_state.difficulty,
        "score": correct,
        "total_questions": total,
        "percentage": percentage,
        "rating": rating,
        "results": st.session_state.results
    }

    st.download_button(
        "📥 Download Report (JSON)",
        data=json.dumps(report, indent=2),
        file_name="quiz_report.json",
        mime="application/json",
        use_container_width=True
    )

    # Restart quiz
    if st.button("🔄 Generate New Quiz", use_container_width=True):
        st.session_state.clear()
        st.rerun()