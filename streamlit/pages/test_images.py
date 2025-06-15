import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import base64

"""
Module: Détection d'Incendie par URL avec Streamlit

Ce script Streamlit permet aux utilisateurs de soumettre une URL d'image à une API FastAPI
pour effectuer une détection d'incendie. L'image annotée par le modèle est ensuite affichée
directement sur la page Streamlit.

Fonctionnalités principales :
- Champ de saisie pour l'URL de l'image.
- Appel à une API FastAPI pour le traitement de l'image.
- Affichage de l'image traitée (annotée par le modèle) directement sur la page.
- Gestion des erreurs courantes (connexion API, format de l'image).
"""

# --- Configuration Générale de l'Application ---
# URL de l'API FastAPI pour la détection d'incendie à partir d'une URL d'image.
# API_URL = "http://localhost:8086/detect_fire_url"     # localhost
API_URL = "http://fastapi:8086/detect_fire_url"       # docker

# --- Configuration de la Page Streamlit ---
#st.set_page_config(layout="centered") # Définit la mise en page de l'application Streamlit.
st.title("🔥 Détection d'incendie via URL d'image") # Titre principal de l'application.

# --- Interface Utilisateur : Saisie de l'URL de l'Image ---
# Champ de texte permettant à l'utilisateur de coller l'URL d'une image.
img_url = st.text_input("Collez l'URL de l'image à analyser ici 👇", key="image_url_input")

# Bouton pour déclencher le processus de détection.
if st.button("Lancer la détection", help="Cliquez pour envoyer l'image à l'API et détecter les incendies."):
    # --- Validation de l'entrée utilisateur ---
    if not img_url:
        st.error("⚠️ Veuillez entrer une URL d'image valide pour lancer la détection.")
    else:
        # --- Processus d'Envoi à l'API et Réception ---
        # Affiche un spinner pour indiquer que le traitement est en cours.
        with st.spinner("⏳ Envoi de l'image à l'API et traitement..."):
            try:
                # Construit le payload JSON. La clé "image_url" doit correspondre au champ
                # attendu par le modèle Pydantic de votre API FastAPI (ex: ImageUrlRequest).
                payload = {"image_url": img_url} 

                # Envoie la requête POST à l'API avec le payload JSON.
                response = requests.post(API_URL, json=payload)
                # Lève une exception HTTPError pour les statuts de réponse 4xx ou 5xx.
                response.raise_for_status()

                # Parse la réponse JSON de l'API.
                data = response.json()
                # Récupère la chaîne de caractères Base64 de l'image annotée depuis la réponse.
                encoded_image_str = data.get("encoded_image")
                # Récupère la confiance de la détection de feu (si fournie par l'API).
                # fire_confidence = data.get("fire_confidence") # Commenté car non utilisé pour l'affichage ici.

                # --- Traitement et Affichage de la Réponse de l'API ---
                if encoded_image_str:
                    st.success("✅ Détection réussie ! Voici l'image annotée :")
                    # Décode la chaîne Base64 en bytes.
                    decoded_image_bytes = base64.b64decode(encoded_image_str)
                    # Ouvre l'image à partir des bytes décodés en utilisant Pillow.
                    img = Image.open(BytesIO(decoded_image_bytes))
                    # Affiche l'image annotée dans Streamlit.
                    st.image(img, caption="Image annotée par le modèle", use_container_width=True)

                    # Vous pourriez ajouter ici un affichage de la confiance si nécessaire
                    # if fire_confidence is not None:
                    #     st.info(f"Confiance de détection de feu : {fire_confidence:.2f}")
                else:
                    st.error("❌ L'API n'a pas retourné d'image encodée ou le format est incorrect.")
            
            except requests.exceptions.ConnectionError:
                # Gère les erreurs de connexion à l'API (ex: API non lancée, problème réseau).
                st.error(f"❌ Impossible de se connecter à l'API. Assurez-vous que FastAPI est bien lancé sur {API_URL}")
            except requests.exceptions.HTTPError as e:
                # Gère les erreurs HTTP retournées par l'API (ex: 400 Bad Request, 500 Internal Server Error).
                # Tente d'extraire des détails d'erreur du corps de la réponse JSON de l'API.
                try:
                    error_detail = response.json().get("detail", "Aucun détail d'erreur fourni.")
                except:
                    error_detail = "Le corps de la réponse n'est pas un JSON valide."
                st.error(f"❌ Erreur de l'API (code {response.status_code}): {e}\nDétail: {error_detail}")
            except Exception as e:
                # Gère toute autre exception inattendue.
                st.error(f"Une erreur inattendue s'est produite : {e}")

