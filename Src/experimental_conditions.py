"""Balanced load-condition trials and staircase-ready trial logging.

This module is deliberately independent of Asteroid Impact's frame logger.  It
writes one row per experimental trial, which is the appropriate unit for a
psychometric/staircase analysis.
"""

import csv
import os
import random

import pygame

from resources import load_sound


CONDITION_TYPES = ("perceptual", "cognitive", "mixed")


class Staircase(object):
    """Bounded one-up/one-down staircase on a common 1--10 intensity scale."""

    def __init__(self, start=5, minimum=1, maximum=10, step_up=1, step_down=1):
        self.level = int(start)
        self.minimum = int(minimum)
        self.maximum = int(maximum)
        self.step_up = int(step_up)
        self.step_down = int(step_down)

    def update(self, successful):
        before = self.level
        # If primary-task performance survives the distractor, make the next
        # distractor harder; otherwise make it easier.
        if successful:
            self.level = min(self.maximum, self.level + self.step_up)
            direction = "up" if self.level != before else "ceiling"
        else:
            self.level = max(self.minimum, self.level - self.step_down)
            direction = "down" if self.level != before else "floor"
        return direction


def balanced_trial_types(condition, trial_count, rng):
    """Return a shuffled list with subtype counts differing by at most one."""
    if condition == "perceptual":
        cells = [("visual_banner", "none"), ("sound", "none")]
    elif condition == "cognitive":
        cells = [("none", "text_message"), ("none", "buffering")]
    elif condition == "mixed":
        cells = [
            ("visual_banner", "text_message"),
            ("visual_banner", "buffering"),
            ("sound", "text_message"),
            ("sound", "buffering"),
        ]
    else:
        raise ValueError("Unknown condition: %s" % condition)

    trials = [cells[i % len(cells)] for i in range(int(trial_count))]
    rng.shuffle(trials)
    return trials


def intensity_parameters(level):
    """Map the shared ordinal level to explicit, reproducible parameters."""
    level = max(1, min(10, int(level)))
    return {
        "banner_alpha": int(round(70 + (level - 1) * (185.0 / 9.0))),
        "banner_height_px": int(round(54 + (level - 1) * 7)),
        "sound_volume": round(0.10 + (level - 1) * 0.09, 3),
        "text_word_count": int(4 + (level - 1) * 2),
        "stimulus_duration_ms": int(600 + (level - 1) * 150),
        "buffer_duration_ms": int(500 + (level - 1) * 250),
        "buffer_opacity": int(round(55 + (level - 1) * (145.0 / 9.0))),
    }


class ConditionController(object):
    """Present balanced distractors and save one staircase row per trial."""

    FIELDNAMES = [
        "subject_number", "subject_run", "condition", "trial_number",
        "perceptual_stimulus", "cognitive_stimulus", "intensity_level",
        "banner_alpha", "banner_height_px", "sound_volume",
        "text_word_count", "stimulus_duration_ms", "buffer_duration_ms",
        "buffer_opacity", "targets_collected", "deaths", "successful",
        "staircase_direction", "next_intensity_level", "trial_duration_ms",
    ]

    MESSAGES = [
        "New message: Are you still there? Please check this update when you can.",
        "Reminder: A new item needs your attention before the session is complete.",
        "System notice: Your recent activity has not yet been saved to the cloud.",
        "Incoming message: Someone mentioned you in an important group conversation.",
    ]

    def __init__(self, screen, settings, subject_number="", subject_run=""):
        self.screen = screen
        self.settings = dict(settings or {})
        self.condition = self.settings.get("name", "perceptual").lower()
        if self.condition not in CONDITION_TYPES:
            raise ValueError("experimental_condition.name must be perceptual, cognitive, or mixed")

        self.trial_count = int(self.settings.get("trial_count", 40))
        self.trial_duration_ms = int(self.settings.get("trial_duration_ms", 6000))
        self.stimulus_onset_ms = int(self.settings.get("stimulus_onset_ms", 1000))
        seed = int(self.settings.get("random_seed", 2026))
        # Including the subject identifier gives reproducible, participant-specific orders.
        subject_seed = sum(ord(c) for c in str(subject_number))
        self.rng = random.Random(seed + subject_seed)
        self.trials = balanced_trial_types(self.condition, self.trial_count, self.rng)
        self.staircase = Staircase(
            start=self.settings.get("start_intensity", 5),
            minimum=self.settings.get("minimum_intensity", 1),
            maximum=self.settings.get("maximum_intensity", 10),
            step_up=self.settings.get("step_up", 1),
            step_down=self.settings.get("step_down", 1),
        )

        self.subject_number = str(subject_number)
        self.subject_run = str(subject_run)
        output_directory = self.settings.get("output_directory", "condition_data")
        os.makedirs(output_directory, exist_ok=True)
        safe_subject = self.subject_number or "anonymous"
        safe_run = self.subject_run or "1"
        self.filename = os.path.join(
            output_directory,
            "%s_run-%s_%s_trials.csv" % (safe_subject, safe_run, self.condition),
        )
        self.file = open(self.filename, "w", newline="")
        self.writer = csv.DictWriter(self.file, fieldnames=self.FIELDNAMES)
        self.writer.writeheader()

        self.trial_index = 0
        self.trial_elapsed_ms = 0
        self.current_level = self.staircase.level
        self.current_params = intensity_parameters(self.current_level)
        self.targets_this_trial = 0
        self.deaths_this_trial = 0
        self.sound_played = False
        self.finished = False

        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 24)
        self.banner_images = [
            pygame.image.load(os.path.join("data", name)).convert_alpha()
            for name in ("notification_red.png", "notification_yellow.png", "notification_magenta.png")
        ]
        self.notification_sounds = [
            load_sound(name) for name in
            ("notification_low.wav", "notification_mid.wav", "notification_high.wav")
        ]

    @property
    def current_types(self):
        if self.finished:
            return ("none", "none")
        return self.trials[self.trial_index]

    def update(self, millis, frame_outbound_triggers):
        if self.finished:
            return
        self.trial_elapsed_ms += millis
        self.targets_this_trial += frame_outbound_triggers.count("game_crystal_collected")
        self.deaths_this_trial += frame_outbound_triggers.count("game_death")

        perceptual, cognitive = self.current_types
        if (perceptual == "sound" and not self.sound_played and
                self.trial_elapsed_ms >= self.stimulus_onset_ms):
            sound_index = min(2, (self.current_level - 1) // 4)
            sound = self.notification_sounds[sound_index]
            sound.set_volume(self.current_params["sound_volume"])
            sound.play()
            self.sound_played = True

        if self.trial_elapsed_ms >= self.trial_duration_ms:
            self._finish_trial()

    def _finish_trial(self):
        minimum_targets = int(self.settings.get("success_minimum_targets", 1))
        successful = self.targets_this_trial >= minimum_targets and self.deaths_this_trial == 0
        direction = self.staircase.update(successful)
        perceptual, cognitive = self.current_types
        row = {
            "subject_number": self.subject_number,
            "subject_run": self.subject_run,
            "condition": self.condition,
            "trial_number": self.trial_index + 1,
            "perceptual_stimulus": perceptual,
            "cognitive_stimulus": cognitive,
            "intensity_level": self.current_level,
            "targets_collected": self.targets_this_trial,
            "deaths": self.deaths_this_trial,
            "successful": int(successful),
            "staircase_direction": direction,
            "next_intensity_level": self.staircase.level,
            "trial_duration_ms": self.trial_duration_ms,
        }
        row.update(self.current_params)
        self.writer.writerow(row)
        self.file.flush()

        self.trial_index += 1
        if self.trial_index >= self.trial_count:
            self.finished = True
            return
        self.trial_elapsed_ms = 0
        self.current_level = self.staircase.level
        self.current_params = intensity_parameters(self.current_level)
        self.targets_this_trial = 0
        self.deaths_this_trial = 0
        self.sound_played = False

    def draw(self):
        if self.finished or self.trial_elapsed_ms < self.stimulus_onset_ms:
            return
        perceptual, cognitive = self.current_types
        elapsed_since_onset = self.trial_elapsed_ms - self.stimulus_onset_ms

        if perceptual == "visual_banner" and elapsed_since_onset < self.current_params["stimulus_duration_ms"]:
            image_index = min(2, (self.current_level - 1) // 4)
            banner = self.banner_images[image_index]
            height = self.current_params["banner_height_px"]
            width = min(self.screen.get_width() - 24, int(banner.get_width() * height / banner.get_height()))
            banner = pygame.transform.smoothscale(banner, (width, height))
            banner.set_alpha(self.current_params["banner_alpha"])
            self.screen.blit(banner, ((self.screen.get_width() - width) // 2, 12))

        if cognitive == "text_message" and elapsed_since_onset < self.current_params["stimulus_duration_ms"]:
            words = self.MESSAGES[self.trial_index % len(self.MESSAGES)].split()
            requested = self.current_params["text_word_count"]
            message = " ".join((words * 5)[:requested])
            self._draw_text_box(message)

        if cognitive == "buffering" and elapsed_since_onset < self.current_params["buffer_duration_ms"]:
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, self.current_params["buffer_opacity"]))
            self.screen.blit(overlay, (0, 0))
            center = self.screen.get_rect().center
            pygame.draw.circle(self.screen, (230, 230, 230), center, 32, 6)
            angle = (self.trial_elapsed_ms // 80) % 12
            end = (center[0] + int(25 * __import__("math").cos(angle * 0.52)),
                   center[1] + int(25 * __import__("math").sin(angle * 0.52)))
            pygame.draw.line(self.screen, (255, 90, 60), center, end, 6)
            label = self.font.render("Buffering...", True, (255, 255, 255))
            self.screen.blit(label, label.get_rect(center=(center[0], center[1] + 60)))

    def _draw_text_box(self, message):
        width = min(560, self.screen.get_width() - 40)
        box = pygame.Surface((width, 96), pygame.SRCALPHA)
        box.fill((245, 245, 250, 235))
        title = self.small_font.render("NEW MESSAGE", True, (80, 70, 130))
        body = self.small_font.render(message, True, (20, 20, 30))
        box.blit(title, (14, 12))
        box.blit(body, (14, 48))
        self.screen.blit(box, ((self.screen.get_width() - width) // 2, self.screen.get_height() - 116))

    def close(self):
        if not self.file.closed:
            self.file.close()

