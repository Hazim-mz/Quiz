import streamlit as st
import json
import pandas as pd
import plotly.express as px

# Initialize session state variables
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.user_answers = []
    st.session_state.questions = []
    st.session_state.feedback = ""
    st.session_state.original_questions = []  # Store original quiz for full restart

def validate_quiz_data(quiz_data):
    try:
        questions = json.loads(quiz_data)
        if not isinstance(questions, list):
            return False, "Quiz data must be a list of questions."
        for q in questions:
            if not all(key in q for key in ["question", "options", "correct_answer", "explanation"]):
                return False, "Each question must have 'question', 'options', 'correct_answer', and 'explanation'."
            if not isinstance(q["options"], list) or len(q["options"]) < 2:
                return False, "Each question must have at least 2 options."
            if q["correct_answer"] not in q["options"]:
                return False, "Correct answer must be one of the options."
        return True, questions
    except json.JSONDecodeError:
        return False, "Invalid JSON format. Please paste valid JSON quiz data."

def main():
    st.title("Lecture Quiz App")
    
    # Input for quiz data
    quiz_input = st.text_area(
        "Paste your quiz JSON data here:",
        height=200,
        placeholder='[{"question": "What is the capital of France?", "options": ["Paris", "London", "Berlin", "Madrid"], "correct_answer": "Paris", "explanation": "Paris is the capital city of France."}, ...]'
    )
    
    if st.button("Start Quiz"):
        if quiz_input:
            is_valid, result = validate_quiz_data(quiz_input)
            if is_valid:
                st.session_state.questions = result
                st.session_state.original_questions = result.copy()  # Save original quiz
                st.session_state.quiz_started = True
                st.session_state.current_question = 0
                st.session_state.score = 0
                st.session_state.user_answers = []
                st.session_state.feedback = ""
            else:
                st.error(result)
        else:
            st.error("Please paste quiz data to start the quiz.")
    
    if st.session_state.quiz_started and st.session_state.questions:
        total_questions = len(st.session_state.questions)
        
        if st.session_state.current_question < total_questions:
            # Display feedback for the previous question (if any)
            if st.session_state.feedback:
                if "Correct!" in st.session_state.feedback:
                    st.success(st.session_state.feedback)
                else:
                    st.error(st.session_state.feedback)
            
            question_data = st.session_state.questions[st.session_state.current_question]
            st.subheader(f"Question {st.session_state.current_question + 1} of {total_questions}")
            st.write(question_data["question"])
            
            # Display answer options
            user_answer = st.radio(
                "Select your answer:",
                question_data["options"],
                key=f"q{st.session_state.current_question}"
            )
            
            if st.button("Submit Answer"):
                if user_answer == question_data["correct_answer"]:
                    st.session_state.score += 1
                    st.session_state.feedback = f"✅ **Correct!** {question_data['explanation']}"
                else:
                    st.session_state.feedback = (
                        f"❌ **Incorrect.** The correct answer is **{question_data['correct_answer']}.** "
                        f"{question_data['explanation']}"
                    )
                st.session_state.user_answers.append({
                    "question": question_data["question"],
                    "user_answer": user_answer,
                    "correct_answer": question_data["correct_answer"],
                    "was_correct": user_answer == question_data["correct_answer"]
                })
                
                # Move to next question
                st.session_state.current_question += 1
                if st.session_state.current_question < total_questions:
                    st.rerun()
                
        else:
            # Quiz completed
            # Display feedback for the last question
            if st.session_state.feedback:
                if "Correct!" in st.session_state.feedback:
                    st.success(st.session_state.feedback)
                else:
                    st.error(st.session_state.feedback)
            
            st.subheader("Quiz Completed!")
            st.write(f"Your final score: {st.session_state.score} out of {total_questions}")
            percentage = (st.session_state.score / total_questions) * 100
            st.write(f"Percentage: {percentage:.2f}%")
            
            # Pie chart for correct vs incorrect answers
            correct_count = st.session_state.score
            incorrect_count = total_questions - correct_count
            chart_data = pd.DataFrame({
                'Category': ['Correct', 'Incorrect'],
                'Count': [correct_count, incorrect_count]
            })
            fig = px.pie(chart_data, values='Count', names='Category', 
                         color='Category', 
                         color_discrete_map={'Correct': '#00FF00', 'Incorrect': '#FF0000'},
                         title='Quiz Results')
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary table
            st.subheader("Summary of Your Answers:")
            summary_data = []
            for i, answer in enumerate(st.session_state.user_answers):
                status = "Correct" if answer["was_correct"] else "Incorrect"
                summary_data.append({
                    "Question": f"Q{i+1}: {answer['question']}",
                    "Your Answer": answer["user_answer"],
                    "Correct Answer": answer["correct_answer"],
                    "Status": status
                })
            
            summary_df = pd.DataFrame(summary_data)
            # Apply custom styling to the table
            def highlight_status(s):
                color = 'background-color: lightgreen' if s['Status'] == 'Correct' else 'background-color: lightcoral'
                return [color] * len(s)
            
            styled_df = summary_df.style.apply(highlight_status, axis=1)
            st.dataframe(styled_df, use_container_width=True)
            
            # Restart options
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Restart Quiz"):
                    st.session_state.quiz_started = False
                    st.session_state.current_question = 0
                    st.session_state.score = 0
                    st.session_state.user_answers = []
                    st.session_state.questions = st.session_state.original_questions.copy()
                    st.session_state.feedback = ""
                    st.rerun()
            
            with col2:
                if st.button("Restart Quiz for Incorrect Answers"):
                    incorrect_questions = [
                        q for i, q in enumerate(st.session_state.questions)
                        if not st.session_state.user_answers[i]["was_correct"]
                    ]
                    if incorrect_questions:
                        st.session_state.quiz_started = True
                        st.session_state.current_question = 0
                        st.session_state.score = 0
                        st.session_state.user_answers = []
                        st.session_state.questions = incorrect_questions
                        st.session_state.feedback = ""
                        st.rerun()
                    else:
                        st.info("All answers were correct! No questions to retry.")
                        st.session_state.feedback = ""

if __name__ == "__main__":
    main()