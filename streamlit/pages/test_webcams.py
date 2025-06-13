import streamlit as st
import cv2
import numpy as np
import requests
import base64
from PIL import Image
from io import BytesIO
import duckdb # Bibliothèque pour la base de données intégrée (DuckDB)
import datetime # Pour gérer les timestamps des détections
import time # Pour contrôler la fréquence des enregistrements en base de données

"""
Module: Détection d'Incendie par Webcam avec Streamlit

Ce script Streamlit permet de visualiser en temps réel la détection d'incendie via une webcam,
en s'appuyant sur un modèle de vision par ordinateur exposé via une API FastAPI.
Les détections de feu dépassant un certain seuil de confiance sont affichées visuellement
sur la page et enregistrées dans une base de données DuckDB locale.

Fonctionnalités principales :
- Capture du flux vidéo de la webcam en temps réel.
- Envoi des images capturées à une API FastAPI pour le traitement et la détection d'objets (feu).
- Affichage du flux vidéo annoté (avec les boîtes de détection) directement sur l'interface Streamlit.
- Déclenchement d'une alerte visuelle (bandeau d'avertissement) sur la page Streamlit
  lorsqu'une détection de feu dépasse un seuil de confiance prédéfini.
- Enregistrement des événements de détection de feu significatifs (confiance > seuil)
  dans une base de données DuckDB embarquée, avec une fréquence limitée pour éviter le spam.
- Affichage d'un historique des détections enregistrées en base de données.

Dépendances requises :
- streamlit
- opencv-python
- numpy
- requests
- Pillow (PIL)
- duckdb
"""

# --- Configuration de la Page Streamlit (DOIT ÊTRE LA PREMIÈRE COMMANDE STREAMLIT) ---
# st.set_page_config doit être la première commande Streamlit appelée dans le script.
# Elle configure l'apparence générale de la page.
#st.set_page_config(layout="centered") # 'centered' pour un contenu centré, 'wide' pour une largeur maximale.
st.title("🔥 Détection d'incendie en direct via API") # Définit le titre principal de l'application affiché en haut de la page.

# --- Configuration Générale de l'Application ---
API_URL_WEBCAM = "http://localhost:8086/detect_fire_webcam" # URL du point de terminaison de l'API FastAPI
                                                           # dédié au traitement des images de la webcam.
#DUCKDB_PATH = "fire_detections.duckdb" # Nom du fichier de la base de données DuckDB.
                                      # Ce fichier sera créé localement dans le répertoire d'exécution du script Streamlit.

DUCKDB_PATH = "/app/fire_detections.duckdb"
FIRE_DETECTION_CONFIDENCE_THRESHOLD = 0.4 # Seuil de confiance (valeur entre 0 et 1) au-delà duquel une détection
                                        # est considérée comme un "feu" valide, déclenchant l'alerte visuelle
                                        # et l'enregistrement en base de données.
DB_LOG_INTERVAL_SECONDS = 10 # Intervalle minimal (en secondes) entre deux enregistrements consécutifs
                             # d'une détection de feu dans la base de données DuckDB.
                             # Cela permet d'éviter un enregistrement excessif lors d'une détection prolongée.

# --- Fonctions de Gestion de la Base de Données DuckDB ---

@st.cache_resource # Décorateur Streamlit essentiel pour la gestion des ressources non-Python (comme une connexion BDD).
                   # Il met en cache l'objet retourné par la fonction, garantissant que la connexion
                   # n'est établie qu'une seule fois au démarrage de l'application et est réutilisée
                   # lors des reruns Streamlit. La connexion reste ouverte tant que l'application tourne.
def get_db_connection():
    """
    Établit et retourne une connexion à la base de données DuckDB.
    Si le fichier de base de données n'existe pas, il est créé.
    La table 'fire_detections' est également créée si elle n'existe pas.

    La connexion étant gérée par `@st.cache_resource`, il est impératif de NE PAS la fermer
    manuellement (`conn.close()`) après chaque opération dans les fonctions qui l'utilisent,
    car cela invaliderait la connexion mise en cache pour les futurs appels.

    Returns:
        duckdb.DuckDBPyConnection: Un objet de connexion actif à la base de données DuckDB.
    """
    conn = duckdb.connect(database=DUCKDB_PATH) # Connecte à la base de données DuckDB.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fire_detections (
            id VARCHAR PRIMARY KEY,         -- Identifiant unique de la détection (basé sur le timestamp pour la traçabilité)
            timestamp TIMESTAMP,            -- Horodatage précis de l'événement de détection
            source_type VARCHAR,            -- Type de source de l'image (ex: 'webcam', utile si d'autres sources sont ajoutées)
            confidence FLOAT                -- Niveau de confiance du modèle pour la détection de feu (entre 0 et 1)
        );
    """) # Exécute une requête SQL pour créer la table si elle n'existe pas.
    return conn

def log_fire_detection(confidence: float):
    """
    Enregistre un événement de détection de feu dans la base de données DuckDB.
    Cette fonction intègre une logique de temporisation pour limiter la fréquence des enregistrements
    en fonction de `DB_LOG_INTERVAL_SECONDS`.

    Args:
        confidence (float): Le niveau de confiance de la détection de feu par le modèle.

    Returns:
        str | None: L'identifiant unique de la détection si l'enregistrement a eu lieu avec succès,
                    sinon None si l'enregistrement a été ignoré (délai non atteint) ou en cas d'erreur.
    """
    conn = get_db_connection() # Récupère la connexion DuckDB mise en cache.
    
    # Contrôle de la fréquence d'enregistrement pour éviter les entrées excessives en BDD.
    current_time = time.time() # Obtient le temps actuel en secondes depuis l'époque.
    if 'last_db_log_time' not in st.session_state:
        st.session_state.last_db_log_time = 0.0 # Initialise le temps du dernier log en BDD lors du premier appel.
    
    # Vérifie si le délai minimum entre les logs est écoulé.
    if (current_time - st.session_state.last_db_log_time) >= DB_LOG_INTERVAL_SECONDS:
        try:
            # Génère un identifiant unique pour cette détection en utilisant l'horodatage précis.
            detection_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
            timestamp = datetime.datetime.now() # Horodatage complet pour l'enregistrement.

            # Exécute la requête d'insertion dans la table `fire_detections`.
            conn.execute(
                "INSERT INTO fire_detections (id, timestamp, source_type, confidence) VALUES (?, ?, ?, ?)",
                (detection_id, timestamp, "webcam", confidence)
            )
            st.session_state.last_db_log_time = current_time # Met à jour le temps du dernier log effectué.
            st.success(f"Détection de feu (confiance: {confidence:.2f}) enregistrée en BDD.") # Message de succès Streamlit.
            return detection_id
        except Exception as e:
            # Affiche un message d'erreur Streamlit si l'enregistrement échoue.
            st.error(f"Erreur lors de l'enregistrement de la détection de feu : {e}")
            return None
    else:
        # Retourne None si l'enregistrement est ignoré en raison du délai non atteint.
        return None

# --- Initialisation de la Base de Données au Démarrage de l'Application ---
# Ce bloc est exécuté une fois au lancement de l'application Streamlit.
# Il garantit que le fichier de base de données DuckDB et sa table sont créés
# ou accessibles dès le début, avant que les opérations de détection ne commencent.
try:
    get_db_connection() # Appelle la fonction pour s'assurer que la BDD est initialisée et en cache.
    # La connexion est maintenue ouverte par @st.cache_resource, donc pas de .close() ici.
    st.info(f"Base de données DuckDB initialisée à : {DUCKDB_PATH}") # Message d'information sur la page.
except Exception as e:
    # Affiche un message d'erreur si l'initialisation de la BDD échoue (ex: problème de permissions).
    st.error(f"Erreur lors de l'initialisation de la base de données DuckDB : {e}")

# --- Gestion de l'État de la Webcam et des Données de Session ---
# st.session_state permet de conserver des variables à travers les reruns de l'application.
if 'webcam_running' not in st.session_state:
    st.session_state.webcam_running = False # État booléen indiquant si la webcam est active.
if 'last_db_log_time' not in st.session_state:
    st.session_state.last_db_log_time = 0.0 # Initialise le timestamp du dernier enregistrement en BDD.

def toggle_webcam():
    """
    Bascule l'état de fonctionnement de la webcam (démarrée ou arrêtée)
    en modifiant la variable `st.session_state.webcam_running`.
    """
    st.session_state.webcam_running = not st.session_state.webcam_running

# --- Boutons de Contrôle de la Webcam ---
# Utilise st.columns pour organiser les boutons côte à côte.
col1, col2 = st.columns(2) # Crée deux colonnes de largeur égale.
with col1:
    # Bouton pour démarrer le flux de la webcam et la détection.
    if col1.button("Démarrer la détection webcam", key="start_webcam"):
        toggle_webcam() # Appelle la fonction pour activer la webcam.
with col2:
    # Bouton pour arrêter le flux de la webcam et la détection.
    if col2.button("Arrêter la détection webcam", key="stop_webcam"):
        toggle_webcam() # Appelle la fonction pour désactiver la webcam.

# --- Placeholders pour l'Affichage Dynamique de l'Interface Utilisateur ---
# Les placeholders (`st.empty()`) permettent de mettre à jour des éléments spécifiques
# de l'interface utilisateur sans avoir à redessiner toute la page à chaque rerun,
# améliorant ainsi la fluidité de l'affichage.
stframe = st.empty() # Placeholder où le flux vidéo de la webcam (annoté) sera affiché.
status_message_placeholder = st.empty() # Placeholder pour les messages de statut généraux (ex: "Webcam active...", erreurs).

# Placeholder dédié spécifiquement à l'alerte visuelle de feu.
# Cela garantit qu'une seule alerte de feu est affichée à la fois,
# évitant l'accumulation de messages et permettant de l'effacer facilement.
fire_alert_placeholder = st.empty() 

# --- Boucle Principale de Traitement du Flux Vidéo ---
# Ce bloc de code s'exécute uniquement si la webcam est active (`st.session_state.webcam_running` est True).
if st.session_state.webcam_running:
    cap = cv2.VideoCapture(0) # Initialise l'objet de capture vidéo pour la webcam par défaut (index 0).

    if not cap.isOpened():
        # Affiche une erreur si la webcam n'est pas accessible ou déjà utilisée.
        st.error("Impossible d'ouvrir la caméra. Veuillez vérifier qu'elle n'est pas déjà utilisée ou qu'elle est connectée.")
        st.session_state.webcam_running = False # Désactive l'état de la webcam pour arrêter la boucle.
    else:
        status_message_placeholder.info("Webcam active. Envoi des images à l'API pour détection...") # Message informatif.
        while st.session_state.webcam_running: # Boucle continue tant que la webcam est censée être active.
            ret, frame = cap.read() # Lit une frame du flux vidéo de la webcam. `ret` est un booléen (succès), `frame` est l'image.
            if not ret:
                status_message_placeholder.warning("Impossible de récupérer une image de la caméra.")
                continue # Passe à l'itération suivante de la boucle si la lecture de la frame échoue.
            
            # --- Prétraitement de l'Image pour l'API ---
            # Convertit le format de couleur de l'image de BGR (utilisé par OpenCV) en RGB (attendu par PIL et YOLO).
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(frame_rgb) # Convertit le tableau NumPy (représentation de l'image) en objet Image PIL.

            # Encode l'image en format Base64 pour qu'elle puisse être transmise via une requête JSON HTTP.
            buffered = BytesIO() # Crée un buffer en mémoire pour stocker les données de l'image.
            img_pil.save(buffered, format="JPEG") # Sauvegarde l'image PIL dans le buffer au format JPEG.
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8") # Encode les bytes du buffer en Base64 et les décode en chaîne UTF-8.

            payload = {"image_data": img_base64} # Construit le dictionnaire de données (payload) à envoyer à l'API.

            # --- Appel à l'API FastAPI et Traitement de la Réponse ---
            try:
                response = requests.post(API_URL_WEBCAM, json=payload, timeout=5) # Envoie la requête POST à l'API. Un timeout de 5 secondes est défini.
                response.raise_for_status() # Vérifie si la requête a réussi (code statut 2xx). Lève une HTTPError sinon.

                data = response.json() # Parse le corps de la réponse JSON de l'API.
                encoded_image_from_api = data.get("encoded_image") # Extrait la chaîne Base64 de l'image annotée.
                fire_confidence = data.get("fire_confidence") # Extrait le niveau de confiance de la détection de feu.

                # --- Affichage de l'Image Annotée et Logique d'Alerte/Enregistrement ---
                # Vérifie si l'API a bien retourné une image encodée valide (non vide et de type chaîne de caractères).
                if encoded_image_from_api and isinstance(encoded_image_from_api, str):
                    # Décode l'image Base64 reçue de l'API en bytes.
                    decoded_image_bytes = base64.b64decode(encoded_image_from_api)
                    # Ouvre les bytes décodés comme une image PIL.
                    annotated_img_pil = Image.open(BytesIO(decoded_image_bytes))
                    # Affiche l'image annotée dans le placeholder Streamlit dédié au flux vidéo.
                    stframe.image(annotated_img_pil, channels="RGB", use_container_width=True, caption="Détection en direct")
                    
                    # Logique conditionnelle basée sur la confiance de détection de feu.
                    if fire_confidence is not None and fire_confidence >= FIRE_DETECTION_CONFIDENCE_THRESHOLD:
                        # Si un feu est détecté avec une confiance suffisante.
                        status_message_placeholder.success(f"🔥 Feu détecté avec une confiance de : {fire_confidence:.2f} !")
                        
                        # ALERTE VISUELLE UNIQUE SUR LA PAGE STREAMLIT : Met à jour le contenu du placeholder d'alerte.
                        fire_alert_placeholder.warning(f"🚨 ALERTE FEU ! Confiance : {fire_confidence:.2f} - Vérifiez la situation !")

                        # Enregistre la détection dans la base de données DuckDB (respecte l'intervalle de temps).
                        log_fire_detection(confidence=fire_confidence)
                        
                    elif fire_confidence is not None and fire_confidence < FIRE_DETECTION_CONFIDENCE_THRESHOLD:
                         # Si une détection de feu est présente mais sous le seuil d'alerte.
                         status_message_placeholder.info(f"Détection de feu (confiance: {fire_confidence:.2f}) en dessous du seuil d'alerte.")
                         fire_alert_placeholder.empty() # Efface toute alerte visuelle précédente.
                    else:
                        # Si aucun feu n'est détecté (fire_confidence est None ou non pertinent).
                        status_message_placeholder.info("Pas de feu détecté pour cette frame.")
                        fire_alert_placeholder.empty() # Efface l'alerte visuelle.
                else:
                    # Gère le cas où l'API ne retourne pas une image encodée valide.
                    status_message_placeholder.warning("L'API n'a pas retourné une image encodée ou le format est incorrect.")
                    fire_alert_placeholder.empty() # Efface l'alerte visuelle.
            
            except requests.exceptions.ConnectionError:
                # Gère les erreurs de connexion au serveur de l'API.
                status_message_placeholder.error("Impossible de se connecter à l'API. Assurez-vous que FastAPI est lancé.")
                st.session_state.webcam_running = False # Arrête la boucle de la webcam.
                fire_alert_placeholder.empty() # Efface l'alerte.
            except requests.exceptions.Timeout:
                # Gère les erreurs de timeout si l'API ne répond pas dans le délai imparti.
                status_message_placeholder.warning("La requête à l'API a expiré. Le traitement prend peut-être trop de temps.")
                fire_alert_placeholder.empty() # Efface l'alerte.
            except requests.exceptions.HTTPError as e:
                # Gère les erreurs HTTP (4xx, 5xx) renvoyées par l'API.
                # Tente d'extraire les détails de l'erreur du corps de la réponse JSON de l'API.
                error_detail = response.json().get("detail", "Aucun détail d'erreur fourni.")
                status_message_placeholder.error(f"Erreur de l'API (code {response.status_code}): {e}\nDétail: {error_detail}")
                st.session_state.webcam_running = False # Arrête la boucle de la webcam.
                fire_alert_placeholder.empty() # Efface l'alerte.
            except Exception as e:
                # Capture et affiche toute autre exception inattendue.
                status_message_placeholder.error(f"Une erreur inattendue s'est produite lors du traitement de la frame : {e}")
                st.session_state.webcam_running = False # Arrête la boucle de la webcam.
                fire_alert_placeholder.empty() # Efface l'alerte.
            
            # --- Contrôle du Flux Vidéo ---
            # Attend 1ms pour permettre à OpenCV de traiter les événements (nécessaire pour garder la fenêtre réactive)
            # et pour contrôler le taux de rafraîchissement des frames.
            cv2.waitKey(1)

# --- Instructions et Nettoyage si la Webcam est Arrêtée ---
else:
    status_message_placeholder.info("Cliquez sur 'Démarrer la détection webcam' pour lancer la diffusion.")
    fire_alert_placeholder.empty() # S'assure que l'alerte visuelle est effacée lorsque la webcam est inactive.

# S'assure de libérer la ressource de la caméra lorsque l'application Streamlit se termine
# ou lorsque la section de la webcam n'est plus active.
if 'cap' in locals() and cap.isOpened():
    cap.release()

# --- Section pour Visualiser l'Historique des Détections ---
st.header("Historique des détections de feu") # Titre de la section dédiée à l'historique.
# Bouton pour rafraîchir l'affichage du tableau des détections enregistrées.
if st.button("Actualiser l'historique"):
    conn = get_db_connection() # Récupère la connexion à la base de données.
    # Exécute une requête SQL pour récupérer toutes les détections, triées par horodatage décroissant.
    # .fetchdf() convertit le résultat en un DataFrame Pandas pour un affichage facile.
    df = conn.execute("SELECT * FROM fire_detections ORDER BY timestamp DESC").fetchdf()
    if not df.empty:
        st.dataframe(df) # Affiche le DataFrame des détections dans Streamlit.
    else:
        st.info("Aucune détection enregistrée pour le moment.") # Message si la base de données est vide.
