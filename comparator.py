import yaml
import os
import json
import unittest

# =================================================================
# TASK-2: CORE FUNCTIONS
# =================================================================

def load_kde_yaml(filepath):
    """
    Function-1: Loads a KDE YAML file and returns the dictionary.
    Includes basic error handling for missing or malformed files.
    """
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[ERROR] Failed to parse YAML {filepath}: {e}")
        return None

def compare_kdes(kde_dict_a, kde_dict_b):
    """
    Function-2: Compares two KDE dictionaries and identifies differences.
    Returns a dictionary with 'added', 'removed', and 'modified' categories.
    """
    results = {
        "added": [],
        "removed": [],
        "modified": []
    }

    # Extract names for easier comparison
    # Structure in YAML: elementX: {name: "...", requirements: [...]}
    names_a = {val['name']: val['requirements'] for val in kde_dict_a.values() if 'name' in val}
    names_b = {val['name']: val['requirements'] for val in kde_dict_b.values() if 'name' in val}

    set_a = set(names_a.keys())
    set_b = set(names_b.keys())

    # 1. Identify Added KDEs
    for name in set_b - set_a:
        results["added"].append({"name": name, "requirements": names_b[name]})

    # 2. Identify Removed KDEs
    for name in set_a - set_b:
        results["removed"].append({"name": name, "requirements": names_a[name]})

    # 3. Identify Modified KDEs (Exist in both but requirements changed)
    for name in set_a & set_b:
        if sorted(names_a[name]) != sorted(names_b[name]):
            results["modified"].append({
                "name": name,
                "old_requirements": names_a[name],
                "new_requirements": names_b[name]
            })

    return results

# =================================================================
# HELPERS & UNIT TESTS
# =================================================================

class TestTask2(unittest.TestCase):
    def test_comparison_logic(self):
        dict_a = {"element1": {"name": "Audit", "requirements": ["Req1"]}}
        dict_b = {"element1": {"name": "Audit", "requirements": ["Req2"]}, 
                  "element2": {"name": "Logging", "requirements": ["Req3"]}}
        
        diff = compare_kdes(dict_a, dict_b)
        self.assertEqual(len(diff["added"]), 1)    # Logging is new
        self.assertEqual(len(diff["modified"]), 1) # Audit changed
        self.assertEqual(diff["added"][0]["name"], "Logging")

def run_comparator_pipeline():
    """
    Runs the comparison for all 9 required combinations and saves the results.
    """
    combinations = [
        ("cis-r1-kdes.yaml", "cis-r1-kdes.yaml"), ("cis-r1-kdes.yaml", "cis-r2-kdes.yaml"),
        ("cis-r1-kdes.yaml", "cis-r3-kdes.yaml"), ("cis-r1-kdes.yaml", "cis-r4-kdes.yaml"),
        ("cis-r2-kdes.yaml", "cis-r2-kdes.yaml"), ("cis-r2-kdes.yaml", "cis-r3-kdes.yaml"),
        ("cis-r2-kdes.yaml", "cis-r4-kdes.yaml"), ("cis-r3-kdes.yaml", "cis-r3-kdes.yaml"),
        ("cis-r3-kdes.yaml", "cis-r4-kdes.yaml")
    ]

    all_comparison_results = {}

    print("[*] Starting Task-2 Comparison...")

    for file_a, file_b in combinations:
        pair_key = f"{file_a}_vs_{file_b}"
        print(f"    Comparing: {pair_key}")
        
        data_a = load_kde_yaml(file_a)
        data_b = load_kde_yaml(file_b)

        if data_a and data_b:
            diff = compare_kdes(data_a, data_b)
            all_comparison_results[pair_key] = diff
        else:
            print(f"    [SKIP] Missing data for {pair_key}")

    # Save final comparison summary
    output_file = "comparison_summary.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_comparison_results, f, indent=4)
    
    print(f"\n[SUCCESS] Task-2 complete. Results saved to {output_file}")

if __name__ == "__main__":
    # Run unit tests first
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTask2)
    test_result = unittest.TextTestRunner(verbosity=1).run(suite)
    
    if test_result.wasSuccessful():
        run_comparator_pipeline()