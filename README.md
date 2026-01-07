# ☁️ Générateur de Nuage de Collaborateurs

Application web développée en **Python + Streamlit** permettant de générer automatiquement
un nuage de photos de collaborateurs à partir d’un **masque graphique** (logo, forme, pictogramme).

L’objectif est d’obtenir un rendu visuel harmonieux, avec une occupation maximale du masque,
tout en contrôlant la taille des photos et le chevauchement.

---

## 🚀 Démonstration en ligne

👉 **Application accessible ici :**  
https://app-photo-cloud.streamlit.app

*(Application hébergée sur Streamlit Community Cloud)*

---

## 🧩 Fonctionnalités principales

- Import d’un **masque graphique** (PNG / JPG)
- Gestion automatique de la **transparence**
- Import multiple de **photos collaborateurs**
- Découpe centrée et normalisation des photos
- Placement intelligent dans le masque :
  - passes multi-échelles
  - contrôle du chevauchement
  - gestion des espaces
- **Estimation du taux de remplissage**
- Génération du nuage final
- Export du rendu :
  - **PNG**
  - **PDF**

---

## 🛠️ Stack technique

- **Python 3**
- **Streamlit**
- **Pillow (PIL)**
- **NumPy**
- **Pandas**

---

## 📁 Structure du projet

photo-cloud-streamlit/
│
├── app.py # Application Streamlit principale
├── requirements.txt # Dépendances Python
└── README.md # Documentation du projet



## ▶️ Lancer l’application en local

### 1️⃣ Installer les dépendances

bash
pip install -r requirements.txt

### 2️⃣ Lancer l’application
bash

streamlit run app.py

L’application sera accessible à l’adresse : https://app-photo-cloud.streamlit.app/

⚙️ Paramètres configurables

Depuis l’interface utilisateur :
- Taille des photos
- Espacement entre les photos
- Taux de chevauchement autorisé
- Résolution du masque
Ces paramètres permettent d’ajuster finement le rendu visuel final.

🎯 Cas d’usage
A venir

🔒 Sécurité & confidentialité

Aucune donnée n’est stockée
Les fichiers sont traités uniquement en mémoire
Application adaptée à un usage démo / interne
Non destinée à traiter des données sensibles sans sécurisation supplémentaire

🧪 Limites connues

Les performances dépendent de la taille et du nombre d’images
Recommandations :
- > 100 photos
- photos < 1 Mo

👤 Auteur

Développé par AlexCNZRZ
Projet réalisé dans un contexte de démonstration et de validation fonctionnelle.

📄 Licence

Projet interne / démonstration
Licence à définir selon l’usage
