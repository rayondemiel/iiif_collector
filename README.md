[![License: MIT](https://img.shields.io/badge/License-MIT--Licence-lightgrey.svg)](https://mit-license.org/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-red.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![made-with-python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue)](https://www.python.org/)

# IIIF Collector

Ce CLI (*Command Line Interface*) permet d'extraire les données selon le framework IIIF à partir de plusieurs fonctions. Il permet notamment le téléchargement des images selon les standards de l'API Image selon les besoins et le serveur d'origine. Le script supporte aussi la manipulation images et des métadonnées d'un manifeste IIIF.

Le script fonctionne sur les environnements Linux/Mac et en cours de test pour Windows.


#### Compatibilités API IIIF:
- API Image: 2.0 et 3.0
- API Presentation: **Uniquement 2.0 (3.0 en cours)**
- OCR extraction: *En cours*

#### Fonctionnalités:
- iiif_singular: Fonction pour télécharger une image ou un manifeste IIIF.
- iiif_list: Fonction pour exploiter une liste (csv ou txt) d'images ou de manifestes IIIF.
- get_list_image: Fonction pour obtenir la liste des liens urls pour les images présentes au sein d'un manifeste.

---

## :gear: Installation

*Nota : commandes à exécuter dans le terminal (Linux ou macOS).*

  * Cloner le dossier : ```git clone https://github.com/rayondemiel/iiif_collector.git``` ou télécharger le [zip](https://github.com/rayondemiel/iiif_collector/archive/refs/heads/main.zip) et décompresser le
  
  * Installer l'environnement virtuel :
  
    * Vérifier que la version de Python est bien 3.x et dans l'idéal 3.10 : ```python --version```;
    
    * Si vous ne possédez pas python, veuillez exécuter cette commande :
      - Linux/Debian ``` sudo apt-get install python3 python3-pip python3-virtualenv ```;
      - Mac(brew) ```brew install python```
    
    * Aller dans le dossier : ```cd iiif_collector```;
    
    * Installer l'environnement : ```python3 -m venv [nom de l'environnement]```.
  
  * Installer les packages et librairies :
  
    * Activer l'environnement : ```source [nom de l'environnement]/bin/activate```;
    
    * Installer les différentes librairies ```pip install -r requirements.txt```;
    
    * Installer les dépendances pour le NLP ```python -m nltk.downloader stopwords```;
    
    * Vérifier que tout est installé : ```pip freeze``` ;
    
    * Sortir de l'environnement : ```deactivate``` .
