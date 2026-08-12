PY = python3

.PHONY: test exemplos limpar

test:
	$(PY) tests/rodar_testes.py

exemplos:
	@for f in tests/programas/*.fun; do \
		printf "%-40s " "$$f"; \
		echo 100 | $(PY) func.py interp $$f; \
	done

limpar:
	rm -rf __pycache__ funlang/__pycache__ tests/__pycache__
