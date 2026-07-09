# Airport AI Platform: Evaluation Suite

This directory contains the strategy and dataset definitions for evaluating the performance, faithfulness, and routing accuracy of the AI agents within the Airport AI Platform.

> **Note:** This repository currently relies on `pytest` for unit and integration testing. The documents in this directory represent the **methodology and dataset** required for establishing an automated LLM evaluation pipeline (e.g., using DeepEval, Ragas, or TruLens) in future development phases.

## Contents

- **[Evaluation Strategy](evaluation_strategy.md)**: Defines the mathematical and logical success criteria for measuring agent performance (Faithfulness, Context Precision, SQL Accuracy).
- **[Test Questions](test_questions.md)**: A curated dataset of natural language queries mapped to their expected routes and agent behaviors, used as the benchmark for regressions.

## Future Implementation

To implement this suite programmatically, the system will require:
1. An LLM-as-a-Judge framework (evaluating responses against the provided context).
2. A shadow database initialized with a static snapshot of `operational_metrics` to ensure SQL evaluation is deterministic.
3. A CI/CD hook that runs the evaluation dataset against the `WorkflowOrchestrator` on every pull request.
