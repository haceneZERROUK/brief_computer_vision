# detect_webcam.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import cv2
import base64
from fastapi.ml import detect_fire_webcam

router = APIRouter()

class WebcamRequest(BaseModel):
    camera_index: int = 0

@router.post("/detect_fire_webcam")  
async def detect_fire_webcam_endpoint(params: WebcamRequest = WebcamRequest()):
    """
    Détecte le feu, dessine sur l'image et la retourne.
    """
    try:
        # <--- CHANGEMENT CLÉ : Récupérer les résultats ET la frame
        results, frame = detect_fire_webcam(params.camera_index)
        
        # Dessiner les boîtes de détection sur l'image
        for detection in results["detections"]:
            x1, y1, x2, y2 = int(detection["x1"]), int(detection["y1"]), int(detection["x2"]), int(detection["y2"])
            confidence = detection["confidence"]
            detection_type = detection["type"]
            color = (0, 0, 255) if detection_type == "fire" else (0, 255, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = f"{detection_type}: {confidence:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Encoder l'image modifiée en base64
        _, buffer = cv2.imencode('.jpg', frame)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Message de réponse
        fire_detected = results["fire_detected"]
        smoke_detected = results["smoke_detected"]
        
        if fire_detected and smoke_detected:
            message = "Feu et fumée détectés via webcam"
        elif fire_detected:
            message = "Feu détecté via webcam"
        elif smoke_detected:
            message = "Fumée détectée via webcam"
        else:
            message = "Aucun feu ou fumée détecté"
        
        return {
            "success": True,
            "message": message,
            "detections": results["detections"],
            "fire_detected": fire_detected,
            "smoke_detected": smoke_detected,
            "timestamp": datetime.now(),
            "image_encoded": image_base64  # <--- L'image encodée est maintenant incluse
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
