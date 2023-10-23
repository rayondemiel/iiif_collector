[![License: MIT](https://img.shields.io/badge/License-MIT--Licence-lightgrey.svg)](https://mit-license.org/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-red.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![made-with-python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue)](https://www.python.org/)

# IIIF Collector

Ce CLI (*Command Line Interface*) permet d'extraire les données selon le framework IIIF à partir de plusieurs fonctions. Il permet notamment le téléchargement des images selon les standards de l'API Image selon les besoins et le serveur d'origine. Le script supporte aussi la manipulation images et des métadonnées d'un manifeste IIIF.

Le script fonctionne sur les environnements UNIX(Linux/Max) et POSIX(Windows).


#### Compatibilités API IIIF:
- API Image: 2.0 et 3.0
- API Presentation: **Uniquement 2.0 (3.0 en cours)**
- OCR extraction: *En cours*

#### Fonctionnalités:
- iiif_singular: Fonction pour télécharger une image ou un manifeste IIIF.
- iiif_list: Fonction pour exploiter une liste (csv ou txt) d'images ou de manifestes IIIF. Le traitement est parallélisé et effectué à partir de requêtes asynchrones.
- get_list_image: Fonction pour obtenir la liste des liens urls pour les images présentes au sein d'un manifeste.

---

## :gear: Installation

*Nota : commandes à exécuter dans le terminal (Linux ou macOS).*

  * Cloner le dossier : ```git clone https://github.com/rayondemiel/iiif_collector.git``` ou télécharger le [zip](https://github.com/rayondemiel/iiif_collector/archive/refs/heads/main.zip) et décompressez-le.
  
  * Installer l'environnement virtuel :
  
    * Vérifier que la version de Python est bien 3.x et dans l'idéal la version 3.10 : ```python --version```;
    
    * Si vous ne possédez pas python, veuillez exécuter cette commande :
      - Linux/Debian ``` sudo apt-get install python3 python3-pip python3-virtualenv ```;
      - Mac(brew) ```brew install python```
    
    * Aller dans le dossier : ```cd iiif_collector```;
    
    * Installer l'environnement : ```python3 -m venv [nom de l'environnement]```.
  
  * Installer les packages et librairies :
  
    * Activer l'environnement : ```source [nom de l'environnement]/bin/activate```;
    
    * Installer les différentes librairies ```pip install -r requirements.txt```;
    
    * Vérifier que tout est installé : ```pip freeze``` ;
    
    * Sortir de l'environnement : ```deactivate``` .
   
*Nota : commandes à exécuter dans le terminal (Windows).*

  * Cloner le dossier : ```git clone https://github.com/rayondemiel/iiif_collector.git``` ou télécharger le [zip](https://github.com/rayondemiel/iiif_collector/archive/refs/heads/main.zip) et décompressez-le.
  
  * Installer l'environnement virtuel :
  
    * Vérifier que la version de Python est bien 3.x et dans l'idéal la version 3.10 : ```python --version```;
    
    * Si vous ne possédez pas python, veuillez installer via le site officiel: https://www.python.org/
    
    * Aller dans le dossier : clique droit dans le dossier puis `Ouvrir dans le terminal`;
    
    * Installer l'environnement : ```python3 -m venv [nom de l'environnement]```.
  
  * Installer les packages et librairies :
  
    * Activer l'environnement : ``` .\[nom de l'environnement]\Scripts\activate```;
    
    * Installer les différentes librairies ```pip install -r requirements.txt```;
    
    * Vérifier que tout est installé : ```pip freeze``` ;
    
    * Sortir de l'environnement : ```deactivate``` .
---

## :rocket: Lancement
  
  * Activer l'environnement : ```source [nom de l'environnement]/bin/activate``` ;
    
  * Lancement : ```python3 run.py [fonction] [Image URL | Manifeste URL | CSV or TXT] --kwargs```

### Examples

##### iiif_singular

  * Téléchargement d'une image sur une zone particulière en qualité bitonal:
    
  ```python3 run.py iiif_singular -i https://examples.org/iiif/3/full/max/0/default.jpg -R 125,15,120,140 -q bitonal```

  * Téléchargement d'un nombre défini d'images aléatoires au format TIFF dans un dossier spécifique:

  ```python3 run.py iiif_singular https://examples.org/iiif/manuscrit_fake/manifest.json -n --random -f tif -d PATH/TO/DIR/```

##### iiif_singular
  
  * Téléchargement de 100 manifestes IIIF au sein d'un fichier texte avec pour format png et une nouvelle dimension
  
  ```python3 run.py iiif_list /PATH/TO/manifest.txt -f png -w 150,```

##### get_list_image

  * Obtenir une liste des images présentes au sein d'un manifeste IIIF.
  
  ```python3 run.py get_list_image https://examples.org/iiif/manuscrit_fake/manifest.json```

  
