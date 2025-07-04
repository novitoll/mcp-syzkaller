SHELL := /bin/bash

.PHONY: init
init:
	uv sync

.PHONY: run
run:
	python main.py