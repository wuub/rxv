test: 
	flake8
	isort --recursive --check-only --diff
	tox

isort:
	isort --recursive --apply

clean:
	rm -rf .virtualenv dist build *.egg-info

.PHONY: clean isort test