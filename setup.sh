#!/bin/bash

verify_installation () {
# Vérifier si Brew est installé
if ! command -v brew &> /dev/null
then
    echo "Homebrew n'est pas installé. Veuillez installer Homebrew d'ab
ord : https://brew.sh/"
    exit 1
fi
# Vérifier si ffmpeg est installé
if brew list | grep  "^ffmpeg$" &> /dev/null ; then
    echo "ffmpeg est déjà installé."
else
    echo "ffmpeg n'est pas installé. Installation en cours..."
    brew install ffmpeg
    if [ $? -eq 0 ]; then
        echo "ffmpeg a été installé avec succès."
    else
        echo "L'installation de ffmpeg a échoué."
    fi
fi
# Vérifier si LilyPond est installé
if brew list | grep  "^lilypond$" &> /dev/null ; then
    echo "LilyPond est déjà installé."
else
    echo "LilyPond n'est pas installé. Installation en cours..."
    brew install lilypond
    if [ $? -eq 0 ]; then
        echo "LilyPond a été installé avec succès."
    else
        echo "L'installation de LilyPond a échoué."
    fi
fi


# Vérifier si Python 3.11 est installé
if ! command -v python3.11 &> /dev/null;
then
    echo "Python 3.11 n'est pas installé. Veuillez installer Python 3.11 avant de continuer."
fi
# look if a venv is already present in local directory
if [ -d "./venv" ]; then
    echo "Un environnement virtuel est déjà présent dans le répertoire local."
    echo "Voulez-vous le supprimer et en créer un nouveau ? (y/n)"
    read response
    if [ "$response" = "y" ]; then
        rm -rf ./venv
    else
        echo "Vous avez choisit de le conserver, le script d'installation a été annulé."
        echo "Vous pouvez exécuter start.sh pour lancer le programme."
        return 1
    fi
fi
}


function complete_setup {
python3.11 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
}
verify_installation
if [ $? -eq 1 ]; then
    echo "verify_installation à échoué"
    exit 1
fi

complete_setup
if [ $? -eq 0 ]; then
    echo "Prérequis complété, vous pouvez désormais executer python mir --help"
else
    "setup.sh à échoué"
fi
