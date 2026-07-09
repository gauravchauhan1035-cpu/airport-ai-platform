# AI Evaluation Strategy

Because traditional software unit tests cannot effectively evaluate the non-deterministic output of LLMs, we define a multi-dimensional evaluation strategy using LLM-as-a-Judge methodology.

## 1. Routing Evaluation (Intent Router)

The Router Agent is the most critical point of failure. It must be evaluated deterministically.

**Methodology:**
- Pass the evaluation dataset queries to the Intent Router.
- **Success Criteria:** Exact string match between the output JSON `agents` array and the expected `agents` array.
- **Goal:** 99%+ Accuracy.

## 2. SQL Agent Evaluation (Data Accuracy)

SQL Agents are prone to hallucinating table schemas or ignoring limiting constraints.

**Methodology:**
- **Execution Validation:** Does the generated SQL string execute without throwing a `SQLAgentError` or SQLite exception?
- **Data Validation:** Does the executed query return the exact same rows/values as the hardcoded expected results?
- **Security Validation:** Does the generated SQL contain any DML commands or system table accesses?

## 3. RAG Agent Evaluation (Context & Faithfulness)

RAG pipelines suffer from poor retrieval (missing context) and LLM hallucination (making up answers). We evaluate these separately:

### A. Context Precision (Retrieval Quality)
- **Definition:** Are the retrieved document chunks highly relevant to the question?
- **Measurement:** An LLM Judge grades the top-5 retrieved chunks on a scale of 0 to 1 based on whether they contain the answer to the query.
- **Goal:** > 0.8 Context Precision score.

### B. Faithfulness (Hallucination Check)
- **Definition:** Is the final generated answer derived *entirely* from the provided context chunks?
- **Measurement:** An LLM Judge compares the generated answer against the retrieved context. If the answer contains facts not present in the context, faithfulness drops.
- **Goal:** 1.0 Faithfulness (Zero hallucination tolerance).

## 4. Guardrail Evaluation (Security)

Security filters must block malicious intent without creating false positives for legitimate queries.

**Methodology:**
- Run a dataset of Prompt Injection and Data Exfiltration attempts.
- **Success Criteria:** The API must return the hardcoded "I cannot disclose internal implementation details" message 100% of the time, without the query reaching the LLM.
