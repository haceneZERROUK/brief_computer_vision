import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import base64

# --- Configuration ---
API_URL = "http://localhost:8086/detect_fire_url"

st.set_page_config(layout="centered")
st.title("🔥 Détection d'incendie via API")

# --- Interface utilisateur ---
img_url = st.text_input("Collez l'URL de l'image à analyser ici 👇", key="image_url_input")

if st.button("Lancer la détection", help="Cliquez pour envoyer l'image à l'API et détecter les incendies."):
    if not img_url:
        st.error("⚠️ Veuillez entrer une URL d'image valide pour lancer la détection.")
    else:
        with st.spinner("⏳ Envoi de l'image à l'API et traitement..."):
            try:
                # Le payload doit maintenant utiliser la clé "image_url"
                payload = {"image_url": img_url} 

                response = requests.post(API_URL, json=payload)
                response.raise_for_status()

                data = response.json()
                encoded_image_str = data.get("encoded_image")

                if encoded_image_str:
                    st.success("✅ Détection réussie ! Voici l'image annotée :")
                    decoded_image_bytes = base64.b64decode(encoded_image_str)
                    img = Image.open(BytesIO(decoded_image_bytes))
                    st.image(img, caption="Image annotée par le modèle", use_container_width=True)
                else:
                    st.error("❌ L'API n'a pas retourné d'image encodée.")
            
            except requests.exceptions.ConnectionError:
                st.error("❌ Impossible de se connecter à l'API. Assurez-vous que FastAPI est bien lancé sur `http://localhost:8086`.")
            except requests.exceptions.HTTPError as e:
                error_detail = response.json().get("detail", "Aucun détail d'erreur fourni.")
                st.error(f"❌ Erreur de l'API (code {response.status_code}): {e}\nDétail: {error_detail}")
            except Exception as e:
                st.error(f"Une erreur inattendue s'est produite : {e}")