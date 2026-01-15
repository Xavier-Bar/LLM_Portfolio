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
    
    # Compiler la regex une seule fois pour améliorer les performances
    HEADING_PATTERN = re.compile(r'^(#{1,4})\s+(.+?)$')
    
    # Mapping pour la classification des sections
    SECTION_KEYWORDS = {
        'projet': 'projet',
        'competence': 'competence',
        'compétence': 'competence',
        'experience': 'experience',
        'expérience': 'experience',
        'alternance': 'experience',
        'formation': 'formation',
        'profil': 'profil',
        'propos': 'profil',
        'contact': 'contact'
    }
    
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
        lines = content.split('\n')
        current_chunk = []
        current_metadata = self._create_initial_metadata(file_name)
        title_stack = []  # Pour garder trace de la hiérarchie des titres
        
        for line in lines:
            match = self.HEADING_PATTERN.match(line)
            
            if match:
                # Sauvegarder le chunk précédent s'il existe
                self._save_chunk(chunks, current_chunk, current_metadata)
                
                # Nouveau titre détecté
                level = len(match.group(1))
                title = match.group(2).strip()
                
                # Mettre à jour la hiérarchie des titres
                while title_stack and title_stack[-1]['level'] >= level:
                    title_stack.pop()
                
                title_stack.append({'level': level, 'title': title})
                hierarchy = [t['title'] for t in title_stack]
                
                # Préparer les métadonnées pour le prochain chunk
                current_metadata = {
                    'source': file_name,
                    'level': level,
                    'title': title,
                    'hierarchy': ' > '.join(hierarchy),
                    'section_type': self._classify_section(file_name, title)
                }
                
                current_chunk = [line]
            else:
                current_chunk.append(line)
        
        # Sauvegarder le dernier chunk
        self._save_chunk(chunks, current_chunk, current_metadata)
        
        return chunks
    
    def _create_initial_metadata(self, file_name: str) -> Dict[str, Any]:
        """Crée les métadonnées initiales pour un fichier"""
        return {
            'source': file_name,
            'level': 0,
            'title': file_name.replace('.md', '').replace('_', ' ').title(),
            'hierarchy': []
        }
    
    def _save_chunk(self, chunks: List[Dict[str, Any]], current_chunk: List[str], metadata: Dict[str, Any]):
        """Sauvegarde un chunk s'il contient du texte"""
        if current_chunk:
            chunk_text = '\n'.join(current_chunk).strip()
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'metadata': metadata.copy()
                })
    
    def _classify_section(self, file_name: str, title: str) -> str:
        """Classifie le type de section pour faciliter la recherche"""
        combined_text = f"{file_name} {title}".lower()
        
        for keyword, section_type in self.SECTION_KEYWORDS.items():
            if keyword in combined_text:
                return section_type
        
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
        max_size = self.chunk_size * 1.5
        
        for chunk in chunks:
            if len(chunk['text']) <= max_size:
                optimized_chunks.append(chunk)
            else:
                optimized_chunks.extend(self._split_chunk_by_paragraphs(chunk))
        
        return optimized_chunks
    
    def _split_chunk_by_paragraphs(self, chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Divise un chunk par paragraphes"""
        paragraphs = chunk['text'].split('\n\n')
        parts = []
        current_text = []
        current_length = 0
        part_num = 1
        
        for para in paragraphs:
            para_length = len(para)
            
            if current_length + para_length > self.chunk_size and current_text:
                parts.append(self._create_split_chunk(current_text, chunk['metadata'], part_num))
                current_text = [para]
                current_length = para_length
                part_num += 1
            else:
                current_text.append(para)
                current_length += para_length
        
        if current_text:
            parts.append(self._create_split_chunk(current_text, chunk['metadata'], part_num))
        
        return parts
    
    def _create_split_chunk(self, text_parts: List[str], metadata: Dict[str, Any], part_num: int) -> Dict[str, Any]:
        """Crée un chunk splitté avec ses métadonnées"""
        return {
            'text': '\n\n'.join(text_parts),
            'metadata': {**metadata, 'part': part_num, 'is_split': True}
        }


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
        return {
            md_file.name: md_file.read_text(encoding='utf-8')
            for md_file in DATA_DIR.glob("*.md")
            if md_file.name != "README.md"
        }
    
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
        all_chunks = [
            chunk
            for file_name, content in documents.items()
            for chunk in self.chunker.extract_sections(content, file_name)
        ]
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
            vectors = self._prepare_vectors(batch, total_indexed)
            
            self.vector_index.upsert(vectors=vectors)
            
            total_indexed += len(batch)
            print(f"   ✓ {total_indexed}/{len(optimized_chunks)} chunks indexés")
        
        print(f"\n✅ Indexation terminée ! {total_indexed} chunks indexés avec succès.")
    
    def _prepare_vectors(self, chunks: List[Dict[str, Any]], offset: int) -> List[Dict[str, Any]]:
        """Prépare les vecteurs pour l'upsert dans Upstash"""
        return [
            {
                'id': f"chunk_{offset + j}",
                'data': chunk['text'],
                'metadata': {**chunk['metadata'], 'text': chunk['text']}
            }
            for j, chunk in enumerate(chunks)
        ]
    
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