.PHONY: research-test research-plan bootstrap-preview

PYTHON ?= .venv/bin/python

research-test:
	$(PYTHON) -m pytest ideation/tests -q

research-plan:
	.venv/bin/researchctl plan

bootstrap-preview:
	scripts/bootstrap-node.sh --dry-run
