PROJECT = getdate-next
OUTDIR = /srv/repo/$(PROJECT)/
VERSION = $(shell date +%Y%m%d%H%M)

PYTHON = python3

.PHONY: build version
.PHONY: clean build rename-sdist sign release all

build: version
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

release: clean build rename-sdist sign

all:

clean:
	-rm *~

sdist:
	$(PYTHON) -m setup sdist --dist-dir /srv/repo/$(PROJECT)/

version:
	@echo '__version__ = "$(VERSION)"' > src/getdate_next/_version.py

push: tag
	git push -u github v$(VERSION)

tag:
	@if git rev-parse v$(VERSION) >/dev/null 2>&1; then \
		echo "Tag v$(VERSION) already exists. Skipping."; \
	else \
		git tag -a v$(VERSION) -m "Release v$(VERSION)"; \
		echo "Tag v$(VERSION) created locally."; \
	fi
