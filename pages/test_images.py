# import streamlit as st
# import requests
# from PIL import Image
# from io import BytesIO

# model = "http://localhost:8086/detect_fire"  # Ton API FastAPI

# st.title("🖼️ Test détection incendie via API")

# img_url = st.text_input("Entrez l'URL de l'image à analyser")

# if st.button("Lancer la détection"):
#     if not img_url:
#         st.error("Merci d'entrer une URL d'image valide.")
#     else:
#         try:
#             # Appeler ton API avec la bonne structure JSON
#             response = requests.post(API_URL, json = {"img_url":img_url})
#             response.raise_for_status()
#             data = response.json()
            
#             # Le chemin relatif de l'image annotée (retournée par l'API)
#             result_img_path = data.get("image_path")
            
#             if result_img_path:
#                 # Comme l'image est sur le serveur local, il faut que Streamlit y ait accès.
#                 # Si Streamlit et l'API tournent sur la même machine, tu peux ouvrir le fichier directement
#                 # Sinon, si accessible via URL, il faudrait ajuster l'URL complète ici.
                
#                 # Ouvrir le fichier localement (chemin relatif)
#                 img = Image.open(result_img_path.lstrip("static/results/result.jpg"))
#                 st.image(img, caption="Image annotée par le modèle", use_container_width=True)
#             else:
#                 st.error("Pas d'image retournée par l'API.")
        
#         except requests.RequestException as e:
#             st.error(f"Erreur lors de l'appel à l'API : {e}")

# Predict with the model
import streamlit as st
from ultralytics import YOLO
from PIL import Image
import numpy as np

st.title("Détection incendie avec YOLO et Streamlit")

# Charger le modèle YOLO
model = YOLO('best.pt')

# Entrée utilisateur : URL ou chemin local de l'image
img_input = st.text_input("Entrez l'URL ou chemin local de l'image à analyser")

if st.button("Lancer la détection"):
    if not img_input:
        st.error("Merci d'entrer une URL ou un chemin d'image valide.")
    else:
        try:
            # Faire la prédiction
            results = model(img_input)

            # Pour chaque résultat (normalement un seul si une seule image)
            for result in results:
                # Obtenir l'image annotée (array numpy) avec les boîtes et labels dessinés
                annotated_img = result.plot()

                # Convertir en image PIL
                annotated_img_pil = Image.fromarray(annotated_img)

                # Afficher dans Streamlit
                st.image(annotated_img_pil, caption="Image annotée par YOLO", use_container_width=True)

                # Optionnel : afficher détails des détections
                st.write("Objets détectés :")
                for box, cls_id, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                    cls_name = result.names[int(cls_id)]
                    x1, y1, x2, y2 = box.cpu().numpy()
                    st.write(f"- {cls_name} (confiance: {conf:.2f}), boîte: [{x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f}]")

        except Exception as e:
            st.error(f"Erreur lors de la détection : {e}")
