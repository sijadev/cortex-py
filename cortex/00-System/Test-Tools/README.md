# Cortex Test Framework

A pip-installable testing and validation framework for the Cortex AI Knowledge Management System.

## Features

- **Link Analysis**: Comprehensive broken link detection for Markdown files
- **AI-Powered Suggestions**: Intelligent repair recommendations
- **Validation System**: Safety and relevance checking for suggestions
- **Fallback Mode**: Graceful degradation when dependencies fail
- **CLI Tools**: Easy-to-use command line interface

## Installation

```bash
# Install from local directory (development)
cd cortex-test-framework
pip install -e .

# Install from PyPI (future)
pip install cortex-test-framework
```

## Usage

### Link Analysis

```bash
# Analyze repository for broken links
cortex-link-advisor analyze --cortex-path /path/to/cortex --output-dir test-results
```

### Generate Suggestions

```bash
# Generate AI-powered repair suggestions
cortex-link-advisor suggest --output suggestions.md --input-dir test-results
```

### Validate Suggestions

```bash
# Validate suggestions for safety
cortex-link-advisor validate --input suggestions.md --output validation.md
```

### Health Check

```bash
# Generate health dashboard
cortex-health-check --output dashboard.html --format html
cortex-health-check --output report.md --format markdown
```

## CLI Commands

### `cortex-link-advisor`

- `analyze`: Scan repository for broken links and patterns
- `suggest`: Generate AI-powered repair suggestions  
- `validate`: Validate suggestions for safety and relevance

### `cortex-health-check`

- Generate health dashboards and reports
- Support for HTML and Markdown formats

## Integration with GitHub Actions

This framework is designed to integrate seamlessly with CI/CD pipelines:

```yaml
- name: Install Cortex Test Framework
  run: |
    cd cortex-test-framework
    pip install -e .

- name: Run Link Analysis
  run: |
    mkdir -p test-results
    cortex-link-advisor analyze --cortex-path . --output-dir test-results
```

## Fallback Mode

When analysis data is missing or corrupted, the framework automatically switches to fallback mode, providing basic validation and helpful reports without failing the entire workflow.

## Development

```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
```

## License

MIT License - see LICENSE file for details.