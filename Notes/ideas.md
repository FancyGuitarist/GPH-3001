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
		- ## IDÉE -> appliquer le single pitch a plusieurs cannaux simultanément?
			- désavantage -> si la note suivante est trop loins on tombera sur **plusieurs** partiel de la première note avant d'obtenir la note suivante.
			- on voudrait supprimer le F_0 du cannaux précedent pour trouver soit: un nouveau F_0, un silence
			-  ainsi de suite jusqu'a avoir un silence PARTOUT.

4. Notes rencontre
	- Avancement du projet [x]
	- Identifier les accords ( template matrix avec HMM) ou le multipitch ( avec un CRNN) ?  [O]
	- # Test unitaires, standardiser les test et la mesure de ceux-ci.
	- Améliorer le model monophonique (dynamiques, tests unitaire, benchmark ) ou se concentrer sur l'avancement du polyphonique?
	- Conserver la structure du logiciel en shell script || Tout implémenter en python? [O]
	- Correct d'avoir suivit (à quelques différences près) un github préexistant pour faire le monophonique?
	Points important rencontre
		- Test unitaire [x]
		- transformer le code selon le paradigme orienté objet [x]
		- la section de transcription en notation abjad devrait être wrapper en objet afin de simplifier sa modification ultérieur si besoin [x]
		- expliquer le code dans le readme [O] -> besoin modification?

# Notes rencontre 17 juin
- Changer le nom de la classe HMM ->. découvrir les notes (NoteProcessor)
- Test coverage (rouler toutes les lignes de code) module coverage de unittest -> mission : trouver le coverage des tests
- pas faire du AI, c'est poche (ou bien débuter par faire le monophonique avec une technique AI)
- Faire la reconnaissance d'accord ou lieu du multipitch.

# Idée méga révolutionnnaire Polyphonie
- suivre la maneouvre pour la reconnaissance d'accord
- utilisé un template de note, préalablement initialisé avec les fréquence identifié automatiquement puis stocker dans un fichier pickle.
- un array 1D représentera chaque Pitch dans le format
$$ {P}_{i} : [N\times 1]= \begin{bmatrix}
f_1 \\ f_2 \\ \vdots \\ f_N
\end{bmatrix} $$

le template sera donc un ensemble, où P est un pitch dans un ensemble de $M$ pitch, par exemple C4:

$$ T_{f}: [N \times M] = [ P_{1}, P_{2}, P_{3}, \cdots,P_{M}] $$

Le produit matriciel d'un échantillon
$E_{i} :  [N \times L ]$ où $N$ est le spectrogramme et $L$ la dimension temporel.
avec la matrice $T_{f}$ sera $T_{f}^T \times E_{i}: [M\times N] \times[N \times L] = [M \times L]$ soit une probabilité d'observer un Pitch dans l'ensemble $M$ dans l'intervalle $T$.
