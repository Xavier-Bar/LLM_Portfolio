"""Interface de chat Streamlit pour l’agent portfolio basé sur openai-agents.

- Utilise `build_portfolio_agent` défini dans `portfolio_agent_openai_agents.py`
- Modèle : gpt-4.1-nano
- RAG via la Tool `search_portfolio` (Upstash Vector)
"""

import os

import streamlit as st
from dotenv import load_dotenv

from portfolio_agent_openai_agents import build_portfolio_agent
from agents import Runner


load_dotenv(override=True)

# Configuration du style personnalisé
def apply_custom_style():
    """Applique un style sobre et moderne sur fond noir."""
    st.markdown("""
    <style>
    /* Arrière-plan principal - noir */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Container principal */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 900px;
    }
    
    /* Titre principal */
    h1 {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
        font-size: 2rem !important;
    }
    
    /* Description */
    .stApp p {
        color: #B4B4B4 !important;
        text-align: center;
        font-size: 1rem;
    }
    
    /* Messages de chat */
    .stChatMessage {
        background-color: #1E1E1E !important;
        border: 1px solid #2D2D2D !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 0.8rem 0 !important;
    }
    
    /* Message utilisateur - légèrement différent */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background-color: #1A1A1A !important;
        border: 1px solid #2A2A2A !important;
    }
    
    /* Texte des messages */
    [data-testid="stChatMessageContent"] {
        color: #E8E8E8 !important;
    }
    
    /* Input du chat */
    .stChatInputContainer {
        background-color: #1E1E1E !important;
        border: 1px solid #3D3D3D !important;
        border-radius: 12px !important;
        padding: 0.5rem !important;
    }
    
    .stChatInputContainer input {
        background-color: transparent !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    
    .stChatInputContainer input::placeholder {
        color: #6B6B6B !important;
    }
    
    /* Bouton d'envoi */
    .stChatInputContainer button {
        background-color: #2D2D2D !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
    }
    
    .stChatInputContainer button:hover {
        background-color: #3D3D3D !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #FFFFFF !important;
    }
    
    /* Messages d'erreur */
    .stAlert {
        background-color: #2D1F1F !important;
        border: 1px solid #5D3D3D !important;
        border-radius: 8px !important;
        color: #FFB4B4 !important;
    }
    
    /* Scrollbar sobre */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1E1E1E;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #3D3D3D;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #4D4D4D;
    }
    
    /* Avatars */
    [data-testid="chatAvatarIcon-user"],
    [data-testid="chatAvatarIcon-assistant"] {
        background-color: #2D2D2D !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource(show_spinner=False)
def get_agent():
    """Construit et met en cache l’agent portfolio.

    `cache_resource` évite de recréer l’agent à chaque interaction.
    """
    return build_portfolio_agent()


def main() -> None:
    st.set_page_config(
        page_title="Portfolio IA - Xavier Barbeau",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Appliquer le style personnalisé
    apply_custom_style()

    # En-tête moderne
    st.markdown("<h1>🤖 Assistant Portfolio Xavier Barbeau</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='margin-bottom: 2rem;'>Posez-moi des questions sur mon parcours, "
        "mes projets, mes compétences ou mon alternance.</p>",
        unsafe_allow_html=True
    )

    # Vérification rapide des variables d’environnement
    missing = []
    if not os.getenv("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")
    if not os.getenv("UPSTASH_VECTOR_REST_URL") or not os.getenv("UPSTASH_VECTOR_REST_TOKEN"):
        missing.extend(["UPSTASH_VECTOR_REST_URL", "UPSTASH_VECTOR_REST_TOKEN"])

    if missing:
        st.error(
            "Variables d’environnement manquantes : " + ", ".join(sorted(set(missing)))
        )
        st.stop()

    agent = get_agent()

    # Initialisation de l’historique dans la session
    if "messages" not in st.session_state:
        st.session_state.messages = []  # liste de dicts {"role": "user"|"assistant", "content": str}

    # Affichage de l’historique
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(msg["content"])

    # Zone de saisie utilisateur
    user_input = st.chat_input("💬 Posez votre question...")

    if user_input:
        # Ajouter le message utilisateur à l'historique
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("💭 Réflexion en cours..."):
                try:
                    result = Runner.run_sync(agent, user_input)
                    answer = result.final_output.strip()
                except Exception as e:
                    answer = f"❌ Une erreur est survenue : {e}"
                st.markdown(answer)

        # Sauvegarder la réponse dans l’historique
        st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
