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

## CODE TO OPTIMIZE
Here is the current implementation of the bottleneck function:

[UPLOAD OR PASTE FULL FUNCTION CODE HERE]

## CONSTRAINTS
- Do NOT change the function's external interface:
  - Keep the same function name
  - Keep the same arguments and return types
- Do NOT change the observable behavior:
  - The function must produce the same outputs for the same inputs
- You MAY:
  - Refactor internals
  - Use more efficient data structures or algorithms
  - Use built-in or standard library functions
  - Vectorize operations where appropriate
- Avoid introducing heavy external dependencies unless absolutely necessary

## WHAT I WANT FROM YOU
1. Briefly analyze the current function:
   - Where is the time likely being spent?
   - Which patterns or operations look expensive?

2. Propose an optimized version of the function:
   - Provide the full updated code
   - Keep it readable and maintainable

3. Explain the changes:
   - What did you change and why?
   - How does this improve performance?
   - Are there any trade-offs (e.g., memory vs speed, readability vs speed)?

4. (Optional but helpful) Suggest additional ideas:
   - If there are further optimizations that depend on broader pipeline changes, mention them

## OPTIONAL EXTRA CONTEXT (IF AVAILABLE)
If it helps, here is a small example of typical input and expected output for this function:

[PASTE SAMPLE INPUT/OUTPUT HERE]

## QUESTIONS FOR CLARITY (PLEASE ASK BEFORE CODING IF NEEDED)
Before you rewrite the function, if anything is unclear, ask me questions such as:
- Are there any edge cases or special inputs I should be aware of?
- Are there any constraints on memory usage?
- Is it acceptable to use additional helper functions within the same module?
- Are there any parts of the behavior that are more important than raw speed (e.g., numerical stability, exact formatting, etc.)?"""


def get_optimization_prompt() -> str:
    """Get the LLM optimization prompt template."""
    return _OPTIMIZATION_PROMPT
