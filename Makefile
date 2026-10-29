SET ?= l06_security
PROFILE ?= lesson-06
STAND_DIR ?= ../paypilot-stand-shared

.PHONY: eval dry-run check replay
eval:
	STAND_DIR="$(STAND_DIR)" docker compose run --rm eval --set "$(SET)" --profile "$(PROFILE)" --gate all --traces

dry-run:
	STAND_DIR="$(STAND_DIR)" docker compose run --rm eval --set "$(SET)" --gate all --dry-run

check:
	STAND_DIR="$(STAND_DIR)" docker compose run --rm eval python /course/homework/scripts/check_oracles.py

replay:
	STAND_DIR="$(STAND_DIR)" docker compose run --rm eval python /course/homework/scripts/replay_checks.py
