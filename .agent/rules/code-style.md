---
trigger: model_decision
---

Please follow this workflow strictly while code writing:
  1. Create files   
  Code Quality Requirements (CRITICAL):
  - ✅ Write extensive, production-ready code with comprehensive functionality
  - ✅ Ensure ZERO errors - function signatures, and logic flow
  - ✅ Use modular design - separate concerns, single responsibility principle
  - ✅ Add clear, concise docstrings for modules, classes, and complex functions
  - ✅ Use type hints for all function parameters and return values
  - ✅ Follow PEP 8 style guidelines strictly
  - ✅ Handle edge cases with explicit conditional logic
  ABSOLUTE PROHIBITIONS:
  - ❌ DO NOT use try/except blocks - I want explicit error handling through validation and conditional logic
  - ❌ DO NOT use bare except clauses
  - ❌ DO NOT wrap code in exception handlers
  - Instead, use defensive programming: validate inputs, check conditions, return error states/None/default values
  Process for each file:
  1. Analyze what the file should contain based on the project architecture
  2. Read any related files to understand interfaces and dependencies
  3. Present the complete file implementation