# ============================================================================
# Win-Task - 开发工具 Makefile
# ============================================================================

.PHONY: help install install-dev run test lint format clean build package docs

# 默认目标
help:
	@echo "Win-Task 开发工具"
	@echo ""
	@echo "可用命令："
	@echo "  install      安装生产环境依赖"
	@echo "  install-dev  安装开发环境依赖"
	@echo "  run          运行应用程序"
	@echo "  test         运行测试"
	@echo "  lint         代码质量检查"
	@echo "  format       代码格式化"
	@echo "  clean        清理构建文件"
	@echo "  build        构建可执行文件"
	@echo "  package      打包发布版本"
	@echo "  docs         生成文档"

# 安装依赖
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

# 运行应用
run:
	python main.py

# 测试
test:
	pytest tests/ -v --cov=src/ --cov-report=html --cov-report=term

test-quick:
	pytest tests/ -x

# 代码质量
lint:
	flake8 src/ tests/
	mypy src/
	bandit -r src/

format:
	black src/ tests/
	isort src/ tests/

check: format lint test

# 清理
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# 构建
build:
	python build.py

package: clean build
	@echo "打包完成，文件位于 dist/release/"

# 文档
docs:
	cd docs && make html

# 开发环境设置
setup-dev: install-dev
	pre-commit install
	@echo "开发环境设置完成"

# 版本管理
bump-patch:
	bump2version patch

bump-minor:
	bump2version minor

bump-major:
	bump2version major
