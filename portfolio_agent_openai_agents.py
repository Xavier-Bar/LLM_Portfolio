"""
Agent portfolio basé sur openai-agents, avec Tool RAG vers Upstash Vector.

Cet agent respecte le sujet du projet :
- utilise la librairie `openai-agents`
- modèle `gpt-4.1-nano`
- Tool pour interroger la base vectorielle Upstash
"""

import os
from typing import List

from dotenv import load_dotenv
from upstash_vector import Index

from agents import Agent, Runner, ModelSettings, function_tool

load_dotenv(override=True)


# Initialisation de l'index Upstash (réutilisé par la Tool)
vector_index = Index(
    url=os.getenv("UPSTASH_VECTOR_REST_URL"),
    token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"),
)


@function_tool
def search_portfolio(query: str, k: int = 5) -> str:
    """Recherche des informations sur le portfolio de Xavier dans l'index Upstash.

    Args:
        query: Question ou mots-clés sur le profil / compétences / projets.
        k: Nombre maximum de passages pertinents à retourner.

    Retourne une concaténation de passages pertinents (texte brut) issus
    des fichiers Markdown du dossier data, déjà indexés dans Upstash.
    """
    results = vector_index.query(
        data=query,
        top_k=k,
        include_metadata=True,
    )

    if not results:
        return "Aucun passage pertinent trouvé dans le portfolio."

    parts: List[str] = []
    for i, res in enumerate(results, 1):
        meta = res.metadata or {}
        source = meta.get("source", "inconnu")
        title = meta.get("title", "(sans titre)")
        hierarchy = meta.get("hierarchy", "")
        text = meta.get("text", "")
        parts.append(
            f"[Passage {i}]\n"
            f"Fichier : {source}\n"
            f"Section : {hierarchy or title}\n"
            f"Score : {res.score:.3f}\n\n"
            f"{text}\n"
        )

    return "\n---\n".join(parts)


def build_portfolio_agent() -> Agent:
    """Construit un agent openai-agents spécialisé sur le portfolio.

    - Modèle : gpt-4.1-nano (comme indiqué dans le sujet)
    - Utilise la Tool `search_portfolio` pour le RAG
    - Parle à la 1ère personne comme si l'agent était Xavier
    """

    instructions = (
        "Tu es un assistant IA qui représente Xavier Barbeau, "
        "étudiant en BUT Science des Données en alternance chez Pierre Guérin.\n\n"
        "Ton rôle est de répondre aux questions sur : son profil, sa formation, "
        "ses compétences, ses projets académiques et son alternance.\n\n"
        "IMPORTANT :\n"
        "- Tu réponds toujours à la première personne (je, mon, mes) comme si tu étais Xavier.\n"
        "- Pour répondre, utilise en priorité la tool `search_portfolio` qui te donne "
        "des extraits exacts du portfolio.\n"
        "- Si la tool ne renvoie rien de pertinent, dis honnêtement que l'information "
        "n'est pas disponible dans le portfolio.\n"
        "- Tu peux synthétiser et reformuler, mais ne rajoute pas de faits qui ne "
        "sont pas dans le contexte.\n"
    )

    agent = Agent(
        name="portfolio-agent",
        instructions=instructions,
        model="gpt-4.1-nano",
        model_settings=ModelSettings(temperature=0.3),
        tools=[search_portfolio],
    )

    return agent


def main() -> None:
    """Petit script de test pour l'agent openai-agents."""
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY manquant dans le .env")
        return
    if not os.getenv("UPSTASH_VECTOR_REST_URL") or not os.getenv("UPSTASH_VECTOR_REST_TOKEN"):
        print("❌ Variables Upstash manquantes dans le .env")
        return

    print("=" * 70)
    print("AGENT PORTFOLIO (openai-agents)")
    print("=" * 70)

    agent = build_portfolio_agent()

    questions = [
        "Qui es-tu ?",
        "Quelles sont tes compétences principales ?",
        "Parle-moi de ton alternance chez Pierre Guérin.",
        "Quel projet as-tu réalisé sur le changement climatique ?",
    ]

    for q in questions:
        print("\n" + "-" * 70)
        print("Question :", q)
        print("-" * 70)
        result = Runner.run_sync(agent, q)
        print("Réponse :", result.final_output.strip())


if __name__ == "__main__":
    main()
