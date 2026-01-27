# Documentation Technique

## Vue d'ensemble du projet

Application de protofolio Intéractif via une agent IA pour créer un chatbot, il se prend pour moi (Xavier Barbeau) et répond au question en utilisant les données sorties en vecteurs sur Upstash.

**Stack technique :**
- Interface : Streamlit
- Agent IA : OpenAI Agents (gpt-4.1-nano) + script
- RAG : Upstash Vector (base vectorielle)
- Langage : Python 3.13.9

---

## Architecture

```
projet-iut-potfolio/
├── data/               # Données sources du portfolio (Markdown)
│   ├── profil.md
│   ├── competences.md
│   └── projets.md
├── src/                # Code source
│   ├── streamlit_app.py           # Interface Streamlit
│   ├── agent_openai_portfolio.py  # Agent IA + Tool RAG
│   └── indexation.py              # Découpage et indexation
├── .env                # Variables d'environnement
└── requirements.txt    # Dépendances Python
```
*Schéma copilot*

---


## Configuration

### Variables d'environnement (`.env`)
```env
OPENAI_API_KEY=sk-...
UPSTASH_VECTOR_REST_URL=https://...
UPSTASH_VECTOR_REST_TOKEN=...
```

### Dépendances (`requirements.txt`)
```
streamlit==1.52.2
openai-agents[redis]==0.6.5
upstash-vector==0.8.0
python-dotenv==1.2.1
```

---

## Installation et Démarrage

### 1. Installation
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration
Créer un fichier `.env` avec les 3 variables d'environnement.

### 3. Indexation (une fois)
```bash
.venv/Scripts/python.exe src/indexation.py
```

### 4. Lancement
```bash
streamlit run src/streamlit_app.py
```

---

## Code source

### 1. Chargement - Chunk - Indexation (`indexation.py`)

**Rôle :** Charge les données des fichiers markdown, les découpes en chunk puis les indexes dans Upstash Vector.

**Fonctions principales :**
- `chunk_markdown(content, source)` : Découpe un fichier .md selon les titres (# à ###)
- `chunk_directory(directory)` : Applique le chunking à tous les .md du dossier data
- `index_chunks(chunks)` : Envoie les chunks vers Upstash Vector
Pour plus de détail lire les docstrings

**Métadonnées stockées :**
- `source` : nom du fichier
- `level` : niveau du titre (1 à 3)
- `title` : titre de la section (titre le plus petit)
- `hierarchy` : hiérarchie complète des titres
- `text` : contenu du chunk

**Exécution :**
```bash
.venv/Scripts/python.exe src/indexation.py
```

---

### 2. Agent IA (`agent_openai_portfolio.py`)

**Rôle :** Appel de l'agent IA (open AI) et utilisation uniquement des données de Upstash (Instruction complète dans le script de l'agent)

**Composants :**

#### Tool `search_portfolio`
- **Type :** function_tool
- **Action :** Recherche sémantique dans Upstash Vector
- **Paramètres :**
  - `query` : question/mots-clés
  - `k` : nombre de résultats (figé à 5 pour rester simple et concis)
- **Retour :** Passages pertinents avec métadonnées

#### Configuration de l'agent
- **Modèle :** gpt-4.1-nano
- **Personnalité :** Parle à la 1ère personne pour les réponses et ce prend pour moi (Xavier)
- **Instructions :** Réponses concises, recherches ciblées, pas d'invention, etc...

**Stratégie de recherche :**
- Questions projet → `"index projets" + mots-clés`
- Questions techniques → `"compétences" + technologies`
- Questions personnes → `nom + "équipe"`
- Questions générales → `"profil" ou "formation"`

**Exécution :**
Automatique via l'appli streamlit

---

### 3. Interface Streamlit (`streamlit_app.py`)

**Rôle :** Interface web pour le chatbot permettant d'échanger avec le model (réaliser par IA puis ajusté)

**Fonctionnalités :**
- Chat persistant avec historique de session
- Style personnalisé (fond noir, design moderne)
- Gestion d'erreurs (variables d'environnement manquantes)
- Cache de l'agent (`@st.cache_resource`)

**Lancement :**
```bash
streamlit run src/streamlit_app.py
```

**URL par défaut :** http://localhost:8501

---

## Maintenance

### Mise à jour des données
1. Modifier ou ajouter des fichiers dans `data/`
2. Réindexer : `.venv/Scripts/python.exe src/indexation.py`
3. Redémarrer Streamlit (si en cours)

---

### Limites connues

- Modèle limité à gpt-4.1-nano
- Upstash Vector en plan Free (limites de stockage)
- Pas de gestion multi-utilisateurs
- Historique de chat sur session uniquement