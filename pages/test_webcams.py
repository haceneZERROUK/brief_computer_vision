# import streamlit as st
# import cv2
# import numpy as np
# from ultralytics import YOLO

# # Charger le modèle YOLO
# yolo = YOLO('best.pt')


# # Fonction pour obtenir les couleurs des classes
# def getColours(cls_num):
#     base_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
#     color_index = cls_num % len(base_colors)
#     increments = [(1, -2, 1), (-2, 1, -1), (1, -1, 2)]
#     color = [base_colors[color_index][i] + increments[color_index][i] * 
#     (cls_num // len(base_colors)) % 256 for i in range(3)]
#     return tuple(color)

# # Fonction de flux vidéo avec détection YOLO
# def video_stream():
#     cap = cv2.VideoCapture(0)
    
#     if not cap.isOpened():
#         st.error("Impossible d'ouvrir la caméra")
#         return
    
#     stframe = st.empty()

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             continue
        
#         results = yolo.track(frame, stream=True)

#         for result in results:
#             classes_names = result.names

#             # Parcours des boîtes de détection
#             for box in result.boxes:
#                 if box.conf[0] > 0.4:
#                     x1, y1, x2, y2 = box.xyxy[0]
#                     x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
#                     cls = int(box.cls[0])
#                     class_name = classes_names[cls]
#                     color = getColours(cls)

#                     # Dessiner le rectangle autour de l'objet
#                     cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

#                     # Afficher le nom de la classe et la confiance
#                     cv2.putText(frame, f'{class_name} {box.conf[0]:.2f}', (x1, y1),
#                                 cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

#         # Convertir l'image en format RGB (OpenCV utilise BGR)
#         frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

#         # Afficher l'image dans Streamlit
#         stframe.image(frame_rgb, channels="RGB", use_container_width=True)

#     # Libérer la caméra et fermer toutes les fenêtres
#     cap.release()

# # Titre de la page Streamlit
# st.title("Page d'Accueil - Détection d'objets avec YOLO")

# if st.button("⛔ Arrêter la webcam"):
#     st.rerun()

# # Ajouter un bouton pour démarrer la webcam
# if st.button("Démarrer la webcam avec YOLO"):
#     video_stream()

import streamlit as st
import cv2
import numpy as np
import requests
import base64
from PIL import Image
from io import BytesIO
import duckdb # Pour la base de données
import datetime # Pour les timestamps
import smtplib # Pour l'envoi d'e-mails
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Configuration Générale ---
API_URL_WEBCAM = "http://localhost:8086/detect_fire_webcam"
DUCKDB_PATH = "fire_detections.duckdb" # Chemin du fichier DuckDB pour Streamlit
FIRE_DETECTION_CONFIDENCE_THRESHOLD = 0.4 # Seuil de confiance pour enregistrer et alerter

# --- Configuration Email ---
EMAIL_SENDER = st.secrets["email"]["sender_email"]
EMAIL_PASSWORD = st.secrets["email"]["sender_password"]
EMAIL_RECEIVER = st.secrets["email"]["receiver_email"]
SMTP_SERVER = st.secrets["email"]["smtp_server"]
SMTP_PORT = st.secrets["email"]["smtp_port"]

# --- Fonction de gestion de la base de données DuckDB ---
@st.cache_resource # Permet de ne pas recréer la connexion à chaque relancement
def get_db_connection():
    """
    Établit une connexion à la base de données DuckDB et crée la table si elle n'existe pas.
    """
    conn = duckdb.connect(database=DUCKDB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fire_detections (
            id VARCHAR PRIMARY KEY,
            timestamp TIMESTAMP,
            source_type VARCHAR, -- 'webcam'
            confidence FLOAT,
            # Vous pouvez ajouter un lien vers l'image si vous décidez de sauvegarder les images localement
            # ou l'encodage base64 si vous voulez les stocker dans la BDD (attention à la taille)
            # image_base64 VARCHAR
        );
    """)
    return conn

def log_fire_detection(
    confidence: float
):
    """
    Enregistre une détection de feu dans la base de données DuckDB.
    """
    conn = get_db_connection()
    try:
        detection_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        timestamp = datetime.datetime.now()

        conn.execute(
            "INSERT INTO fire_detections (id, timestamp, source_type, confidence) VALUES (?, ?, ?, ?)",
            (detection_id, timestamp, "webcam", confidence)
        )
        st.success(f"Détection de feu (confiance: {confidence:.2f}) enregistrée en BDD.")
        return detection_id
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement de la détection de feu : {e}")
        return None

# --- Fonction d'envoi d'e-mail d'alerte ---
def send_email_alert(confidence: float):
    """
    Envoie un e-mail d'alerte en cas de détection de feu.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = f"ALERTE INCENDIE - Détection avec confiance {confidence:.2f}!"

        body = f"Un feu a été détecté par la webcam à {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} avec une confiance de {confidence:.2f}."
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls() # Mettre en place le chiffrement TLS
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        st.success(f"Alerte email envoyée à {EMAIL_RECEIVER} !")
    except Exception as e:
        st.error(f"Erreur lors de l'envoi de l'e-mail d'alerte : {e}")
        st.info("Vérifiez vos paramètres SMTP et si l'accès pour les applications moins sécurisées est activé (pour Gmail).")

# --- Interface utilisateur Streamlit ---
st.set_page_config(layout="centered")
st.title("🔥 Détection d'incendie en direct via API")

# --- État de la webcam ---
if 'webcam_running' not in st.session_state:
    st.session_state.webcam_running = False

def toggle_webcam():
    st.session_state.webcam_running = not st.session_state.webcam_running

col1, col2 = st.columns(2)
with col1:
    if col1.button("Démarrer la détection webcam", key="start_webcam"):
        toggle_webcam()
with col2:
    if col2.button("Arrêter la détection webcam", key="stop_webcam"):
        toggle_webcam()

stframe = st.empty()
status_message_placeholder = st.empty() # Placeholder pour les messages de statut

# --- Flux vidéo avec envoi à l'API ---
if st.session_state.webcam_running:
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("Impossible d'ouvrir la caméra. Veuillez vérifier qu'elle n'est pas déjà utilisée ou qu'elle est connectée.")
        st.session_state.webcam_running = False
    else:
        status_message_placeholder.info("Webcam active. Envoi des images à l'API pour détection...")
        while st.session_state.webcam_running:
            ret, frame = cap.read()
            if not ret:
                status_message_placeholder.warning("Impossible de récupérer une image de la caméra.")
                continue
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(frame_rgb)

            buffered = BytesIO()
            img_pil.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            payload = {"image_data": img_base64}

            try:
                response = requests.post(API_URL_WEBCAM, json=payload, timeout=5)
                response.raise_for_status()

                data = response.json()
                encoded_image_from_api = data.get("encoded_image")
                fire_confidence = data.get("fire_confidence")

                if encoded_image_from_api:
                    decoded_image_bytes = base64.b64decode(encoded_image_from_api)
                    annotated_img_pil = Image.open(BytesIO(decoded_image_bytes))
                    stframe.image(annotated_img_pil, channels="RGB", use_container_width=True, caption="Détection en direct")
                    
                    if fire_confidence is not None and fire_confidence >= FIRE_DETECTION_CONFIDENCE_THRESHOLD:
                        status_message_placeholder.success(f"🔥 Feu détecté avec une confiance de : {fire_confidence:.2f} !")
                        log_fire_detection(confidence=fire_confidence) # Enregistrer dans DuckDB
                        send_email_alert(confidence=fire_confidence) # Envoyer l'alerte email
                    elif fire_confidence is not None and fire_confidence < FIRE_DETECTION_CONFIDENCE_THRESHOLD:
                         status_message_placeholder.info(f"Détection de feu (confiance: {fire_confidence:.2f}) en dessous du seuil d'alerte.")
                    else:
                        status_message_placeholder.info("Pas de feu détecté pour cette frame.")
                else:
                    status_message_placeholder.warning("L'API n'a pas retourné d'image annotée.")
            
            except requests.exceptions.ConnectionError:
                status_message_placeholder.error("Impossible de se connecter à l'API. Assurez-vous que FastAPI est lancé.")
                st.session_state.webcam_running = False
            except requests.exceptions.Timeout:
                status_message_placeholder.warning("La requête à l'API a expiré. Le traitement prend peut-être trop de temps.")
            except requests.exceptions.HTTPError as e:
                error_detail = response.json().get("detail", "Aucun détail d'erreur fourni.")
                status_message_placeholder.error(f"Erreur de l'API (code {response.status_code}): {e}\nDétail: {error_detail}")
                st.session_state.webcam_running = False
            except Exception as e:
                status_message_placeholder.error(f"Une erreur inattendue s'est produite lors du traitement de la frame : {e}")
                st.session_state.webcam_running = False
            
            # Attendre un court instant pour ne pas surcharger
            cv2.waitKey(1)
else:
    status_message_placeholder.info("Cliquez sur 'Démarrer la détection webcam' pour lancer la diffusion.")

# Assurez-vous de libérer la caméra à la fin
if 'cap' in locals() and cap.isOpened():
    cap.release()

# --- Section pour visualiser les détections (optionnel) ---
st.header("Historique des détections de feu")
if st.button("Actualiser l'historique"):
    try:
        conn = get_db_connection()
        df = conn.execute("SELECT * FROM fire_detections ORDER BY timestamp DESC").fetchdf()
        if not df.empty:
            st.dataframe(df)
        else:
            st.info("Aucune détection enregistrée pour le moment.")
    except Exception as e:
        st.error(f"Impossible de lire l'historique des détections : {e}")