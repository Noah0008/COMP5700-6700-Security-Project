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
1. Identify KDEs.
2. Map to requirements.
3. Output YAML.
STRICT: No dashes for names.

Document: [DOC]

Let's think step by step.
```
