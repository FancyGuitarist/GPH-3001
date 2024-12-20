import librosa
import numpy as np
import scipy
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from Test.generate_sample_for_test import MusicGenerator
from mir.MusicRetrieval import AudioSignal, AudioParams, Note
from functools import cached_property
import matplotlib.pyplot as plt

# import pdb; pdb.set_trace()

class Pseudo2D(AudioParams):
    def __init__(self, audio: AudioSignal) -> None:
        super().__init__()
        self.n_bins_per_octave = 36
        self.n_harmonics = 3
        self.audio = audio
        self.threshold = 0.54
        self.std_threshold = 1e-3
        self.gamma = 1
        self.min_length = 4

    @cached_property
    def cqt(self):
        """
        Compute the constant-Q transform (CQT) of the harmonic audio signal.
        Returns:
        - cqt: Constant-Q transform of the harmonic audio signal.
        """
        cqt = librosa.cqt(y=self.audio.y_harmonic,
                          sr=self.sampling_rate, fmin=self.note_min.hz,
                          hop_length=self.hop_length,
                          n_bins=((self.note_max.midi - self.note_min.midi + 1)
                                  * (self.n_bins_per_octave // 12)),
                          bins_per_octave=self.n_bins_per_octave,
                          window='hann'
                          )
        return cqt

    def logstft(self):
        """
        Compute the short-time Fourier transform (STFT) of the harmonic audio signal and bin the output in log scale.

        Its not currently used but may be of use later on in the project

        Returns:
        - Logstft: Log Short-time Fourier transform of the harmonic audio signal.
        """
        X_stft = librosa.stft(
            y=self.audio.y_harmonic,
            hop_length=self.hop_length)
        # bin the note from the stft
        # Convert frequency bins to MIDI note numbers
        ax_freq_lin = librosa.fft_frequencies(sr=self.sampling_rate)
        ax_freq_lin = np.arange(
            X_stft.shape[0]) * self.sampling_rate / self.window_length
        pitches = np.arange(self.note_min.midi, self.note_max.midi + 1)
        ax_freq_log = librosa.midi_to_hz(pitches)

        frequencies = librosa.fft_frequencies(
            sr=self.sampling_rate, n_fft=X_stft.shape[0])

        def center_freq(p, A4_tuning=440.0):
            return A4_tuning * 2**((p - 69) / 12)

        X_stft_log = np.zeros((len(pitches), X_stft.shape[1]))

        for cur_pitch in pitches:
            f_lower_bound = center_freq(cur_pitch - 0.5)
            f_upper_bound = center_freq(cur_pitch + 0.5)

            cur_idxs = np.where(
                (ax_freq_lin >= f_lower_bound) & (
                    ax_freq_lin < f_upper_bound))
            X_stft_log[cur_pitch - pitches[0]
                       ] = np.sum(np.abs(X_stft[cur_idxs]), axis=0)
        return X_stft_log

    def R(self, x):
        return self.n_bins_per_octave * np.log2(np.ceil(x))

    @cached_property
    def template_matrix(self):
        """
        Create a sparse 2-D template matrix for multi-pitch estimation.
        Returns:
        - Q: Sparse 2-D template matrix.
        """

        rq = np.zeros(self.R(self.n_harmonics).astype(int) + 1)
        harmonics = np.arange(1, self.n_harmonics + 1)
        harmo = self.R(harmonics).astype(int)
        damping_factor = 1
        for i in harmo:
            rq[i] = 1 * damping_factor
            damping_factor /= librosa.db_to_amplitude(4.7)
        template_matrix = np.outer(rq, rq)
        template_matrix = template_matrix / np.sqrt(np.sum(template_matrix**2))
        return template_matrix

    def generate_template_from_audio_file(self, path):
        #import pdb; pdb.set_trace()
        #breakpoint()
        audio = AudioSignal(path)
        cqt = librosa.cqt(y=audio.y,
                          sr=audio.sampling_rate,
                          fmin=self.note_min.hz,
                          hop_length=self.hop_length,
                          n_bins=((self.note_max.midi - self.note_min.midi + 1)
                                  * (self.n_bins_per_octave // 12)),
                          bins_per_octave=self.n_bins_per_octave,
                          window='hann',
                          )
        # detect onset
        onset = librosa.onset.onset_detect(y=audio.y, sr=audio.sampling_rate)
        # Detect the fundamental frequency using pyin
        f0, voiced_flag, voiced_probs = librosa.pyin(audio.y, fmin=self.note_min.hz, fmax=self.note_max.hz, sr=audio.sampling_rate)
        frame = np.argmax(voiced_probs)
        fundamental_freq = f0[frame]
        midi_shift = int(librosa.hz_to_midi(fundamental_freq) - self.note_min.midi)
        template_1D = np.roll(np.abs(cqt[:,frame]), -midi_shift*(self.n_bins_per_octave // 12 ), axis=0).flatten()

        # Find indices of local maxima
        local_maxima_indices = np.argwhere(
            (template_1D > np.roll(template_1D, 1, axis=0)) &
            (template_1D > np.roll(template_1D, -1, axis=0))
        ).flatten()

        output_array = np.zeros_like(template_1D)

        # Set only the local maxima to their original values
        output_array[local_maxima_indices] = template_1D[local_maxima_indices]

        # only keep the first n_harmonics
        size = self.R(self.n_harmonics).astype(int) + 1
        template_1D = output_array[:size]

        template_1D /= np.linalg.norm(template_1D)
        return np.abs(np.outer(template_1D.conj(), template_1D))

    @property
    def pseudo_2d(self):

        res = (np.outer(self.cqt[:, i], self.cqt[:, i].conj())
            for i in range(self.cqt.shape[1]))
        return res

    def cross_correlate_diag(self, pseudo2dSpectrum, _2D=True):
        """
        Cross-correlate the pseudo2dSpectrum with the template matrix

        Returns:
            np.ndarray(1,): the cross-correlation of the pseudo2dSpectrum with the template matrix

        """
        std = np.std(pseudo2dSpectrum)
        gamma = self.gamma  # 6_7k sweet spot pareille.
        pseudo2dSpectrum = np.log(
            1 + gamma * np.abs(
                pseudo2dSpectrum + np.finfo( np.float32).eps
            )
        )
        # normalize spectrum
        pseudo2dSpectrum /= np.sqrt(np.sum(pseudo2dSpectrum))
        if std < self.std_threshold:
            return np.zeros(pseudo2dSpectrum.diagonal().shape)
        if not _2D:
            conv = scipy.signal.correlate(
                pseudo2dSpectrum.diagonal(),
                self.template_matrix.diagonal(),
                mode="same",
                method="fft")
        else:
            conv = np.diag(
                scipy.signal.correlate(
                    pseudo2dSpectrum,
                    self.template_matrix,
                    mode="same",
                    method="fft"))
        return conv

    def best_estimate(self, cross_corr: np.ndarray) -> np.ndarray:
        """
        Gives best estimate of the pitch by returning the
        index of the cross correlation that is
        in a local maxima and above the threshold.

        Parameters:
            cross_corr: np.ndarray(N,): the cross correlation of the pseudo2dSpectrum with the template matrix.

        Returns:
            indexs: np.ndarray(L,): the indexs of the cross correlation that is in a local maxima and above the threshold.
        """

        max_cross_corr = np.max(cross_corr)
        min_cross_corr = np.min(cross_corr)
        bin_per_note = self.n_bins_per_octave // 12

        indexs = np.argwhere((
            cross_corr > self.threshold * (max_cross_corr - min_cross_corr))
            & (cross_corr > np.roll(cross_corr, 1))
            & (cross_corr > np.roll(cross_corr, -1))
        )

        return (indexs.flatten() -
                self.template_matrix.shape[0] // 2) // bin_per_note

    def filter_short_notes(self, piano_roll: np.ndarray):
        """
        Filter out notes that are shorter than the specified minimum length.
        """
        for note in range(piano_roll.shape[0]):
            note_onsets = np.where(np.diff(np.concatenate(
                ([0], piano_roll[note, :], [0]))) == 1)[0]
            note_offsets = np.where(np.diff(np.concatenate(
                ([0], piano_roll[note, :], [0]))) == -1)[0]
            length = len(note_onsets)
            for i in range(length):
                if note_offsets[i] - note_onsets[i] < self.min_length:
                    piano_roll[note, note_onsets[i]:note_offsets[i]] = 0


        return piano_roll

    def multipitch_estimate(self):
        """
        Estimate the multipitch of the audio signal.
        Returns: (song, piano_roll)
            song: list of np.array of frequencies in hz
            piano_roll: np.ndarray of shape (n_notes, n_frames)

        """
        song = [
            self.best_estimate(
                self.cross_correlate_diag(
                    frame,
                    _2D=True)) for frame in self.pseudo_2d]

        piano_roll = np.zeros((self.n_notes, len(song)))

        for index, notes in enumerate(song):
            piano_roll[notes, index] = 1

        piano_roll = self.filter_short_notes(piano_roll)

        song = [librosa.midi_to_hz(np.argwhere(
            piano_roll[:, i]) + self.note_min.midi).flatten() for i in np.arange(piano_roll.shape[1])]
        return song, piano_roll



    def to_simple_notation_v2(self, piano_roll: np.ndarray):
        """
        Group simultaneous notes together in piano_roll. Making it a good choice to create chords.

        Parameters
        ----------
        piano_roll : np.ndarray
            piano roll matrix

        Returns
        -------
        simple notation : list[tuple[ndarray, float, float]]
            list of tuples where
            the first element of the tuple is the note in standard english notation. ex: 'C4', 'A#3'
        """
        simple_grouped_notes = []
        i = 0
        last_change = 0
        for frame in piano_roll.T:
            if  i > 0:
                last_frame = piano_roll.T[i-1]
            else:
                last_frame = piano_roll.T[i]
            last_group = np.nonzero(last_frame)[0]

            if any(frame != last_frame):
                # save the last_change time
                # store the value of last frame
                if last_group.size > 0:
                    simple_grouped_notes.append((librosa.midi_to_note(last_group + self.note_min.midi).tolist(), last_change * self.hop_time, (i-last_change)*self.hop_time))
                last_change = i

            # handle the end of the piano roll
            if i == len(piano_roll.T) - 1:
                current_group = np.nonzero(frame > 0)[0]
                if current_group.size > 0:
                    simple_grouped_notes.append((librosa.midi_to_note(current_group+ self.note_min.midi).tolist(), last_change * self.hop_time, (i-last_change)*self.hop_time))
            i += 1

        return simple_grouped_notes

    def show_multipitch_estimate(self, piano_roll: np.ndarray, ax=None):
        librosa.display.specshow(
            piano_roll,
            fmin=self.note_min.hz,
            y_axis='cqt_note',
            x_axis='time',
            sr=self.sampling_rate,
            hop_length=self.hop_length,
            ax=ax)
        plt.xlabel('Time')
        plt.ylabel('Pitch')
        plt.title('Multipitch estimation')
        plt.show()

    def show(self, time):
        frame = librosa.time_to_frames(
            time, sr=self.sampling_rate, hop_length=self.hop_length)
        p2d = list(self.pseudo_2d)
        if frame >= len(p2d):
            raise ValueError(f"Time: {time} is out of bounds with time of the audio: {librosa.frames_to_time(len(p2d), sr=self.sampling_rate, hop_length=self.hop_length)}")

        from itertools import islice
        i = list(islice(self.pseudo_2d, frame - 1, frame))[0]

        cross_corr = self.cross_correlate_diag(i, _2D=True)
        fig, ax = plt.subplots(1, 3)
        ax[0].imshow(np.abs(scipy.signal.correlate(self.template_matrix,i)), origin='lower')
        ax[1].imshow(self.template_matrix, origin='lower')
        ax[2].imshow(np.abs(i), origin='lower')

        ax[0].set_title('Correlation croisée avec le modèle harmonique')
        ax[1].set_title('Modèle harmonique')
        ax[2].set_title('Spectre pseudo 2D')
        fig.tight_layout()
        plt.show()


if __name__ == "__main__":
    # bunch of code to test functionnality
    audio = AudioSignal("song&samples/gamme_C.wav")
    fig, ax = plt.subplots(2, 1)

    pseudo = Pseudo2D(audio)
    pseudo.gamma = 1
    # librosa.display.specshow(librosa.cqt(audio.y,sr=audio.sampling_rate), sr=pseudo.sampling_rate, x_axis='time', y_axis='cqt_note', ax=plt.gca())
    # plt.show()
    from MusicRetrieval import Note

    # song, piano = pseudo.multipitch_estimate()
    # pseudo.show_multipitch_estimate(piano, ax=ax[0])
    # pseudo.template_matrix = pseudo.generate_template_from_audio_file("/Users/antoine/Desktop/GPH/E2024/PFE/mir/single-piano-note-a4_100bpm_C_major.wav")
    # song, piano = pseudo.multipitch_estimate()
    # pseudo.show_multipitch_estimate(piano, ax=ax[1])
    # plt.show()
    pseudo.show(3)

    #print(pseudo.to_simple_notation_v2(piano))
