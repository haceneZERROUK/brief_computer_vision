# # import streamlit as st
# # import requests
# # from PIL import Image
# # from io import BytesIO

# # API_URL = "http://localhost:8086/detect_fire"  # Ton API FastAPI

# # st.title("🖼️ Test détection incendie via API")

# # img_url = st.text_input("Entrez l'URL de l'image à analyser")
# # dico = {'image_url':img_url}
# # if st.button("Lancer la détection"):
# #     if not img_url:
# #         st.error("Merci d'entrer une URL d'image valide.")
# #     else:
# #         try:
# #             # Appeler ton API avec la bonne structure JSON
# #             response = requests.post(API_URL, json = dico.image_url)
# #             response.raise_for_status()
# #             data = response.json() # Le chemin relatif de l'image annotée (retournée par l'API)
# #             result_img_path = data.get("image_path")
            
# #             if result_img_path:
# #                 # Comme l'image est sur le serveur local, il faut que Streamlit y ait accès.
# #                 # Si Streamlit et l'API tournent sur la même machine, tu peux ouvrir le fichier directement
# #                 # Sinon, si accessible via URL, il faudrait ajuster l'URL complète ici.
                
# #                 # Ouvrir le fichier localement (chemin relatif)
# #                 img = Image.open(result_img_path.lstrip("static/results/result.jpg"))
# #                 st.image(img, caption="Image annotée par le modèle", use_container_width=True)
# #             else:
# #                 st.error("Pas d'image retournée par l'API.")
        
# #         except requests.RequestException as e:
# #             st.error(f"Erreur lors de l'appel à l'API : {e}")

# # Predict with the model
# # import streamlit as st
# # from ultralytics import YOLO
# # from PIL import Image
# # import numpy as np

# # st.title("Détection incendie avec YOLO et Streamlit")

# # # Charger le modèle YOLO
# # model = YOLO('best.pt')

# # # Entrée utilisateur : URL ou chemin local de l'image
# # img_input = st.text_input("Entrez l'URL ou chemin local de l'image à analyser")

# # if st.button("Lancer la détection"):
# #     if not img_input:
# #         st.error("Merci d'entrer une URL ou un chemin d'image valide.")
# #     else:
# #         try:
# #             # Faire la prédiction
# #             results = model(img_input)

# #             # Pour chaque résultat (normalement un seul si une seule image)
# #             for result in results:
# #                 # Obtenir l'image annotée (array numpy) avec les boîtes et labels dessinés
# #                 annotated_img = result.plot()

# #                 # Convertir en image PIL
# #                 annotated_img_pil = Image.fromarray(annotated_img)

# #                 # Afficher dans Streamlit
# #                 st.image(annotated_img_pil, caption="Image annotée par YOLO", use_container_width=True)

# #                 # Optionnel : afficher détails des détections
# #                 st.write("Objets détectés :")
# #                 for box, cls_id, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
# #                     cls_name = result.names[int(cls_id)]
# #                     x1, y1, x2, y2 = box.cpu().numpy()
# #                     st.write(f"- {cls_name} (confiance: {conf:.2f}), boîte: [{x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f}]")

# #         except Exception as e:
# #             st.error(f"Erreur lors de la détection : {e}")

# # api/app/use_model.py

# import requests
# from PIL import Image
# from io import BytesIO
# import base64 # Importez la bibliothèque base64
# from ultralytics import YOLO

# # Charger le modèle une seule fois au démarrage de l'application
# # Assurez-vous que le chemin du modèle est correct par rapport à la racine de votre projet FastAPI
# model = YOLO("api/app/best.pt")

# def use_model(URL_IMAGE: str) -> str:
#     """
#     Télécharge une image, la traite avec le modèle YOLO,
#     et retourne l'image annotée encodée en Base64.
#     """
#     # Télécharger ou charger l'image
#     if URL_IMAGE.startswith("http"):
#         try:
#             response = requests.get(URL_IMAGE)
#             response.raise_for_status() # Lève une erreur pour les codes HTTP 4xx/5xx

#             # Vérifier si le contenu semble être une image (heuristique)
#             if not response.headers.get('Content-Type', '').startswith('image'):
#                 raise ValueError(f"L'URL ne semble pas pointer vers une image valide (Content-Type: {response.headers.get('Content-Type')})")

#             img = Image.open(BytesIO(response.content)).convert("RGB")
#         except requests.exceptions.RequestException as e:
#             raise ValueError(f"Erreur lors du téléchargement de l'image depuis {URL_IMAGE}: {e}")
#         except Image.UnidentifiedImageError:
#             raise ValueError(f"Impossible d'identifier l'image depuis l'URL {URL_IMAGE}. Le contenu n'est peut-être pas une image valide.")
#         except Exception as e:
#             raise ValueError(f"Une erreur inattendue s'est produite lors du traitement de l'URL {URL_IMAGE}: {e}")
#     else:
#         # Si vous ne voulez pas prendre en charge les chemins locaux, vous pouvez supprimer ce bloc
#         # ou lever une erreur si l'URL n'est pas HTTP.
#         # Pour cet exemple, je pars du principe que vous n'utiliserez que des URLs HTTP.
#         raise ValueError("Seules les URLs HTTP sont acceptées pour le moment.")
    
#     # Utiliser le modèle déjà chargé
#     results = model(img)
    
#     # Il n'y a pas de boucle ici si vous n'avez qu'un seul résultat par image.
#     # YOLOv8 peut retourner plusieurs résultats pour différents modes (détection, segmentation, etc.)
#     # Si 'results' est une liste d'objets 'Results', prenez le premier pour l'affichage.
#     if results:
#         annotated_image = results[0].plot() # La méthode .plot() retourne une image NumPy array (BGR)
#     else:
#         # Gérer le cas où aucun résultat n'est retourné (pas de détection)
#         annotated_image = img # Retourner l'image originale si rien n'est détecté

#     # Convertir l'image NumPy array (OpenCV format BGR) en image PIL (RGB)
#     annotated_image_pil = Image.fromarray(annotated_image[..., ::-1]) # Convertir BGR en RGB
    
#     # Encodage de l'image en Base64
#     buffered = BytesIO()
#     annotated_image_pil.save(buffered, format="JPEG") # Vous pouvez choisir un autre format si besoin
#     img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
#     return img_str # Retourne la chaîne Base64

import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import base64

# --- Configuration ---
API_URL = "http://localhost:8086/detect_fire"

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