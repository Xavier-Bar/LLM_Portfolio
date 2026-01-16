# Imports
import re
import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from upstash_vector import Index

load_dotenv()  # Charger les variables d'environnement


def chunk_markdown(content: str, source: str) -> List[Dict[str, Any]]:
    """Découpe un texte Markdown en chunks basés sur les titres.
    
    Parcourt le contenu Markdown et crée un nouveau chunk à chaque titre rencontré.
    Chaque chunk contient le titre et tout le contenu jusqu'au prochain titre de même
    niveau ou supérieur. Les métadonnées incluent la hiérarchie complète des titres.
    
    Args:
        content (str): Le contenu Markdown à découper
        source (str): Le nom du fichier source (pour les métadonnées)
    
    Returns:
        List[Dict[str, Any]]: Liste de dictionnaires contenant:
            - 'text': Le texte du chunk
            - 'metadata': Dictionnaire avec source, level, title, hierarchy
    """
    chunks = []
    lines = content.split('\n')
    current_chunk = []
    title_stack = []
    pattern = re.compile(r'^(#{1,4})\s+(.+?)$')
    
    for line in lines:
        match = pattern.match(line)
        
        if match:
            if current_chunk:
                text = '\n'.join(current_chunk).strip()
                if text:
                    chunks.append({'text': text, 'metadata': metadata.copy()})
            
            level = len(match.group(1))
            title = match.group(2).strip()
            
            while title_stack and title_stack[-1]['level'] >= level:
                title_stack.pop()
            
            title_stack.append({'level': level, 'title': title})
            hierarchy = ' > '.join([t['title'] for t in title_stack])
            
            metadata = {
                'source': source,
                'level': level,
                'title': title,
                'hierarchy': hierarchy
            }
            
            current_chunk = [line]
        else:
            current_chunk.append(line)
    
    if current_chunk:
        text = '\n'.join(current_chunk).strip()
        if text:
            chunks.append({'text': text, 'metadata': metadata})
    
    return chunks


def chunk_directory(directory: str) -> List[Dict[str, Any]]:
    """Découpe tous les fichiers .md d'un répertoire.
    
    Parcourt tous les fichiers .md du répertoire spécifié (à l'exception de README.md)
    et applique la fonction chunk_markdown à chacun d'eux. Les chunks de tous les
    fichiers sont combinés dans une seule liste.
    
    Args:
        directory (str): Chemin vers le répertoire contenant les fichiers Markdown
    
    Returns:
        List[Dict[str, Any]]: Liste de tous les chunks de tous les fichiers,
            chaque chunk ayant la même structure que celle retournée par chunk_markdown
    """
    all_chunks = []
    for file in Path(directory).glob("*.md"):
        # Exclure README.md
        if file.name.lower() != 'readme.md':
            content = file.read_text(encoding='utf-8')
            chunks = chunk_markdown(content, file.name)
            all_chunks.extend(chunks)
    return all_chunks


def index_chunks(chunks: List[Dict[str, Any]]):
    """Indexe les chunks dans Upstash Vector.
    
    Envoie tous les chunks à l'index vectoriel Upstash.
    Chaque chunk est converti en vecteur avec un ID unique et ses métadonnées associées.
    Le texte du chunk est inclus dans les métadonnées pour faciliter la récupération.
    
    Args:
        chunks (List[Dict[str, Any]]): Liste des chunks à indexer, chaque chunk
            doit contenir 'text' et 'metadata'
    
    Returns:
        None
    """
    index = Index.from_env()
    
    total = len(chunks)
    print(f"Indexation de {total} chunks...")
    
    vectors = [
        {
            'id': f"chunk_{i}",
            'data': chunk['text'],
            'metadata': {**chunk['metadata'], 'text': chunk['text']}
        }
        for i, chunk in enumerate(chunks)
    ]
    
    index.upsert(vectors=vectors)
    print(f"{total}/{total} chunks indexés")
    print("Indexation terminée !")


if __name__ == "__main__":
    print("=" * 60)
    print("INDEXATION DU PORTFOLIO")
    print("=" * 60)
    
    # Découpage
    print("\nDécoupage des fichiers...")
    chunks = chunk_directory("data")
    print(f"{len(chunks)} chunks créés")
    
    # Indexation
    print()
    index_chunks(chunks)