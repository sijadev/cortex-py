# 00-System Directory

Central system components and tools for Cortex AI Knowledge Management System.

## Directory Structure

### 🧠 AI Components

- **AI-Learning-Engine/** - Multi-vault AI learning and pattern detection
- **Cross-Vault-Linker/** - Intelligent linking system between vaults
- **Management-Service/** - Centralized system management and coordination

### 🛠️ Development Tools

- **Test-Tools/** - Pip-installable test framework with CLI tools
- **Development-Tools/** - Health checks and system utilities
- **cortex-cli-commands/** - Command documentation and references

### 📊 Analysis & Monitoring

- **Services/** - Background services and automated tasks
- **Dashboards/** - System monitoring and visualization
- **Algorithms/** - Core algorithms and calculations

### 📋 Configuration & Documentation

- Various system configuration files and documentation
- Cross-vault analysis results and reports
- Roadmap and progress tracking

## Key Features

### Test Framework (Test-Tools/)

```bash
# Install the test framework
cd 00-System/Test-Tools
pip install -e .

# Available CLI tools
cortex-link-advisor    # Link analysis and suggestions
cortex-health-check    # Health dashboards and reports
cortex-test           # Main test framework CLI
```

### AI Learning Engine

- Automated pattern detection across vaults
- Knowledge gap identification and research integration
- Multi-vault correlation analysis

### Cross-Vault Linker

- Rule-based intelligent linking
- Adaptive rule engine with confidence scoring
- MCP bridge integration for Obsidian

### Management Service

- Centralized coordination of all system components
- Combined reporting and analytics
- Service lifecycle management

## Integration

All components are designed to work together through:

- Shared configuration files (YAML)
- JSON-based data interchange
- Standardized logging and reporting
- CLI tools for automation and CI/CD

## Monitoring

The system includes comprehensive monitoring through:

- Health check scripts
- Automated testing framework
- GitHub Actions workflows
- Dashboard generation tools
