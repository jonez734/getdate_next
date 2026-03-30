PROJECT = getdate_next
OUTDIR = dist/
VERSION = 0.1.0.dev$(shell date +%Y%m%d%H%M)

PYTHON = python3.12

.PHONY: build version
.PHONY: clean build rename-sdist sign release all

all:

build: version
	VERSION=$(VERSION) $(PYTHON) -m build --outdir $(OUTDIR)

clean:
	-rm *~

version:
#	@echo '__version__ = "'`git log -1 --format='%H' | cut -c 1-16`'"' > src/$(PROJECT)/_version.py
	@echo '__version__ = "0.0.1.dev$(VERSION)"' > src/$(PROJECT)/_version.py
	@echo '__datestamp__ = "'`date +%Y%m%d-%H%M`-`whoami`'"' >> src/$(PROJECT)/_version.py
