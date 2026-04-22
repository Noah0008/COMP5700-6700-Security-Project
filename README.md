# COMP 5700/6700 Software Process - Class Project

## Team Members
- Name: Noah Shi
- Email: yus0002@auburn.edu
  
- Name: Francis Collopy
- Email: fpc0005@auburn.edu

## Project Overview
This project provides an automated pipeline to bridge the gap between static security compliance documents (CIS Benchmarks) and live Kubernetes configurations. It automates the extraction of security rules, version comparison, and real-world compliance scanning.

The pipeline consists of three core phases:
1. **Extraction (Task-1):** Parses CIS Benchmark PDFs into structured YAML files using LLMs.
2. **Comparison (Task-2):** Analyzes differences between benchmark versions to identify requirement gaps.
3. **Execution (Task-3):** Maps these gaps to Kubescape controls and performs security scans on target K8s manifests.

## Repository Organization
All core components are located in the root directory for easy access and execution:
- `extractor.py`: Script for LLM-based security requirement extraction.
- `comparator.py`: Script for identifying differences between KDE versions.
- `executor.py`: Script for Kubescape-based security auditing and reporting.
- `run.sh`: Unified automation script to trigger the entire pipeline.
- `requirements.txt`: Environment dependencies.
- `.github/workflows/tests.yaml`: Automated CI/CD testing configuration.
- `project-yamls/`: Target directory containing Kubernetes manifest files for scanning.

## Prerequisites
- **Python 3.10+**
- **Kubescape CLI**: Must be installed and accessible in your system's PATH.
- **HuggingFace API Token**: Required for the LLM inference in Task-1.

## Installation
Clone this repository and install the dependencies:
```bash
pip install -r requirements.txt