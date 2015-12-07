.PHONY: clean clean-build clean-pyc clean-test clean-docs lint test test-all coverage coverage docs servedocs release dist install register requirements
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

BROWSER 		:= python -c "$$BROWSER_PYSCRIPT"
DOCSBUILDDIR	= docs/_build
DOCSSOURCEDIR	= docs/source

help:
	@echo "clean			remove all build, test, coverage and Python artifacts"
	@echo "clean-build		remove build artifacts"
	@echo "clean-pyc		remove Python file artifacts"
	@echo "clean-test		remove test and coverage artifacts"
	@echo "clean-docs		remove autogenerated docs files"
	@echo "lint				check style with flake8"
	@echo "test				run tests quickly with the default Python"
	@echo "test-all			run tests on every Python version with tox"
	@echo "coverage			check code coverage quickly with the default Python"
	@echo "docs				generate Sphinx HTML documentation, including API docs"
	@echo "servedocs		semi-live edit docs"
	@echo "release			package and upload a release"
	@echo "dist				package"
	@echo "install			install the package to the active Python's site-packages"
	@echo "register			update pypi"
	@echo "requirements		update and install requirements"

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr $(DOCSBUILDDIR)/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

clean-docs:
	rm -f $(DOCSSOURCEDIR)/cache_requests.rst
	rm -f $(DOCSSOURCEDIR)/modules.rst
	$(MAKE) -C docs clean

lint:
	flake8 cache_requests tests

test: lint
	python setup.py test

test-all: lint
	tox

coverage:
	coverage run --source cache_requests setup.py test
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html
	$(MAKE) -C docs coverage

docs: clean-docs
	# -P include private; -M modules first (before submodules); -T No TOC
	sphinx-apidoc -PMT --output-dir=$(DOCSSOURCEDIR)/ cache_requests
	$(MAKE) -C docs html
	$(BROWSER) $(DOCSBUILDDIR)/html/index.html

servedocs: docs
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

release: clean docs
	python setup.py sdist upload
	python setup.py bdist_wheel upload

dist: clean docs
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean
	python setup.py install

register:
	python setup.py register

requirements:
	pip install --quiet pip-tools
	pip-compile requirements_dev.in > /dev/null
	pip-compile requirements.in > /dev/null
	pip-sync requirements_dev.txt > /dev/null
	pip install --quiet -r requirements.txt
	pip wheel --quiet -r requirements_dev.txt
	pip wheel --quiet -r requirements.txt
	git diff requirements.txt requirements_dev.txt > .requirements.diff
