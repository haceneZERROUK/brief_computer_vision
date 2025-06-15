# ml.py

import cv2
import numpy as np
from ultralytics import YOLO

# Charger le modèle une seule fois
model = YOLO("best.pt")

def detect_fire_image(image_array):
    # ... (cette fonction ne change pas)
    results = model(image_array)
    
    detections = []
    fire_detected = False
    smoke_detected = False
    
    for result in results:
        if result.boxes is not None:
            for box in result.boxes:
                confidence = float(box.conf[0])
                if confidence >= 0.5:
                    class_id = int(box.cls[0])
                    
                    if class_id == 0:
                        detection_type = "fire"
                        fire_detected = True
                    elif class_id == 1:
                        detection_type = "smoke"
                        smoke_detected = True
                    else:
                        continue
                    
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    detections.append({
                        "type": detection_type,
                        "confidence": confidence,
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2
                    })
    
    return {
        "detections": detections,
        "fire_detected": fire_detected,
        "smoke_detected": smoke_detected
    }

def detect_fire_webcam(camera_index=0):
    """
    Détecte le feu via webcam et retourne les résultats ET l'image.
    """
    cap = None
    try:
        # Essayer -1 en premier, puis 0, 1
        for index in [-1, 0, 1]:
            cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
            if cap.isOpened():
                break
        else:
            raise Exception("Aucune caméra accessible trouvée")

        ret, frame = cap.read()
        
        if not ret or frame is None:
            raise Exception("Impossible de capturer une frame")
        
        # Effectuer la détection
        results = detect_fire_image(frame)
        
        # <--- CHANGEMENT CLÉ : retourner les résultats ET la frame
        return results, frame
        
    except Exception as e:
        raise Exception(f"Erreur webcam: {str(e)}")
    finally:
        if cap is not None:
            cap.release()
