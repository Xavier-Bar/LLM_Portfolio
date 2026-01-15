# Guide d'Utilisation des Données du Portfolio
##### J'ai pu généré les fichiers markdown avec un requête IA en lui fournissant l'ensemble des informations et fichiers de mon portfolio. J'ai par la suite ajusté les fichiers markdown pour mieux répondre à des questions que je pouvais imaginer posé (combien de projet en python ? --> Ajout des langages utilisées par projet, etc...)


## Structure des Fichiers

Ce dossier `data` contient l'ensemble des informations du portfolio de Xavier Barbeau, organisées en plusieurs fichiers Markdown structurés pour faciliter le chunking et l'utilisation dans un chatbot.

### Liste des Fichiers

1. **profil.md** - Présentation personnelle et parcours
2. **formation.md** - Parcours académique détaillé
3. **experience_professionnelle.md** - Alternance chez Pierre Guérin
4. **competences.md** - Compétences techniques et transversales
5. **projets.md** - Tous les projets académiques (BUT 1 et BUT 2)
6. **contact.md** - Informations de contact et liens

## Structure des Documents

Chaque fichier utilise une structure hiérarchique avec :
- `#` pour les titres principaux
- `##` pour les sections
- `###` pour les sous-sections
- `####` pour les détails

Cette structure facilite le découpage (chunking) des documents pour l'indexation et la recherche.

## Contenu par Fichier

### profil.md
- Présentation personnelle
- Personnalité et centres d'intérêt
- Formation actuelle
- Bilan de parcours
- Réorientation et motivations
- Points forts

### formation.md
- BUT Science des Données (année par année)
- Modules et compétences par semestre
- Licence Mathématiques et Informatique
- BAC STI2D
- Certifications et distinctions
- Évolution et maturité acquise

### experience_professionnelle.md
- Alternance chez Pierre Guérin
- Description détaillée de l'entreprise
- Missions et réalisations
- Technologies utilisées
- Compétences développées
- Impact et apports professionnels

### competences.md
- Compétences techniques (langages, outils, technologies)
- Compétences méthodologiques
- Compétences transversales
- Domaines d'expertise
- Langues
- Points forts professionnels

### projets.md
**Projets BUT 2** (5 projets) :
1. Flash Prévisions Économiques - Mexique
2. Site Web Dynamique Ordiginal
3. Application VBA Recrutement Football
4. Collecte Automatisée Données Web - Islande

**Projets BUT 1** (9 projets) :
1. Analyse de Données AcVC
2. Portfolio Numérique
3. Concours National Datavisualisation (1ère place)
4. Indicateurs Performance Financière - Poujoulat SA
5. Estimation par Échantillonnage
6. Régression Prix Immobilier Paris
7. Base de Données SDIS 79
8. Application PanNote
9. Transformation JSON vers CSV
10. Présentation Islande

Chaque projet inclut :
- Type et contexte
- Année et équipe
- Technologies utilisées
- Description détaillée
- Fonctionnalités
- Compétences développées

### contact.md
- Coordonnées
- Liens GitHub et portfolio
- Disponibilité
- Centres d'intérêt
- Atouts professionnels

## Utilisation pour le Chatbot

### Stratégie de Chunking

Les documents sont déjà structurés pour faciliter le découpage :
- Chaque section `##` peut être un chunk indépendant
- Les projets peuvent être indexés individuellement
- Les compétences peuvent être extraites par catégorie

### Mots-clés et Concepts

**Profil** : Xavier Barbeau, BUT SD, alternance, apprentissage pratique, réorientation

**Formation** : BUT Science des Données, IUT Niort, BAC STI2D, licence mathématiques

**Expérience** : Pierre Guérin, VBA, automatisation, chiffrage, tableaux de bord

**Compétences** : Python, R, VBA, SQL, Power BI, tkinter, PHP, MySQL, Excel, analyse de données, machine learning

**Projets** : 
- Datavisualisation (Power BI)
- Applications de gestion (Python, VBA)
- Web scraping et APIs
- Bases de données
- Analyse statistique (R)
- Développement web

### Types de Questions Attendues

1. **Questions sur le profil** :
   - "Qui es-tu ?"
   - "Quel est ton parcours ?"
   - "Pourquoi le BUT SD ?"

2. **Questions sur l'expérience** :
   - "Parle-moi de ton alternance"
   - "Qu'as-tu fait chez Pierre Guérin ?"
   - "Quelles compétences professionnelles ?"

3. **Questions sur les compétences** :
   - "Quels langages maîtrises-tu ?"
   - "Connais-tu Python/R/VBA ?"
   - "Expérience en bases de données ?"

4. **Questions sur les projets** :
   - "Quels projets as-tu réalisés ?"
   - "Projets en Python ?"
   - "Expérience en datavisualisation ?"
   - "Projets en équipe ?"

5. **Questions spécifiques** :
   - "Projet sur le changement climatique ?"
   - "Application de gestion des notes ?"
   - "Site web Ordiginal ?"

## Recommandations pour l'Implémentation

### Prétraitement
1. Charger tous les fichiers .md
2. Parser le Markdown (titres, sections)
3. Créer des chunks par section `##` ou `###`
4. Indexer avec embeddings

### Métadonnées à Associer
- Fichier source
- Type de contenu (profil, projet, compétence, etc.)
- Année (pour les projets)
- Technologies mentionnées
- Équipe (si applicable)

### Stratégie de Réponse
1. Identifier l'intention de la question
2. Rechercher dans les chunks pertinents
3. Contextualiser avec informations du profil
4. Fournir réponse structurée avec sources

### Tonalité du Chatbot
- Professionnel mais accessible
- Première personne (je)
- Concis et factuel
- Capable de détailler si demandé
- Mentionner les équipes quand pertinent

## Mise à Jour des Données

Pour maintenir le portfolio à jour :
1. Ajouter nouveaux projets dans `projets.md`
2. Mettre à jour `competences.md` avec nouvelles compétences
3. Compléter `experience_professionnelle.md` avec nouvelles missions
4. Actualiser `formation.md` à la fin de chaque semestre

## Structure Technique

### Format
- Tous les fichiers en UTF-8
- Format Markdown standard
- Titres hiérarchiques pour chunking
- Listes à puces pour énumérations
- Gras pour éléments importants

### Taille des Fichiers
- profil.md : ~2 KB
- formation.md : ~8 KB
- experience_professionnelle.md : ~4 KB
- competences.md : ~9 KB
- projets.md : ~25 KB (le plus volumineux)
- contact.md : ~1 KB

### Sections Principales par Fichier
- **profil.md** : 6 sections principales
- **formation.md** : 8 sections principales
- **experience_professionnelle.md** : 5 sections principales
- **competences.md** : 11 sections principales
- **projets.md** : 13 projets détaillés
- **contact.md** : 5 sections

## Exemples de Requêtes et Réponses Attendues

### Exemple 1
**Question** : "Quelles sont tes compétences en Python ?"
**Sources** : competences.md (section Python) + projets.md (projets Python)
**Réponse attendue** : Niveau avancé, applications (tkinter, scraping, APIs, pandas, ML), projets réalisés

### Exemple 2
**Question** : "Parle-moi de ton alternance"
**Sources** : experience_professionnelle.md + profil.md (bilan)
**Réponse attendue** : Pierre Guérin, service chiffrage, missions d'automatisation VBA, impact positif

### Exemple 3
**Question** : "Quel projet en datavisualisation ?"
**Sources** : projets.md (Concours National + AcVC)
**Réponse attendue** : Concours changement climatique (1ère place), Power BI, projet AcVC avec Power BI

## Notes Importantes

- Les équipes sont mentionnées pour chaque projet collaboratif
- Les années sont précisées (BUT 1 vs BUT 2)
- Les technologies sont listées systématiquement
- L'évolution personnelle est documentée (bilan après 2 ans)
- Le style reste professionnel mais personnel (usage du "je")
