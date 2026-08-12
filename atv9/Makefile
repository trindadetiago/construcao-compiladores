PY = python3

.PHONY: test exemplos limpar

test:
	$(PY) tests/rodar_testes.py

exemplos:
	@for f in tests/programas/*.cmd; do \
		printf "%-36s " "$$f"; \
		echo 10 | $(PY) cmdc.py interp $$f; \
	done

limpar:
	rm -rf __pycache__ cmdlang/__pycache__ tests/__pycache__
