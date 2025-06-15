from fastapi import FastAPI
from fastapi.endpoints.detect_image import router as image_router
from fastapi.endpoints.detect_webcam import router as webcam_router

"""
Point d'entrée principal de l'API de détection de feu et fumée avec YOLO11.

Ce module initialise l'application FastAPI et configure les routes
pour la détection de feu et fumée sur images et flux webcam.

Application Properties:
    title: "API de détection de feu et fumée"
    description: "API utilisant YOLO11 pour détecter le feu et la fumée"
    version: "1.0.0"

Routes incluses:
    - /detect_image: Détection sur images uploadées
    - /detect_webcam: Détection via flux webcam

Note:
    L'API utilise FastAPI pour:
    - Documentation automatique (Swagger UI sur /docs)
    - Validation des données avec Pydantic
    - Gestion des routes avec APIRouter
    - Support asynchrone natif
    - Intégration avec YOLO11 pour la détection en temps réel
"""

# Créer l'application FastAPI
app = FastAPI(
    title="API de détection de feu et fumée", 
    description="API utilisant YOLO11 pour détecter le feu et la fumée en temps réel", 
    version="1.0.0"
)

# Inclure les routes de détection
app.include_router(image_router)
app.include_router(webcam_router)

# Endpoint de santé simple
@app.get("/")
async def root():
    """
    Endpoint racine pour vérifier que l'API fonctionne.
    """
    return {
        "message": "API de détection de feu et fumée avec YOLO11",
        "status": "active",
        "endpoints": [
            "/detect_fire_url - Détection sur images",  
            "/detect_fire_webcam - Détection via webcam",  
            "/docs - Documentation Swagger"
        ]
    }
