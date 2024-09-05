name: tests

on:
  pull_request:
    branches: ["main"]

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]

    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install .
      - name: Test with pytest
        run: |
          pip install pytest pytest-cov
          pytest --cov=src tests/ --doctest-modules --junitxml=junit/test-results.xml --cov=com --cov-report=xml --cov-report=html