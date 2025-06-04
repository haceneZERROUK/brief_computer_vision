import streamlit as st
import requests
from PIL import Image
from io import BytesIO

API_URL = "http://localhost:8086/detect_fire"  # Ton API FastAPI

st.title("🖼️ Test détection incendie via API")

img_url = st.text_input("Entrez l'URL de l'image à analyser")

if st.button("Lancer la détection"):
    if not img_url:
        st.error("Merci d'entrer une URL d'image valide.")
    else:
        try:
            # Appeler ton API avec la bonne structure JSON
            response = requests.post(API_URL, json = {"img_url":img_url})
            response.raise_for_status()
            data = response.json()
            
            # Le chemin relatif de l'image annotée (retournée par l'API)
            result_img_path = data.get("image_path")
            
            if result_img_path:
                # Comme l'image est sur le serveur local, il faut que Streamlit y ait accès.
                # Si Streamlit et l'API tournent sur la même machine, tu peux ouvrir le fichier directement
                # Sinon, si accessible via URL, il faudrait ajuster l'URL complète ici.
                
                # Ouvrir le fichier localement (chemin relatif)
                img = Image.open(result_img_path.lstrip("static/results/result.jpg"))
                st.image(img, caption="Image annotée par le modèle", use_container_width=True)
            else:
                st.error("Pas d'image retournée par l'API.")
        
        except requests.RequestException as e:
            st.error(f"Erreur lors de l'appel à l'API : {e}")
