import abjad
import numpy as np
class Partition:
    def __init__(self, simple_notation, tempo):
        self.tempo = tempo
        self.simple_notation = simple_notation
        self.treble_notes, self.bass_notes = self.convert_notes_to_abjad(simple_notation)

    def _get_closest_duration(self, duration):
        """
        Get closest musical duration to the given time duration using tempo estimation
        assuming 4/4 time signature
        Parameters
        ----------
        duration : float
        tempo : float

        Returns
        -------
        best_fit : str -> 1/4, 1/8, 1/16, 1/32 ... etc
        """
        quarter_note = 60 / self.tempo
        half_note = quarter_note * 2
        whole_note = quarter_note * 4
        eighth_note = quarter_note / 2
        sixteenth_note = quarter_note / 4
        thirty_second_note = quarter_note / 8

        dotted_whole_note = whole_note + half_note
        dotted_half_note = quarter_note + half_note
        dotted_quarter_note = quarter_note + eighth_note
        dotted_eighth_note = eighth_note + sixteenth_note
        dotted_sixteenth_note = sixteenth_note + thirty_second_note

        full_note = [("1/1" , whole_note), ("1/2" , half_note), ("1/4" , quarter_note), ("1/8" , eighth_note),
            ( "1/16" , sixteenth_note), ("1/32" , thirty_second_note)]
        dotted_note = [ ("3/2"  , dotted_whole_note) , ("3/4" , dotted_half_note) ,
            ("3/8" , dotted_quarter_note), ("3/16" , dotted_eighth_note) , ("3/32" , dotted_sixteenth_note)]
        total_note = full_note + dotted_note

        value_of_best_fit = lambda duration:\
            min(total_note, key = lambda x: np.abs(duration - x[1]))
        best_fit = value_of_best_fit(duration)[0]

        return best_fit
    def convert_pianoroll_to_simple_notation(self, pianoroll):
        for note in pianoroll:
            if note[0] == 'N':
                note[0] = 'R'


    def convert_notes_to_abjad(self, simple_notation):
        """Convertit les tuples de notes en objets Abjad."""
        treble_notes = []
        bass_notes = []
        for note_name, start_time, duration in simple_notation:
            # Convert the duration from float to a rational number
            duration = self._get_closest_duration(duration)
            if duration == "1/1":
                duration_rational = abjad.Duration(1)
            else:
                duration_rational = abjad.Duration(duration)
            if note_name == 'N':  # Handle rest
                abjad_note = abjad.Rest(duration_rational)
                treble_notes.append(abjad_note)
                bass_notes.append(abjad.Skip(duration_rational))
            else:
                # Convert note name to abjad format
                note : str = note_name[:-1].lower()
                if '#' in note or "♯" in note:
                    note = note.replace('#', 's')
                    note = note.replace('♯', 's')
                octave = int(note_name[-1])
                octave_adjustment = octave - 3
                if octave_adjustment >= 1:
                    octave_str = '\'' * octave_adjustment
                    treble_notes.append(abjad.Note(f"{note}{octave_str}", duration_rational))
                    bass_notes.append(abjad.Skip(duration_rational))

                else:
                    octave_str = ',' * abs(octave_adjustment)
                    bass_notes.append(abjad.Note(f"{note}{octave_str}", duration_rational))
                    treble_notes.append(abjad.Skip(duration_rational))

        return treble_notes, bass_notes
    @property
    def score(self):
        treble_staff = abjad.Staff(self.treble_notes,lilypond_type='Staff',name='treble')
        bass_staff = abjad.Staff(self.bass_notes,lilypond_type='Staff',name='bass')

        if treble_staff:
            abjad.attach(abjad.Clef('treble'), treble_staff[0])
        if bass_staff:
            abjad.attach(abjad.Clef('bass'), bass_staff[0])

        mark = abjad.MetronomeMark(abjad.Duration(1, 4), int(self.tempo))
        abjad.attach(mark, treble_staff[0])

        score = abjad.Score([treble_staff,bass_staff])
        return score
    def save_score(self, output_path):
        """Exporte la partition en format LilyPond."""
        abjad.persist.as_ly(self.score, output_path)



if __name__ == "__main__":
    pass
