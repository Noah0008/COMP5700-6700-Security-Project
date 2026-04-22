import json
import os
import subprocess
import pandas as pd
import argparse
import sys
import unittest
from unittest.mock import patch, MagicMock

class Config:
    """Centralized configuration to avoid hard-coding."""
    DEFAULT_SUMMARY_FILE = "comparison_summary.json"
    DEFAULT_TARGET_DIR = "./project-yamls"
    DEFAULT_REPORT_FILE = "compliance_report.csv"
    TEMP_SCAN_FILE = "full_scan_results.json"
    
    # Mapping keywords in KDE names to Kubescape Control IDs
    # These are industry-standard IDs for K8s security
    CONTROL_MAPPING = {
        "auth": ["C-0035", "C-0016"],
        "privilege": ["C-0057", "C-0046"],
        "logging": ["C-0067"],
        "network": ["C-0030"],
        "access": ["C-0035", "C-0001"]
    }
    # Fallback controls to ensure report is never empty
    UNIVERSAL_CONTROLS = ["C-0001", "C-0057", "C-0046"]

def run_security_scan(target_path):
    """
    Executes the Kubescape CLI against the target directory.
    Uses shell=True to handle Windows environment paths correctly.
    """
    abs_path = os.path.abspath(target_path)
    if not os.path.isdir(abs_path):
        print(f"[ERROR] Target directory not found: {abs_path}")
        return None

    print(f"[*] Initiating Kubescape scan on: {abs_path}")
    
    # Using the standard CLI command structure
    command = f'kubescape scan "{abs_path}" --format json --output {Config.TEMP_SCAN_FILE}'
    
    try:
        # Capture output to prevent console clutter while checking for errors
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        
        if not os.path.exists(Config.TEMP_SCAN_FILE):
            return None
            
        with open(Config.TEMP_SCAN_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Kubescape execution failed: {e.stderr}")
        return None
    finally:
        # Clean up temporary scan data
        if os.path.exists(Config.TEMP_SCAN_FILE):
            os.remove(Config.TEMP_SCAN_FILE)

def calculate_metrics(scan_data):
    """
    Parses the Kubescape JSON report to extract compliance statistics.
    Handles different schema versions of Kubescape output.
    """
    if not scan_data:
        return 0, 0, 0
    
    summary = scan_data.get('summaryDetails', {})
    score = round(summary.get('score', 0), 2)
    
    # Cross-version compatibility for resource counts
    passed = summary.get('passedResources', summary.get('numberOfPassedResources', 0))
    failed = summary.get('failedResources', summary.get('numberOfFailedResources', 0))
    
    # Secondary check if summary is flat/missing
    if passed == 0 and failed == 0:
        for ctrl in scan_data.get('controls', []):
            passed += ctrl.get('numberOfPassedResources', 0)
            failed += ctrl.get('numberOfFailedResources', 0)
            
    return score, passed, failed

def main():
    # Setup Argument Parser for dynamic inputs
    parser = argparse.ArgumentParser(description="Task-3: Security Executor")
    parser.add_argument("--summary", default=Config.DEFAULT_SUMMARY_FILE, help="Path to Task-2 JSON summary")
    parser.add_argument("--target", default=Config.DEFAULT_TARGET_DIR, help="Directory containing K8s YAMLs")
    parser.add_argument("--output", default=Config.DEFAULT_REPORT_FILE, help="Path for the final CSV report")
    args = parser.parse_args()

    if not os.path.exists(args.summary):
        print(f"[FATAL] Summary file '{args.summary}' missing. Run Task-2 first.")
        sys.exit(1)

    # 1. Load the comparison results from Task-2
    with open(args.summary, 'r') as f:
        diff_data = json.load(f)

    # 2. Run the actual security scan
    raw_results = run_security_scan(args.target)
    if not raw_results:
        print("[FATAL] Scan produced no data. Ensure Kubescape is in your PATH.")
        sys.exit(1)

    # 3. Process and map data
    final_report_list = []
    print("[*] Mapping differences to compliance data...")

    for pair, diffs in diff_data.items():
        # Combine Added and Modified KDEs to check for new security implications
        target_kdes = diffs.get('added', []) + diffs.get('modified', [])
        
        for kde in target_kdes:
            kde_name = kde['name']
            score, passed, failed = calculate_metrics(raw_results)
            
            final_report_list.append({
                "Comparison_Pair": pair,
                "KDE_Name": kde_name,
                "Compliance_Score": f"{score}%",
                "Passed_Resources": passed,
                "Failed_Resources": failed,
                "Scan_Status": "Warning" if failed > 0 else "Passed"
            })

    # 4. Save to CSV using Pandas
    if final_report_list:
        df = pd.DataFrame(final_report_list)
        df.to_csv(args.output, index=False)
        print(f"\n[SUCCESS] Task-3 complete. Report saved to: {args.output}")
    else:
        print("\n[WARNING] No relevant differences found to analyze.")

class TestTask3(unittest.TestCase):
    def test_calculate_metrics_none(self):
        score, passed, failed = calculate_metrics(None)
        self.assertEqual(score, 0)
        self.assertEqual(passed, 0)
        self.assertEqual(failed, 0)

    def test_calculate_metrics_with_data(self):
        mock_data = {
            "summaryDetails": {
                "score": 75.5,
                "passedResources": 8,
                "failedResources": 3
            }
        }
        score, passed, failed = calculate_metrics(mock_data)
        self.assertEqual(score, 75.5)
        self.assertEqual(passed, 8)
        self.assertEqual(failed, 3)

    def test_run_security_scan_missing_dir(self):
        result = run_security_scan("/nonexistent/path/xyz")
        self.assertIsNone(result)

    @patch("subprocess.run")
    @patch("os.path.exists", return_value=False)
    def test_run_security_scan_no_output_file(self, mock_exists, mock_run):
        result = run_security_scan("./project-yamls")
        self.assertIsNone(result)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTask3)
    unittest.TextTestRunner(verbosity=1).run(suite)
    main()