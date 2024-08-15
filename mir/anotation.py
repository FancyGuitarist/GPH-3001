
from functools import cached_property, partial

from numpy.core.multiarray import ndarray
import abjad
import numpy as np
# import pdb;
#pdb.set_trace()




def is_almost_equal(start_of_second_note: float, end_of_first_note : float, epsilon: float):
    return  (start_of_second_note - end_of_first_note < epsilon) & (start_of_second_note - end_of_first_note > 0)

def full_notes(tempo):
    quarter_note = 60 / tempo
    half_note = quarter_note * 2
    whole_note = quarter_note * 4
    eighth_note = quarter_note / 2
    sixteenth_note = quarter_note / 4
    thirty_second_note = quarter_note / 8
    sixty_fourth_note = quarter_note / 16
    one_hundred_twenty_eighth_note = quarter_note / 32

    dotted_whole_note = whole_note + half_note
    dotted_half_note = quarter_note + half_note
    dotted_quarter_note = quarter_note + eighth_note
    dotted_eighth_note = eighth_note + sixteenth_note
    dotted_sixteenth_note = sixteenth_note + thirty_second_note

    full_note = [("1" , whole_note), ("1/2" , half_note), ("1/4" , quarter_note), ("1/8" , eighth_note),
        ( "1/16" , sixteenth_note), ("1/32" , thirty_second_note),("1/64",sixty_fourth_note),("1/128",one_hundred_twenty_eighth_note)]
    dotted_note = [ ("3/2"  , dotted_whole_note) , ("3/4" , dotted_half_note) ,
        ("3/8" , dotted_quarter_note), ("3/16" , dotted_eighth_note) , ("3/32" , dotted_sixteenth_note)]
    total_note = full_note + dotted_note
    return total_note


class Partition:
    def __init__(self,  tempo):
        self.tempo = tempo
        self.duration_mapping_dict = dict(full_notes(self.tempo))

    @cached_property
    def valid_note_name(self):
        valid_note_name = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        valid_note_name += [note.lower() for note in valid_note_name]
        valid_note_name += [note + '#' for note in valid_note_name] + [note + '♯' for note in valid_note_name]
        return valid_note_name
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
        total_note = full_notes(self.tempo)
        value_of_best_fit = lambda duration:\
            min(total_note, key = lambda x: np.abs(duration - x[1]))
        best_fit = value_of_best_fit(duration)[0]
        return best_fit


    def _get_melody_chords_estimate(self, simple_notation):
        """
        Convert note/chord name to abjad str format
        Parameters
        ----------
        simple_notation : list[tuples(note: list[str], start_time: float, duration: float)]
            list of tuples containing note/chord start time and duration
        Returns
        -------
        melody + chord_estimate : list[tuples(note | chord: str of abjad format, start_time: float, duration: float))]
            list of grouped simple notation tuples present in the chords in abjad notation string format.
        """
        note_name_to_abjad_format = partial(self.note_name_to_abjad_format, join=True)
        chord_estimate : list[tuple[str,float,float]]  = []
        melody : list[tuple[str,float,float]]  = []
        dictionnary_of_time_repr = self.duration_mapping_dict
        res = []
        for note_or_chord, start, duration in simple_notation:
            if len(note_or_chord) > 1: # if its a chord
                iterable = ' '.join(list(map(note_name_to_abjad_format, note_or_chord )))
                # print("iterable : ", iterable)
                simple_chord_notation = (f"<{iterable}>", start, duration)
            else: # single note
                simple_chord_notation = (note_name_to_abjad_format(*note_or_chord), start, duration)
            res.append(simple_chord_notation)
        return res

    def note_name_to_abjad_format(self, note_name, join=False) -> str | tuple[str, str]:
        """Converts note name to abjad format.
        return : tuple = (note: str, octave_str: str)

        """
        if note_name == 'N':
            return note_name

        note : str = note_name[:-1].lower()
        if note not in self.valid_note_name:
            raise ValueError(f"Invalid note name {note_name}")
        if '#' in note or "♯" in note:
            note = note.replace('#', 's')
            note = note.replace('♯', 's')
        # breakpoint()
        octave = int(note_name[-1])
        octave_adjustment = octave - 3
        if octave_adjustment >= 1:
            octave_str = '\'' * octave_adjustment
        else:
            octave_str = ',' * abs(octave_adjustment)
        if join:
            return note + octave_str

        return note, octave_str
    def _get_duration_rationnal(self, duration: float):
        """
        input : duration: float

        return : abjad.Duration object
        """
        closest_dur = self._get_closest_duration(duration)

        return abjad.Duration(closest_dur)

    def sequential_correction(self, simp_notation_vec, i, smallest_duration=None):
        """
        Correct the sequential notes or chords in the simple notation
        by adding a rest in between if there is a gap.
        """
        if smallest_duration is None:
           epsilon_as_float = 0.0001
        else:
            # smallest duration needs to be a str in the form of "1/32"
            epsilon_as_float = self.duration_mapping_dict[smallest_duration]

        if (len(simp_notation_vec) <= i + 1): # early return if last note
            return [simp_notation_vec[i]]

        start_of_second_note = simp_notation_vec[i+1][1] # start of the second note
        end_of_first_note = simp_notation_vec[i][2] + simp_notation_vec[i][1] # end of the first note

        if not is_almost_equal(start_of_second_note, end_of_first_note, epsilon=epsilon_as_float):
            if start_of_second_note-end_of_first_note > 0:
                return [simp_notation_vec[i] , ("N",
                    end_of_first_note,
                    start_of_second_note-end_of_first_note)]
            else:
                return [simp_notation_vec[i]]
        else:
            return [simp_notation_vec[i]]

    def is_bass_treble(self, simple_notation_unit):
        """
        Determine if the note or chord is in the bass or treble staff.

        Parameters:
            simple_notation_unit : tuple(note | chord, start_time, duration)

        return : str = "bass" | "treble"
        """
        #if simple_notation_unit[0].__contains__('<'):
            # is already in abjad format
        if "'" in simple_notation_unit[0]:
            return "treble"
        else:
            return "bass"
    def separate_treble_bass(self, simple_notation_vec: list[tuple[str, float, float]]):
        """
        Seperate the treble and bass staff from the simple notation unit.

        Parameters:
            simple_notation_unit : tuple(note | chord, start_time, duration)
        """
        treble, bass = [], []
        # seperate the treble and bass
        for i in range(len(simple_notation_vec)):
            simple_notation_unit = simple_notation_vec[i]
            maybe_bass_or_treb = self.is_bass_treble(simple_notation_unit)
            if maybe_bass_or_treb == "treble":
                treble.append(simple_notation_unit)
            elif maybe_bass_or_treb == "bass" :
                bass.append(simple_notation_unit)
            else:
                raise ValueError("The note or chord is neither in the bass nor treble staff.")
        return treble, bass

    def extract_bass_treble_staff(self, simple_notation_vec: list[tuple[str, float, float]]) -> tuple[list[tuple[str, float, float]], list[tuple[str, float, float]]]:

        """
        Extract the bass and treble staff from the simple notation.
        Will also apply sequential correction in the simple notation so it fits in the score properly.
        (see sequential_correction() method for more details.)

        Parameters:
            simple_notation : list[tuple()]
                list of tuples containing (note | chord, start_time, duration)

        Returns:
            treble_staff : list[tuple()],
            bass_staff : list[tuple()]

        """
        treb, bass = self.separate_treble_bass(simple_notation_vec)
        new_treb, new_bass = [], []
        if treb:
            for i in range(len(treb)):
                temp = self.sequential_correction(treb, i)
                new_treb += temp
        if bass:
            for i in range(len(bass)):
                b_temp = self.sequential_correction(bass, i)
                new_bass += b_temp
        # adjust the rest at the start of the notation
        if treb:
            if new_treb[0][1] != 0:
                new_treb = [("N", 0., new_treb[0][1])] + new_treb
        if bass:
            if new_bass[0][1] != 0:
                new_bass = [("N", 0., new_bass[0][1])] + new_bass
        # print("new_treb, new_bass: line 274", new_treb, new_bass)
        return new_treb, new_bass

    def convert_notes_to_abjad(self, simple_notation, polyphonic=False):
        """
        Convert tuples of note to abjad objects usable in a score.

        Parameters:
            simple_notation : list[tuple()]
                list of tuples containing note in abjad str format, start time and duration
            polyphonic : bool
                if True, the simple notation is polyphonic, else monophonic
        Returns:
            treble_notes : list[abjad.Note]
                list of treble notes
            bass_notes : list[abjad.Note]
                list of bass notes
        """

        def to_abjad_staff(this_staff):
            """
            create a list of abjad notes or rest or chord from the input list of ("abjad string format", start_time, duration)

            Parameters:
                this_staff : list[tuple()]
                    list of tuples containing note, start time and duration
            Returns:
                res : list[abjad.Note | abjad.Chord | abjad.Rest]
            """
            res = []
            for note_name, start_time, duration in this_staff:
                # Convert the duration from float to a rational number
                duration_rational = self._get_duration_rationnal(duration)
                # print("note name",note_name)
                if note_name == 'N':
                    res.append(abjad.Rest(duration_rational))
                elif '<' in note_name:
                    chord = abjad.Chord(note_name)
                    chord.written_duration = duration_rational
                    res.append(chord)
                else:
                    res.append(abjad.Note(note_name, duration_rational))
            return res





        treble_notes = []
        bass_notes = []
        if not polyphonic:
            for note_name, start_time, duration in simple_notation:
                # Convert the duration from float to a rational number
                duration_rational = self._get_duration_rationnal(duration)
                if note_name == 'N':  # Handle rest
                    abjad_note = abjad.Rest(duration_rational)
                    treble_notes.append(abjad_note)
                    bass_notes.append(abjad.Skip(duration_rational))
                else:
                    # Convert note name to abjad format
                    note, octave_str = self.note_name_to_abjad_format(note_name)

                    if octave_str.__contains__('\''):
                        treble_notes.append(abjad.Note(f"{note}{octave_str}", duration_rational))
                        bass_notes.append(abjad.Skip(duration_rational))

                    else:
                        bass_notes.append(abjad.Note(f"{note}{octave_str}", duration_rational))
                        treble_notes.append(abjad.Skip(duration_rational))
        else:
            song = self._get_melody_chords_estimate(simple_notation)

            # print("in convert_note_to_abjad() -> song:",song)
            treb, bass = self.extract_bass_treble_staff(song)
            # print("treb, bass line 341: ", treb,bass)
            treble_notes = to_abjad_staff(treb)
            bass_notes = to_abjad_staff(bass)


        return treble_notes, bass_notes


    def score(self,simple_notation, polyphonic=False):
        """
        Create a score from a simple notation.

        Parameters:
            simple_notation : list[tuple()]
                list of tuples containing note, start time and duration
            polyphonic : bool
                if True, the simple notation is polyphonic, else monophonic
        Returns:
            score : abjad.Score
                the score object
        """
        self.treble_notes, self.bass_notes = self.convert_notes_to_abjad(simple_notation, polyphonic=polyphonic)
        treble_container = abjad.Container(self.treble_notes, name='treble') if self.treble_notes else None
        bass_container = abjad.Container(self.bass_notes, name='bass') if self.bass_notes else None
        meter = abjad.Meter((4, 4))
        time_signature = abjad.TimeSignature((4, 4))
        if treble_container is not None:
            treble_measures = abjad.mutate.split(treble_container[:], [meter], cyclic=True)

        if bass_container is not None:
            bass_measures = abjad.mutate.split(bass_container[:], [meter], cyclic=True)


        if treble_container is not None:
            abjad.attach(abjad.Clef('treble'), treble_container[0])
        if bass_container is not None:
            abjad.attach(abjad.Clef('bass'), bass_container[0])

        mark = abjad.MetronomeMark(abjad.Duration(1, 4), int(self.tempo))
        if treble_container:
            abjad.attach(mark, treble_container[0])
        elif bass_container:
            abjad.attach(mark, bass_container[0])
        #container_t = abjad.Container(treble_staff)
        #container_b = abjad.Container(bass_staff)
        treble_staff = abjad.Staff([treble_container], lilypond_type="Staff", name="treble_staff") if treble_container else None
        bass_staff = abjad.Staff([bass_container], lilypond_type="Staff", name="bass_staff") if bass_container else None
        if treble_container and bass_container:
            staff_group = abjad.StaffGroup([treble_staff, bass_staff], lilypond_type="PianoStaff", name="piano_staff", simultaneous=True)
        elif treble_container:
            staff_group = abjad.StaffGroup([treble_staff], lilypond_type="Staff", name="treble_staff", simultaneous=True)
        elif bass_container:
            staff_group = abjad.StaffGroup([bass_staff], lilypond_type="Staff", name="bass_staff", simultaneous=True)
        else:
            raise ValueError("No treble or bass staff found")
        score = abjad.Score([staff_group])




        return score

    def save_score(self, score, output_path=None):
        """Export score to a pdf file.

        Parameters:
            score : abjad.Score
                the score object
            output_path : str
                the path where the pdf file will be saved

        Returns:
            str
                the path of the pdf file

        """
        if output_path is None:
            from os import getcwd
            output_path = getcwd()
        return abjad.persist.as_pdf(score, pdf_file_path=output_path)

    def show(self,simple_notation,polyphonic=False):
        if polyphonic:
            score = self.score(simple_notation,polyphonic=True)
        else:
            score = self.score(simple_notation)
        abjad.show(score)



if __name__ == "__main__":
    from MusicRetrieval import AudioSignal
    from Pseudo2D import Pseudo2D
    from Test.generate_sample_for_test import MusicGenerator
    music = MusicGenerator()
    sample = music.generate_audio(["Am","Dm","G"])
    audio = AudioSignal(sample)
    pseudo = Pseudo2D(audio)

    _, piano = pseudo.multipitch_estimate()
    pseudo.show_multipitch_estimate(piano)
    partition = Partition(audio.tempo)
    #chord_estimate = partition._get_melody_chords_estimate(pseudo.to_simple_notation(piano))
    sc = partition.score(pseudo.to_simple_notation_v2(piano),polyphonic=True)

    abjad.show(sc)
