ASTEROID IMPACT -- ARITHMETIC 1-BACK AND THREE STAIRCASES

1-BACK: Compare numerical answers with the immediately previous trial. The
first trial of EACH block is unscored. Right-click = same; left-click = different.
Equation display = 8 seconds; 15 practice, 23 calibration, 43 per condition.

ASTEROID STAIRCASE (CALIBRATION ONLY): 10 difficulty levels; after two
consecutive crystal collections, increase one level; after one collision,
decrease one level. Calibrated difficulty is fixed for all four conditions.

COGNITIVE STAIRCASE (COGNITIVE CONDITION): 5 interference levels, starts at 2.
Every five scored 1-back trials, increase one level if accuracy >= 80%,
otherwise decrease one level. Bounds 1..5. Changes notifications and buffering.

PERCEPTUAL STAIRCASE (PERCEPTUAL CONDITION): same rule, independent state,
changing red/flashing banners and peripheral visual clutter.

COMBINED CONDITION: uses the FINAL cognitive and perceptual staircase levels
from their separate conditions, held constant. This prevents confounding
independent dimension-specific thresholds with simultaneous adaptations to
the same correctness signal. No independent combined-load threshold is measured.

CONTROL CONDITION: no distractors.

DISTRactor intensity parameters are exploratory/pilot settings. A five-trial
window and an 80% cutoff do not by themselves establish a psychometric capacity
threshold. Levels 1..5 and actual distractor occurrences are recorded per trial;
only staircase changes/reversals are logged, not a validated fitted threshold.

The experiment conditions run in fixed order: control, cognitive, perceptual,
combined. This introduces possible order/practice effects.

The game must be tested on the intended Windows/Pygame setup before collecting
data. Automated checks in this package do not replace interactive gameplay QA.

Run RUN_PART_A.bat. CSV data appear in part_a_data. R analysis:
analyze_part_a.R.
