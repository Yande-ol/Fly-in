.PHONY: install run visual debug clean lint lint-strict

# Instala as dependências do projeto
install:
	pip install -r requirements.txt

# Executa a simulação padrão. Uso: make run MAP=maps/easy/01_linear_path.txt
run:
	python3 main.py $(MAP)

# Executa a simulação com a interface visual. Uso: make visual MAP=maps/easy/01_linear_path.txt
visual:
	python3 main.py $(MAP) -v

# Abre o depurador interativo do Python
debug:
	python3 -m pdb main.py $(MAP)

# Limpa todos os caches de compilação e linters
clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache
	find . -type d -name "__pycache__" -exec rm -r {} +

# Verificação obrigatória de qualidade de código (Capítulo III.2)
lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores \
        --ignore-missing-imports --disallow-untyped-defs \
        --check-untyped-defs

# Verificação estrita opcional
lint-strict:
	flake8 .
	mypy . --strict
