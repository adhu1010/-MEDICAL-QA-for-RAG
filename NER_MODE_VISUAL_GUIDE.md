# NER & Mode Detection - Visual Guide

## 🧠 NER Processing Pipeline

```
User Input: "What are the side effects of Metformin?"
        ↓
┌──────────────────────────────────────────────┐
│ Initialize QueryPreprocessor                 │
├──────────────────────────────────────────────┤
│ Try to load scispaCy model                    │
│ (en_core_sci_md - ~40MB)                     │
└──────────────────────────────────────────────┘
        ↓
   /─────────\
  / scispaCy  \
 / Loaded? YES \
  \           /
   \─────────/
     YES ↓
┌──────────────────────────────────────────────┐
│ PRIMARY: scispaCy NER                        │
├──────────────────────────────────────────────┤
│ 1. Load model: spacy.load("en_core_sci_md")  │
│ 2. Process text: doc = nlp(text)             │
│ 3. Extract: for ent in doc.ents:             │
│    - ent.text: "Metformin"                   │
│    - ent.label_: "DRUG"                      │
│    - confidence: 0.8                         │
│ 4. Try UMLS linking (if available)           │
└──────────────────────────────────────────────┘
         ↓
    ✅ MedicalEntity
    text="Metformin"
    entity_type="DRUG"
    confidence=0.8
    umls_concept=C0025598

     NO ↓
┌──────────────────────────────────────────────┐
│ FALLBACK: Regex Patterns                     │
├──────────────────────────────────────────────┤
│ Drug patterns:                               │
│  - [A-Z][a-z]+(?:in|ate|ide|...)            │
│  - Specific drugs: Metformin, Insulin, etc  │
│                                              │
│ Disease patterns:                            │
│  - [Tt]ype.*[Dd]iabetes                     │
│  - [Hh]ypertension, [Ss]inusitis            │
│                                              │
│ Match "Metformin" → Confidence 0.7           │
└──────────────────────────────────────────────┘
         ↓
    ✅ MedicalEntity
    text="Metformin"
    entity_type="DRUG"
    confidence=0.7
    umls_concept=None
```

---

## 👥 Mode Detection Pipeline

```
User Input: "What are the side effects of Metformin?"
        ↓
┌──────────────────────────────────────────────────────┐
│ STEP 1: Check Technical Medical Terminology          │
├──────────────────────────────────────────────────────┤
│ Technical terms:                                     │
│  ✗ pathophysiology (NOT PRESENT)                    │
│  ✗ pharmacokinetics (NOT PRESENT)                   │
│  ✗ contraindication (NOT PRESENT)                   │
│  ✗ differential (NOT PRESENT)                       │
│  ✗ etiology (NOT PRESENT)                           │
│  ✗ therapeutic index (NOT PRESENT)                  │
│  ✗ bioavailability (NOT PRESENT)                    │
│  ✗ efficacy (NOT PRESENT)                           │
│                                                      │
│ has_technical = False  →  Continue to Step 2        │
└──────────────────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────────────────┐
│ STEP 2: Check Personal Pronouns                      │
├──────────────────────────────────────────────────────┤
│ Personal phrases:                                    │
│  ✓ "i have" (NOT PRESENT in question)              │
│  ✓ "i am" (NOT PRESENT)                            │
│  ✓ "my " (NOT PRESENT)                             │
│  ✓ "should i" (NOT PRESENT)                        │
│                                                      │
│ has_personal = False  →  Continue to Step 3         │
└──────────────────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────────────────┐
│ STEP 3: Count Keyword Scores                         │
├──────────────────────────────────────────────────────┤
│ Doctor Keywords (sample):                            │
│  - differential diagnosis (NO)                       │
│  - pathophysiology (NO)                              │
│  - treatment protocol (NO)                           │
│  - management of (NO)                                │
│  - clinical guidelines (NO)                          │
│  → doctor_score = 0                                  │
│                                                      │
│ Patient Keywords (sample):                           │
│  - i have (NO)                                       │
│  - side effects (✓ YES!)                            │
│  - is it safe (NO)                                   │
│  - how long (NO)                                     │
│  - should i (NO)                                     │
│  → patient_score = 1                                 │
│                                                      │
│ Comparison: doctor_score (0) > patient_score (1)?   │
│ NO, patient_score wins  →  Continue to Step 4       │
└──────────────────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────────────────┐
│ STEP 4: Default to PATIENT (Safety Default)          │
├──────────────────────────────────────────────────────┤
│ No strong indicators found                           │
│ Default mode = PATIENT (safest, simplest language)   │
└──────────────────────────────────────────────────────┘
        ↓
✅ FINAL MODE: PATIENT
   (Simplified, lay language response)
```

---

## 📊 Comparison: Different Questions

### Example 1: Simple Question
```
Question: "What is diabetes?"
           ↓
Step 1: Technical terms? NO
Step 2: Personal pronouns? NO
Step 3: Keyword score? doctor=0, patient=0
Step 4: Default to PATIENT
           ↓
Result: 🟦 PATIENT MODE
```

### Example 2: Patient Asking About Self
```
Question: "I have diabetes, what should I do?"
           ↓
Step 1: Technical terms? NO
Step 2: Personal pronouns? YES ("I have")
           ↓
Result: 🟦 PATIENT MODE (via Step 2)
```

### Example 3: Medical Professional
```
Question: "What is the pathophysiology of Type 2 Diabetes?"
           ↓
Step 1: Technical terms? YES ("pathophysiology")
           ↓
Result: 🟥 DOCTOR MODE (via Step 1)
```

### Example 4: Complex Clinical Question
```
Question: "What are first-line therapies and treatment 
           protocols for hypertension management?"
           ↓
Step 1: Technical terms? NO
Step 2: Personal pronouns? NO
Step 3: Keyword score? 
        doctor_keywords = 2 ("first-line", "treatment protocol")
        patient_keywords = 0
        doctor_score (2) > patient_score (0)? YES
           ↓
Result: 🟥 DOCTOR MODE (via Step 3)
```

---

## 🎯 NER Confidence Levels

```
┌─────────────────────────────────────────────────────┐
│          NER Method Comparison                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│ scispaCy  ████████░░  85% Confidence               │
│ BioBERT   █████████░  92% Confidence               │
│ Regex     ██████░░░░  65% Confidence               │
│ Dict      ██████████  98% Confidence               │
│                                                     │
└─────────────────────────────────────────────────────┘

Speed vs Accuracy Trade-off:

     SPEED
      ↑
      │  Regex ✓ (Fast, Low Accuracy)
      │        ╱╲
      │       ╱  ╲
      │      ╱    ╲ scispaCy ✓ (Balanced)
      │     ╱      ╲
      │    ╱        ╲
      │   ╱          ╱╲
      │  ╱          ╱  ╲
      │ ╱          ╱    ╲ BioBERT ✓ (Slow, High Accuracy)
      │────────────────────────────────→
      └         ACCURACY
```

---

## 🔄 Complete Query Processing Flow

```
                    User Query
                        │
                        ↓
    ┌───────────────────────────────────────┐
    │  1. QUERY PREPROCESSING               │
    │     backend/preprocessing/            │
    │     query_processor.py                │
    ├───────────────────────────────────────┤
    │  ┌─ NER (scispaCy or Regex) ────────┐ │
    │  │ Extract entities                  │ │
    │  │ "Metformin" → DRUG                │ │
    │  └────────────────────────────────────┘ │
    │                                         │
    │  ┌─ Mode Detection (4-step) ────────┐   │
    │  │ Check: Technical → Personal      │   │
    │  │ Score: Keywords                   │   │
    │  │ Default: PATIENT                  │   │
    │  │ Result: PATIENT or DOCTOR         │   │
    │  └────────────────────────────────────┘  │
    │                                         │
    │  ┌─ Query Type Detection ────────────┐  │
    │  │ DEFINITION / COMPLEX / CONTEXTUAL │  │
    │  └────────────────────────────────────┘  │
    │                                         │
    │  ┌─ Retrieval Strategy ──────────────┐  │
    │  │ VECTOR_ONLY / KG_ONLY / HYBRID    │  │
    │  └────────────────────────────────────┘  │
    └───────────────────────────────────────┘
                        │
                        ↓
    ┌───────────────────────────────────────┐
    │  2. AGENT DECISION                    │
    │     backend/agents/                   │
    │     agent_controller.py               │
    │     Uses: entities, strategy          │
    └───────────────────────────────────────┘
                        │
                        ↓
    ┌───────────────────────────────────────┐
    │  3. RETRIEVAL (Vector + KG)           │
    │     backend/retrievers/               │
    │     Uses: entities for search         │
    └───────────────────────────────────────┘
                        │
                        ↓
    ┌───────────────────────────────────────┐
    │  4. ANSWER GENERATION                 │
    │     backend/generators/               │
    │     answer_generator.py               │
    │     Uses: MODE for language style     │
    │     PATIENT: Simple, lay language     │
    │     DOCTOR: Technical, detailed       │
    └───────────────────────────────────────┘
                        │
                        ↓
                   Final Answer
```

---

## 📈 Accuracy Scenarios

### High Accuracy (95%+)
```
Question: "I have Type 2 Diabetes. What are side effects 
           of Metformin treatment?"

NER Detection:
  ✓ "Type 2 Diabetes" → DISEASE (matched pattern)
  ✓ "Metformin" → DRUG (specific drug list)
  
Mode Detection:
  ✓ "I have" → Personal pronoun detected
  ✓ "side effects" → Patient keyword
  
Result: High confidence in both
```

### Medium Accuracy (75%)
```
Question: "Tell me about metformin dosage"

NER Detection:
  ~ "metformin" → DRUG (regex pattern, lowercase)
  ~ Case-sensitivity may miss capitalized version
  
Mode Detection:
  ~ No strong technical terms
  ~ No personal pronouns
  ~ Falls back to default PATIENT
  
Result: Medium confidence
```

### Low Accuracy (50%)
```
Question: "What's xerophobia?"

NER Detection:
  ✗ "xerophobia" → Not recognized (rare term)
  ✗ Doesn't match predefined patterns
  
Mode Detection:
  ✓ "What's" → Neutral, defaults to PATIENT
  
Result: NER fails, but mode detection succeeds
```

---

## 🛠️ Customization Points

```
┌─────────────────────────────────────────┐
│ CUSTOMIZE NER                           │
├─────────────────────────────────────────┤
│ File: query_processor.py                │
│ Lines: 109-170 (Regex patterns)         │
│                                         │
│ Add drug pattern:                       │
│ r'\bYourDrug\b'                         │
│                                         │
│ Add disease pattern:                    │
│ r'\b[Yy]ourDisease\b'                  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ CUSTOMIZE MODE DETECTION                │
├─────────────────────────────────────────┤
│ File: query_processor.py                │
│ Lines: 185-222 (Keywords)               │
│                                         │
│ Add doctor keyword:                     │
│ 'your_professional_term'                │
│                                         │
│ Add patient keyword:                    │
│ 'your_lay_term'                         │
│                                         │
│ Modify thresholds: (Line 250)            │
│ if doctor_score > patient_score >= 2    │
└─────────────────────────────────────────┘
```

---

## 🚀 API Testing

### Test NER Only
```bash
curl -X POST http://localhost:8000/api/preprocess \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are side effects of Metformin?",
    "mode": null
  }'

Response shows:
{
  "entities": [
    {"text": "Metformin", "entity_type": "DRUG", "confidence": 0.8}
  ],
  "detected_mode": "PATIENT"
}
```

### Test Full Pipeline
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "I have diabetes, what should I do?",
    "mode": null
  }'

Response shows:
{
  "answer": "...",
  "mode": "PATIENT",
  "metadata": {
    "entities_found": 1,
    "detected_mode": "PATIENT",
    "retrieval_strategy": "VECTOR_ONLY"
  }
}
```

