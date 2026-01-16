# Imports
import os
from typing import List
from dotenv import load_dotenv
from upstash_vector import Index
from agents import Agent, Runner, ModelSettings, function_tool

# Overrride pour forcer le rechargement des variables d'environnement
load_dotenv(override=True)


# Initialisation de l'index Upstash (réutilisé par la Tool)
vector_index = Index(
    url=os.getenv("UPSTASH_VECTOR_REST_URL"),
    token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"),
)


@function_tool
def search_portfolio(query: str, k: int = 5) -> str:
    """Recherche des informations dans l'index d'Upstash Vector.

    Args:
        query: Question ou mots-clés sur le profil / compétences / projets.
        k: Nombre maximum de passages pertinents à retourner.

    Retourne une concaténation de passages pertinents (texte brut) issus
    des fichiers Markdown du dossier data, déjà indexés dans Upstash.
    
    Reminder : Privilégie des recherches ciblées avec k réduit pour des réponses concises.
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
    """
    - Modèle : gpt-4.1-nano
    - Utilise la Tool `search_portfolio` pour le RAG
    - Parle à la 1ère personne comme si l'agent était moi ( Xavier Barbeau )
    """

    # Instructions détaillées pour l'agent LLM
    instructions = (
        "Tu es un assistant IA qui représente Xavier Barbeau."
        "Xavier est étudiant en BUT Science des Données et en alternance chez Pierre Guérin.\n\n"
        
        "=== RÈGLES FONDAMENTALES ===\n"
        "1. TOUJOURS répondre à la 1ère personne (je, mon, mes) comme Xavier\n"
        "2. TOUJOURS utiliser search_portfolio pour chercher les informations\n"
        "3. Pour questions larges : faire 2-3 recherches avec différents mots-clés\n"
        "4. RÉPONSES CONCISES : maximum 3 phrases pour questions simples\n"
        "5. Pour les listes : format condensé avec puces, sans détails excessifs\n"
        "6. NE JAMAIS inventer - si pas d'info trouvée, le dire clairement\n\n"
        
        "=== STRATÉGIE DE RECHERCHE ===\n"
        "• Questions sur projets : chercher 'index projets' + mots-clés spécifiques\n"
        "• Questions techniques : chercher 'compétences' + technologies mentionnées\n"
        "• Questions sur personnes : chercher nom + 'équipe' ou 'collaboration'\n"
        "• Questions générales : chercher 'profil' ou 'formation' ou 'expérience'\n\n"
        
        "=== STYLE DE RÉPONSE ===\n"
        "• Questions simples (qui/quoi/où) : 1-2 phrases directes\n"
        "• Questions complexes : max 3 phrases synthétiques\n"
        "• Listes : format bullet points concis\n"
        "  Exemple : \"J'ai travaillé sur 3 projets Python : AcVC (visualisation), "
        "SDIS 79 (dashboard), et Streamlit API (app web).\"\n\n"
        
        "• Questions ouvertes : réponse structurée mais brève\n"
        "  Exemple : \"Je suis alternant data chez Pierre Guérin. Je travaille sur "
        "l'analyse de données et la création de dashboards. J'utilise Python et Power BI.\"\n\n"
        
        "IMPORTANT : Privilégie la clarté et la concision. Évite les détails superflus.\n"
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
        print("OPENAI_API_KEY manquant dans le .env")
        return
    if not os.getenv("UPSTASH_VECTOR_REST_URL") or not os.getenv("UPSTASH_VECTOR_REST_TOKEN"):
        print("Variables Upstash manquantes dans le .env")
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