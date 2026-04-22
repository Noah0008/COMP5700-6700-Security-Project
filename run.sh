
#!/bin/bash
set -e

# Usage: bash run.sh <HuggingFace_Token>
# All PDFs (cis-r1.pdf through cis-r4.pdf) must be in the same directory.

HF_TOKEN="${1:-}"

echo "======================================================"
echo "  COMP5700  Security Project"
echo "======================================================"

if [ -z "$HF_TOKEN" ]; then
    echo "[ERROR] HuggingFace token required."
    echo "Usage: bash run.sh <HuggingFace_Token>"
    exit 1
fi

for pdf in cis-r1.pdf cis-r2.pdf cis-r3.pdf cis-r4.pdf; do
    if [ ! -f "$pdf" ]; then
        echo "[ERROR] Missing required PDF: $pdf"
        exit 1
    fi
done
echo "[OK] All required PDFs found."

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

pip install -r requirements.txt --quiet

echo "[*] Running all test cases..."
python3 -m unittest extractor.TestTask1 comparator.TestTask2 executor.TestTask3 -v

echo "[*] Running Task-1: Extractor..."
echo "$HF_TOKEN" | python3 extractor.py

echo "[*] Running Task-2: Comparator..."
python3 comparator.py

echo "[*] Running Task-3: Executor..."
python3 executor.py

echo "======================================================"
echo "  Done. Outputs: YAML files, all_llm_outputs.txt,"
echo "  comparison_summary.json, compliance_report.csv"
echo "======================================================"

deactivate
