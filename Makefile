PROJECT = getdate_next
# Pinned so sub-make invocations (deploy-tui -> build) share one version.
VERSION ?= $(shell date +%Y%m%d%H%M)
# Artifact glob for the version being built. Publish targets upload only
# these files so stale artifacts left in $(OUTDIR) are never re-sent.
ARTIFACTS = $(OUTDIR)$(PROJECT)-0.1.0.dev$(VERSION)*

# All output paths are overridable. Nothing here hard-codes a host path.
# OUTDIR: local build output (sdist + wheel). No sudo needed.
OUTDIR ?= $(CURDIR)/dist/
# REPO_DEST: publish target for `repo` (rsync). Empty = `repo` refuses to run.
REPO_DEST ?=

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

# DEPLOY_UPGRADE is set by `deploytool --upgrade` (default true) and
# unset by `--no-upgrade`. When "1", pip installs pass `--upgrade`.
DEPLOY_UPGRADE ?=
PIP_UPGRADE_FLAG := $(if $(filter 1,$(DEPLOY_UPGRADE)),--upgrade,)

# DEPLOY_EDITABLE is set by `deploytool --editable`. When "1", deploy-tui
# installs editable from this checkout instead of the built wheel.
DEPLOY_EDITABLE ?=

# GETDATE_SOURCE selects what `deploy-tui` installs into $VIRTUAL_ENV:
#   local   build a wheel from this checkout and install it (default)
#   pypi    pip install getdate-next from PyPI
#   <other> passed to pip verbatim as a spec or path (fork, wheel, URL)
GETDATE_SOURCE ?= local

# Upload targets refuse to run unless PYPI_CONFIRM=1 is set.
PYPI_CONFIRM ?=

# Package index used by `testpypi` and `pypi`. Credentials come from the
# environment only: TWINE_USERNAME=__token__ and TWINE_PASSWORD=<token>.
TESTPYPI_URL = https://test.pypi.org/legacy/

.PHONY: all help clean clean-egg-info version build stage check rename-sdist \
	ensure-repo repo deploy-tui deploy-venv deploy testpypi pypi \
	verify-tokens tag push backup

all: help

# Wipe in-tree *.egg-info/ dirs that a prior `pip install -e .` may have
# left behind. Such egg-infos bake absolute paths into SOURCES.txt and
# poison any later `python -m build`.
clean-egg-info:
	-rm -rf *.egg-info src/*.egg-info

clean: clean-egg-info
	-rm -rf build build.old dist
	-find . -type d -name __pycache__ -exec rm -rf {} +
	-find . -type d -name .pytest_cache -exec rm -rf {} +
	-find . -type d -name .ruff_cache -exec rm -rf {} +

version:
	@echo '__version__ = "0.1.0.dev$(VERSION)"' > src/$(PROJECT)/_version.py

# Make sure build/ exists with mode 1775 before invoking `python -m build`.
# If build/ is foreign-owned, rename it out of the way first. Without the
# rename, the chmod fails with EPERM and the build aborts.
PREPARE_BUILD = \
	if [ -d build ] && [ ! -O build ]; then \
		mv build build.stale.$$$$ 2>/dev/null || true; \
	fi; \
	mkdir -p build && chmod 1775 build

# Build sdist + wheel into $(OUTDIR). No sudo, no publish.
build: version clean-egg-info
	$(PREPARE_BUILD)
	@mkdir -p $(OUTDIR)
	$(PYTHON) -m build --outdir $(OUTDIR)

rename-sdist:
	@for f in $(OUTDIR)/*.tar.gz; do \
		if [ -f "$$f" ] && echo "$$f" | grep -vq '\-src\.tar\.gz' ; then \
			mv "$$f" "$${f%.tar.gz}-src.tar.gz"; \
			echo "Renamed $$f -> $${f%.tar.gz}-src.tar.gz"; \
		fi \
	done

# Stage: build artifacts only. Used by every publish path.
stage: build

# Validate the artifacts in $(OUTDIR) with twine before any upload.
check: stage
	$(PYTHON) -m twine check $(OUTDIR)/*

release: clean version build check

# Publish targets always start from a clean release build of this version.
publish-ready: release

# Local install into the active venv. The default GETDATE_SOURCE=local
# builds a wheel from this checkout; `pypi` and other values pip-install
# from the named source.
deploy-tui:
ifeq ($(DEPLOY_EDITABLE),1)
	@command -v $(VIRTUAL_ENV)/bin/pip >/dev/null 2>&1 || { \
		echo "Error: deploy-tui requires an active virtualenv (set VIRTUAL_ENV)"; exit 1; }
	$(VIRTUAL_ENV)/bin/pip install $(PIP_UPGRADE_FLAG) --no-cache-dir -e .
	-rm -rf src/*.egg-info
else ifeq ($(GETDATE_SOURCE),local)
	@command -v $(VIRTUAL_ENV)/bin/pip >/dev/null 2>&1 || { \
		echo "Error: deploy-tui requires an active virtualenv (set VIRTUAL_ENV)"; exit 1; }
	$(MAKE) build VERSION=$(VERSION)
	$(VIRTUAL_ENV)/bin/pip install $(PIP_UPGRADE_FLAG) --no-deps \
		$(ARTIFACTS).whl
	@$(VERIFY_INSTALL)
else ifeq ($(GETDATE_SOURCE),pypi)
	@command -v $(VIRTUAL_ENV)/bin/pip >/dev/null 2>&1 || { \
		echo "Error: deploy-tui requires an active virtualenv (set VIRTUAL_ENV)"; exit 1; }
	$(VIRTUAL_ENV)/bin/pip install $(PIP_UPGRADE_FLAG) getdate-next
else
	@command -v $(VIRTUAL_ENV)/bin/pip >/dev/null 2>&1 || { \
		echo "Error: deploy-tui requires an active virtualenv (set VIRTUAL_ENV)"; exit 1; }
	$(VIRTUAL_ENV)/bin/pip install $(PIP_UPGRADE_FLAG) "$(GETDATE_SOURCE)"
endif
	@echo "Installed $(PROJECT) into $(VIRTUAL_ENV)"

# Verify that the wheel just installed is the one `pip show` reports.
# Catches silent no-ops where pip exits 0 without replacing the install.
VERIFY_INSTALL = \
	WHEEL=$$(ls $(ARTIFACTS).whl | head -1); \
	EXPECTED_FROM_FILENAME=$$(basename "$$WHEEL" | sed -E 's/^$(PROJECT)-(.+)-py3-none-any\.whl$$/\1/'); \
	EXPECTED_FROM_METADATA=$$(unzip -p "$$WHEEL" '*/METADATA' 2>/dev/null | awk -F': ' '/^Version: / {print $$2; exit}'); \
	SHOW_OUTPUT=$$($(VIRTUAL_ENV)/bin/pip show $(PROJECT) 2>&1); \
	INSTALLED=$$(echo "$$SHOW_OUTPUT" | awk '/^Version: / {print $$2; exit}'); \
	echo "=== verify-install ($(PROJECT)) ==="; \
	echo "  wheel filename Version: $$EXPECTED_FROM_FILENAME"; \
	echo "  wheel METADATA Version: $$EXPECTED_FROM_METADATA"; \
	echo "  pip show Version:       $$INSTALLED"; \
	if [ "$$INSTALLED" != "$$EXPECTED_FROM_FILENAME" ] \
		|| [ "$$INSTALLED" != "$$EXPECTED_FROM_METADATA" ]; then \
		echo "verify-install FAILED: $$WHEEL was installed but pip show does not agree" >&2; \
		exit 1; \
	fi; \
	echo "verify-install OK: pip show reports $$INSTALLED"

# Back-compat alias for the pre-deploytool name.
deploy-venv: deploy-tui

deploy: deploy-tui

# Publish to /srv/repo/<project>/ by rsync. Only target that touches
# $(REPO_DEST). Refuses to run unless REPO_DEST is set.
repo: require-repo-dest stage
	rsync -av --delete $(OUTDIR) $(REPO_DEST)

# Refuse before any build work when REPO_DEST is unset.
require-repo-dest:
	@test -n "$(REPO_DEST)" || { echo "repo: REPO_DEST is not set; nothing published" >&2; exit 1; }

# Credential and confirmation guard for index uploads.
verify-tokens:
	@test -n "$$TWINE_PASSWORD" || { \
		echo "Error: TWINE_PASSWORD is not set. Set TWINE_USERNAME=__token__ and TWINE_PASSWORD=<token>." >&2; exit 1; }
	@test "$${TWINE_USERNAME:-}" = "__token__" || { \
		echo "Error: TWINE_USERNAME must be __token__ for token auth." >&2; exit 1; }

# Upload to TestPyPI. Run this before `pypi`.
testpypi: publish-ready verify-tokens
	@test "$(PYPI_CONFIRM)" = "1" || { echo "testpypi: set PYPI_CONFIRM=1 to upload" >&2; exit 1; }
	$(PYTHON) -m twine upload --repository-url $(TESTPYPI_URL) $(ARTIFACTS)*

# Upload to PyPI. Requires PYPI_CONFIRM=1.
pypi: publish-ready verify-tokens
	@test "$(PYPI_CONFIRM)" = "1" || { echo "pypi: set PYPI_CONFIRM=1 to upload" >&2; exit 1; }
	$(PYTHON) -m twine upload $(ARTIFACTS)*

help:
	@echo "getdate_next - natural language date expression parser"
	@echo ""
	@echo "Targets:"
	@echo "  build        Build sdist + wheel into \$$(OUTDIR) (default: ./dist/)"
	@echo "  stage        Same as build; artifacts only, no install or publish"
	@echo "  check        twine check on the built artifacts"
	@echo "  deploy-tui   Install into \$$VIRTUAL_ENV (GETDATE_SOURCE=local|pypi|<spec>)"
	@echo "  deploy       alias for deploy-tui"
	@echo "  repo         rsync artifacts to \$$(REPO_DEST); fails if unset"
	@echo "  testpypi     Upload to TestPyPI (PYPI_CONFIRM=1, TWINE_* env)"
	@echo "  pypi         Upload to PyPI (PYPI_CONFIRM=1, TWINE_* env); run testpypi first"
	@echo "  release      clean + version + build + check"
	@echo "  clean        Remove build artifacts"
	@echo "  version      Stamp src/getdate_next/_version.py with date"
	@echo "  tag          Create git tag v$(VERSION) if absent"
	@echo "  push         Push v$(VERSION) to origin"
	@echo "  backup       rsync the tree to \$$(BACKUP_DEST); fails if unset"

tag:
	@if git rev-parse v$(VERSION) >/dev/null 2>&1; then \
		echo "Tag v$(VERSION) already exists. Skipping."; \
	else \
		git tag -a v$(VERSION) -m "Release v$(VERSION)"; \
		echo "Tag v$(VERSION) created locally."; \
	fi

push: tag
	git push -u origin v$(VERSION)

# Backup destination is operator-supplied; no host path is hard-coded.
BACKUP_DEST ?=
backup:
	@test -n "$(BACKUP_DEST)" || { echo "backup: BACKUP_DEST is not set" >&2; exit 1; }
	rsync --recursive --verbose --exclude=.venv . $(BACKUP_DEST)/$(PROJECT)/
