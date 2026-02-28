"""Generate the OpenClaw skill file and recommendation summary."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.integrations.openclaw_tool import generate_skill_file
from src.config import PROJECT_ROOT
from src.utils.logging import get_logger

log = get_logger("recommendations")


def main():
    log.info("Generating OpenClaw skill file...")
    skill_dir = PROJECT_ROOT / "skills"
    skill_path = generate_skill_file(skill_dir)
    log.info(f"Skill file ready at: {skill_path}")
    log.info("Done.")


if __name__ == "__main__":
    main()
