.PHONY: proto demo test infra-up analysis-test

proto:
	@echo "Proto contracts in proto/ (generate stubs on Linux: protoc --python_out=... )"

infra-up:
	docker compose up -d postgres minio

demo:
	docker compose up -d --build
	@echo "Open http://localhost — apiserver :8191"

test:
	python -m pytest tests/ -q --cov=analysis --cov-report=term-missing || python tests/test_topn.py
	python tests/test_topn.py
	cd apiserver && go test ./... -count=1 2>/dev/null || true

analysis-test:
	@echo "Run on Linux with perf.data:"
	@echo "  python analysis/hotmethod_analyzer.py --task-id test --local-perf /path/to/perf.data --no-save"
