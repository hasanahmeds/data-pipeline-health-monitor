"""
LLM optimization prompt template for bottleneck functions.

This module provides a reusable prompt template that users can copy and use
with their preferred LLM (ChatGPT, Claude, etc.) to optimize performance-critical
functions identified by PipelineScope.
"""

import warnings

warnings.filterwarnings(action="ignore", category=DeprecationWarning)

_OPTIMIZATION_PROMPT = """# LLM Prompt Template for Optimizing Bottleneck Functions

Use this template with your LLM of choice to optimize bottleneck functions identified by PipelineScope.

---

## ROLE
You are an expert Python performance engineer and software architect. You specialize in analyzing real-world profiling data, identifying bottlenecks, and rewriting code to be faster and more efficient while preserving behavior and interfaces.

## OBJECTIVE
I have a Python function that has been identified as a performance bottleneck in my pipeline by a profiling tool (PipelineScope). Your job is to:
- Analyze the function in the context of the pipeline
- Use the provided profiling data to understand why it is slow
- Propose an optimized version of the function
- Explain the changes, trade-offs, and any potential risks
- Keep the external behavior, inputs, and outputs identical

## PIPELINE CONTEXT (FROM PIPELINESCOPE)
[Paste a short description of what your pipeline does, in your own words.
Example: "This pipeline loads data from disk, preprocesses text, runs a model, and writes predictions to a database."]

## BOTTLENECK FUNCTION METRICS (FROM PIPELINESCOPE)
Function name: [e.g., preprocess.clean_text]
Module/file: [e.g., preprocess.py]
Total observed time: [e.g., 3.2 seconds]
Percentage of total pipeline time: [e.g., 47%]
Projected time at scale (expected_size): [e.g., 2.1 hours]
Number of calls: [e.g., 10,000]
