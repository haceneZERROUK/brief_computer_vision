import streamlit as st
from PIL import Image

# Logo fictif ou image de feu
st.set_page_config(page_title="Ignis - IA pour la détection d'incendies", page_icon="🔥", layout="wide")

# En-tête
st.markdown("# 🔥 Bienvenue chez Ignis")
st.markdown("### L'intelligence artificielle au service de la détection précoce d'incendies")

# Image illustrative
image = Image.open("image.png")  # Remplace par une image locale ou supprime cette ligne si inutile
st.image(image, use_container_width=True, caption="Détection de feu via caméras et satellites")

# Présentation
st.markdown("""
Ignis est une entreprise innovante spécialisée dans le **développement de solutions d’intelligence artificielle** pour la détection d’incendies.  
Nos algorithmes sont conçus pour être embarqués dans **des caméras de surveillance**, **des drones**, et **des satellites d'observation** afin d'assurer une détection **rapide**, **précise**, et **automatisée** des départs de feu.

### 🌍 Nos technologies :
- Détection en temps réel via flux vidéo
- Analyse d'images satellite pour surveillance à grande échelle
- Systèmes embarqués compatibles IoT
- Alertes intelligentes et intégration aux systèmes de sécurité existants

### 🚀 Nos objectifs :
- Réduire les délais d’intervention
- Prévenir la propagation des incendies
- Protéger les vies, les forêts et les infrastructures

---

### 📩 Contactez-nous :
Vous souhaitez en savoir plus ou intégrer nos solutions à vos dispositifs ?  
📧 **contact@ignis-ai.com**  
🌐 [www.ignis-ai.com](http://www.ignis-ai.com) *(fictif)*

""")

# Footer
st.markdown("---")
st.markdown("© 2025 Ignis. Tous droits réservés.")
