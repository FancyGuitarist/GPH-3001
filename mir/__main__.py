from mir.MusicRetrieval import AudioSignal, Mono
import numpy as np
import sys
import os
from mir.anotation import Partition
import argparse
from termcolor import colored

def error(message):
    print(colored(f'Error:', 'red', attrs=['bold']), message)

def pgb(message):
    print(colored(message, 'green', attrs=['bold']))

def pcb(message):
    print(colored(message, 'cyan', attrs=['bold']))

credits_to_demucs =r"""
This project uses the Demucs model for music source separation (MSS). Thank you @Alexandre Défossez!
https://github.com/adefossez/demucs
"""

def handle_benchmark(args):
    from mir.Validation.Validator import benchmark
    if not os.path.exists(args.benchmark):
        error(f"File {args.benchmark} not found")
        sys.exit(1)
    # if args.benchmark is in validation folder print the credit to maestro dataset
    if "Validation" in  args.benchmark:
        l = len("Curtis Hawthorne, Andriy Stasyuk, Adam Roberts, Ian Simon, Cheng-Zhi Anna Huang,")
        pgb("Benchmarking against MAESTRO dataset:")
        pgb("-"*l)
        pcb("""Curtis Hawthorne, Andriy Stasyuk, Adam Roberts, Ian Simon, Cheng-Zhi Anna Huang,
        Sander Dieleman, Erich Elsen, Jesse Engel, and Douglas Eck. 'Enabling
        Factorized Piano Music Modeling and Generation with the MAESTRO Dataset.'
        In International Conference on Learning Representations, 2019.""")
        pgb("-"*l)
    score = benchmark(args.benchmark, show_piano=args.piano_roll)
    import pprint
    pprint.pprint(dict(score.items()))

class CapitalizedHelpFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
            if not action.option_strings:
                return self._metavar_formatter(action, action.dest)(1)[0]
            else:
                parts = []
                if action.nargs == 0:
                    parts.extend(action.option_strings)
                else:
                    default = action.dest
                    args_string = self._format_args(action, default)
                    for option_string in action.option_strings:
                        parts.append(f'{option_string} {args_string}')
                return ', '.join(parts)

    def _get_help_string(self, action):
        help_string = action.help
        if help_string and help_string[0].islower():
            help_string = help_string.capitalize()
        return help_string

def add_common_argument(parser):
    piano_debug_group = parser.add_mutually_exclusive_group(required=False)
    piano_debug_group.add_argument('-pr', '--piano-roll', action='store_true', help='Show piano roll visualization')
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("-u", '--url', type=str, help='URL to the music file')
    input_group.add_argument('-r', '--recording', action='store_true', help='Record audio from microphone')
    input_group.add_argument('-f', '--file', type=str, help='Path to the music file with .wav extension')
    parser.add_argument('-o', '--output', type=str, help='Output file name')
    parser.add_argument('-e', '--extract', type=str, help='Extract the audio of an instrument using Music Source Separation ', metavar='<guitar|piano|drums|vocals|other>')

# Create the CustomArgumentParser
def parse_args(arg_list: list[str] | None = None):
    parser = argparse.ArgumentParser(prog="mir", description="Automatic music transcription & identification for musicians.", epilog="Music is the arithmetic of sounds as optics is the geometry of light. -Claude Debussy", formatter_class=CapitalizedHelpFormatter)
    analysis_parser = parser.add_subparsers(title='Analysis modes', dest='Modes')
    mono = analysis_parser.add_parser('monophonic', help='Monophonic mode',formatter_class=CapitalizedHelpFormatter )
    poly = analysis_parser.add_parser('polyphonic', help='Polyphonic mode',formatter_class=CapitalizedHelpFormatter )
    chord = analysis_parser.add_parser('chord-only', help='Chord-only mode',formatter_class=CapitalizedHelpFormatter)

    for p in [mono, poly, chord]:
        piano_debug_group = p.add_mutually_exclusive_group(required=False)
        piano_debug_group.add_argument('-pr', '--piano-roll', action='store_true', help='Show piano roll visualization')

        input_group = p.add_mutually_exclusive_group(required=True)
        p.add_argument('-e', '--extract', type=str, help='Extract the audio of an instrument using Music Source Separation ', metavar='<guitar|piano|drums|vocals|other>')
        if p == poly:
            input_group.add_argument('-b','--benchmark', type=str, help='Compare against ground truth from midi file', metavar='<path/to/midi/file.midi>')
            p.add_argument('-t','--threshold', type=float, help='Threshold for the detection of note in with respect to the highest correlation value in a frame', metavar='[0-1]')
            p.add_argument('-g','--gamma', type=int, help='Gamma factor used in logarithmic compression, higher values increase the sensitivity', metavar='[1-inf]')
            p.add_argument('-std','--standard-deviation', type=float, help='''
                Standard deviation threshold used to determine if a frame is voiced or not,
                1e-8 work best for polyphonic piano while 1e-3 work best for noisy guitar recording
                ''', metavar='<float>')
            piano_debug_group.add_argument('-d', '--debug', type=float, help='debug a certain time frame, will show the cross-correlation with the template matrix and pseudo2D spectrum', metavar='<time in seconds>')
            p.set_defaults(gamma=50, standard_deviation=1e-3, threshold=0.55)

        input_group.add_argument("-u", '--url', type=str, help='URL to the music file')
        input_group.add_argument('-r', '--recording', action='store_true', help='Record audio from microphone')
        input_group.add_argument('-f', '--file', type=str, help='Path to the music file with .wav extension')
        p.add_argument('-o', '--output', type=str, help='Output file name')

    if len(sys.argv) == 1:
        parser.print_help(sys.stdout)
        sys.exit(1)
    args = parser.parse_args(arg_list)
    return args

def handle_extraction(STEM, path_to_audio):
    # get the path to the local file
    pcb(credits_to_demucs)
    current_directory = os.getcwd()
    import demucs.separate
    name =  os.path.split(path_to_audio)[-1].split(".")[0]
    model = "htdemucs_6s"
    res_path = os.path.join(current_directory, "separated", model, name, STEM + ".mp3")
    valid_STEM = ["guitar", "piano", "drums", "vocals", "bass", "other"]
    if STEM not in valid_STEM:
        print(colored("Invalid instrument to extract","red", attrs=["bold"]),": please provide one of the following: guitar, piano, drums, vocals, bass or other.",sep="")
        sys.exit(1)
    demucs.separate.main(["--mp3", "--two-stems", STEM, "-n", model, path_to_audio])
    return res_path

def main(arg_list: list[str] | None = None):

    args = parse_args(arg_list)

    if args.file:
        audio_path = str(args.file)

    elif args.recording:
        from mir.rec_unlimited import record
        audio_path = record()

    elif args.url:
        import yt_dlp
        with yt_dlp.YoutubeDL({'format': 'bestaudio', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav'}]}) as ydl:
            info_dict = ydl.extract_info(args.url, download=True)
            audio_path = str(ydl.prepare_filename(info_dict).replace('.webm', '.wav').replace('.m4a', '.wav'))

    elif args.Modes == "polyphonic" and args.benchmark:
        handle_benchmark(args)
        sys.exit(0)

    else:
        error("No input provided")
        audio_path = ""
        sys.exit(1)

    if args.extract:
        audio_path = handle_extraction(args.extract, audio_path)
    audio = AudioSignal(audio_path)
    partition = Partition(audio.tempo)






    if args.Modes == "polyphonic":
        pgb("Polyphonic mode enabled")
        from mir.Pseudo2D import Pseudo2D
        pseudo2d = Pseudo2D(audio)
        pseudo2d.gamma = args.gamma
        pseudo2d.threshold = args.threshold
        pseudo2d.std_threshold = args.standard_deviation
        _, piano = pseudo2d.multipitch_estimate()
        if args.piano_roll:
            pseudo2d.show_multipitch_estimate(piano)
            sys.exit(0)
        elif args.debug:
            pseudo2d.show(args.debug)
            sys.exit(0)
        simple_notation = pseudo2d.to_simple_notation_v2(piano)
        #print(simple_notation)


    elif args.Modes == "chord-only":
        pgb("chord-Only mode enabled")
        from Chord import ChordIdentifier
        chord = ChordIdentifier(audio)
        if args.piano_roll:
            chord.show()
            sys.exit(0)
        from pprint import pprint
        pprint(chord.simple_notation())
        sys.exit(0)
        #simple_notation = chord.simple_notation()



    else:
        if args.piano_roll:
            error("Monophonic mode does not support piano roll visualization")
            sys.exit(1)
        pgb("Monophonic mode enabled")
        mono = Mono(audio)
        result = mono.decoded_states
        simple_notation = mono.simple_notation(result)

    if args.output:
        partition.save_score(partition.score(simple_notation, polyphonic=(args.Modes == "polyphonic")), args.output)

    if args.recording:
        # delete audio file after processing
        if args.output:
            import shutil
            if args.output[-4:] != ".wav":
                args.output += ".wav"
            shutil.copy(audio_path,  args.output)
        else:
            is_keep = input("Do you want to keep the audio file? [y/n]")
            if is_keep.lower() == "n":
                os.remove(audio_path)
    elif args.url:
        if args.output:
            import shutil
            shutil.copy(audio_path,  args.output + ".wav")
        else:
            is_keep = input("Do you want to keep the audio file? [y/n]")
            if is_keep.lower() == "n":
                os.remove(audio_path)

    partition.show(simple_notation,polyphonic=(args.Modes == "polyphonic"))


if __name__ == '__main__':
    main()
