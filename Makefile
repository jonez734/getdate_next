PROJECT = getdate_next
OUTDIR = dist/
VERSION = $(shell date +%Y%m%d%H%M)

PYTHON = python3.12

.PHONY: build version
.PHONY: clean build rename-sdist sign release all

all:

build: version
	VERSION=$(VERSION) $(PYTHON) -m build --outdir $(OUTDIR)

clean:
	-rm *~

version:
#	@echo '__version__ = "'`git log -1 --format='%H' | cut -c 1-16`'"' > bbsengine6/_version.py
	@echo '__version__ = "0.0.1.dev$(VERSION)"' > $(PROJECT)/_version.py
	@echo '__datestamp__ = "'`date +%Y%m%d-%H%M`-`whoami`'"' >> $(PROJECT)/_version.py
