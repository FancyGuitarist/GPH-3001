import sys
from types import GeneratorType
from mir.Pseudo2D import Pseudo2D
import unittest
from mir.MusicRetrieval import AudioSignal
import numpy as np

class TestPseudo2D(unittest.TestCase):
    def setUp(self) -> None:
        self.audio = AudioSignal("song&samples/polyphonic.wav")
        self.pseudo = Pseudo2D(self.audio)

    def test_pseudo2D(self):
        self.assertIsInstance(self.pseudo, Pseudo2D)

    def test_get_pseudo_2d(self):
        self.assertIsInstance(self.pseudo.pseudo_2d, GeneratorType)

    def test_cross_correlate_diag(self):
        for i in self.pseudo.pseudo_2d:
            cross_corr = self.pseudo.cross_correlate_diag(i)
            self.assertIsInstance(cross_corr, np.ndarray)

    def test_convolution(self):
        for i in self.pseudo.pseudo_2d:
            conv = self.pseudo.cross_correlate_diag(i, _2D=True)
            self.assertIsInstance(conv, np.ndarray)


    def test_best_estimate(self):
        pseudo = next(self.pseudo.pseudo_2d)
        cross_corr = self.pseudo.cross_correlate_diag(pseudo, _2D=True)
        best_estimate = self.pseudo.best_estimate(cross_corr)
        self.assertIsInstance(best_estimate, np.ndarray)


    def test_show_multipitch_estimate(self):
        song, piano = self.pseudo.multipitch_estimate()
        self.assertEqual(len(song), len(piano.T))
        #self.pseudo.show_multipitch_estimate(piano)

    def test_to_simple_notation(self):
        _, piano = self.pseudo.multipitch_estimate()
        song_simple = self.pseudo.to_simple_notation(piano)
        self.assertIsInstance(song_simple, list)
