import re
import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from upstash_vector import Index

load_dotenv()  # Charger les variables d'environnement


def chunk_markdown(content: str, source: str) -> List[Dict[str, Any]]:
    """Découpe un texte Markdown en chunks basés sur les titres"""
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
    """Découpe tous les fichiers .md d'un répertoire"""
    all_chunks = []
    for file in Path(directory).glob("*.md"):
        if file.name.lower() != 'readme.md':
            content = file.read_text(encoding='utf-8')
            chunks = chunk_markdown(content, file.name)
            all_chunks.extend(chunks)
    return all_chunks


def index_chunks(chunks: List[Dict[str, Any]], batch_size: int = 10):
    """Indexe les chunks dans Upstash Vector"""
    index = Index.from_env()
    
    total = len(chunks)
    print(f"🔮 Indexation de {total} chunks...")
    
    for i in range(0, total, batch_size):
        batch = chunks[i:i + batch_size]
        
        vectors = [
            {
                'id': f"chunk_{i + j}",
                'data': chunk['text'],
                'metadata': {**chunk['metadata'], 'text': chunk['text']}
            }
            for j, chunk in enumerate(batch)
        ]
        
        index.upsert(vectors=vectors)
        print(f"   ✓ {min(i + batch_size, total)}/{total} chunks indexés")
    
    print(f"✅ Indexation terminée !")


if __name__ == "__main__":
    print("=" * 60)
    print("INDEXATION DU PORTFOLIO")
    print("=" * 60)
    
    # Découpage
    print("\n📖 Découpage des fichiers...")
    chunks = chunk_directory("data")
    print(f"   ✓ {len(chunks)} chunks créés")
    
    # Indexation
    print()
    index_chunks(chunks)
    
    # Affichage exemple
    print("\n📋 Exemples de chunks indexés:")
    for i, chunk in enumerate(chunks[:3], 1):
        m = chunk['metadata']
        print(f"{i}. [{m['source']}] {m['title']} (niveau {m['level']})")
