import streamlit as st
import requests
import base64
from PIL import Image
import io
import time

# Titre de l'application
st.title("🔥 Détection d'incendie en temps réel")
st.caption("Le flux s'actualise en appelant l'API en continu.")

# URL de l'endpoint webcam de ton API
# API_URL = "http://localhost:8086/detect_fire_webcam"    # localhost
API_URL = "http://fastapi:8086/detect_fire_webcam"    # docker

# Initialiser l'état de la détection dans la session
if 'run_detection' not in st.session_state:
    st.session_state.run_detection = False

# Créer deux colonnes pour les boutons
col1, col2 = st.columns(2)

with col1:
    if st.button("Démarrer le flux", type="primary"):
        st.session_state.run_detection = True

with col2:
    if st.button("Arrêter le flux"):
        st.session_state.run_detection = False
        st.info("Détection arrêtée.")

# Espace réservé pour afficher l'image et le statut
image_placeholder = st.empty()
status_placeholder = st.empty()

# Boucle principale pour simuler le flux vidéo
if st.session_state.run_detection:
    while st.session_state.run_detection:
        try:
            # Appel à l'API qui gère la capture et la détection
            response = requests.post(API_URL, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and "image_encoded" in data:
                    img_b64 = data["image_encoded"]
                    img_bytes = base64.b64decode(img_b64)
                    image = Image.open(io.BytesIO(img_bytes))
                    
                    # Afficher l'image analysée
                    image_placeholder.image(
                        image, 
                        caption=data.get("message", "Image analysée"), 
                        use_container_width=True
                    )
                    
                    # Afficher l'alerte correspondante
                    if data.get("fire_detected"):
                        status_placeholder.error("🚨 ALERTE FEU DÉTECTÉ ! 🚨")
                    elif data.get("smoke_detected"):
                        status_placeholder.warning("⚠️ ALERTE FUMÉE DÉTECTÉE ! ⚠️")
                    else:
                        status_placeholder.success("✅ Aucune menace détectée.")
                else:
                    status_placeholder.warning("L'API a répondu mais n'a pas retourné d'image valide.")

            else:
                status_placeholder.error(f"Erreur de l'API (code {response.status_code}): {response.text}")
                st.session_state.run_detection = False  # Arrêter la boucle en cas d'erreur
                break

        except requests.exceptions.RequestException as e:
            status_placeholder.error(f"Impossible de se connecter à l'API : {e}")
            st.session_state.run_detection = False  # Arrêter la boucle en cas d'erreur
            break
            
        # Pause pour contrôler la fréquence de rafraîchissement
        time.sleep(0.1)  # Environ 10 images par seconde (en théorie)

