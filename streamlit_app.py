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


@st.cache_resource(show_spinner=False)
def get_agent():
    """Construit et met en cache l’agent portfolio.

    `cache_resource` évite de recréer l’agent à chaque interaction.
    """
    return build_portfolio_agent()


def main() -> None:
    st.set_page_config(page_title="Portfolio IA - Xavier Barbeau", page_icon="💼")

    st.title("💼 Portfolio IA - Chatbot")
    st.write(
        "Discute avec ton portfolio : pose des questions sur tes projets, "
        "ton alternance, tes compétences, etc."
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
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])

    # Zone de saisie utilisateur
    user_input = st.chat_input("Pose une question sur ton portfolio…")

    if user_input:
        # Ajouter le message utilisateur à l’historique
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("L’agent réfléchit…"):
                try:
                    result = Runner.run_sync(agent, user_input)
                    answer = result.final_output.strip()
                except Exception as e:
                    answer = f"Une erreur est survenue : {e}"
                st.markdown(answer)

        # Sauvegarder la réponse dans l’historique
        st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
