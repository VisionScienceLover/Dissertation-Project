ASTEROID IMPACT PART A - FEEDBACK-CONTROLLED ABSTRACT 3-BACK V4
================================================================

This is a complete standalone Asteroid Impact folder. Do not copy its files
into an older experiment. Extract the ZIP into a new folder.

RUN FROM ANACONDA PROMPT
------------------------
  conda activate asteroid
  cd /d "C:\Users\gerha\Desktop\AsteroidImpact_PART_A_ABSTRACT_3BACK_V4"
  RUN_PART_A.bat

The terminal must print:

  ASTEROID IMPACT PART A - FEEDBACK-CONTROLLED 3-BACK V4

If that exact line is absent, stop: a different experiment is running.

PARTICIPANT TASK
----------------
1. Blue, green, and purple patterns repeat in a three-item cycle.
2. Compare the current pattern with the most recent pattern of the SAME COLOR.
   That same-color pattern appeared exactly three trials earlier.
3. Both the line orientation and dot position must match exactly.
4. Right-click for SAME and left-click for DIFFERENT.
5. The first three patterns of every section initialize memory and are unscored.
6. After the fixed 5,000-ms pattern period, collect the crystal and avoid the
   asteroids. Ignore notifications, banners, and buffering symbols.

DESIGN
------
  Practice:      15 presentations = 3 memory + 12 scored trials
  Calibration:  23 presentations = 3 memory + 20 scored trials
  Control:       43 presentations = 3 memory + 40 scored trials
  Cognitive:     43 presentations = 3 memory + 40 scored trials
  Perceptual:    43 presentations = 3 memory + 40 scored trials
  Combined:      43 presentations = 3 memory + 40 scored trials

The four experimental conditions occur in the fixed order control, cognitive,
perceptual, and combined. A participant-paced break screen appears before each
experimental block. The calibrated asteroid level is locked across these four
blocks. There are no shields, slowdown objects, or other power-ups.

FEEDBACK CONTROLS IMPLEMENTED
-----------------------------
Each experimental condition contains exactly:
  10 exact matches
  10 line-only differences
  10 dot-only differences
  10 differences in both features

For every nonmatch category, small and large changes are balanced:
  Small line change: 15 degrees
  Large line change: 90 degrees
  Small dot change: another position within the same quadrant (45 degrees)
  Large dot change: corresponding position in the opposite quadrant (180 degrees)

The comparison-type order differs across conditions, but the counts and change
magnitudes are matched. Exact N-1 and N-2 lures are excluded. Partial feature
overlaps at N-1 and N-2 are held to 8 of each per experimental condition and
are recorded in the CSV. Recurring color streams make the correct N-3
comparison explicit without reducing the requirement to maintain three items.

DISTRACTOR BALANCE WITHIN THE 40 SCORED TRIALS
----------------------------------------------
  Cognitive:   20 text notifications and 20 buffering displays
  Perceptual:  20 red banners and 20 flashing banners
  Combined:    10 trials of each distractor pairing

DATA
----
  part_a_data\subject-<ID>_part-a_run-1.csv

The CSV records condition, distractors, cue stream/color, line angle, dot
position/quadrant, comparison type, change magnitude, feature distance,
N-1/N-2 overlap and lure status, expected and actual mouse response, N-back
accuracy, omission and reaction time, game outcome and crystal RT, asteroid
parameters, and the calibrated level.

Run analyze_part_a.R to verify the design and create condition, comparison-type,
change-magnitude, and 30-second performance summaries.
