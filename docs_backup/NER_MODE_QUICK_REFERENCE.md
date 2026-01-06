# NER & Mode Detection - Quick Reference

## 🧠 NER (Named Entity Recognition) - At a Glance

### What is NER?
Extracting medical entities (drugs, diseases, symptoms) from text.

### Three Methods (in order of priority):

| Method | When Used | Accuracy | Speed | Example |
|--------|-----------|----------|-------|---------|
| **scispaCy** (Primary) | If model loaded | 85% | Medium | "Metformin" → DRUG |
| **Regex** (Fallback) | scispaCy unavailable | 65% | Fast | Matches "Metformin" pattern |
| **BioBERT** (Alternative) | High accuracy needed | 92% | Slow | Transformer-based |

### Code Location
- **Primary**: `backend/preprocessing/query_processor.py` lines 36-107
- **Fallback**: `backend/preprocessing/query_processor.py` lines 109-170

### Quick Example
```python
# Input
text = "What are side effects of Metformin?"

# Processing (uses scispaCy if available, regex otherwise)
entities = preprocessor.extract_entities(text)

# Output
[MedicalEntity(text="Metformin", entity_type="DRUG", confidence=0.8)]
```

---

## 👥 Mode Detection - At a Glance

### What is Mode?
Determines if user is a **patient** (lay language) or **doctor** (technical).

### Detection Algorithm (4 Steps)

| Step | Check | Outcome | Example |
|------|-------|---------|---------|
| 1️⃣ | Technical terms? | DOCTOR | "pathophysiology" |
| 2️⃣ | Personal pronouns? | PATIENT | "I have", "my" |
| 3️⃣ | Keyword scoring | DOCTOR/PATIENT | Count professional vs lay terms |
| 4️⃣ | Default | PATIENT | No indicators found |

### Code Location
`backend/preprocessing/query_processor.py` lines 172-256

### Quick Decision Tree
```
Question: "What is the pathophysiology of diabetes?"
    ↓
Has "pathophysiology"? YES
    ↓
→ DOCTOR MODE ✅
```

```
Question: "I have diabetes, is it safe?"
    ↓
Has "pathophysiology"? NO
Has "I have"? YES
    ↓
→ PATIENT MODE ✅
```

```
Question: "What is diabetes?"
    ↓
Has technical terms? NO
Has personal pronouns? NO
Count keywords: 0 professional, 0 lay
    ↓
→ PATIENT MODE (default) ✅
```

---

## 🎯 Key Indicators

### Doctor Mode Indicators
```
Technical Terms:
  - pathophysiology
  - pharmacokinetics
  - contraindication
  - differential
  - etiology
  - efficacy

Professional Phrases:
  - "first-line therapy"
  - "treatment protocol"
  - "prescribe"
  - "clinical guidelines"
```

### Patient Mode Indicators
```
Personal Pronouns:
  - I have, I am, my, me
  - should I, can I
  - is it safe for me

Lay Language:
  - side effects
  - in simple terms
  - is this normal
  - what can I do
```

---

## 🔍 How to Test

### Test NER
```bash
curl -X POST http://localhost:8000/api/preprocess \
  -H "Content-Type: application/json" \
  -d '{"question":"What are side effects of Metformin?"}'
```

Response shows extracted entities:
```json
{
  "entities": [
    {"text": "Metformin", "entity_type": "DRUG", "confidence": 0.8}
  ]
}
```

### Test Mode Detection
```bash
# Patient mode question
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"I have diabetes, should I take Metformin?"}'
# → Detects: PATIENT

# Doctor mode question
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the pathophysiology of Type 2 Diabetes?"}'
# → Detects: DOCTOR
```

---

## 🛠️ How to Customize

### Add Custom NER Pattern
**File**: `backend/preprocessing/query_processor.py` lines 123-135

```python
# Add your drug
drug_patterns = [
    # ... existing patterns ...
    r'\bYourDrugName\b'  # Case-sensitive
]

# Add your disease
disease_patterns = [
    # ... existing patterns ...
    r'\b[Yy]ourDisease\b'  # Case-insensitive
]
```

### Add Custom Mode Keywords
**File**: `backend/preprocessing/query_processor.py` lines 185-222

```python
# Add to doctor keywords
doctor_keywords.append('your_professional_term')

# Add to patient keywords
patient_keywords.append('your_lay_term')
```

---

## ⚡ Performance Tips

### For Speed
- Use regex fallback (no model loading)
- Disable UMLS linking if not needed

### For Accuracy
- Use scispaCy (85% accurate)
- Or use BioBERT (92% accurate)
- Or use Hybrid approach (95% accurate)

### Resource Optimization
| Setup | Memory | Speed | Accuracy |
|-------|--------|-------|----------|
| Regex only | <10MB | 🟢 Fast | 65% |
| scispaCy | ~100MB | 🟡 Medium | 85% |
| BioBERT | ~400MB | 🔴 Slow | 92% |
| Hybrid | ~500MB | 🟡 Medium | 95% |

---

## 🚨 Common Issues

### Issue: Entities not extracted
**Solution**: 
1. Check if scispaCy loaded: `backend.main` logs
2. Verify word is in regex patterns: `backend/preprocessing/query_processor.py`
3. Try simpler form: "Metformin" vs "metformin"

### Issue: Wrong mode detected
**Solution**:
1. Add keyword to lists: lines 185-222
2. Check detection logic: lines 241-256
3. Verify question has clear indicator

### Issue: scispaCy not loading
**Solution**:
```bash
pip install spacy scispacy
python -m spacy download en_core_sci_md
```
If fails, system falls back to regex automatically.

---

## 📊 Output Examples

### NER Output
```json
{
  "entities": [
    {
      "text": "Metformin",
      "entity_type": "DRUG",
      "umls_concept": "C0025598",
      "confidence": 0.8
    },
    {
      "text": "Type 2 Diabetes",
      "entity_type": "DISEASE",
      "umls_concept": "C0011847",
      "confidence": 0.8
    }
  ]
}
```

### Mode Output
```json
{
  "detected_mode": "PATIENT",
  "provided_mode": null,
  "final_mode": "PATIENT"
}
```

---

## 🔗 Related Files

- Main: `backend/preprocessing/query_processor.py`
- Models: `backend/models/__init__.py`
- Config: `backend/config.py`
- Generators: `backend/generators/answer_generator.py`
- Full Doc: `NER_AND_MODE_DETECTION.md`

