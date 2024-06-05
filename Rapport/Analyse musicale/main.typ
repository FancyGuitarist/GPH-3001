#import "lib.typ": abstract, front_page
#set page(margin: 1.0in)
#set par(leading: 0.55em, justify: true)
#set text(font: "New Computer Modern",lang: "fr")
#show raw: set text(font: "New Computer Modern Mono")
#show par: set block(spacing: 0.55em)
#show heading: set block(above: 1.4em, below: 1em)
#set document(
  author: "Antoine Veillette",
  title: "Analyse musicale en python",
  date: auto)
  
#front_page(titre:[Transcription musicale automatique en python\ _Détail du projet et plan de travail_])
#set page(numbering: "1/1")
#set heading(numbering: "1.")
#counter(page).update(1)
#pagebreak()


//#show: it => columns(2,it) 
= Introduction
Un aspect important de la musique consiste à communiquer efficacement l'idée musicale du compositeur à l’interprète. De la partition à l'oreille, et inversement, de l'oreille à la partition. Le second étant beaucoup plus difficile que le premier malgré que des génies comme Mozart étaient autrefois capables de transcrire un concerto complet après une seule et unique écoute.@mozart

\ Ce projet tentera d'utiliser les techniques de transcription musicale automatique modernes pour recréer les prouesses exécutées par le jeune Mozart, 254 ans plus tôt.

= Description du projet et objectifs
#set enum(tight: false)
Ce projet vise à extraire et transcrire les informations musicales contenues dans un fichier audio d'une interprétation musicale, transformant ainsi un enregistrement sonore en partitions musicales précises et lisibles au format PDF. Les principaux objectifs sont les suivants :

    + Extraction des Informations Musicales : Identifier et extraire les informations rythmiques et fréquentielles présentes dans un fichier audio. Cela comprend la détection des hauteurs des notes, des durées, des attaques et des dynamiques de chaque note jouée. On inclut aussi les effets comme les _vibratos_ et les _bend_ à la guitare.

    + Transcription pour un Instrument Unique Monophonique : Développer et perfectionner un système de transcription automatique capable de traiter l'audio d'un seul instrument. Ce système doit être capable de produire une partition musicale fidèle à l'interprétation originale.

    + Transcription Polyphonique : Étendre le système pour qu'il puisse gérer des échantillons musicaux polyphoniques.
    + Transcription à Plusieurs Instruments Polyphonique : Cela implique la capacité de différencier et transcrire les performances de plusieurs instruments jouant simultanément, en produisant des partitions distinctes pour chaque instrument de l'ensemble.

    + Génération de Partitions au Format PDF : Convertir les transcriptions musicales obtenues en fichiers PDF.

    
Pour atteindre ces objectifs, le projet sera réalisé en plusieurs étapes clés, comprenant l'analyse du signal audio, la modélisation des séquences musicales, et l'utilisation de bibliothèques spécialisées pour la génération des partitions. Nous utiliserons des outils comme *Librosa* pour l'extraction des caractéristiques audios, des modèles de Markov à états cachés et/ou des réseaux neuronaux pour l'identification des accords polyphonique et la séparation des instruments, ainsi que *abjad* pour la génération de partition qui seront ensuite enregistrés en PDF.
#pagebreak()

= Cahier de charge (ou information similaire tel que les spécifications à atteindre)
#set table(fill: (x,y) => 
  if y == 0 {
    gray.lighten(40%)
  },
  stroke: none
)
#show table.cell.where(y: 0): strong


\
\
#align(center, text(16pt)[*Cahier des charges*])
#table(
    align: horizon, 
    inset: 7pt,
    columns: (1fr, 1fr, 0.2fr),
    table.vline(start: 0,end: 10,), 
    table.hline(start: 0, end: 3),
    table.header([*Critère à évaluer*], [*Condition générale à respecter*], [*Poids %*]),    table.vline(start: 0,end: 10,),
    table.hline(start: 0, end: 3), 
    [Reconnaissance des rythmes], [Le bon rythme au moins 80% du temps], [15], 
    table.hline(start: 0, end: 3), 
    [Reconnaissance des notes], [La bonne note au moins 80% du temps], [15], 
    table.hline(start: 0, end: 3), 
    [Identifier le bon tempo], [Identifie le bon tempo à 2% de précision], [10], 
    table.hline(start: 0, end: 3), 
    [Transcription des dynamiques], [Les variations de volume et d'intensité bien capturées], [10], 
    table.hline(start: 0, end: 3), 
    [Reconnaissance des articulations], [Capturer les accents, staccatos, et autres articulations au moins 70% du temps], [10], 
    table.hline(start: 0, end: 3), 
    [Précision de la transcription polyphonique et reconnaissance d'accord], [Identifier correctement les notes jouées simultanément dans un ensemble polyphonique#footnote[Plusieurs notes à la fois e.g. un accord.] au moins 70% du temps], [10],
    table.hline(start: 0, end: 3),
    [Séparation des instruments], [Séparer les instruments présent dans l'échantillon audio], [10],
    table.hline(start: 0, end: 3), 
    [Exportation au format PDF], [Exporter la partition transcrite en un format PDF lisible et correct], [10], 
    table.hline(start: 0, end: 3),
    [Interface utilisateur], [Facilité d'utilisation et clarté de l'interface utilisateur pour charger des fichiers audios et visualiser les résultats], [10],
    table.hline(start: 0, end: 3)
)
#pagebreak(weak: true)
= Plan de travail: 


== Listes des tâches
=== Recherche et Planification

    - *Étude du sujet* : Revue de la littérature actuelle en transcription musicale et recherche d'information musicale. Notamment @müller2016fundamentals et @Benetos2013AutomaticMT.
#let phase_1 = [Développement Monophonie]
#let phase_2 = [Développement polyphonie]
#let phase_3 = [Séparation des instruments]
#let phase_4 = [Tests et Validation]

=== #phase_1

    - *Implémentation de l'Extraction Audio* : Développement des modules d'extraction des caractéristiques audio.
    - *Transcription Monophonique* : Développement et test du module de transcription pour un seul instrument jouant une note à la fois.

=== #phase_2
    - *Transcription Polyphonique* : Extension du système pour gérer les ensembles polyphoniques à un instrument.

=== #phase_3
    - *Séparer les instruments* : Développement de la fonctionnalité pour séparer les différents instruments présents dans l'échantillon audio.
    - *Génération de Partitions* : Développement des fonctionnalités de génération de fichiers PDF.

=== #phase_4
    - *Tests Unitaires et Intégration* : Validation des modules individuellement et en intégration.
    - *Évaluation de la Précision* : Tests sur des ensembles de données réelles pour  évaluer la précision.


== échéancier
#table(align: center, columns: (6cm,10cm),
table.header([Date],[Action]),
[6-mai $->$ 30-mai],[#phase_1],
[1-juin $->$ 29-juin],[#phase_2],
[30-juin $->$ 20-juillet],[#phase_3],
[20-juillet $->$ 18-août],[#phase_4]
)

== jalons
#table(
    align: horizon, 
    columns: (0.2fr, 1fr, 0.3fr),
    table.hline(start: 0,end: 3),
    table.header(
        table.vline(), 
        [*Jalon*], 
        table.vline(), 
        [*Description*], 
        table.vline(), 
        [*Date Cible*]
    ),    
    table.vline(), 
    table.hline(start: 0, end: 3), 
    [Jalon 1], [Développement initial, tests de base et production d'une partition pour un instrument monophonique], [18 juin], 
    table.hline(start: 0, end: 3), 
    [Jalon 2], [Amélioration de la reconnaissance pour un instrument en polyphonie], [10 juillet], 
    table.hline(start: 0, end: 3), 
    [Jalon 3], [Amélioration pour plusieurs instruments en polyphonie], [7 août], 
    table.hline(start: 0, end: 3), 
    [Jalon 4], [Finalisation et tests de performance], [18 août], 
    table.hline(start: 0, end: 3)
)

#pagebreak()
#bibliography("biblio.bib", style: "american-institute-of-aeronautics-and-astronautics")
