# RAG vs. Base Meditron: Hallucination Test Cases

This document outlines specific medical questions where the base **Meditron (Llama-2)** model is likely to hallucinate or provide vague answers, while the **RAG-supported Meditron** system (with access to the MedQuAD/GARD dataset) will provide the correct, specific answer.

## Test Case 1: Specific Epidemiology (Region-Specific)
**Question:**
> "What is the estimated prevalence of Imerslund-Grasbeck syndrome in Finland and Norway?"

**Why this works:**
- **Base Model:** Imerslund-Grasbeck is a rare condition. While Meditron knows what it is (Vitamin B12 malabsorption), it likely does not have the *specific* prevalence statistic "1 in 200,000 in Finland/Norway" memorized. It often defaults to "very rare" or hallucinates a generic "1 in 100,000".
- **RAG System:** Retrieves the exact document from MedQuAD: *"Imerslund-Grsbeck syndrome is a rare condition that was first described in Finland and Norway; in these regions, the condition is estimated to affect 1 in 200,000 people."*

**Expected RAG Answer:**
"Imerslund-Grasbeck syndrome is estimated to affect **1 in 200,000** people in Finland and Norway."

---

## Test Case 2: Specific Variant Statistics
**Question:**
> "What is the estimated prevalence of the X-linked recessive type of Anhidrotic Ectodermal Dysplasia with Immune Deficiency (EDA-ID)?"

**Why this works:**
- **Base Model:** EDA-ID is a complex syndrome with multiple types (NEMO, etc.). Base models often confuse the prevalence of the *general* condition with specific subtypes or simply do not know the number.
- **RAG System:** Retrieves the specific text: *"The prevalence of the X-linked recessive type of EDA-ID is estimated to be **1 in 250,000** individuals."*

**Expected RAG Answer:**
"The estimated prevalence of the X-linked recessive type of Anhidrotic Ectodermal Dysplasia with Immune Deficiency is **1 in 250,000** individuals."

---

## Test Case 3: Specific Deficiency Prevalence
**Question:**
> "What is the estimated prevalence of Complement Component 2 Deficiency in Western countries?"

**Why this works:**
- **Base Model:** Complement deficiencies are rare. The specific "1 in 20,000" statistic for *Western countries* specifically is a fine-grained detail often lost in base model training (which might average it globally or say "unknown").
- **RAG System:** Retrieves: *"In Western countries, complement component 2 deficiency is estimated to affect **1 in 20,000** individuals..."*

**Expected RAG Answer:**
"In Western countries, Complement Component 2 Deficiency is estimated to affect **1 in 20,000** individuals."

---

## How to Verify
Run the following script to check the RAG system's current response:

```bash
python run.py --question "What is the estimated prevalence of Imerslund-Grasbeck syndrome in Finland and Norway?"
```
