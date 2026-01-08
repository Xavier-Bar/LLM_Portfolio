"""
Script d'indexation des documents du portfolio dans Upstash Vector

Ce script charge les fichiers Markdown du dossier data, les découpe en chunks
intelligents par section et les indexe dans Upstash Vector.
Upstash Vector génère automatiquement les embeddings.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from upstash_vector import Index

# Charger les variables d'environnement
load_dotenv()

# Configuration
DATA_DIR = Path("data")
CHUNK_SIZE = 1000  # Nombre de caractères approximatif par chunk


class MarkdownChunker:
    """Classe pour découper les documents Markdown en chunks intelligents"""
    
    def __init__(self, chunk_size: int = CHUNK_SIZE):
        self.chunk_size = chunk_size
    
    def extract_sections(self, content: str, file_name: str) -> List[Dict[str, Any]]:
        """
        Extrait les sections d'un fichier Markdown basé sur les titres (#, ##, ###)
        
        Args:
            content: Contenu du fichier Markdown
            file_name: Nom du fichier source
            
        Returns:
            Liste de dictionnaires contenant les chunks et leurs métadonnées
        """
        chunks = []
        
        # Pattern pour détecter les titres Markdown
        # Capture le niveau de titre, le titre et le contenu jusqu'au prochain titre
        pattern = r'^(#{1,4})\s+(.+?)$'
        
        lines = content.split('\n')
        current_chunk = []
        current_metadata = {
            'source': file_name,
            'level': 0,
            'title': file_name.replace('.md', '').replace('_', ' ').title(),
            'hierarchy': []
        }
        
        title_stack = []  # Pour garder trace de la hiérarchie des titres
        
        for line in lines:
            match = re.match(pattern, line)
            
            if match:
                # Si on a du contenu accumulé, on le sauvegarde
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk).strip()
                    if chunk_text:  # Ignorer les chunks vides
                        chunks.append({
                            'text': chunk_text,
                            'metadata': current_metadata.copy()
                        })
                
                # Nouveau titre détecté
                level = len(match.group(1))  # Nombre de #
                title = match.group(2).strip()
                
                # Mettre à jour la hiérarchie des titres
                # Supprimer les titres de niveau inférieur ou égal
                while title_stack and title_stack[-1]['level'] >= level:
                    title_stack.pop()
                
                title_stack.append({'level': level, 'title': title})
                
                # Créer la hiérarchie complète
                hierarchy = [t['title'] for t in title_stack]
                
                # Préparer les métadonnées pour le prochain chunk
                current_metadata = {
                    'source': file_name,
                    'level': level,
                    'title': title,
                    'hierarchy': ' > '.join(hierarchy),
                    'section_type': self._classify_section(file_name, title)
                }
                
                # Réinitialiser le chunk avec le titre
                current_chunk = [line]
            else:
                current_chunk.append(line)
        
        # Sauvegarder le dernier chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk).strip()
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'metadata': current_metadata.copy()
                })
        
        return chunks
    
    def _classify_section(self, file_name: str, title: str) -> str:
        """Classifie le type de section pour faciliter la recherche"""
        file_lower = file_name.lower()
        title_lower = title.lower()
        
        if 'projet' in file_lower or 'projet' in title_lower:
            return 'projet'
        elif 'competence' in file_lower or 'compétence' in title_lower:
            return 'competence'
        elif 'experience' in file_lower or 'expérience' in title_lower or 'alternance' in title_lower:
            return 'experience'
        elif 'formation' in file_lower or 'formation' in title_lower:
            return 'formation'
        elif 'profil' in file_lower or 'propos' in title_lower:
            return 'profil'
        elif 'contact' in file_lower:
            return 'contact'
        else:
            return 'general'
    
    def split_large_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Divise les chunks trop grands en plus petits morceaux
        
        Args:
            chunks: Liste de chunks à vérifier
            
        Returns:
            Liste de chunks avec tailles optimisées
        """
        optimized_chunks = []
        
        for chunk in chunks:
            text = chunk['text']
            metadata = chunk['metadata']
            
            if len(text) <= self.chunk_size * 1.5:
                # Le chunk est de taille acceptable
                optimized_chunks.append(chunk)
            else:
                # Diviser le chunk par paragraphes
                paragraphs = text.split('\n\n')
                current_text = []
                current_length = 0
                part_num = 1
                
                for para in paragraphs:
                    para_length = len(para)
                    
                    if current_length + para_length > self.chunk_size and current_text:
                        # Sauvegarder le chunk actuel
                        optimized_chunks.append({
                            'text': '\n\n'.join(current_text),
                            'metadata': {
                                **metadata,
                                'part': part_num,
                                'is_split': True
                            }
                        })
                        current_text = [para]
                        current_length = para_length
                        part_num += 1
                    else:
                        current_text.append(para)
                        current_length += para_length
                
                # Sauvegarder le dernier morceau
                if current_text:
                    optimized_chunks.append({
                        'text': '\n\n'.join(current_text),
                        'metadata': {
                            **metadata,
                            'part': part_num,
                            'is_split': True
                        }
                    })
        
        return optimized_chunks


class PortfolioIndexer:
    """Classe principale pour indexer le portfolio dans Upstash Vector"""
    
    def __init__(self):
        # Initialiser l'index Upstash Vector
        self.vector_index = Index(
            url=os.getenv("UPSTASH_VECTOR_REST_URL"),
            token=os.getenv("UPSTASH_VECTOR_REST_TOKEN")
        )
        
        self.chunker = MarkdownChunker()
    
    def load_markdown_files(self) -> Dict[str, str]:
        """
        Charge tous les fichiers Markdown du dossier data
        
        Returns:
            Dictionnaire {nom_fichier: contenu}
        """
        documents = {}
        
        for md_file in DATA_DIR.glob("*.md"):
            if md_file.name == "README.md":
                continue  # Ignorer le README
            
            with open(md_file, 'r', encoding='utf-8') as f:
                documents[md_file.name] = f.read()
        
        return documents
    
    def index_documents(self, batch_size: int = 10):
        """
        Indexe tous les documents dans Upstash Vector
        Upstash génère automatiquement les embeddings
        
        Args:
            batch_size: Nombre de chunks à traiter en un seul batch
        """
        print("🚀 Démarrage de l'indexation...")
        
        # 1. Charger les documents
        print("\n📖 Chargement des fichiers Markdown...")
        documents = self.load_markdown_files()
        print(f"   ✓ {len(documents)} fichiers chargés")
        
        # 2. Découper en chunks
        print("\n✂️  Découpage des documents en chunks...")
        all_chunks = []
        for file_name, content in documents.items():
            chunks = self.chunker.extract_sections(content, file_name)
            all_chunks.extend(chunks)
        
        print(f"   ✓ {len(all_chunks)} chunks extraits")
        
        # 3. Optimiser les tailles de chunks
        print("\n🔧 Optimisation de la taille des chunks...")
        optimized_chunks = self.chunker.split_large_chunks(all_chunks)
        print(f"   ✓ {len(optimized_chunks)} chunks optimisés")
        
        # 4. Indexer dans Upstash Vector (avec génération automatique des embeddings)
        print("\n🔮 Indexation dans Upstash Vector...")
        total_indexed = 0
        
        for i in range(0, len(optimized_chunks), batch_size):
            batch = optimized_chunks[i:i + batch_size]
            
            # Préparer les données pour Upstash (avec data au lieu de vector)
            # Upstash génère automatiquement les embeddings à partir du texte
            vectors = []
            for j, chunk in enumerate(batch):
                vector_id = f"chunk_{total_indexed + j}"
                vectors.append({
                    'id': vector_id,
                    'data': chunk['text'],  # Upstash génère l'embedding automatiquement
                    'metadata': chunk['metadata']
                })
            
            # Upserter dans Upstash Vector
            self.vector_index.upsert(vectors=vectors)
            
            total_indexed += len(batch)
            print(f"   ✓ {total_indexed}/{len(optimized_chunks)} chunks indexés")
        
        print(f"\n✅ Indexation terminée ! {total_indexed} chunks indexés avec succès.")
    
    def get_index_stats(self):
        """Affiche les statistiques de l'index"""
        try:
            info = self.vector_index.info()
            print("\n📊 Statistiques de l'index:")
            print(f"   - Nombre de vecteurs: {info.get('vectorCount', 'N/A')}")
            print(f"   - Dimensions: {info.get('dimension', 'N/A')}")
        except Exception as e:
            print(f"\n⚠️  Impossible de récupérer les stats: {e}")
    
    def search_example(self, query: str, top_k: int = 3):
        """
        Exemple de recherche dans l'index
        
        Args:
            query: Question ou recherche
            top_k: Nombre de résultats à retourner
        """
        print(f"\n🔍 Recherche: '{query}'")
        
        # Rechercher directement avec la requête textuelle
        # Upstash génère automatiquement l'embedding
        results = self.vector_index.query(
            data=query,
            top_k=top_k,
            include_metadata=True
        )
        
        print(f"\n📋 Top {top_k} résultats:")
        for i, result in enumerate(results, 1):
            metadata = result.metadata
            print(f"\n{i}. [{metadata.get('source', 'N/A')}] {metadata.get('title', 'N/A')}")
            print(f"   Score: {result.score:.4f}")
            print(f"   Hiérarchie: {metadata.get('hierarchy', 'N/A')}")


def main():
    """Fonction principale"""
    print("=" * 60)
    print("INDEXATION DU PORTFOLIO DANS UPSTASH VECTOR")
    print("=" * 60)
    
    # Vérifier que les variables d'environnement sont définies
    # OpenAI n'est plus nécessaire car Upstash génère les embeddings
    required_vars = ["UPSTASH_VECTOR_REST_URL", "UPSTASH_VECTOR_REST_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n❌ Erreur: Variables d'environnement manquantes:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Assurez-vous que le fichier .env contient toutes les variables nécessaires.")
        return
    
    # Créer l'indexeur
    indexer = PortfolioIndexer()
    
    # Indexer les documents
    indexer.index_documents()
    
    # Afficher les stats
    indexer.get_index_stats()
    
    # Exemple de recherche
    print("\n" + "=" * 60)
    print("TESTS DE RECHERCHE")
    print("=" * 60)
    
    test_queries = [
        "Quelles sont tes compétences en Python ?",
        "Parle-moi de ton alternance",
        "Projet sur le changement climatique"
    ]
    
    for query in test_queries:
        indexer.search_example(query, top_k=3)
        print()


if __name__ == "__main__":
    main()
