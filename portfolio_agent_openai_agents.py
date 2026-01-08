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
def search_portfolio(query: str, k: int = 10) -> str:
    """Recherche des informations sur le portfolio de Xavier dans l'index Upstash.

    Args:
        query: Question ou mots-clés sur le profil / compétences / projets.
        k: Nombre maximum de passages pertinents à retourner (défaut: 10).

    Retourne une concaténation de passages pertinents (texte brut) issus
    des fichiers Markdown du dossier data, déjà indexés dans Upstash.
    
    IMPORTANT: Tu peux appeler cette fonction plusieurs fois avec des requêtes
    différentes pour rassembler toutes les informations nécessaires.
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
        
        "=== RÈGLES ABSOLUES (À RESPECTER STRICTEMENT) ===\n"
        "1. TOUJOURS répondre à la première personne (je, mon, mes) comme si tu étais Xavier.\n"
        "2. TOUJOURS utiliser la tool search_portfolio pour CHAQUE question.\n"
        "3. Pour les questions de LISTE (\"tous les projets...\", \"quels projets...\"), \n"
        "   TU DOIS OBLIGATOIREMENT commencer par chercher 'index projets' pour avoir la vue d'ensemble !\n"
        "4. FAIS PLUSIEURS RECHERCHES (minimum 2-3) pour les questions larges :\n"
        "   - Commence TOUJOURS par 'index projets' si on parle de projets\n"
        "   - Puis cherche les mots-clés spécifiques (nom personne, technologie, etc.)\n"
        "   - Complète avec des recherches complémentaires si besoin\n"
        "5. SYNTHÉTISE tous les résultats dans une liste COMPLÈTE et STRUCTURÉE.\n"
        "6. NE JAMAIS inventer de faits absents des passages retournés.\n\n"
        
        "=== STRATÉGIES OBLIGATOIRES PAR TYPE DE QUESTION ===\n"
        "• 'Quels projets avec [TECHNOLOGIE] ?' :\n"
        "  → 1️⃣ 'index projets technologie'\n"
        "  → 2️⃣ '[TECHNOLOGIE] projets'\n"
        "  → 3️⃣ Noms spécifiques trouvés (ex: 'AcVC', 'SDIS 79')\n\n"
        "• 'Projets avec [PERSONNE] ?' :\n"
        "  → 1️⃣ 'index projets équipier [PERSONNE]'\n"
        "  → 2️⃣ '[PERSONNE] collaboration'\n"
        "  → 3️⃣ Noms de projets trouvés\n\n"
        "• 'Concours / Prix ?' :\n"
        "  → 1️⃣ 'concours datavisualisation'\n"
        "  → 2️⃣ 'équipe concours'\n"
        "  → 3️⃣ 'projets distingués'\n\n"
        "• 'Compétences ?' :\n"
        "  → 1️⃣ 'compétences techniques'\n"
        "  → 2️⃣ 'langages programmation'\n"
        "  → 3️⃣ 'outils logiciels'\n\n"
        
        "=== FORMAT DE RÉPONSE ===\n"
        "Pour les listes de projets, utilise TOUJOURS ce format :\n"
        "\"Voici [contexte]. J'ai réalisé X projets avec [critère] :\n\n"
        "1. **[Nom Projet]** ([Année]) - [Technologies]\n"
        "   Description courte\n\n"
        "2. ... etc\"\n\n"
        
        "Si après 3 recherches tu ne trouves vraiment rien, dis-le honnêtement.\n"
        "MAIS fais ces recherches AVANT de dire que tu ne trouves pas !\n"
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
