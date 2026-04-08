import os
import yaml
import PyPDF2
import unittest
import torch
import re
from transformers import pipeline
from unittest.mock import patch, mock_open, MagicMock

# =================================================================
# TASK-1: CORE FUNCTIONS (6 REQUIRED)
# =================================================================

def load_and_validate_documents(doc_path1, doc_path2):
    """
    Function-1: Validates existence and extracts text from two PDF files.
    """
    extracted_data = {}
    for path in [doc_path1, doc_path2]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing required file: {path}")
        
        text = ""
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
        
        extracted_data[os.path.basename(path)] = text.strip()
    return extracted_data
    
def clean_text(text):
    text = re.sub(r'Page\s+\d+', ' ', text)
    text = re.sub(r'Terms of Use.*?(?=Overview|Recommendations|1\s+Control Plane Components|2\s+Control Plane Configuration)', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'Table of Contents.*?(?=Overview|Recommendations|1\s+Control Plane Components|2\s+Control Plane Configuration)', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'Internal Only - General', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
    
def construct_zero_shot_prompt(doc_text):
    """
    Function-2: Creates a zero-shot prompt for KDE extraction.
    """
    return (
        "TASK: Extract Key Data Elements (KDEs) from text.\n"
        "FORMAT: YAML list of objects.\n"
        "SCHEMA: - element1: {name: string, requirements: [string]}\n\n"
        f"Text: {doc_text}"
    )

def construct_few_shot_prompt(doc_text):
    """
    Function-3: Creates a few-shot prompt with a structured example.
    """
    example = (
        "Example:\nInput: 'User_IDs must be encrypted.'\nOutput:\n"
        "- element1:\n    name: User_IDs\n    requirements: ['encrypted']\n\n"
    )
    return f"{example}Task: Extract KDEs from:\n{doc_text}"

def construct_chain_of_thought_prompt(doc_text):
    """
    Function-4: Creates a Chain of Thought prompt.
    """
    return f"""
You are a security requirements analyst.

Extract Key Data Elements (KDEs) and their associated requirements.

Rules:
- Ignore table of contents, page numbers, headers, footers, terms of use, and document metadata.
- Only extract real security requirements.
- Do NOT describe the document.
- Do NOT summarize the document.
- Output ONLY valid YAML.
- Use this exact format:

element1:
  name: "example_kde"
  requirements:
    - "requirement 1"
    - "requirement 2"

element2:
  name: "example_kde"
  requirements:
    - "requirement 1"

Text:
{doc_text}
"""

def extract_kdes_with_llm(pipe, prompt, doc_name):
    """
    Function-5: Executes LLM inference and saves results to a YAML file.
    """
    print(f"    [DEBUG] Starting LLM inference for {doc_name}...")
    
    # Use only max_new_tokens to avoid conflict with model config's max_length
def extract_kdes_with_llm(pipe, prompt, doc_name):
    """
    Function-5: Executes LLM inference and saves results to a YAML file.
    """
    print(f"    [DEBUG] Starting LLM inference for {doc_name}...")

    result = pipe(
        prompt,
        max_new_tokens=512,
        do_sample=False,
        pad_token_id=pipe.tokenizer.eos_token_id
    )

    raw_output = result[0]['generated_text']
    clean_yaml = raw_output.replace(prompt, "").strip()

    if "```yaml" in clean_yaml:
        clean_yaml = clean_yaml.split("```yaml", 1)[1].split("```", 1)[0].strip()
    elif "```" in clean_yaml:
        clean_yaml = clean_yaml.split("```", 1)[1].strip()

    if "element1:" in clean_yaml:
        clean_yaml = clean_yaml[clean_yaml.index("element1:"):].strip()

    if "The document is about" in clean_yaml:
        raise ValueError(f"Bad summary output for {doc_name}")

    if "Data source:" in clean_yaml or "Security focus:" in clean_yaml:
        raise ValueError(f"Bad summary-style output for {doc_name}")

    if "element1:" not in clean_yaml:
        raise ValueError(f"No KDE YAML structure found for {doc_name}")

    output_filename = f"{os.path.splitext(doc_name)[0]}-kdes.yaml"

    try:
        data = yaml.safe_load(clean_yaml)

        if not isinstance(data, dict) or not data:
            raise ValueError("Parsed YAML is empty or not a dictionary.")

        for key, value in data.items():
            if not isinstance(value, dict):
                raise ValueError("Each element must map to a dictionary.")
            if "name" not in value or "requirements" not in value:
                raise ValueError("Missing name or requirements field.")
            if not isinstance(value["requirements"], list):
                raise ValueError("Requirements must be a list.")

        with open(output_filename, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, sort_keys=False, default_flow_style=False)
        print(f"    [DEBUG] Successfully saved {output_filename}")

    except Exception as e:
        print(f"    [WARNING] YAML parsing failed for {doc_name}. Saving raw text.")
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(clean_yaml)

    return clean_yaml

def collect_output_and_dump(llm_name, prompt_used, p_type, llm_output, log_path):
    """
    Function-6: Appends LLM interaction metadata to a central log file.
    """
    entry = (
        f"*LLM Name*\n{llm_name}\n\n"
        f"*Prompt Used*\n{prompt_used}\n\n"
        f"*Prompt Type*\n{p_type}\n\n"
        f"*LLM Output*\n{llm_output}\n"
        f"{'='*50}\n\n"
    )
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(entry)

# =================================================================
# HELPERS & TESTING
# =================================================================

def generate_prompt_markdown():
    """Generates the PROMPT.md deliverable."""
    content = (
        "# Task-1 Prompt Deliverables\n\n"
        "## zero-shot\n```text\n" + construct_zero_shot_prompt("[DOC]") + "\n```\n\n"
        "## few-shot\n```text\n" + construct_few_shot_prompt("[DOC]") + "\n```\n\n"
        "## chain-of-thought\n```text\n" + construct_chain_of_thought_prompt("[DOC]") + "\n```\n"
    )
    with open("PROMPT.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("[DEBUG] PROMPT.md written.")

class TestTask1(unittest.TestCase):
    @patch('os.path.exists', return_value=True)
    @patch('PyPDF2.PdfReader')
    def test_f1_load(self, m_reader, m_exists):
        m_reader.return_value.pages = [MagicMock(extract_text=lambda: "data")]
        with patch('builtins.open', mock_open()):
            res = load_and_validate_documents("r1.pdf", "r2.pdf")
            self.assertEqual(len(res), 2)
    def test_f2_z(self): self.assertIn("Text", construct_zero_shot_prompt("t"))
    def test_f3_f(self): self.assertIn("Example", construct_few_shot_prompt("t"))
    def test_f4_c(self): self.assertIn("Output ONLY valid YAML", construct_chain_of_thought_prompt("t"))
    @patch('builtins.open', new_callable=mock_open)
    def test_f5_llm(self, m_open):
        m_p = MagicMock(); m_p.return_value = [{'generated_text': 'e: test'}]; m_p.tokenizer.eos_token_id=2
        res = extract_kdes_with_llm(m_p, "p", "t.pdf"); self.assertIn("e", res)
    @patch('builtins.open', new_callable=mock_open)
    def test_f6_log(self, m_open): collect_output_and_dump("G", "p", "t", "o", "l.txt"); m_open.assert_called()

def run_pipeline(token):
    generate_prompt_markdown()
    
    print("[DEBUG] Loading Gemma-3-1B-it into GPU...")
    try:
        # Force specific device to ensuring it uses your 4060 Ti
        pipe = pipeline(
            "text-generation", 
            model="google/gemma-3-1b-it", 
            token=token, 
            device=0, # Use first GPU
            torch_dtype=torch.bfloat16
        )
    except Exception as e:
        print(f"[ERROR] Failed to init LLM: {e}")
        return

    combinations = [
        ("cis-r1.pdf", "cis-r1.pdf"), ("cis-r1.pdf", "cis-r2.pdf"),
        ("cis-r1.pdf", "cis-r3.pdf"), ("cis-r1.pdf", "cis-r4.pdf"),
        ("cis-r2.pdf", "cis-r2.pdf"), ("cis-r2.pdf", "cis-r3.pdf"),
        ("cis-r2.pdf", "cis-r4.pdf"), ("cis-r3.pdf", "cis-r3.pdf"),
        ("cis-r3.pdf", "cis-r4.pdf")
    ]
    
    log_file = "all_llm_outputs.txt"
    if os.path.exists(log_file): os.remove(log_file)

    llm_cache = {}

    for idx, (f_a, f_b) in enumerate(combinations):
        print(f"\n[*] STARTING COMBINATION {idx+1}/9: ({f_a}, {f_b})")
        try:
            doc_texts = load_and_validate_documents(f_a, f_b)
            for fname, text in doc_texts.items():
                if fname not in llm_cache:
                    # Truncate text if it's too long for 1B model's comfort
                    cleaned = clean_text(text)
                    truncated_text = text[:3000] # Safe limit for standard context
                    p_text = construct_chain_of_thought_prompt(truncated_text)
                    raw_out = extract_kdes_with_llm(pipe, p_text, fname)
                    llm_cache[fname] = (p_text, raw_out)
                
                cached_p, cached_out = llm_cache[fname]
                collect_output_and_dump("Gemma-3-1B", cached_p, "chain-of-thought", cached_out, log_file)
        except Exception as e:
            print(f"    [ERROR] Skipping pair: {e}")

    print("\n[SUCCESS] All files and logs generated.")

if __name__ == "__main__":
    test_result = unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestTask1))
    if test_result.wasSuccessful():
        hf_token = input("Enter HF Token: ").strip()
        if hf_token: run_pipeline(hf_token)
