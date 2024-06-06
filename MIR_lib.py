
"""Enum for the different Situations that can happen when transitioning from one note to another"""

from enum import Enum

class Situation(Enum):
    SILENCE_to_SILENCE = 0
    SILENCE_to_ONSET = 1
    SILENCE_to_SUSTAIN = 2
    ONSET_to_SILENCE = 3
    ONSET_to_ONSET = 4
    ONSET_to_SUSTAIN = 5
    SUSTAIN_to_SILENCE = 6
    SUSTAIN_to_ONSET = 7
    SUSTAIN_to_SUSTAIN = 8
    IMPOSSIBLE = 9

class Note_State(Enum):
    SILENCE = "s"
    ONSET = "o"
    SUSTAIN = "sus"
    VIBRATO = "vib"
    BEND = "ben"
class MusicDynamics(Enum):
    PIANISSIMO = "pp"
    PIANO = "p"
    FORTE = "f"
    NORMAL = "n"



"""Inner logic for the transition matrix generation. This function is used to generate the transition matrix for the HMM model."""
    # state 1, 3, 5 ... are onsets
    # state 2, 4, 6 ... are sustains
def classify_case(i:int,j:int):
    if i == 0:
        if j == 0:
            return Situation.SILENCE_to_SILENCE
        elif j % 2 != 0:
            return Situation.SILENCE_to_ONSET
        else:
            return Situation.IMPOSSIBLE
    elif i % 2 != 0:
        if j == 0:
            return Situation.ONSET_to_SILENCE
        elif j % 2 != 0:
            # we cant realisticly go from onset to onset in such a short window
            return Situation.IMPOSSIBLE
        if j == i+1:
            return Situation.ONSET_to_SUSTAIN
    elif i % 2 == 0:
        if j == 0:
            return Situation.SUSTAIN_to_SILENCE
        elif j % 2 != 0:
            return Situation.SUSTAIN_to_ONSET
        if j == i:
            return Situation.SUSTAIN_to_SUSTAIN
    return Situation.IMPOSSIBLE
