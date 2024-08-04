
from functools import partial
import abjad
import numpy as np
import pdb;
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

    def _group_overlapping_notes(self, simple_notation, epsilon=0.05):
        # Sort the data by start frame
        simple_notation.sort(key=lambda x: x[1])

        # List to store grouped notes
        grouped_notes = []

        # Initialize the first group with the first note
        current_group = [simple_notation[0]]

        # Iterate through the sorted list
        for i in range(1, len(simple_notation)):
            note, start, duration = simple_notation[i]
            # Check if the current note overlaps with the last note in the current group
            last_note, last_start, last_duration = current_group[-1]

            if start < last_start + last_duration - epsilon:
                # If they overlap, add the current note to the current group
                current_group.append(simple_notation[i])
            else:
                # If they don't overlap, save the current group and start a new group
                grouped_notes.append(current_group)
                current_group = [simple_notation[i]]
        grouped_notes.append(current_group)

        return grouped_notes

    def _get_melody_chords_estimate(self, simple_notation, extract=False):
        """
        function to estimate chords from simple notation by :

            1. Grouping overlapping notes.

            2. Estimating the chord from the grouped notes by comparing with mean and standard deviation of start time and duration.

        Parameters
        ----------
        simple_notation : list[tuples(note: str, start_time: float, duration: float)]
            list of tuples containing note, start time and duration
        extract : bool
            if True, extract the melody notes from the chords in tuple format.

        Returns
        -------
        melody + chord_estimate : list[tuples(note | chord: str of abjad format, start_time: float, duration: float))]
            list of grouped simple notation tuples present in the chords in abjad notation string format.
        """
        grouped_notes = self._group_overlapping_notes(simple_notation)
        note_name_to_abjad_format = partial(self.note_name_to_abjad_format, join=True)
        chord_estimate : list[tuple[str,float,float]]  = []
        melody : list[tuple[str,float,float]]  = []
        dictionnary_of_time_repr = dict(full_notes(self.tempo))

        for group in grouped_notes:

            g = np.array(group)
            (start_time , duration) = g.T[1:,...].astype(float)
            mu_duration, sigma_duration = np.mean(duration),np.std(duration)
            mu_start_time, sigma_start_time = np.mean(start_time),np.std(start_time)
            # grab the notes where the duration and start_time are in sigma range of the mean
            is_chord = (np.abs(duration - mu_duration) < mu_duration/2)# & (np.abs(start_time - mu_start_time) < sigma_start_time*2)
            in_chord = g[is_chord]

            out_chord = g[~is_chord]
            for note, start, duration in out_chord:
                # modify note to abjad notation
                melody.append((note_name_to_abjad_format(note), float(start), float(duration)))

            if len(in_chord) > 1: # verify if any chord are present
                #print("in chord",in_chord)
                # estimate start time and duration of the chord
                start_time: float = np.min(in_chord.T[1].astype(float)).astype(float)
                duration: float = np.max(in_chord.T[2].astype(float)).astype(float)
                # convert the chord to abjad format
                iterable = ' '.join(list(map(note_name_to_abjad_format, in_chord.T[0].astype(str) )))
                # print("iterable : ", iterable)
                simple_chord_notation = (f"<{iterable}>", start_time, duration)

                chord_estimate.append(simple_chord_notation)
        #breakpoint()
        if extract:
            return melody, chord_estimate
        else:
            # sorted by start time
            # print("melody + chord_estimate melody, chord estimate:", melody +chord_estimate)
            all = melody + chord_estimate
            res = sorted(all, key=lambda x: x[1])
            return res


    def note_name_to_abjad_format(self, note_name, join=False) -> str | tuple[str, str]:
        """Converts note name to abjad format.
        return : tuple = (note: str, octave_str: str)

        """
        note : str = note_name[:-1].lower()
        if '#' in note or "♯" in note:
            note = note.replace('#', 's')
            note = note.replace('♯', 's')
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

    def extract_bass_treble_staff(self, simple_notation_vec: list[tuple[str, float, float]]) -> tuple[list[tuple[str, float, float]], list[tuple[str, float, float]]]:

        """
        Extract the bass and treble staff from the simple notation.
        Will also correct the sequential notes or chords in the simple notation so it fits in the score properly.

        Parameters:
            simple_notation : list[tuple()]
                list of tuples containing (note | chord, start_time, duration)

        Returns:
            treble_staff : list[tuple()],
            bass_staff : list[tuple()]

        """
        duration_mapping_dict = dict(full_notes(self.tempo))
        def sequential_correction(simp_notation_vec, i, smallest_duration="1/32"):
            """
            Correct the sequential notes or chords in the simple notation
            by adding a rest in between if there is a gap.
            """
            epsilon_as_float = duration_mapping_dict[smallest_duration]
            # print("in sequential correction()")
            if (len(simp_notation_vec) <= i + 1): # early return if last note

                return [simp_notation_vec[i]]
            # print("i",i,"len(simp_notation)",len(simp_notation_vec))

            start_of_second_note = simp_notation_vec[i+1][1] # start of the second note
            end_of_first_note = simp_notation_vec[i][2] + simp_notation_vec[i][1] # end of the first note
            # print("is_almost_equalt line 200",is_almost_equal(
            #    print("Line 212: gap in between the note should add a N like this",("N",
                    # simple_notation_vec[i][2] + simple_notation_vec[i][1],
                    # simple_notation_vec[i+1][1] - simple_notation_vec[i][2] + simple_notation_vec[i][1]))
                # gap in between notes | chords, need a rest in between
            if not is_almost_equal(start_of_second_note, end_of_first_note, epsilon=epsilon_as_float):
                if start_of_second_note-end_of_first_note > 0:
                    return [simp_notation_vec[i] , ("N",
                        end_of_first_note,
                        start_of_second_note-end_of_first_note)]
                else:
                    return [simp_notation_vec[i]]
            else:
                return [simp_notation_vec[i]]


        def is_bass_treble(simple_notation_unit):
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



        def seperate_treble_bass(simple_notation_vec: list[tuple[str, float, float]]):
            """
            Seperate the treble and bass staff from the simple notation unit.

            Parameters:
                simple_notation_unit : tuple(note | chord, start_time, duration)
            """
            treble, bass = [], []
            # seperate the treble and bass
            for i in range(len(simple_notation_vec)):
                simple_notation_unit = simple_notation_vec[i]
                maybe_bass_or_treb = is_bass_treble(simple_notation_unit)
                if maybe_bass_or_treb == "treble":
                    treble.append(simple_notation_unit)
                elif maybe_bass_or_treb == "bass" :
                    bass.append(simple_notation_unit)
                else:
                    raise ValueError("The note or chord is neither in the bass nor treble staff.")
            return treble, bass

        treb, bass = seperate_treble_bass(simple_notation_vec)
        # print("treb, bass: line 260", treb, bass)

        new_treb, new_bass = [], []
        if treb:
            for i in range(len(treb)):
                temp = sequential_correction(treb, i)
                new_treb += temp
        if bass:
            for i in range(len(bass)):
                b_temp = sequential_correction(bass, i)
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
                list of tuples containing note, start time and duration
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
                elif ' ' in note_name:
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

        self.treble_notes, self.bass_notes = self.convert_notes_to_abjad(simple_notation, polyphonic=polyphonic)

        treble_container = abjad.Container(self.treble_notes, name='treble') if self.treble_notes else None
        bass_container = abjad.Container(self.bass_notes, name='bass') if self.bass_notes else None
        meter = abjad.Meter((4, 4))
        time_signature = abjad.TimeSignature((4, 4))
        if treble_container is not None:
            treble_measures = abjad.mutate.split(treble_container[:], [meter],cyclic=True,)
            # for measure in treble_measures:
            #     measure_duration = sum([leaf.written_duration for leaf in measure])
            #     print(f"Treble measure duration: {measure_duration}")
        if bass_container is not None:
            bass_measures = abjad.mutate.split(bass_container[:], [meter], cyclic=True)
            # for measure in bass_measures:
            #     measure_duration = sum([leaf.written_duration for leaf in measure])
            #     print(f"Bass measure duration: {measure_duration}")




        #for voice in [treble_container, bass_container]:
        #    for measure in abjad.mutate.split(voice[1:], meter):
        #        print(measure)
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
        """Exporte la partition en format LilyPond."""
        if output_path is None:
            from os import getcwd
            output_path = getcwd()
        abjad.show(score, output_directory=output_path, should_open=False)

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

    song, piano = pseudo.multipitch_estimate()
    pseudo.show_multipitch_estimate()
    partition = Partition(audio.tempo)
    #chord_estimate = partition._get_melody_chords_estimate(pseudo.to_simple_notation(piano))
    sc = partition.score(pseudo.to_simple_notation(piano),polyphonic=True)

    abjad.show(sc)
