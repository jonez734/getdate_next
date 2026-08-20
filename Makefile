PROJECT = getdate_next
OUTDIR = /srv/repo/$(PROJECT)/
VERSION = $(shell date +%Y%m%d%H%M)

PYTHON = python3
WHEEL_DIR = /tmp/$(PROJECT)-$$

.PHONY: all help clean clean-egg-info ensure-repo ensure-build-dir build version rename-sdist sign release deploy-venv deploy push tag backup

all: help

# Wipe in-tree *.egg-info/ dirs that a prior `pip install -e .` may have
# left behind. Such egg-infos bake absolute paths into SOURCES.txt and
# poison any later `python -m build`, which trips the setuptools
# "no absolute paths" guard with messages like:
#   "setup script specifies an absolute path:
#    /home/opencode/data/work/getdate_next/src/getdate_next/__init__.py"
clean-egg-info:
	-rm -rf *.egg-info src/*.egg-info

clean: clean-egg-info
	-rm -rf build build.old
	-find . -type d -name __pycache__ -exec rm -rf {} +
	-find . -type d -name .pytest_cache -exec rm -rf {} +
	-find . -type d -name .ruff_cache -exec rm -rf {} +

version:
	@echo '__version__ = "0.1.0.dev$(VERSION)"' > src/$(PROJECT)/_version.py

# Make sure build/ exists with mode 1775 (sticky + rwxrwxr-x) before
# invoking `python -m build`. Mode 1775 is intentional:
#   - sticky (t): only the owner of a file inside may delete/rename it,
#     so concurrent builds under a shared group can't stomp each other.
#   - setgid (s) is intentionally NOT set: setuptools' shutil.copystat
#     mirrors build/'s mode onto the freshly-created dist-info dir, and
#     a setgid'd dist-info EPERMs the subsequent bdist_wheel step in
#     SELinux-enforcing + NoNewPrivs containers (we lack CAP_FSETID).
#   - group write (g+w): any user in the build group can rebuild
#     without needing to chown.
# `chmod 1775` is used (rather than just `chmod g-s`) because it's
# idempotent and pins the mode even when the source tree's umask would
# otherwise drop the sticky bit on mkdir.
#
# If build/ exists but is owned by a different user (e.g. left over
# from a prior build run as a different uid), rename it out of the way
# first. Without this, the subsequent chmod fails with EPERM and the
# build aborts.
PREPARE_BUILD = \
	if [ -d build ] && [ ! -O build ]; then \
		mv build build.stale.$$ 2>/dev/null || true; \
	fi; \
	mkdir -p build && chmod 1775 build

ensure-repo:
	@stat -c '%G' /srv/repo 2>/dev/null | grep -qx repo || sudo chgrp repo /srv/repo
	@stat -c '%a' /srv/repo 2>/dev/null | grep -q '^2775$$' || sudo chmod 2775 /srv/repo

ensure-build-dir: ensure-repo
	@mkdir -p /srv/repo/$(PROJECT)/
	@stat -c '%G' /srv/repo/$(PROJECT)/ 2>/dev/null | grep -qx repo || sudo chgrp repo /srv/repo/$(PROJECT)/
	@stat -c '%a' /srv/repo/$(PROJECT)/ 2>/dev/null | grep -q '^2775$$' || sudo chmod 2775 /srv/repo/$(PROJECT)/

build: version clean-egg-info ensure-build-dir
	$(PREPARE_BUILD)
	VERSION=$(VERSION) $(PYTHON) -m build --outdir $(OUTDIR)

rename-sdist:
	@for f in $(OUTDIR)/*.tar.gz; do \
		if [ -f "$$f" ] && echo "$$f" | grep -vq '\-src\.tar\.gz' ; then \
			mv "$$f" "$${f%.tar.gz}-src.tar.gz"; \
			echo "Renamed $$f -> $${f%.tar.gz}-src.tar.gz"; \
		fi \
	done

sign:
	@for f in $(OUTDIR)/*; do \
		if [ -f "$$f" ] && [ ! -f "$$f.asc" ] && [ "$${f##*.}" != "asc" ]; then \
			gpg --armor --detach-sign "$$f"; \
			echo "Signed $$f"; \
		fi \
	done

release: clean version build rename-sdist sign

# Non-sudo: build a getdate_next wheel and pip install it into the
# active virtualenv (`$VIRTUAL_ENV`). Intended for developer/CI use
# when testing local source changes before publishing to PyPI.
# deploytool no longer orchestrates this target — `bbsengine6/py/
# pyproject.toml` declares `getdate-next` as a runtime dep and pip
# resolves it via PyPI when bbsengine6 installs. To use local source
# instead of PyPI, run this target manually before deploying anything
# that pulls in bbsengine6.
deploy-venv: clean-egg-info
	@command -v $(VIRTUAL_ENV)/bin/pip >/dev/null 2>&1 || { \
		echo "Error: deploy-venv requires an active virtualenv (set VIRTUAL_ENV)"; \
		exit 1; \
	}
	@mkdir -p $(WHEEL_DIR)
	@rm -f $(WHEEL_DIR)/*.whl
	$(MAKE) version
	$(PREPARE_BUILD)
	$(PYTHON) -m build --wheel --outdir $(WHEEL_DIR) .
	$(VIRTUAL_ENV)/bin/pip install $(WHEEL_DIR)/*.whl
	-rm -rf $(WHEEL_DIR)
	@echo "Installed $(PROJECT) into $(VIRTUAL_ENV)"

help:
	@echo "getdate_next - natural language date expression parser"
	@echo ""
	@echo "Targets:"
	@echo "  build           Build sdist+wheel into $(OUTDIR)"
	@echo "  rename-sdist    Rename built sdist to include -src suffix"
	@echo "  sign            GPG-detach-sign every artifact in $(OUTDIR)"
	@echo "  release         clean + version + build + rename-sdist + sign"
	@echo "  deploy-venv     Build wheel and pip install into \$$VIRTUAL_ENV"
	@echo "  clean           Remove build artifacts"
	@echo "  clean-egg-info  Remove in-tree *.egg-info/ dirs (defensive)"
	@echo "  version         Stamp src/getdate_next/_version.py with date"
	@echo "  tag             Create git tag v$(VERSION) if absent"
	@echo "  push            Push v$(VERSION) to github"
	@echo "  backup          rsync the tree to /srv/backups/minotaur/$(PROJECT)/"
	@echo "  deploy          alias for deploy-venv"

push: tag
	git push -u github v$(VERSION)

tag:
	@if git rev-parse v$(VERSION) >/dev/null 2>&1; then \
		echo "Tag v$(VERSION) already exists. Skipping."; \
	else \
		git tag -a v$(VERSION) -m "Release v$(VERSION)"; \
		echo "Tag v$(VERSION) created locally."; \
	fi

backup:
	rsync --recursive --verbose --exclude=.venv . /srv/backups/minotaur/$(PROJECT)/

deploy: deploy-venv
