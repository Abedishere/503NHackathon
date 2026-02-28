.PHONY: install pipeline api test docker-build docker-run pdf smoke all clean

install:
	pip install -r requirements.txt

pipeline:
	python scripts/run_pipeline.py

train:
	python scripts/train_models.py

api:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest tests/ -v

smoke:
	python scripts/demo_smoke_test.py

pdf:
	python -c "import weasyprint; weasyprint.HTML(filename='docs/executive_brief.html').write_pdf('docs/executive_brief.pdf')"

docker-build:
	docker build -f docker/Dockerfile.api -t conut-ops-agent .

docker-run:
	docker compose -f docker/docker-compose.yml up

all: install pipeline train test smoke
	@echo "Full pipeline complete."

clean:
	rm -rf artifacts/__pycache__ .pytest_cache
