"""Small launcher for the three-condition Asteroid Impact experiment."""

import os
import subprocess
import sys


def main():
    subject = input("Subject number: ").strip() or "anonymous"
    run = input("Run number [1]: ").strip() or "1"
    os.makedirs("logs", exist_ok=True)
    command = [
        sys.executable, "game.py",
        "--subject-number", subject,
        "--subject-run", run,
        "--script-json", "experimental_conditions.json",
        "--log-filename", "logs/%s_run-%s_frames.csv" % (subject, run),
        "--reaction-log-filename", "logs/%s_run-%s_reactions.csv" % (subject, run),
        "--log-overwrite", "true",
        "--display-mode", "windowed",
        "--music-volume", "0.0",
        "--effects-volume", "1.0",
    ]
    raise SystemExit(subprocess.call(command))


if __name__ == "__main__":
    main()
