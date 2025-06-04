import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO

# Charger le modèle YOLO
yolo = YOLO('best_2.pt')
# Fonction pour obtenir les couleurs des classes
def getColours(cls_num):
    base_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    color_index = cls_num % len(base_colors)
    increments = [(1, -2, 1), (-2, 1, -1), (1, -1, 2)]
    color = [base_colors[color_index][i] + increments[color_index][i] * 
    (cls_num // len(base_colors)) % 256 for i in range(3)]
    return tuple(color)

# Fonction de flux vidéo avec détection YOLO
def video_stream():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        st.error("Impossible d'ouvrir la caméra")
        return
    
    stframe = st.empty()

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        results = yolo.track(frame, stream=True)

        for result in results:
            classes_names = result.names

            # Parcours des boîtes de détection
            for box in result.boxes:
                if box.conf[0] > 0.4:
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    cls = int(box.cls[0])
                    class_name = classes_names[cls]
                    color = getColours(cls)

                    # Dessiner le rectangle autour de l'objet
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                    # Afficher le nom de la classe et la confiance
                    cv2.putText(frame, f'{class_name} {box.conf[0]:.2f}', (x1, y1),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        # Convertir l'image en format RGB (OpenCV utilise BGR)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Afficher l'image dans Streamlit
        stframe.image(frame_rgb, channels="RGB", use_column_width=True)

    # Libérer la caméra et fermer toutes les fenêtres
    cap.release()

# Titre de la page Streamlit
st.title("Page d'Accueil - Détection d'objets avec YOLO")

# Ajouter un bouton pour démarrer la webcam
if st.button("Démarrer la webcam avec YOLO"):
    video_stream()
