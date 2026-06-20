.PHONY: proto demo test infra-up analysis-test

proto:
	@echo "Proto contracts in proto/ (generate stubs on Linux: protoc --python_out=... )"

infra-up:
	docker compose up -d postgres minio

demo:
	docker compose up -d --build
	@echo "Open http://localhost — apiserver :8191"

test:
	@echo "=== Go tests + coverage ==="
	cd apiserver && go test ./... -count=1 -coverprofile=cover.out
	cd apiserver && go tool cover -func=cover.out | tail -1
	@echo "=== Python analysis tests ==="
	python -m pytest analysis/hotmethod_analyzer_test.py tests/ -q --cov=analysis --cov-report=term-missing --cov-fail-under=50
	@echo "=== Python drop tests ==="
	cd drop && python -m pytest agent_test.py server_test.py -q --cov=agent --cov=server --cov-report=term-missing --cov-fail-under=50

analysis-test:
	@echo "Run on Linux with perf.data:"
	@echo "  python analysis/hotmethod_analyzer.py --task-id test --local-perf /path/to/perf.data --no-save"
