library(tidyverse)

# Select any CSV inside the part_a_data folder.
data_dir <- dirname(file.choose())
files <- list.files(data_dir, pattern = "_part-a-arithmetic-1back-run-.*\\.csv$", full.names = TRUE)
stopifnot(length(files) > 0)
trials <- purrr::map_dfr(files, readr::read_csv, show_col_types = FALSE)
experimental <- trials |> filter(condition %in% c("control", "cognitive", "perceptual", "combined"))

trial_check <- experimental |>
  group_by(subject_number, subject_run, condition) |>
  summarise(presentations = n(), scored_trials = sum(nback_scored == 1),
            .groups = "drop")
print(trial_check)
stopifnot(all(trial_check$presentations == 43), all(trial_check$scored_trials == 42))

condition_summary <- experimental |>
  group_by(subject_number, subject_run, condition) |>
  summarise(n_scored = sum(nback_scored == 1),
            accuracy = mean(nback_correct[nback_scored == 1], na.rm = TRUE),
            correct_rt_ms = mean(nback_rt_ms[nback_scored == 1 & nback_correct == 1], na.rm = TRUE),
            omissions = sum(nback_omission, na.rm = TRUE),
            crystals = sum(crystals_collected), collisions = sum(asteroid_collisions),
            asteroid_level = first(level_before),
            final_cognitive_load = last(cognitive_load_after),
            final_perceptual_load = last(perceptual_load_after), .groups = "drop")

staircase_updates <- experimental |>
  filter(staircase_updated == 1) |>
  select(subject_number, subject_run, condition, trial_in_condition,
         staircase_dimension, staircase_window_accuracy, staircase_reversal,
         cognitive_load_before, cognitive_load_after,
         perceptual_load_before, perceptual_load_after)

readr::write_csv(trial_check, file.path(data_dir, "part_a_design_check.csv"))
readr::write_csv(condition_summary, file.path(data_dir, "part_a_condition_summary.csv"))
readr::write_csv(staircase_updates, file.path(data_dir, "part_a_staircase_updates.csv"))
print(condition_summary)
