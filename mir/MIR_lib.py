
"""Enum for the different Situations that can happen when transitioning from one note to another"""

from enum import Enum
from os import truncate
import numpy as np
from numpy.lib.twodim_base import diag

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

def build_transition_matrix( n_notes: int, prob_stay_note=0.9, prob_stay_silence=0.5):

    """
    Initialize the transition matrix for the HMM model.

    Parameters
    ----------
    prob_stay_note : float
        The probability of staying in the same note state.
    prob_stay_silence : float
        The probability of staying in the silence state.
    Return
    ------
    transition_matrix : 2D np.array
        The transition matrix for the HMM model.
    """
    # state 1, 3, 5 ... are onsets
    # state 2, 4, 6 ... are sustains
    N = 2 * n_notes + 1  # +1 for silence state
    transition_matrix = np.zeros((N,N))

    for i in range(N):
        for j in range(N):
            match classify_case(i,j):
                case Situation.SILENCE_to_SILENCE:
                    transition_matrix[i,j] = prob_stay_silence
                case Situation.SILENCE_to_ONSET:
                    transition_matrix[i,j] = (1 - prob_stay_silence)/n_notes
                case Situation.ONSET_to_SUSTAIN: # assuming window is to small to go from onset to onset or onset to silence
                    transition_matrix[i,j] = 1
                case Situation.SUSTAIN_to_SUSTAIN:
                    transition_matrix[i,j] = prob_stay_note
                case Situation.SUSTAIN_to_SILENCE:
                    transition_matrix[i,j] = (1 - prob_stay_note)/(n_notes+1)
                case Situation.SUSTAIN_to_ONSET:
                    transition_matrix[i,j] = (1 - prob_stay_note)/(n_notes+1)
    return transition_matrix



if __name__ == "__main__":
    print(build_transition_matrix(3))
