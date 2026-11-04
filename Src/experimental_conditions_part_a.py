"""Feedback-controlled Asteroid Impact arithmetic-answer 1-back experiment."""

import csv
import math
import os
import random
from datetime import datetime

import pygame


CONDITION_TYPES = ("control", "cognitive", "perceptual", "combined")
COMPARISON_TYPES = ("exact_match", "answer_difference")
ANSWER_VALUES = tuple(range(2, 13))
CUE_COLORS = (
    ("blue", (37, 150, 207)),
    ("green", (73, 168, 72)),
)


def condition_cells(condition):
    return {
        "practice": [("none", "none")],
        "calibration": [("none", "none")],
        "control": [("none", "none")],
        "cognitive": [("none", "text_notification"), ("none", "buffering")],
        "perceptual": [("red_banner", "none"), ("flashing_banner", "none")],
        "combined": [
            ("red_banner", "text_notification"),
            ("flashing_banner", "buffering"),
            ("red_banner", "buffering"),
            ("flashing_banner", "text_notification"),
        ],
    }[condition]


def level_parameters(level):
    level = max(1, min(10, int(level)))
    counts = [1, 1, 2, 2, 3, 3, 4, 5, 6, 7]
    sizes = ["small", "small", "small", "small", "small", "medium", "medium", "medium", "large", "large"]
    speeds = ["veryslow", "slow", "slow", "medium", "medium", "medium", "medium", "fast", "extreme", "plaid"]
    return {
        "asteroid_count": counts[level - 1],
        "asteroid_size_class": sizes[level - 1],
        "asteroid_speed_class": speeds[level - 1],
    }


def _seed_for(subject_number, suffix=""):
    text = str(subject_number) + str(suffix)
    return 8117 + sum((index + 1) * ord(char) for index, char in enumerate(text))


def _balanced_comparison_plan(subject_number, condition, scored_count):
    """Balance trial types and small/large changes, with no long response runs."""
    rng = random.Random(_seed_for(subject_number, "comparison-plan-%s-%d" % (condition, scored_count)))
    base, remainder = divmod(scored_count, len(COMPARISON_TYPES))
    counts = {name: base + int(index < remainder) for index, name in enumerate(COMPARISON_TYPES)}
    plan = []
    for comparison_type in COMPARISON_TYPES:
        count = counts[comparison_type]
        if comparison_type == "exact_match":
            plan.extend([(comparison_type, "none")] * count)
        else:
            small = count // 2
            plan.extend([(comparison_type, "small")] * small)
            plan.extend([(comparison_type, "large")] * (count - small))
    for _ in range(5000):
        rng.shuffle(plan)
        responses = [item[0] == "exact_match" for item in plan]
        longest = 1
        run = 1
        for index in range(1, len(responses)):
            run = run + 1 if responses[index] == responses[index - 1] else 1
            longest = max(longest, run)
        if longest <= 3:
            return list(plan)
    return list(plan)


def _feature_overlap(first, second):
    """One if numerical answers match, regardless of equation wording."""
    return int(first["answer"] == second["answer"])


def _equation_for_answer(answer, rng, avoid=()):
    """Generate a nonnegative, single-digit addition/subtraction equation."""
    candidates = []
    for left in range(1, 10):
        for right in range(1, 10):
            if left + right == answer:
                candidates.append((left, "+", right))
            if left - right == answer:
                candidates.append((left, "-", right))
    if not candidates:
        raise ValueError("No equation for answer %s" % answer)
    alternatives = [c for c in candidates if c not in avoid]
    return rng.choice(alternatives or candidates)


def make_pattern_schedule(subject_number, condition, trial_count):
    """Balanced arithmetic-answer 1-back, first trial unscored."""
    if trial_count < 2:
        raise ValueError("A 1-back block requires at least two trials.")
    plan = _balanced_comparison_plan(subject_number, condition, trial_count - 1)
    rng = random.Random(_seed_for(subject_number, "arithmetic-1back-" + condition))
    answers = [rng.choice(ANSWER_VALUES)]
    for comparison_type, magnitude in plan:
        if comparison_type == "exact_match":
            answers.append(answers[-1])
        else:
            answers.append(rng.choice([v for v in ANSWER_VALUES if v != answers[-1]]))
    patterns = []
    for index, answer in enumerate(answers):
        avoid = [patterns[-1]["equation_tuple"]] if index and answer == answers[index-1] else []
        equation_tuple = _equation_for_answer(answer, rng, avoid)
        cue_name, cue_rgb = CUE_COLORS[index % 2]
        patterns.append(dict(answer=answer, equation_tuple=equation_tuple,
                             equation="%d %s %d" % equation_tuple,
                             comparison_type="memory_item" if not index else plan[index-1][0],
                             change_magnitude="none" if not index or plan[index-1][0] == "exact_match" else "not_applicable",
                             cue_stream=index % 2 + 1, cue_color=cue_name, cue_rgb=cue_rgb))
    return patterns


# Load schedules are explicit pilot parameters, not psychometrically validated intensities.
# Each staircase updates after five SCORED 1-back trials within its own condition.
LOAD_WINDOW = 5
LOAD_CRITERION = 0.80
LOAD_MIN, LOAD_MAX = 1, 5


class ConditionController(object):
    FIELDNAMES = [
        "timestamp_utc", "subject_number", "subject_run", "session_phase",
        "condition", "condition_order", "is_practice", "trial_in_condition",
        "scored_trial_in_condition", "global_trial", "global_scored_trial",
        "trial_type", "perceptual_distractor", "cognitive_distractor",
        "pattern_id", "cue_stream", "cue_color", "equation", "numerical_answer",
        "comparison_type", "change_magnitude",
        "answer_difference_from_1back", "n1_answer_match", "n2_answer_match",
        "nback_n", "nback_scored", "nback_target", "nback_expected_response",
        "nback_response", "nback_correct", "nback_rt_ms", "nback_omission",
        "pattern_display_ms", "level_before", "level_after", "game_correct",
        "game_outcome", "crystal_rt_ms", "crystals_collected", "asteroid_collisions",
        "performance_component", "block_elapsed_ms", "analysis_window_30s",
        "asteroid_count", "asteroid_size_class", "asteroid_speed_class",
        "powerups_enabled", "stop_reason", "protocol_version",
        "cognitive_load_before", "cognitive_load_after", "perceptual_load_before", "perceptual_load_after",
        "staircase_window_accuracy", "staircase_updated", "staircase_reversal", "staircase_dimension",
    ]

    NOTIFICATIONS = [
        ("Messages", "Alex: Are you still coming tonight?"),
        ("Calendar", "Meeting moved to 3:30 PM"),
        ("Social", "3 new reactions to your post"),
        ("Mail", "New sign-in detected on your account"),
        ("News", "Breaking update: tap to read more"),
        ("Photos", "A new memory is ready to view"),
    ]

    def __init__(self, screen, settings, subject_number="", subject_run="", level_provider=None):
        self.screen = screen
        self.settings = dict(settings or {})
        self.condition = self.settings.get("name", "control").lower()
        if self.condition not in ("practice", "calibration") + CONDITION_TYPES:
            raise ValueError("Unknown Part A condition: %s" % self.condition)
        self.subject_number = str(subject_number)
        self.subject_run = str(subject_run or "1")
        self.session_phase = "part_a"
        self.level_provider = level_provider
        self.condition_order = 0 if self.condition in ("practice", "calibration") else CONDITION_TYPES.index(self.condition) + 1
        self.trial_count = int(self.settings.get("trial_count", 43))
        self.pattern_display_ms = int(self.settings.get("crystal_activation_delay_ms", 5000))
        self.freeze_difficulty = self.condition in CONDITION_TYPES or self.condition == "practice"
        provider_level = getattr(getattr(self.level_provider, "level_list", None), "level_score", 2)
        self.current_level = max(1, min(10, int(provider_level) + 1))
        self.patterns = make_pattern_schedule(self.subject_number, self.condition, self.trial_count)
        cells = condition_cells(self.condition)
        self.trials = [cells[index % len(cells)] for index in range(self.trial_count)]
        globals_ = self.level_provider.game_globals if self.level_provider else {}
        self.cognitive_load = int(globals_.get("cognitive_load", 2))
        self.perceptual_load = int(globals_.get("perceptual_load", 2))
        self.load_window = []
        self.last_direction = 0

        self.trial_index = 0
        self.trial_elapsed_ms = 0
        self.block_elapsed_ms = 0
        self.crystal_rt_ms = 0
        self.crystal_available = False
        self.response_key = ""
        self.response_correct = ""
        self.response_rt_ms = ""
        self.finished = False
        self.stop_reason = ""
        self.consecutive_correct = 0

        output_directory = self.settings.get("output_directory", "part_a_data")
        if not os.path.isabs(output_directory):
            output_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_directory)
        os.makedirs(output_directory, exist_ok=True)
        filename = "subject-%s_part-a-arithmetic-1back-run-%s.csv" % (self.subject_number, self.subject_run)
        self.filename = os.path.join(output_directory, filename)
        exists = os.path.exists(self.filename) and os.path.getsize(self.filename) > 0
        self.file = open(self.filename, "a", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.file, fieldnames=self.FIELDNAMES)
        if not exists:
            self.writer.writeheader()
            self.file.flush()

        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 23)
        print("Part A data file:", self.filename)

    @property
    def current_types(self):
        if self.finished:
            return ("none", "none")
        perceptual, cognitive = self.trials[self.trial_index]
        return (perceptual if self._distractor_active(self.perceptual_load, "perceptual") else "none",
                cognitive if self._distractor_active(self.cognitive_load, "cognitive") else "none")

    def _distractor_active(self, level, dimension):
        if dimension == "cognitive" and self.condition not in ("cognitive", "combined"):
            return False
        if dimension == "perceptual" and self.condition not in ("perceptual", "combined"):
            return False
        if level <= 1:
            return False
        # A deterministic event schedule, increasing with load. Higher loads
        # increase event duty cycle; all load parameters logged per trial.
        period = {2: 4, 3: 3, 4: 2, 5: 1}[level]
        return self.trial_index % period == 0

    def _nback_design(self):
        if self.trial_index < 1:
            return False, False, ""
        target = self.patterns[self.trial_index]["comparison_type"] == "exact_match"
        return True, target, "right_click" if target else "left_click"

    def update(self, millis, frame_outbound_triggers, events=None):
        if self.finished:
            return
        self.trial_elapsed_ms += millis
        self.block_elapsed_ms += millis
        scored, target, expected_response = self._nback_design()
        if scored and not self.response_key and self.trial_elapsed_ms <= self.pattern_display_ms:
            for event in events or []:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                    self.response_key = "right_click" if event.button == 3 else "left_click"
                    self.response_correct = int(self.response_key == expected_response)
                    self.response_rt_ms = self.trial_elapsed_ms
                    break
        if "experimental_crystal_available" in frame_outbound_triggers:
            self.crystal_available = True
            self.crystal_rt_ms = 0
        elif self.crystal_available:
            self.crystal_rt_ms += millis
        if "game_crystal_collected" in frame_outbound_triggers:
            self._finish_trial(True, "crystal_collected")
        elif "game_death" in frame_outbound_triggers:
            self._finish_trial(False, "asteroid_collision")

    def _finish_trial(self, game_correct, outcome):
        before = self.current_level
        if self.freeze_difficulty:
            after = before
        elif game_correct:
            self.consecutive_correct += 1
            if self.consecutive_correct >= 2:
                after = min(10, before + 1)
                self.consecutive_correct = 0
            else:
                after = before
        else:
            self.consecutive_correct = 0
            after = max(1, before - 1)

        scored, target, expected_response = self._nback_design()
        if scored and self.response_key == "":
            self.response_correct = 0
        completed = self.trial_index + 1
        scored_trial = completed - 1 if scored else 0
        perceptual, cognitive = self.current_types
        stop_reason = "fixed_trial_count_complete" if completed >= self.trial_count else ""
        experimental = self.condition in CONDITION_TYPES
        global_trial = (self.condition_order - 1) * self.trial_count + completed if experimental else 0
        global_scored = (self.condition_order - 1) * (self.trial_count - 1) + scored_trial if experimental and scored else 0
        pattern = self.patterns[self.trial_index]
        n1_overlap = _feature_overlap(pattern, self.patterns[self.trial_index - 1]) if scored else ""
        n2_overlap = _feature_overlap(pattern, self.patterns[self.trial_index - 2]) if self.trial_index >= 2 else ""
        cognitive_before = self.cognitive_load
        perceptual_before = self.perceptual_load
        window_accuracy = ""
        staircase_updated = 0
        reversal = 0
        dimension = self.condition if self.condition in ("cognitive", "perceptual") else "none"
        # The combined block uses both separately calibrated load levels,
        # held fixed to avoid conflating the effects of the two dimensions.
        if scored and dimension != "none":
            self.load_window.append(int(self.response_correct))
            if len(self.load_window) >= LOAD_WINDOW:
                window_accuracy = sum(self.load_window) / float(len(self.load_window))
                direction = 1 if window_accuracy >= LOAD_CRITERION else -1
                attr = "cognitive_load" if dimension == "cognitive" else "perceptual_load"
                old_load = getattr(self, attr)
                new_load = max(LOAD_MIN, min(LOAD_MAX, old_load + direction))
                setattr(self, attr, new_load)
                staircase_updated = int(new_load != old_load)
                reversal = int(staircase_updated and self.last_direction != 0 and direction != self.last_direction)
                if staircase_updated:
                    self.last_direction = direction
                self.load_window = []
        row = {
            "timestamp_utc": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            "subject_number": self.subject_number, "subject_run": self.subject_run,
            "session_phase": self.session_phase, "condition": self.condition,
            "condition_order": self.condition_order, "is_practice": int(self.condition == "practice"),
            "trial_in_condition": completed, "scored_trial_in_condition": scored_trial if scored else "",
            "global_trial": global_trial, "global_scored_trial": global_scored,
            "trial_type": "%s+%s" % (perceptual, cognitive),
            "perceptual_distractor": perceptual, "cognitive_distractor": cognitive,
            "pattern_id": "EQUATION_%03d" % completed,
            "cue_stream": pattern["cue_stream"], "cue_color": pattern["cue_color"],
            "equation": pattern["equation"],
            "numerical_answer": pattern["answer"],
            "comparison_type": pattern["comparison_type"],
            "change_magnitude": pattern["change_magnitude"],
            "answer_difference_from_1back": abs(pattern["answer"] - self.patterns[self.trial_index - 1]["answer"]) if scored else "",
            "n1_answer_match": n1_overlap, "n2_answer_match": n2_overlap,
            "nback_n": 1, "nback_scored": int(scored),
            "nback_target": int(target) if scored else "",
            "nback_expected_response": expected_response, "nback_response": self.response_key,
            "nback_correct": self.response_correct if scored else "",
            "nback_rt_ms": self.response_rt_ms if scored else "",
            "nback_omission": int(scored and not self.response_key),
            "pattern_display_ms": self.pattern_display_ms,
            "level_before": before, "level_after": after,
            "game_correct": int(game_correct), "game_outcome": outcome,
            "crystal_rt_ms": self.crystal_rt_ms if self.crystal_available else "",
            "crystals_collected": int(game_correct), "asteroid_collisions": int(not game_correct),
            "performance_component": int(game_correct) / float(1 + int(not game_correct)),
            "block_elapsed_ms": self.block_elapsed_ms,
            "analysis_window_30s": int(self.block_elapsed_ms // 30000) + 1,
            "powerups_enabled": 0, "stop_reason": stop_reason,
            "cognitive_load_before": cognitive_before, "cognitive_load_after": self.cognitive_load,
            "perceptual_load_before": perceptual_before, "perceptual_load_after": self.perceptual_load,
            "staircase_window_accuracy": window_accuracy, "staircase_updated": staircase_updated,
            "staircase_reversal": reversal, "staircase_dimension": dimension,
            "protocol_version": "asteroid-feedback-controlled-arithmetic-answer-1back-8sec-part-a-v8",
        }
        row.update(level_parameters(before))
        self.writer.writerow(row)
        self.file.flush()

        self.trial_index += 1
        self.current_level = after
        self.trial_elapsed_ms = 0
        self.crystal_rt_ms = 0
        self.crystal_available = False
        self.response_key = ""
        self.response_correct = ""
        self.response_rt_ms = ""
        if completed >= self.trial_count:
            if self.condition in ("cognitive", "perceptual"):
                self.level_provider.game_globals[self.condition + "_load"] = getattr(self, self.condition + "_load")
            if self.condition == "calibration":
                self.level_provider.game_globals["calibrated_level"] = self.current_level
            self.finished = True
            self.stop_reason = stop_reason

    def _occupied_rects(self):
        occupied = []
        try:
            occupied.append(self.level_provider.cursor.rect.inflate(60, 60))
        except Exception:
            pass
        try:
            for target in self.level_provider.target_list:
                if target.active:
                    occupied.append(target.rect.inflate(40, 40))
        except Exception:
            pass
        return occupied

    def _safe_rect(self, width, height):
        sw, sh = self.screen.get_size()
        candidates = [
            ((sw - width) // 2, 82), ((sw - width) // 2, sh - height - 82),
            (20, (sh - height) // 2), (sw - width - 20, (sh - height) // 2),
        ]
        occupied = self._occupied_rects()
        for x, y in candidates:
            rect = pygame.Rect(x, y, width, height)
            if not any(rect.colliderect(item) for item in occupied):
                return rect
        return pygame.Rect(candidates[0], (width, height))

    def draw(self):
        if self.finished:
            return
        perceptual, cognitive = self.current_types
        if perceptual == "red_banner":
            self._draw_visual_banner(False)
            self._draw_peripheral_noise(False)
        elif perceptual == "flashing_banner":
            self._draw_visual_banner(True)
            self._draw_peripheral_noise(True)
        if cognitive == "text_notification":
            self._draw_text_notification()
        elif cognitive == "buffering":
            self._draw_buffering()
        if self.trial_elapsed_ms <= self.pattern_display_ms:
            self._draw_pattern_card()

    def _draw_pattern_card(self):
        width, height = min(620, self.screen.get_width() - 40), 250
        rect = self._safe_rect(width, height)
        card = pygame.Surface((width, height), pygame.SRCALPHA)
        card.fill((247, 248, 252, 248))
        pattern = self.patterns[self.trial_index]
        equation_font = pygame.font.Font(None, 88)
        equation = equation_font.render(pattern["equation"] + " = ?", True, (43, 47, 62))
        card.blit(equation, equation.get_rect(center=(width // 2, 94)))
        scored, target, expected = self._nback_design()
        if scored:
            instruction = "Same ANSWER as previous trial? Right=YES  Left=NO"
        else:
            instruction = "Solve and remember the answer - no response yet"
        prompt = self.small_font.render(instruction, True, (55, 62, 82))
        card.blit(prompt, prompt.get_rect(center=(width // 2, 190)))
        if self.response_key:
            recorded = self.small_font.render("Response recorded", True, (35, 125, 70))
            card.blit(recorded, recorded.get_rect(center=(width // 2, 222)))
        pygame.draw.rect(card, pattern["cue_rgb"], card.get_rect(), 5, border_radius=10)
        self.screen.blit(card, rect.topleft)

    def _draw_visual_banner(self, flashing):
        pulse = (self.trial_elapsed_ms // max(70, 310 - 45 * self.perceptual_load)) % 2 == 0
        alpha = 225 if (not flashing or pulse) else 85
        banner = pygame.Surface((self.screen.get_width(), 54), pygame.SRCALPHA)
        banner.fill((235, 30, 55, alpha))
        self.screen.blit(banner, (0, 0))

    def _draw_peripheral_noise(self, flashing):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        occupied = self._occupied_rects()
        phase = (self.trial_elapsed_ms // 120) % 2
        alpha = min(230, 45 + self.perceptual_load * 25) if (not flashing or phase == 0) else 210
        sw, sh = self.screen.get_size()
        for x in range(18, sw, max(22, 95 - 13 * self.perceptual_load)):
            for y in range(62, sh, max(22, 90 - 12 * self.perceptual_load)):
                rect = pygame.Rect(x, y, 18, 7)
                if any(rect.colliderect(item) for item in occupied):
                    continue
                color = (255, 45, 65, alpha) if (x // 62 + y // 56 + phase) % 2 else (255, 215, 40, alpha)
                pygame.draw.rect(overlay, color, rect, border_radius=3)
        self.screen.blit(overlay, (0, 0))

    def _draw_text_notification(self):
        elapsed = self.trial_elapsed_ms
        duration = {1: 0, 2: 1100, 3: 1900, 4: 3100, 5: 5000}[self.cognitive_load]
        if elapsed > duration:
            return
        width = min(440, self.screen.get_width() - 30)
        rect = pygame.Rect(self.screen.get_width() - width - 20, 90, width, 90)
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        surface.fill((244, 245, 250, 235))
        source, message = self.NOTIFICATIONS[self.trial_index % len(self.NOTIFICATIONS)]
        surface.blit(self.small_font.render(source, True, (35, 45, 65)), (14, 10))
        surface.blit(self.small_font.render(message[:39], True, (35, 45, 65)), (14, 44))
        self.screen.blit(surface, rect.topleft)

    def _draw_buffering(self):
        duration = {1: 0, 2: 1100, 3: 1900, 4: 3100, 5: 5000}[self.cognitive_load]
        if self.trial_elapsed_ms > duration:
            return
        x, y = self.screen.get_width() - 90, 140
        phase = self.trial_elapsed_ms / 160.0
        for i in range(8):
            theta = (i + phase) * math.pi / 4
            pygame.draw.circle(self.screen, (70, 110, 180),
                               (int(x + 23 * math.cos(theta)), int(y + 23 * math.sin(theta))), 4)

    def close(self):
        if not self.file.closed:
            self.file.close()
