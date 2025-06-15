# detect_image.py - Endpoint pour la détection de feu via URL d'image
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import numpy as np
from PIL import Image
import io
import cv2
import base64
from api_fastapi.ml import detect_fire_image

router = APIRouter()

class ImageUrlRequest(BaseModel):
    image_url: str

@router.post("/detect_fire_url")  
async def detect_fire_url(request: ImageUrlRequest):
    """
    Détecte le feu et la fumée dans une image fournie par URL.
    """
    try:
        # Télécharger l'image depuis l'URL
        response = requests.get(request.image_url, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Impossible de télécharger l'image depuis l'URL")
        
        # Vérifier le type de contenu
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="L'URL ne pointe pas vers une image valide")
        
        # Convertir en image PIL puis en array numpy
        image = Image.open(io.BytesIO(response.content))
        image_array = np.array(image)
        
        # Convertir RGB en BGR pour OpenCV
        if len(image_array.shape) == 3:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        
        # Garder une copie pour dessiner les détections
        image_with_detections = image_array.copy()
        
        # Utiliser la fonction du ml.py
        results = detect_fire_image(image_array)
        
        # Dessiner les boîtes de détection sur l'image
        for detection in results["detections"]:
            x1, y1, x2, y2 = int(detection["x1"]), int(detection["y1"]), int(detection["x2"]), int(detection["y2"])
            confidence = detection["confidence"]
            detection_type = detection["type"]
            
            # Couleur selon le type
            color = (0, 0, 255) if detection_type == "fire" else (0, 255, 255)  # Rouge pour feu, jaune pour fumée
            
            # Dessiner la boîte
            cv2.rectangle(image_with_detections, (x1, y1), (x2, y2), color, 2)
            
            # Ajouter le texte
            label = f"{detection_type}: {confidence:.2f}"
            cv2.putText(image_with_detections, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Convertir l'image en base64 pour l'envoyer à Streamlit
        _, buffer = cv2.imencode('.jpg', image_with_detections)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Message de réponse
        fire_detected = results["fire_detected"]
        smoke_detected = results["smoke_detected"]
        
        if fire_detected and smoke_detected:
            message = "Feu et fumée détectés dans l'image"
        elif fire_detected:
            message = "Feu détecté dans l'image"
        elif smoke_detected:
            message = "Fumée détectée dans l'image"
        else:
            message = "Aucun feu ou fumée détecté"
        
        return {
            "success": True,
            "message": message,
            "detections": results["detections"],
            "fire_detected": fire_detected,
            "smoke_detected": smoke_detected,
            "encoded_image": image_base64  # ← Change "image_encoded" en "encoded_image"
        }
            
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors du téléchargement: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
