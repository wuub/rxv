# SPDX-FileCopyrightText: 2013 Joanna Tustanowska & Wojciech Bederski
#
# SPDX-License-Identifier: BSD-3-Clause

test: 
	flake8
	isort --recursive --check-only --diff
	tox

isort:
	isort --recursive --apply

clean:
	rm -rf .virtualenv dist build *.egg-info

.PHONY: clean isort test