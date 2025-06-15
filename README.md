# 🔥 Système de Détection d'Incendie en Temps Réel (Webcam & URL)

Ce projet propose une solution complète pour la détection d'incendies en temps réel, combinant une API robuste basée sur **FastAPI** pour le traitement des images et une interface utilisateur interactive développée avec **Streamlit**.  
Il permet la détection d'incendies à partir de flux webcam en direct ou d'images fournies par URL, avec un enregistrement des détections dans une base de données locale.

---

## 🌟 Fonctionnalités Principales

- **Détection d'Incendie en Temps Réel (Webcam)** : Analyse continue du flux vidéo d'une webcam pour détecter la présence de feu.
- **Détection d'Incendie par URL** : Possibilité de soumettre une URL d'image pour une analyse à la demande.
- **API FastAPI** : Backend performant hébergeant le modèle de détection d'objets (YOLOv8) et traitant les requêtes d'images.
- **Interface Utilisateur Streamlit** : Application web conviviale pour visualiser les détections en direct, gérer la webcam et consulter l'historique.
- **Base de Données Locale (DuckDB)** : Enregistrement persistant des détections de feu (avec timestamp, source et confiance) pour la traçabilité et l'analyse ultérieure.
- **Déploiement Dockerisé** : L'ensemble de l'application est conteneurisé avec Docker Compose pour un déploiement local facile et isolé.

---

## 🏗️ Architecture du Projet

Le système est conçu avec une **architecture de microservices**, divisée en deux composants principaux s'exécutant dans des conteneurs Docker distincts :

**Service API (FastAPI)**
- **Rôle** : Cœur de la logique de détection. Il expose des endpoints HTTP pour recevoir des images (webcam stream ou URL) et renvoyer les résultats de détection (image annotée et confiance).
- **Technos** : FastAPI, Uvicorn, Ultralytics (YOLOv8), OpenCV.
- **Modèle** : Utilise un modèle pré-entraîné (`best.pt`) pour la détection de "feu".

**Service Interface Utilisateur (Streamlit)**
- **Rôle** : Interface web interactive. Capture le flux webcam, envoie les images à l'API FastAPI, affiche les résultats annotés et gère l'enregistrement/affichage des détections dans une base DuckDB.
- **Technos** : Streamlit, Requests, DuckDB, Pillow, OpenCV.
- **Persistance** : Un volume Docker permet de conserver la base DuckDB (`fire_detections.duckdb`) même si le conteneur Streamlit est redémarré ou supprimé.

---

## 📁 Structure du Projet

```text
brief_computer_vision/
├── api/
│   ├── app/
│   │   ├── main.py             # Point d'entrée principal de l'API
│   │   ├── modeles.py          # Modèles Pydantic pour les données
│   │   ├── schemas.py          # Schémas de données
│   │   ├── utils.py            # Fonctions utilitaires
│   │   └── best.pt             # Modèle YOLO
│   ├── endpoints/
│   │   └── route_prediction.py # Routes spécifiques de l'API
│   └── requirements.txt        # Dépendances Python pour l'API
├── streamlit/
│   ├── app.py                  # Point d'entrée principal de Streamlit
│   ├── pages/
│   │   ├── test_images.py      # Page détection par URL
│   │   └── test_webcams.py     # Page détection webcam
│   └── requirements.txt        # Dépendances Python pour Streamlit
├── Dockerfile.fastapi          # Build image FastAPI
├── Dockerfile.streamlit        # Build image Streamlit
└── docker-compose.yml          # Orchestration Docker Compose
````

---

## 🚀 Installation et Lancement (Local avec Docker Compose)

### Prérequis

* **Docker Desktop** (Windows/macOS, inclut Docker Compose)
* **Ou** Docker Engine + Docker Compose Plugin (Linux)

### Étapes

1. **Cloner le dépôt :**

   ```bash
   git clone <URL_DU_VOTRE_DEPOT>
   cd brief_computer_vision
   ```

   > Remplacez `<URL_DU_VOTRE_DEPOT>` par l'URL réelle de votre repo GitHub.

2. **Naviguer dans le dossier racine du projet :**

   ```bash
   cd /chemin/vers/votre/dossier/brief_computer_vision
   ```

   > Exemple : `cd ~/Documents/Simplon/brief_computer_vision`

3. **Lancer l'application avec Docker Compose :**

   ```bash
   docker compose up --build
   ```

   > Cette commande construit les images Docker de vos services (FastAPI & Streamlit) et les démarre.

4. **Accéder à l'application :**
   Ouvrez votre navigateur sur [http://localhost:8501](http://localhost:8501)

---

## 🖐️ Utilisation de l'Application

* **Détection par webcam (`test_webcams.py`)** :
  Cliquez sur "Démarrer la détection webcam". Vous verrez le flux vidéo annoté en temps réel. Si un feu est détecté (au-delà du seuil de confiance), une alerte s'affichera et l'événement sera enregistré.

* **Détection par URL (`test_images.py`)** :
  Collez une URL d'image potentiellement concernée, puis cliquez sur "Lancer la détection".

---

## 🗄️ Persistance des Données (DuckDB)

Les détections de feu sont enregistrées dans une base DuckDB (`fire_detections.duckdb`).
Ce fichier est persistant grâce à un volume Docker nommé `fire_data` (cf. `docker-compose.yml`).
L’historique de vos détections est donc conservé même après arrêt/redémarrage des conteneurs.

---

## 🛑 Arrêter l'Application

* **Arrêter tous les services Docker :**
  Dans le terminal où tourne `docker compose up`, faites `Ctrl+C`.

* **Supprimer les conteneurs et réseaux :**

  ```bash
  docker compose down
  ```

* **Supprimer aussi les données DuckDB (volume Docker) :**

  ```bash
  docker compose down --volumes
  ```

---

## 🛠️ Technologies Utilisées

* **FastAPI** : API backend
* **Uvicorn** : Serveur ASGI
* **Streamlit** : Interface web
* **Ultralytics YOLOv8** : Modèle de détection d'objets
* **OpenCV (cv2)** : Traitement image/vidéo
* **Pillow (PIL)** : Manipulation d’images
* **Requests** : Requêtes HTTP entre services
* **DuckDB** : Base de données OLAP locale
* **Docker & Docker Compose** : Conteneurisation
* **Python 3.9**

---

## 💡 Améliorations Futures Possibles

* Authentification utilisateur
* Notifications (e-mail, SMS) en cas d'alerte
* Déploiement sur cloud (AWS, Google Cloud, Azure…)
* Amélioration/entraînement du modèle YOLO
* Interface d’admin (gestion des seuils, détections…)
* Support multi-caméras/sources vidéo

---

## 👥 Contributeurs

<section align="center">

<table>
  <tr>
    <td align="center"><b>[Khadija Aassi]</b></td>
    <td align="center"><b>[Khadija Abdelmalek]</b></td>
    <td align="center"><b>[Malek Boumedine]</b></td>
    <td align="center"><b>[Hacène Zerrouk]</b></td>
  </tr>
</table>

</section>


