import os
import json
import subprocess
import pandas as pd
import argparse
import sys
import unittest
from unittest.mock import patch, MagicMock

# =================================================================
# TASK-3: CONFIGURATION
# =================================================================

class Config:
    DEFAULT_NAMES_FILE        = "names_diff_cis-r1_vs_cis-r2.txt"
    DEFAULT_REQUIREMENTS_FILE = "requirements_diff_cis-r1_vs_cis-r2.txt"
    DEFAULT_TARGET_DIR        = "./project-yamls"
    DEFAULT_REPORT_FILE       = "compliance_report.csv"
    TEMP_SCAN_FILE            = "full_scan_results.json"

    # Keyword → Kubescape Control ID mapping
    CONTROL_MAPPING = {
        "logging":    ["C-0067"],
        "audit":      ["C-0067"],
        "rbac":       ["C-0035", "C-0016"],
        "auth":       ["C-0035", "C-0016"],
        "privilege":  ["C-0057", "C-0046"],
        "pod":        ["C-0057", "C-0046"],
        "network":    ["C-0030"],
        "cni":        ["C-0030"],
        "image":      ["C-0069"],
        "registry":   ["C-0069"],
        "secret":     ["C-0015"],
        "kms":        ["C-0015"],
        "kubelet":    ["C-0002"],
        "access":     ["C-0035", "C-0001"],
        "cluster":    ["C-0001"],
        "worker":     ["C-0002"],
    }
    UNIVERSAL_CONTROLS = ["C-0001", "C-0002", "C-0015", "C-0030", "C-0035",
                          "C-0046", "C-0057", "C-0067", "C-0069"]


# =================================================================
# TASK-3: CORE FUNCTIONS (4 REQUIRED)
# =================================================================

def load_diff_text_files(names_file, requirements_file):
    """
    Function-1: Loads the two TEXT files produced by Task-2.
    Returns a tuple of (names_lines, requirements_lines).
    Raises FileNotFoundError if either file is missing.
    """
    for path in [names_file, requirements_file]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"[ERROR] Task-2 output file not found: {path}")

    with open(names_file, 'r', encoding='utf-8') as f:
        names_lines = [line.strip() for line in f.readlines() if line.strip()]

    with open(requirements_file, 'r', encoding='utf-8') as f:
        reqs_lines = [line.strip() for line in f.readlines() if line.strip()]

    print(f"[INFO] Loaded names diff: {len(names_lines)} line(s)")
    print(f"[INFO] Loaded requirements diff: {len(reqs_lines)} line(s)")
    return names_lines, reqs_lines


def determine_controls(names_lines, reqs_lines):
    """
    Function-2: Determines whether the TEXT files contain differences and,
    if so, maps the differing KDE names to relevant Kubescape control IDs.

    Returns a list of control IDs to scan with, or Config.UNIVERSAL_CONTROLS
    if no differences are found (i.e. files contain only 'NO DIFFERENCES' messages).
    """
    no_diff_names = (len(names_lines) == 1 and
                     "NO DIFFERENCES IN REGARDS TO ELEMENT NAMES" in names_lines[0])
    no_diff_reqs  = (len(reqs_lines) == 1 and
                     "NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS" in reqs_lines[0])

    if no_diff_names and no_diff_reqs:
        print("[INFO] No differences found — will run full Kubescape scan.")
        return Config.UNIVERSAL_CONTROLS

    # Collect KDE names from both files (first field in each tuple line)
    kde_names = set()
    for line in names_lines + reqs_lines:
        parts = line.split(",")
        if parts and not line.startswith("NO DIFFERENCES"):
            kde_names.add(parts[0].strip().lower())

    # Map KDE keywords → control IDs
    matched_controls = set()
    for kde in kde_names:
        for keyword, controls in Config.CONTROL_MAPPING.items():
            if keyword in kde:
                matched_controls.update(controls)

    if not matched_controls:
        matched_controls = set(Config.UNIVERSAL_CONTROLS)

    control_list = sorted(matched_controls)
    print(f"[INFO] Mapped differences to controls: {control_list}")
    return control_list


def run_kubescape_scan(target_dir, controls):
    """
    Function-3: Executes the Kubescape tool on project-yamls.zip/directory
    using the control IDs determined by Function-2.
    Returns a pandas DataFrame with raw scan results.

    If controls == UNIVERSAL_CONTROLS (no differences), runs without --include flag.
    Otherwise, runs only on the specified controls.
    """
    abs_path = os.path.abspath(target_dir)
    if not os.path.isdir(abs_path):
        print(f"[ERROR] Target directory not found: {abs_path}")
        return pd.DataFrame()

    # Build the Kubescape command
    if set(controls) == set(Config.UNIVERSAL_CONTROLS):
        cmd = f'kubescape scan "{abs_path}" --format json --output {Config.TEMP_SCAN_FILE}'
    else:
        control_str = ",".join(controls)
        cmd = (f'kubescape scan control {control_str} "{abs_path}" '
               f'--format json --output {Config.TEMP_SCAN_FILE}')

    print(f"[*] Running: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Kubescape failed: {e.stderr}")
        return pd.DataFrame()

    if not os.path.exists(Config.TEMP_SCAN_FILE):
        print("[ERROR] Kubescape produced no output file.")
        return pd.DataFrame()

    try:
        with open(Config.TEMP_SCAN_FILE, 'r', encoding='utf-8') as f:
            scan_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Could not parse Kubescape output: {e}")
        return pd.DataFrame()
    finally:
        if os.path.exists(Config.TEMP_SCAN_FILE):
            os.remove(Config.TEMP_SCAN_FILE)

    # Parse into rows — data lives in summaryDetails.controls (a dict keyed by controlID)
    rows = []
    controls_dict = scan_data.get("summaryDetails", {}).get("controls", {})

    for ctrl_id, ctrl in controls_dict.items():
        ctrl_name  = ctrl.get("name", "Unknown")
        severity   = ctrl.get("severity", "Unknown")
        counters   = ctrl.get("ResourceCounters", {})
        failed     = counters.get("failedResources", 0)
        passed     = counters.get("passedResources", 0)
        total      = failed + passed
        compliance = f"{round(ctrl.get('complianceScore', 0), 2)}%"

        rows.append({
            "FilePath":         abs_path,
            "Severity":         severity,
            "Control name":     f"{ctrl_id}: {ctrl_name}",
            "Failed resources": failed,
            "All Resources":    total,
            "Compliance score": compliance,
        })

    df = pd.DataFrame(rows, columns=[
        "FilePath", "Severity", "Control name",
        "Failed resources", "All Resources", "Compliance score"
    ])
    print(f"[INFO] Scan complete — {len(df)} control results.")
    return df


def generate_csv_report(df, output_file):
    """
    Function-4: Saves the pandas DataFrame produced by Function-3 to a CSV file
    with the required headers:
        FilePath, Severity, Control name, Failed resources, All Resources, Compliance score
    """
    required_cols = ["FilePath", "Severity", "Control name",
                     "Failed resources", "All Resources", "Compliance score"]

    if df is None or df.empty:
        print("[WARNING] No scan data to write — creating empty report with headers.")
        df = pd.DataFrame(columns=required_cols)

    # Ensure correct column order
    df = df.reindex(columns=required_cols)
    df.to_csv(output_file, index=False)
    print(f"[SUCCESS] CSV report saved to: {output_file}")


# =================================================================
# PIPELINE
# =================================================================

def main():
    parser = argparse.ArgumentParser(description="Task-3: Security Executor")
    parser.add_argument("--names",   default=Config.DEFAULT_NAMES_FILE,
                        help="Path to names diff TEXT file from Task-2")
    parser.add_argument("--reqs",    default=Config.DEFAULT_REQUIREMENTS_FILE,
                        help="Path to requirements diff TEXT file from Task-2")
    parser.add_argument("--target",  default=Config.DEFAULT_TARGET_DIR,
                        help="Directory containing K8s YAML files to scan")
    parser.add_argument("--output",  default=Config.DEFAULT_REPORT_FILE,
                        help="Output CSV file path")
    args = parser.parse_args()

    # Function-1
    try:
        names_lines, reqs_lines = load_diff_text_files(args.names, args.reqs)
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    # Function-2
    controls = determine_controls(names_lines, reqs_lines)

    # Function-3
    df = run_kubescape_scan(args.target, controls)

    # Function-4
    generate_csv_report(df, args.output)


# =================================================================
# UNIT TESTS  (4 required — one per function)
# =================================================================

class TestTask3(unittest.TestCase):

    def test_f1_load_diff_text_files_missing(self):
        """Function-1: raises FileNotFoundError for missing Task-2 output files."""
        with self.assertRaises(FileNotFoundError):
            load_diff_text_files("nonexistent_names.txt", "nonexistent_reqs.txt")

    def test_f2_determine_controls_no_differences(self):
        """Function-2: returns UNIVERSAL_CONTROLS when both files have no differences."""
        names = ["NO DIFFERENCES IN REGARDS TO ELEMENT NAMES"]
        reqs  = ["NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS"]
        result = determine_controls(names, reqs)
        self.assertEqual(set(result), set(Config.UNIVERSAL_CONTROLS))

    def test_f2_determine_controls_with_differences(self):
        """Function-2: maps KDE names to correct Kubescape controls when differences exist."""
        names = ["Logging,ABSENT-IN-cis-r1-kdes.yaml,PRESENT-IN-cis-r2-kdes.yaml,NA"]
        reqs  = ["NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS"]
        result = determine_controls(names, reqs)
        self.assertIn("C-0067", result)   # logging → C-0067

    def test_f3_run_kubescape_scan_missing_dir(self):
        """Function-3: returns empty DataFrame when target directory does not exist."""
        df = run_kubescape_scan("/nonexistent/path/xyz", Config.UNIVERSAL_CONTROLS)
        self.assertTrue(df.empty)

    def test_f4_generate_csv_report(self):
        """Function-4: creates a CSV file with the correct required headers."""
        test_df = pd.DataFrame([{
            "FilePath": "/test/file.yaml",
            "Severity": "High",
            "Control name": "C-0001: Test Control",
            "Failed resources": 2,
            "All Resources": 5,
            "Compliance score": "60.0%",
        }])
        out = "test_compliance_report.csv"
        generate_csv_report(test_df, out)
        self.assertTrue(os.path.exists(out))

        result_df = pd.read_csv(out)
        for col in ["FilePath", "Severity", "Control name",
                    "Failed resources", "All Resources", "Compliance score"]:
            self.assertIn(col, result_df.columns)
        os.remove(out)


# =================================================================
# ENTRY POINT
# =================================================================

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTask3)
    test_result = unittest.TextTestRunner(verbosity=2).run(suite)

    if test_result.wasSuccessful():
        main()
