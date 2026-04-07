# Task-1 Prompt Deliverables

## zero-shot
```text
TASK: Extract Key Data Elements (KDEs) from text.
FORMAT: YAML list of objects.
SCHEMA: - element1: {name: string, requirements: [string]}

Text: [DOC]
```

## few-shot
```text
Example:
Input: 'User_IDs must be encrypted.'
Output:
- element1:
    name: User_IDs
    requirements: ['encrypted']

Task: Extract KDEs from:
[DOC]
```

## chain-of-thought
```text
You are a security requirements analyst.

Extract Key Data Elements (KDEs).

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
[DOC]
```
