1. Pour un instrument (guitare)
   - Identifier les notes d'un présent dans un échantillon audio
   - Identifier les composantes rythmiques dans un échantillon audio
2. Découplage des instruments

   - [PLCA](http://web.mit.edu/~punk/Public/AudioExtraction/PLCApage.html)/[LDA](https://en.wikipedia.org/wiki/Linear_discriminant_analysis)
   - voir [Automatic Music Transcription/ Challenges and Future Directions.pdf] page 6

3. Polyphonie
	- gérer les Unissons (ex:A4 & A5 simultanément)
	- gérer les accords (identifier l'accord jouer, identifier les transpositions)
	- ou bien tout simplement identifier _toutes les notes jouer par frame_.
		- appliquer le single pitch a plusieurs cannaux simultanément?
			- on voudrait supprimer le F_0 du cannaux précedent pour trouver soit: un nouveau F_0, un silence
			-  ainsi de suite jusqu'a avoir un silence PARTOUT.
