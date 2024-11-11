import os
import streamlit as st
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define a function to generate the story response using OpenAI
def generate_story_response(conversation_history):
    # Using the updated method with openai.ChatCompletion.create for the new API
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=conversation_history,
        temperature=0.7,
    )
    return response.choices[0].message["content"]

# Main Streamlit app function
def main():
    st.title("The Cursed Forest - Interactive Adventure")

    # Introduction to the story
    intro_message = {
        "role": "assistant",
        "content": (
            "Welcome, brave soul! You are Kaelen, a wanderer who finds himself lost in the mysterious Cursed Forest. "
            "Strange creatures, hidden dangers, and an ancient curse lurk in the shadows. Legend has it that the heart of the forest holds a powerful artifact, "
            "but no one who has ventured deep enough has ever returned. It's up to you to decide whether to seek the artifact or escape the forest alive. "
            "But beware, not all paths lead to safety... "
            "\n\nYour adventure begins at the edge of the forest, where an eerie fog hangs in the air. Do you wish to enter the forest or turn back to safety?"
        )
    }

    # Initialize chat history in session state
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = [intro_message]
        st.session_state.messages = [intro_message]

    # Display the chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Function to handle interaction and generate the next part of the story
    def handle_interaction(user_input):
        # Add user input to conversation history
        user_message = {"role": "user", "content": user_input}
        st.session_state.conversation_history.append(user_message)

        # Generate AI response based on the updated conversation history
        ai_response = generate_story_response(st.session_state.conversation_history)

        # Add AI response to conversation history
        ai_message = {"role": "assistant", "content": ai_response}
        st.session_state.conversation_history.append(ai_message)

        # Update the messages displayed on the app
        st.session_state.messages.append(user_message)
        st.session_state.messages.append(ai_message)

    # Accept user input
    user_input = st.chat_input("What will you do next?")

    # When user enters a response, process it
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        handle_interaction(user_input)

        # Check for an end condition in the AI response
        if "The End." in st.session_state.messages[-1]["content"]:
            st.write("### Game Over")

if __name__ == "__main__":
    main()
