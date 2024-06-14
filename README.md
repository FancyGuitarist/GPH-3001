# Instructions
`chmod +x setup.sh` accorde la permission d'execution de setup.sh
`./setup.sh` initialise l'environnement virtuel et installe les librairies requises
`./start.sh song\&samples/gC.wav  `

# Explication de la procédure de la reconnaissance monophonique
1. Chargement de l'audio d'un fichier `.wav` et séparation de la partie percussive et harmonique

2. estimation des F0 (fréquences fondamentales) de la partie harmonique du signal avec [PYIN](Mauch, Matthias, and Simon Dixon. “pYIN: A fundamental frequency estimator using probabilistic threshold distributions.”), ces fréquences fondamentales sont par la suite ajustées à la note la plus proche et convertie en format numérique (midi).

2.1 PYIN transforme l'audio par STFT (short time fourier transform) YIN avec un threshold variable pour trouver la fréquence fondamentale la plus probable pour chaque fenêtre de l'audio.

![PYIN Schema içi](https://github.com/craqu/GPH-3001/blob/main/Notes/images/pyin.png?raw=true)

  - on utilise *conjointement* les *F0* avec la fonction *"librosa.onset.onset_detect"* pour initialiser le *vecteur d'observation* à priori qui consiste à en un vecteur normalisé ou les positions paires sont l'état sustain (une note continue de sonner), les composantes impaires sont l'état onset (une note est frappée) et la position 0 représente le silence.

  `[silence, onset E2, sustain E2, onset F2, sustain F2, ... onset E6, sustain E6]`

  - par exemple: la note E2 est représentée par l’onset à la position 1 et le sustain à la position 2. On utilise E2 comme note minimal et E6 comme note maximal puisqu'ils correspondent aux notes extrêmes d'une guitare standard.

2.2 création de la *matrice de transition* qui est une matrice carrée de taille 2n+1 ou n est le nombre de notes entre E2 et E6. La matrice de transition est une matrice de taille 2n+1 x 2n+1 ou chaque élément est la *probabilité de passer d'un état à un autre*. On initialise la matrice de transition avec des valeurs qui

*accentue la probabilité* de:
  - Rester sur une note.
  - Passer de l’onset d'une note au sustain de cette même note.
  - Passer d'un sustain à un silence ou un autre onset, etc.

Les autres transitions sont initialisées avec des valeurs plus faibles s’assurant de respecter la condition qu'*une rangée est normalisée* (la probabilité de passer d'un état à un état quelconque est 1).

3.  Utilisation de l'*algorithme de Viterbi* pour déterminer la séquence d'état la plus probable avec une matrice de transition et la matrice d'observation à priori. (Trouve la séquence d'état la plus probable dans le *HMM (Hiden Markov Model) qui correspond à la combinaison des probabilités à priori / matrice de transition*)

4.  Par la suite, on 'dérive' la séquence d'index qui identifie les changements d'état sachant la durée d'une fenêtre pour identifier les durées des notes et silence. `pitche_to_simple_notation()`


5. On transforme la notation simplifiée qui est un tuple de 3 éléments (temps où la note est jouée : float, note : str, temps que la note dure : float) en notation pouvant être utilisés par la librairie abjad qui assemblera le fichier `[nom du fichier audio].ly`

6. qui pourra être compilé par lilypond en format PDF.
