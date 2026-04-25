import yaml
import os
import unittest

# =================================================================
# TASK-2: CORE FUNCTIONS (3 REQUIRED)
# =================================================================

def load_kde_yaml(filepath):
    """
    Function-1: Loads a KDE YAML file and returns the parsed dictionary.
    Includes input validation and error handling for missing or malformed files.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"[ERROR] File not found: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(f"[ERROR] YAML does not contain a dictionary: {filepath}")
        return data
    except yaml.YAMLError as e:
        raise ValueError(f"[ERROR] Failed to parse YAML {filepath}: {e}")


def compare_element_names(kde_dict_a, kde_dict_b, file_a, file_b, output_file, mode='a'):
    """
    Function-2: Identifies differences in the two YAML files with respect to
    NAMES of key data elements only. Appends results to a single TEXT file.

    Output format per differing element:
        NAME,ABSENT-IN-<FILENAME>,PRESENT-IN-<FILENAME>,NA

    If no differences for this pair:
        NO DIFFERENCES IN REGARDS TO ELEMENT NAMES
    """
    names_a = {val['name'] for val in kde_dict_a.values() if isinstance(val, dict) and 'name' in val}
    names_b = {val['name'] for val in kde_dict_b.values() if isinstance(val, dict) and 'name' in val}

    lines = []

    # Names in A but not in B
    for name in sorted(names_a - names_b):
        lines.append(f"{name},ABSENT-IN-{file_b},PRESENT-IN-{file_a},NA")

    # Names in B but not in A
    for name in sorted(names_b - names_a):
        lines.append(f"{name},ABSENT-IN-{file_a},PRESENT-IN-{file_b},NA")

    with open(output_file, mode, encoding='utf-8') as f:
        f.write(f"# {file_a} vs {file_b}\n")
        if lines:
            f.write("\n".join(lines) + "\n")
        else:
            f.write("NO DIFFERENCES IN REGARDS TO ELEMENT NAMES\n")
        f.write("\n")

    print(f"    [INFO] Names comparison appended to: {output_file}")
    return lines if lines else ["NO DIFFERENCES IN REGARDS TO ELEMENT NAMES"]


def compare_element_names_and_requirements(kde_dict_a, kde_dict_b, file_a, file_b, output_file, mode='a'):
    """
    Function-3: Identifies differences in the two YAML files with respect to
    (i) names of key data elements AND (ii) requirements for those elements.
    Appends results to a single TEXT file.

    Output format:
        NAME,ABSENT-IN-<FILENAME>,PRESENT-IN-<FILENAME>,NA       # KDE absent in one file
        NAME,ABSENT-IN-<FILENAME>,PRESENT-IN-<FILENAME>,REQ_TEXT # requirement missing in one file

    If no differences for this pair:
        NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS
    """
    names_a = {val['name']: val.get('requirements', [])
               for val in kde_dict_a.values() if isinstance(val, dict) and 'name' in val}
    names_b = {val['name']: val.get('requirements', [])
               for val in kde_dict_b.values() if isinstance(val, dict) and 'name' in val}

    lines = []

    # Names in A but not in B
    for name in sorted(set(names_a) - set(names_b)):
        lines.append(f"{name},ABSENT-IN-{file_b},PRESENT-IN-{file_a},NA")

    # Names in B but not in A
    for name in sorted(set(names_b) - set(names_a)):
        lines.append(f"{name},ABSENT-IN-{file_a},PRESENT-IN-{file_b},NA")

    # Names in both — compare requirements
    for name in sorted(set(names_a) & set(names_b)):
        reqs_a = set(str(r).strip() for r in (names_a[name] or []))
        reqs_b = set(str(r).strip() for r in (names_b[name] or []))

        for req in sorted(reqs_a - reqs_b):
            lines.append(f"{name},ABSENT-IN-{file_b},PRESENT-IN-{file_a},{req}")

        for req in sorted(reqs_b - reqs_a):
            lines.append(f"{name},ABSENT-IN-{file_a},PRESENT-IN-{file_b},{req}")

    with open(output_file, mode, encoding='utf-8') as f:
        f.write(f"# {file_a} vs {file_b}\n")
        if lines:
            f.write("\n".join(lines) + "\n")
        else:
            f.write("NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS\n")
        f.write("\n")

    print(f"    [INFO] Requirements comparison appended to: {output_file}")
    return lines if lines else ["NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS"]


# =================================================================
# PIPELINE
# =================================================================

def run_comparator_pipeline():
    """
    Runs the comparison for all 9 required input combinations.
    Produces exactly TWO TEXT files total:
        - names_diff.txt         (element name differences for all pairs)
        - requirements_diff.txt  (element name + requirement differences for all pairs)
    """
    combinations = [
        ("cis-r1-kdes.yaml", "cis-r1-kdes.yaml"),
        ("cis-r1-kdes.yaml", "cis-r2-kdes.yaml"),
        ("cis-r1-kdes.yaml", "cis-r3-kdes.yaml"),
        ("cis-r1-kdes.yaml", "cis-r4-kdes.yaml"),
        ("cis-r2-kdes.yaml", "cis-r2-kdes.yaml"),
        ("cis-r2-kdes.yaml", "cis-r3-kdes.yaml"),
        ("cis-r2-kdes.yaml", "cis-r4-kdes.yaml"),
        ("cis-r3-kdes.yaml", "cis-r3-kdes.yaml"),
        ("cis-r3-kdes.yaml", "cis-r4-kdes.yaml"),
    ]

    NAMES_OUT = "names_diff.txt"
    REQS_OUT  = "requirements_diff.txt"

    # Clear existing output files before writing
    for f in [NAMES_OUT, REQS_OUT]:
        if os.path.exists(f):
            os.remove(f)

    print("[*] Starting Task-2 Comparison Pipeline...")

    for file_a, file_b in combinations:
        print(f"\n  Comparing: {file_a} vs {file_b}")
        try:
            data_a = load_kde_yaml(file_a)
            data_b = load_kde_yaml(file_b)
        except (FileNotFoundError, ValueError) as e:
            print(f"    [SKIP] {e}")
            continue

        compare_element_names(data_a, data_b, file_a, file_b, NAMES_OUT)
        compare_element_names_and_requirements(data_a, data_b, file_a, file_b, REQS_OUT)

    print(f"\n[SUCCESS] Task-2 complete.")
    print(f"  -> {NAMES_OUT}")
    print(f"  -> {REQS_OUT}")


# =================================================================
# UNIT TESTS  (3 required — one per function)
# =================================================================

class TestTask2(unittest.TestCase):

    # --- sample data shared across tests ---
    DICT_A = {
        "element1": {"name": "Audit",   "requirements": ["Enable logs", "Rotate logs"]},
        "element2": {"name": "Network", "requirements": ["Restrict ports"]},
    }
    DICT_B = {
        "element1": {"name": "Audit",   "requirements": ["Enable logs", "Encrypt logs"]},
        "element2": {"name": "Logging", "requirements": ["Collect logs"]},
    }

    def test_f1_load_kde_yaml(self):
        """Function-1: load_kde_yaml raises FileNotFoundError for missing file."""
        with self.assertRaises(FileNotFoundError):
            load_kde_yaml("nonexistent_file.yaml")

    def test_f2_compare_element_names(self):
        """Function-2: compare_element_names detects name-level differences."""
        out = "test_names_diff.txt"
        result = compare_element_names(self.DICT_A, self.DICT_B, "a.yaml", "b.yaml", out)

        # 'Network' is in A but not B; 'Logging' is in B but not A
        self.assertTrue(any("Network" in line for line in result))
        self.assertTrue(any("Logging" in line for line in result))
        self.assertTrue(any("NA" in line for line in result))

        # Verify the file was actually written
        self.assertTrue(os.path.exists(out))
        with open(out) as f:
            content = f.read()
        self.assertIn("Network", content)
        self.assertIn("Logging", content)
        os.remove(out)

    def test_f3_compare_element_names_and_requirements(self):
        """Function-3: compare_element_names_and_requirements detects requirement-level differences."""
        out = "test_reqs_diff.txt"
        result = compare_element_names_and_requirements(self.DICT_A, self.DICT_B, "a.yaml", "b.yaml", out)

        # 'Rotate logs' in A not in B; 'Encrypt logs' in B not in A
        self.assertTrue(any("Rotate logs" in line for line in result))
        self.assertTrue(any("Encrypt logs" in line for line in result))

        self.assertTrue(os.path.exists(out))
        with open(out) as f:
            content = f.read()
        self.assertIn("Audit", content)
        os.remove(out)


# =================================================================
# ENTRY POINT
# =================================================================

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTask2)
    test_result = unittest.TextTestRunner(verbosity=2).run(suite)

    if test_result.wasSuccessful():
        run_comparator_pipeline()
