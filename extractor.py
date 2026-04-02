import os
import pdfplumber
import yaml
import torch
from transformers import pipeline

class SecurityRequirementsExtractor:
    def __init__(self, model_id="google/gemma-3-1b-it"):
        """
        Initialize the LLM pipeline for Gemma-3.
        The device_map="auto" will automatically handle CPU/GPU allocation.
        """
        print(f"Loading model: {model_id}...")
        self.generator = pipeline(
            "text-generation", 
            model=model_id, 
            torch_dtype=torch.bfloat16, 
            device_map="auto"
        )

    def get_pdf_text(self, file_path):
        """
        Extracts all text content from the specified PDF file.
        """
        text = ""
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} not found.")
            return None
            
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    def build_prompt(self, technique, text_segment):
        """
        Constructs the LLM prompt based on the chosen prompting technique.
        """
        if technique == "zero-shot":
            return f"Role: Security Auditor. Task: Extract security requirements from the following text as a list:\n\n{text_segment}"
        
        elif technique == "few-shot":
            return (
                "Example 1: 'Enable S3 bucket versioning.' -> Requirement: S3 versioning enabled.\n"
                "Example 2: 'Restrict SSH access to specific IPs.' -> Requirement: SSH restricted.\n"
                f"Task: Extract requirements from this text: {text_segment}"
            )
        
        elif technique == "cot":
            return (
                "Step 1: Identify all security-related policy statements in the text.\n"
                "Step 2: Summarize them as concise security requirements.\n"
                f"Text: {text_segment}"
            )

    def run_full_task(self, pdf_file):
        """
        Runs the extraction using all three techniques and saves results to YAML.
        """
        raw_text = self.get_pdf_text(pdf_file)
        if not raw_text:
            return

        # Use the first 1500 characters for initial testing
        context = raw_text[:1500] 

        techniques = ["zero-shot", "few-shot", "cot"]
        for tech in techniques:
            print(f"--- Running {tech} extraction ---")
            prompt = self.build_prompt(tech, context)
            
            # Generate response from LLM
            output = self.generator(
                prompt, 
                max_new_tokens=250, 
                do_sample=True, 
                temperature=0.7
            )
            result_text = output[0]['generated_text']

            # Prepare data for YAML storage
            data = {
                "course": "COMP 5700/6700",
                "technique": tech,
                "source": pdf_file,
                "extracted_requirements": result_text
            }
            
            output_filename = f"requirements_{tech}.yaml"
            with open(output_filename, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
            print(f"Successfully saved results to: {output_filename}")

if __name__ == "__main__":
    # Ensure the file 'cis-r1.pdf' exists in the same directory
    extractor = SecurityRequirementsExtractor()
    extractor.run_full_task("cis-r1.pdf")
