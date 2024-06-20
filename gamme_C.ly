\version "2.24.3"
\language "english"
\score
{
    % OPEN_BRACKETS:
    \new Score
    <<
        % OPEN_BRACKETS:
        \context Staff = "treble"
        {
            % BEFORE:
            % COMMANDS:
            \tempo 4=129
            % OPENING:
            % COMMANDS:
            \clef "treble"
            r1.
            s4
            s4
            s4
            s4
            s4
            s4
            s4
            c'2.
        % CLOSE_BRACKETS:
        }
        % OPEN_BRACKETS:
        \context Staff = "bass"
        {
            % OPENING:
            % COMMANDS:
            \clef "bass"
            s1.
            c4
            d4
            e4
            f4
            g4
            a4
            b4
            s2.
        % CLOSE_BRACKETS:
        }
    % CLOSE_BRACKETS:
    >>
}
