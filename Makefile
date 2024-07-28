.PHONY: tc
tc:
	@python -m mypy .


.PHONY: test
test:
	@python -m pytest .


.PHONY: testv
testv:
	@python -m pytest -s .
