# RAG Hallucination Problem - Root Cause Analysis & Solution

**Issue:** The Medical RAG QA system is generating hallucinated answers unrelated to the user's query.

**Test Query:** "What are the symptoms of diabetes?"  
**Actual Answer:** Talking about brain tumors, cesarean sections, and unrelated conditions  
**Expected:** Symptoms like increased thirst, frequent urination, fatigue, blurred vision

---

## 🔍 Root Cause Analysis

### Issue 1: **Poor Vector Store Quality** (CRITICAL)
**Problem:** ChromaDB contains 10,000 documents but mostly genetics/rare diseases, NOT common conditions

**Evidence:**
- Query: "diabetes symptoms" 
- Retrieved docs: Brain tumor papers, genetic disorders, rare diseases
- Confidence: 2-3% (system knows it's wrong!)

**Why This Happens:**
- Vector store was built from MedQuAD which includes:
  - Cancer documents (116 files)
  - Genetics Home Reference (1,086 files - rare genetic conditions)
  - Genetic and Rare Diseases (2,685 files)
  - Very few general health topics about common conditions

**Impact:** ❌ **RAG retrieves irrelevant documents → LLM has no good evidence → hallucination**

---

### Issue 2: **BioGPT Ignoring Evidence** (MAJOR)
**Problem:** BioGPT generates text from its training data instead of using the provided evidence

**Evidence:**
```
Prompt includes: "Diabetes TREATED_BY Metformin"  
BioGPT outputs: "cesarean section due to fetal distress..."
```

**Why This Happens:**
- BioGPT-Large is pre-trained on PubMed abstracts
- Model has strong priors from 3.5B parameters
- Generation parameters allow model to "drift" from prompt
- Prompt format not optimized for instruction-following

**Impact:** ⚠️ Even with correct evidence, model hallucinates

---

### Issue 3: **Low Confidence Not Acting as Circuit Breaker**
**Problem:** System generates answers even with 2% confidence

**Evidence:**
```json
"confidence": 0.024223477160929405  // 2.4%
"answer": "<hallucinated content>"
```

**Why This Happens:**
- No minimum confidence threshold enforced
- Low confidence triggers fallback retrieval but still generates
- Safety validator only checks medical safety, not factual accuracy

**Impact:** ⚠️ System outputs garbage instead of refusing to answer

---

## ✅ Solution Strategy

### **Immediate Fix (Phase 1)** - Prevent Hallucination

#### 1. Add Confidence Threshold Guard
```python
# In backend/generators/answer_generator.py
MIN_CONFIDENCE_THRESHOLD = 0.3  # 30% minimum

if evidence.combined_confidence < MIN_CONFIDENCE_THRESHOLD:
    return GeneratedAnswer(
        answer="I don't have enough reliable information in my knowledge base to answer this question accurately. Please consult a healthcare professional.",
        confidence=0.0,
        sources=[],
        reasoning="Insufficient evidence confidence"
    )
```

#### 2. Improve Fallback to Use ONLY Evidence
```python
def _generate_fallback(self, prompt: str, evidence_texts: List[str]) -> str:
    """STRICT evidence-only fallback - NO hallucination"""
    if not evidence_texts or len(evidence_texts) == 0:
        return "No relevant medical information found."
    
    # Extract ONLY from evidence, first 3 sources
    answer_parts = []
    for evidence in evidence_texts[:3]:
        # Extract Q&A format answers
        if 'A:' in evidence:
            answer = evidence.split('A:', 1)[1].strip()
            answer_parts.append(answer)
    
    # Combine and limit to 40 words
    combined = ' '.join(answer_parts)
    words = combined.split()[:40]
    return ' '.join(words) + '.'
```

#### 3. Force BioGPT to Follow Evidence
```python
# Use constrained beam search
gen_kwargs = {
    'max_new_tokens': 60,
    'min_new_tokens': 20,
    'num_beams': 4,          # Beam search for better coherence
    'no_repeat_ngram_size': 3,
    'temperature': 0.3,      # LOWER temp = less creativity = less hallucination
    'top_p': 0.85,
    'do_sample': False,      # Greedy decoding = more deterministic
}
```

---

### **Data Quality Fix (Phase 2)** - Improve Retrieval

#### 1. Add Common Medical Conditions Dataset
**Current Data:** Mostly rare/genetic diseases  
**Needed:** Common health topics (diabetes, hypertension, flu, etc.)

**Sources to Add:**
- NIH MedlinePlus (general health topics)
- CDC health info (common conditions)
- Mayo Clinic symptom guides
- WHO fact sheets

**Command:**
```bash
# Process general health topics
python scripts/download_medlineplus.py  # Create this script
python scripts/build_vector_store.py --include-general-health
```

#### 2. Improve BM25 Coverage
**Current:** 3 documents (almost useless)  
**Needed:** Process full MedQuAD dataset

**Command:**
```bash
cd /home/adhu/alefragnani.project-manager/medical-rag-qa
python scripts/process_medquad.py  # Takes ~10 minutes
python scripts/build_sparse_index.py  # Rebuild with 16K docs
```

#### 3. Add Diabetes-Specific Knowledge to KG
**Current KG:** 9 nodes (very limited)  
**Needed:** Expand with common conditions

```python
# In backend/retrievers/kg_retriever.py
# Add common medical facts:
kg.add_edge("Diabetes", "CAUSES", "High_Blood_Sugar")
kg.add_edge("Type_1_Diabetes", "SYMPTOM", "Increased_Thirst")
kg.add_edge("Type_1_Diabetes", "SYMPTOM", "Frequent_Urination")
kg.add_edge("Type_2_Diabetes", "RISK_FACTOR", "Obesity")
kg.add_edge("Diabetes", "COMPLICATION", "Diabetic_Retinopathy")
```

---

### **Model Fix (Phase 3)** - Replace or Fine-tune BioGPT

#### Option A: Use Template-Only (Safest)
Disable BioGPT generation entirely, use evidence-extraction only

```python
# Force fallback mode always
def generate(self, query, evidence, mode):
    return self._generate_fallback("", [ev.content for ev in evidence.evidences])
```

**Pros:** ✅ No hallucination  
**Cons:** ❌ Less fluent answers

#### Option B: Switch to GPT-3.5/4 (Best Quality)
Use OpenAI API for better instruction-following

```python
# In .env
MODEL_TYPE=openai
OPENAI_API_KEY=sk-xxx
```

**Pros:** ✅ Excellent instruction-following, no hallucination  
**Cons:** ❌ Requires API key, costs money

#### Option C: Fine-tune BioGPT (Most Work)
Train BioGPT on medical Q&A pairs to follow evidence

**Pros:** ✅ Local, no API costs, optimized for medical domain  
**Cons:** ❌ Requires GPU, training data, time

---

## 📊 Implementation Priority

### **HIGH PRIORITY** (Do Now)
1. ✅ Add confidence threshold guard (5 min)
2. ✅ Improve fallback to extract-only (10 min)
3. ✅ Lower BioGPT temperature to 0.3 (1 min)

### **MEDIUM PRIORITY** (This Week)
4. Process full MedQuAD → rebuild BM25 (30 min)
5. Expand Knowledge Graph with common conditions (1 hour)
6. Add logging to track retrieval quality (30 min)

### **LOW PRIORITY** (Future)
7. Add general health dataset (MedlinePlus, etc.)
8. Consider switching to GPT-3.5-turbo
9. Fine-tune BioGPT on medical Q&A pairs

---

## 🧪 Testing Plan

### Test Queries (Common Conditions)
```
1. "What are the symptoms of diabetes?"
2. "How is hypertension treated?"
3. "What causes a heart attack?"
4. "What are the signs of depression?"
5. "How do I prevent the flu?"
```

### Expected Behavior AFTER Fixes
- **If good evidence found (confidence > 30%):** Generate from evidence, no hallucination
- **If poor evidence (confidence < 30%):** Refuse to answer, suggest consulting doctor
- **If no evidence:** Return "Information not available in knowledge base"

### Success Metrics
- ✅ Confidence > 50% for common conditions
- ✅ Zero hallucinations (answers match evidence)
- ✅ Graceful degradation (refuse when unsure)
- ✅ Sources correctly cited

---

## 🎯 Summary

**The RAG system hallucination is caused by:**

1. **PRIMARY:** Vector store lacks common medical knowledge (has rare diseases instead)
2. **SECONDARY:** BioGPT not constrained enough, generates from training data
3. **TERTIARY:** No confidence threshold to refuse low-quality answers

**Quickest fix:** Add confidence guard + improve fallback (< 20 min)  
**Best fix:** Add general health data + process full MedQuAD (< 2 hours)  
**Ultimate fix:** Use GPT-3.5 or fine-tune BioGPT (requires resources)

**Remember:** RAG is only as good as its knowledge base. If ChromaDB doesn't have diabetes info, no amount of prompt engineering will help!

---

*Analysis Date: January 7, 2026*  
*System: Medical RAG QA v1.0*
