import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict, Any
import re

# Load environment variables and configure API
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Define game items and their effects
GAME_ITEMS = {
    'health_potion': {'name': 'Health Potion', 'health_effect': 30},
    'healing_herb': {'name': 'Healing Herb', 'health_effect': 15},
    'cursed_artifact': {'name': 'Cursed Artifact', 'health_effect': -20},
    'magic_shield': {'name': 'Magic Shield', 'defense': 10},
    'ancient_sword': {'name': 'Ancient Sword', 'attack': 15},
    'mysterious_ring': {'name': 'Mysterious Ring', 'magic': 10},
    'forest_map': {'name': 'Forest Map', 'navigation': True},
    'magic_compass': {'name': 'Magic Compass', 'navigation': True},
    'crystal_key': {'name': 'Crystal Key', 'unlock': True},
}

# Define dangerous actions and their health impacts
DANGEROUS_ACTIONS = {
    'fight': {'min_damage': 10, 'max_damage': 25},
    'fall': {'min_damage': 5, 'max_damage': 15},
    'poison': {'min_damage': 15, 'max_damage': 30},
    'curse': {'min_damage': 20, 'max_damage': 40},
    'trap': {'min_damage': 10, 'max_damage': 20},
}

def apply_custom_styles():
    st.markdown("""
        <style>
        .stButton button {
            width: 100%;
            border-radius: 5px;
            margin: 2px;
        }
        .story-text {
            background-color: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }
        .health-critical {
            color: red;
            font-weight: bold;
        }
        .health-warning {
            color: orange;
            font-weight: bold;
        }
        .health-good {
            color: green;
            font-weight: bold;
        }
        .item-found {
            color: purple;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "game_state" not in st.session_state:
        st.session_state.game_state = {
            "health": 100,
            "inventory": [],
            "choices_made": 0,
            "damage_taken": 0,
            "items_found": 0
        }

def create_model() -> genai.GenerativeModel:
    """Create and configure the Gemini model"""
    generation_config = {
        "temperature": 0.8,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1024,
        "response_mime_type": "text/plain",
    }
    
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config
    )

def check_for_items(text: str) -> List[str]:
    """Check for items mentioned in the text and return found items"""
    found_items = []
    for item_key, item_data in GAME_ITEMS.items():
        if item_data['name'].lower() in text.lower():
            found_items.append(item_key)
    return found_items

def check_for_danger(text: str) -> List[str]:
    """Check for dangerous actions in the text"""
    dangers = []
    for danger in DANGEROUS_ACTIONS.keys():
        if danger in text.lower():
            dangers.append(danger)
    return dangers

def update_game_state(response_text: str):
    """Update game state based on the story response"""
    
    # Check for items
    found_items = check_for_items(response_text)
    for item in found_items:
        if item not in st.session_state.game_state['inventory']:
            st.session_state.game_state['inventory'].append(item)
            st.session_state.game_state['items_found'] += 1
            
            # Apply immediate health effects if applicable
            if 'health_effect' in GAME_ITEMS[item]:
                health_change = GAME_ITEMS[item]['health_effect']
                st.session_state.game_state['health'] = min(100, st.session_state.game_state['health'] + health_change)
    
    # Check for dangerous actions
    dangers = check_for_danger(response_text)
    for danger in dangers:
        damage = DANGEROUS_ACTIONS[danger]['min_damage']
        st.session_state.game_state['health'] -= damage
        st.session_state.game_state['damage_taken'] += damage
    
    # Ensure health stays within bounds
    st.session_state.game_state['health'] = max(0, min(100, st.session_state.game_state['health']))
    
    # Increment choices counter
    st.session_state.game_state['choices_made'] += 1

def display_game_state():
    """Display the current game state in the sidebar"""
    st.sidebar.header("Game Status")
    
    # Health bar with color coding
    health = st.session_state.game_state['health']
    health_color = (
        'red' if health < 30 else
        'orange' if health < 60 else
        'green'
    )
    st.sidebar.markdown(f"<p style='color: {health_color}'>Health: {health}%</p>", unsafe_allow_html=True)
    st.sidebar.progress(health / 100)
    
    # Inventory
    st.sidebar.subheader("Inventory")
    if st.session_state.game_state['inventory']:
        for item in st.session_state.game_state['inventory']:
            item_name = GAME_ITEMS[item]['name']
            effects = []
            if 'health_effect' in GAME_ITEMS[item]:
                effects.append(f"Health: {'+'if GAME_ITEMS[item]['health_effect'] > 0 else ''}{GAME_ITEMS[item]['health_effect']}")
            if 'defense' in GAME_ITEMS[item]:
                effects.append(f"Defense: +{GAME_ITEMS[item]['defense']}")
            if 'attack' in GAME_ITEMS[item]:
                effects.append(f"Attack: +{GAME_ITEMS[item]['attack']}")
            
            effect_text = f" ({', '.join(effects)})" if effects else ""
            st.sidebar.write(f"- {item_name}{effect_text}")
    else:
        st.sidebar.write("Empty")
    
    # Statistics
    st.sidebar.subheader("Statistics")
    st.sidebar.write(f"Choices made: {st.session_state.game_state['choices_made']}")
    st.sidebar.write(f"Damage taken: {st.session_state.game_state['damage_taken']}")
    st.sidebar.write(f"Items found: {st.session_state.game_state['items_found']}")

def generate_story_response(conversation_history: List[Dict[str, Any]]) -> str:
    """Generate the next part of the story using the Gemini model"""
    try:
        model = create_model()
        chat_session = model.start_chat(history=conversation_history)
        
        # Enhanced context for better story generation
        context = f"""
        Current game state:
        - Health: {st.session_state.game_state['health']}
        - Inventory: {', '.join([GAME_ITEMS[item]['name'] for item in st.session_state.game_state['inventory']])}
        - Choices made: {st.session_state.game_state['choices_made']}

        Please continue the story and include one or more of these elements:
        1. Opportunities to find items: {', '.join([item['name'] for item in GAME_ITEMS.values()])}
        2. Potential dangers: {', '.join(DANGEROUS_ACTIONS.keys())}
        
        Provide 2-3 clear choices for the player that could lead to:
        - Finding useful items
        - Facing dangers with potential rewards
        - Safe but less rewarding paths
        
        Incorporate the player's current inventory and health into the narrative.
        """
        
        response = chat_session.send_message(
            conversation_history[-1]["parts"][0]["text"] + "\n" + context
        )
        
        return response.text
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return "Something went wrong in the forest... Please try again."

def main():
    st.set_page_config(page_title="The Cursed Forest", layout="wide")
    apply_custom_styles()
    
    st.title("🌲 The Cursed Forest - Interactive Adventure")
    
    initialize_session_state()
    
    # Add restart button in sidebar
    if st.sidebar.button("Restart Game"):
        st.session_state.clear()
        st.rerun()
    
    # Introduction message if starting new game
    if not st.session_state.conversation_history:
        intro_message = {
            "role": "model",
            "parts": [{
                "text": (
                    "Welcome, brave soul! You are Kaelen, a wanderer who finds yourself lost in the mysterious Cursed Forest. "
                    "Strange creatures, hidden dangers, and an ancient curse lurk in the shadows. Legend has it that the heart "
                    "of the forest holds a powerful artifact, but no one who has ventured deep enough has ever returned.\n\n"
                    "Your adventure begins at the edge of the forest, where an eerie fog hangs in the air. You notice:\n\n"
                    "1. A narrow path leading deeper into the woods, where you spot something glinting in the distance\n"
                    "2. A hollow tree with strange mushrooms growing around it - they might be healing herbs... or poison\n"
                    "3. A mysterious figure in the distance, beckoning you to follow\n\n"
                    "What would you like to do?"
                )}
        ]}
        st.session_state.conversation_history.append(intro_message)
        st.session_state.messages.append(intro_message)
    
    display_game_state()
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message("assistant" if message["role"] == "model" else "user"):
            st.markdown(message["parts"][0]["text"])
    
    # Game over check
    if st.session_state.game_state['health'] <= 0:
        st.error("💀 Game Over - You have perished in the Cursed Forest")
        st.write(f"Final Statistics:\n- Choices made: {st.session_state.game_state['choices_made']}\n- Items found: {st.session_state.game_state['items_found']}\n- Total damage taken: {st.session_state.game_state['damage_taken']}")
        if st.button("Start New Game"):
            st.session_state.clear()
            st.rerun()
        return
    
    # User input
    user_input = st.chat_input("What will you do next?", key="user_input")
    
    if user_input:
        user_message = {"role": "user", "parts": [{"text": user_input}]}
        st.session_state.conversation_history.append(user_message)
        st.session_state.messages.append(user_message)
        
        with st.spinner("The forest whispers..."):
            response = generate_story_response(st.session_state.conversation_history)
            update_game_state(response)
            
            ai_message = {"role": "model", "parts": [{"text": response}]}
            st.session_state.conversation_history.append(ai_message)
            st.session_state.messages.append(ai_message)
        
        st.rerun()

if __name__ == "__main__":
    main()
