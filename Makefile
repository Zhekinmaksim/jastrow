# Everything here runs with no dependencies beyond python3, except the asset
# and page checks, which need playwright and node respectively.

.PHONY: help test check audit page assets bundle fixture serve clean all

help:
	@echo "  make test      run the contract test suite"
	@echo "  make audit     recompute web/report.json and check it adds up"
	@echo "  make page      check the page arithmetic against the contract"
	@echo "  make check     all three, which is what CI runs"
	@echo "  make fixture   regenerate the layout fixture and embed it"
	@echo "  make assets    regenerate the favicons and the social card"
	@echo "  make bundle    build the one file version with assets inlined"
	@echo "  make serve     serve web/ on http://localhost:8000"

test:
	python3 test/test_jastrow.py

audit:
	python3 scripts/check_report.py web/report.json

page:
	python3 scripts/check_page_math.py

check: test audit page

fixture:
	python3 scripts/fixture.py
	python3 scripts/embed_report.py web/report.json
	python3 scripts/bundle.py

assets:
	python3 scripts/make_assets.py

bundle:
	python3 scripts/bundle.py

serve:
	cd web && python3 -m http.server 8000

clean:
	find . -name __pycache__ -type d -exec rm -rf {} +
	rm -f .jastrow.json

all: check
