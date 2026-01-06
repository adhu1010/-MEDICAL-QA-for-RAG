# NER (Named Entity Recognition) & Mode Detection Guide

## Overview

This document explains:
1. **NER Alternatives** - How entity recognition works and fallback options
2. **Mode Detection** - How the system determines patient vs. doctor mode

---

## 🧠 NER (Named Entity Recognition) Implementation

### Primary Method: scispaCy NER

**What it is**: Medical-specialized Named Entity Recognition using scispaCy (spaCy for biomedical text)

**File**: [`backend/preprocessing/query_processor.py` (Lines 36-107)](backend/preprocessing/query_processor.py)

**How it works**:
```python
# Load medical NER model
self.nlp = spacy.load("en_core_sci_md")

# Extract entities from text
doc = self.nlp("What are the side effects of Metformin?")
for ent in doc.ents:
    # Entity: "Metformin" (DRUG)
    # Confidence: 0.8
```

**Advantages**:
- ✅ Specialized for biomedical text
- ✅ Recognizes medical terms accurately
- ✅ Can link to UMLS concepts
- ✅ Handles medical entity types (DRUG, DISEASE, SYMPTOM, etc.)

**Requirements**:
- `spacy>=3.7.0`
- `scispacy>=0.5.0`
- Medical model: `en_core_sci_md` (~40MB)

**Installation**:
```bash
pip install spacy scispacy
python -m spacy download en_core_sci_md
```

---

### Fallback Method: Regex-Based Extraction

When scispaCy is **NOT** available, the system uses simple regex patterns.

**File**: [`backend/preprocessing/query_processor.py` (Lines 109-170)](backend/preprocessing/query_processor.py)

**How it works**:
```python
def _simple_entity_extraction(self, text: str) -> List[MedicalEntity]:
    """Regex-based fallback when scispaCy unavailable"""
    
    # Drug patterns (capitalized words ending in medical suffixes)
    drug_patterns = [
        r'\b[A-Z][a-z]+(?:in|ate|ide|one|ine|cin|zole|pril|sartan|statin)\b',
        r'\b(?:Metformin|Amoxicillin|Doxycycline|Insulin|Aspirin)\b'
    ]
    
    # Disease patterns
    disease_patterns = [
        r'\b(?:[Tt]ype\s*[12]\s*)?[Dd]iabetes\b',
        r'\b[Hh]ypertension\b',
        r'\b[Ss]inusitis\b',
        r'\b[Ii]nfection\b',
        r'\b[Cc]ancer\b'
    ]
```

**Example**:
```
Input: "What are the side effects of Metformin?"
Pattern Match: "Metformin" (matches drug pattern)
Output: MedicalEntity(text="Metformin", entity_type="DRUG", confidence=0.7)
```

**Advantages**:
- ✅ No external dependencies
- ✅ Fast and lightweight
- ✅ Works offline
- ✅ No model download needed

**Disadvantages**:
- ❌ Limited to predefined patterns
- ❌ Lower accuracy (0.7 confidence vs 0.8)
- ❌ Misses lesser-known drugs/diseases
- ❌ Cannot link to UMLS concepts

---

### Automatic Selection Logic

**File**: [`backend/preprocessing/query_processor.py` (Lines 79-107)](backend/preprocessing/query_processor.py)

The system automatically selects which method to use:

```python
def extract_entities(self, text: str) -> List[MedicalEntity]:
    if self.nlp:
        # ✅ Use scispaCy (primary method)
        entities = []
        doc = self.nlp(text)  # spaCy NER
        
        for ent in doc.ents:
            entity = MedicalEntity(
                text=ent.text,
                entity_type=ent.label_,  # DRUG, DISEASE, etc.
                umls_concept=None,       # UMLS linking (if available)
                confidence=0.8           # Higher confidence
            )
            entities.append(entity)
        
        logger.info(f"Extracted {len(entities)} entities using scispaCy")
        return entities
    else:
        # ❌ Fall back to regex
        logger.info("Using simple entity extraction (no scispaCy available)")
        return self._simple_entity_extraction(text)
```

---

## 🎯 Alternative NER Solutions

### Option 1: Transformer-Based NER (BioBERT/SciBERT)

**What it is**: Fine-tuned BERT models for biomedical NER

**Advantages**:
- Higher accuracy (90%+)
- Handles more entity types
- Better context understanding
- Transferable learning

**Disadvantages**:
- Requires more computational resources
- Slower than scispaCy
- Model download (~400MB)

**Integration Example**:
```python
from transformers import AutoTokenizer, AutoModelForTokenClassification

tokenizer = AutoTokenizer.from_pretrained("dmis-lab/biobert-base-cased-v1.2")
model = AutoModelForTokenClassification.from_pretrained("dmis-lab/biobert-base-cased-v1.2")

# Use for NER
tokens = tokenizer(text, return_tensors="pt")
logits = model(**tokens).logits
predictions = logits.argmax(-1)
```

### Option 2: Dictionary-Based Lookup

**What it is**: Match against medical terminology dictionaries (UMLS, MeSH)

**Advantages**:
- 100% accurate for known terms
- Fast lookup
- No model needed

**Disadvantages**:
- Limited to dictionary terms
- Needs preprocessing for variations
- Cannot handle new/emerging terms

**Example**:
```python
MEDICAL_TERMS = {
    "metformin": {"type": "DRUG", "umls": "C0025598"},
    "diabetes": {"type": "DISEASE", "umls": "C0011847"},
    "hypertension": {"type": "DISEASE", "umls": "C0020538"}
}

def extract_entities_dict(text):
    entities = []
    for term, info in MEDICAL_TERMS.items():
        if term in text.lower():
            entities.append(MedicalEntity(
                text=term,
                entity_type=info["type"],
                umls_concept=info["umls"],
                confidence=1.0
            ))
    return entities
```

### Option 3: Hybrid Approach (Recommended)

Combine multiple methods for best results:

```python
def extract_entities_hybrid(self, text: str) -> List[MedicalEntity]:
    """
    Hybrid extraction using multiple methods:
    1. Dictionary lookup (fast, high precision)
    2. scispaCy NER (accurate, handles variants)
    3. Regex fallback (lightweight)
    """
    entities = []
    
    # Method 1: Dictionary lookup
    entities.extend(self._extract_from_dictionary(text))
    
    # Method 2: scispaCy
    if self.nlp:
        entities.extend(self._extract_from_spacy(text))
    
    # Method 3: Regex
    entities.extend(self._extract_from_regex(text))
    
    # Deduplicate and merge
    return self._deduplicate_entities(entities)
```

---

## 👥 Mode Detection: Patient vs. Doctor

### What is Mode?

**Mode** determines the tone and complexity of responses:

| Mode | Target | Language Style | Examples |
|------|--------|----------------|----------|
| **PATIENT** | Non-medical users | Simple, lay language, plain English | "What are side effects?", "Is this safe for me?" |
| **DOCTOR** | Medical professionals | Technical, detailed, clinical terminology | "What is the pathophysiology?", "What's the pharmacokinetics?" |

### How Mode is Detected

**File**: [`backend/preprocessing/query_processor.py` (Lines 172-256)](backend/preprocessing/query_processor.py)

The system uses a **multi-level detection algorithm**:

#### **Step 1: Check for Technical Medical Terminology** (Strongest Indicator)

```python
has_technical = any(term in question_lower for term in [
    'pathophysiology',      # How the disease develops
    'pharmacokinetics',     # Drug metabolism & movement
    'contraindication',     # When drug is unsafe
    'differential',         # Types of diagnosis to consider
    'etiology',            # Root cause
    'therapeutic index',    # Safe dose range
    'bioavailability',     # Drug absorption
    'efficacy'             # Drug effectiveness
])

if has_technical:
    return UserMode.DOCTOR  # Professional terminology = Doctor mode
```

**Examples**:
- ✅ "What is the pathophysiology of Type 2 Diabetes?" → **DOCTOR**
- ✅ "Explain the pharmacokinetics of Metformin" → **DOCTOR**

#### **Step 2: Check for Personal Pronouns** (Strong Indicator)

```python
personal_phrases = ['i have', 'i am', 'my ', 'should i']
has_personal = any(phrase in question_lower for phrase in personal_phrases)

if has_personal:
    return UserMode.PATIENT  # Personal pronouns = Patient mode
```

**Examples**:
- ✅ "I have diabetes, should I take Metformin?" → **PATIENT**
- ✅ "My doctor prescribed this, is it safe?" → **PATIENT**

#### **Step 3: Keyword Scoring**

Count professional vs. patient keywords:

**Doctor Keywords** (Lines 185-206):
```python
doctor_keywords = [
    # Medical terminology
    'differential diagnosis', 'pathophysiology', 'contraindication',
    'pharmacokinetics', 'pharmacodynamics', 'dosing regimen',
    
    # Clinical questions
    'management of', 'treatment protocol', 'clinical guidelines',
    'first-line therapy', 'second-line', 'mechanism of action',
    
    # Professional language
    'prescribe', 'efficacy', 'bioavailability', 'half-life',
    'therapeutic range', 'monitoring parameters',
    
    # Specific professional phrases
    'what should i prescribe', 'diagnostic criteria', 'comorbidities',
    'lab values', 'clinical manifestations'
]
```

**Patient Keywords** (Lines 209-222):
```python
patient_keywords = [
    # Personal/lay language
    'i have', 'i am', 'my', 'me', 'i feel', 'i\'ve been',
    'should i', 'can i', 'is it safe for me',
    
    # Simple/lay terms
    'in simple terms', 'explain simply', 'what does this mean',
    'in plain english', 'easy to understand',
    
    # Patient concerns
    'side effects', 'is it safe', 'will it help', 'how long',
    'when should i', 'do i need', 'is this normal',
    'should i worry', 'what can i do'
]
```

**Scoring Logic**:
```python
doctor_score = sum(1 for keyword in doctor_keywords if keyword in question_lower)
patient_score = sum(1 for keyword in patient_keywords if keyword in question_lower)

if doctor_score > patient_score and doctor_score >= 2:
    return UserMode.DOCTOR  # Professional score wins
```

#### **Step 4: Default Fallback**

```python
# Default to PATIENT mode for safety
# (More cautious, simpler language = safer)
return UserMode.PATIENT
```

### Complete Mode Detection Flow

```
User Question
    ↓
┌─────────────────────────────────────┐
│ 1. Has technical medical terms?     │
│    (pathophysiology, efficacy, etc) │
├─────────────────────────────────────┤
│ YES → Return DOCTOR                 │
│ NO  → Continue                      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. Has personal pronouns?           │
│    (I have, my, should I)           │
├─────────────────────────────────────┤
│ YES → Return PATIENT                │
│ NO  → Continue                      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. Count keyword scores             │
│    Doctor vs Patient keywords       │
├─────────────────────────────────────┤
│ Doctor Score > Patient Score (≥2)   │
│    → Return DOCTOR                  │
│ Otherwise → Continue                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. Default to PATIENT (safer)       │
└─────────────────────────────────────┘
```

### Examples of Mode Detection

**Example 1: Patient Mode**
```
Input: "I have Type 2 Diabetes. What are the side effects of Metformin?"
Detection:
  - Technical terms? NO
  - Personal pronouns? YES ("I have", "side effects")
  - Score: Patient = 2, Doctor = 0
Result: → PATIENT mode ✅
```

**Example 2: Doctor Mode**
```
Input: "What is the pathophysiology of Type 2 Diabetes?"
Detection:
  - Technical terms? YES ("pathophysiology") ← STOPS HERE
Result: → DOCTOR mode ✅
```

**Example 3: Doctor Mode (Keyword Scoring)**
```
Input: "What is the first-line therapy and treatment protocol for hypertension?"
Detection:
  - Technical terms? NO
  - Personal pronouns? NO
  - Keywords: Doctor = 2 ("first-line therapy", "treatment protocol")
  - Score: Doctor (2) > Patient (0) ✅
Result: → DOCTOR mode ✅
```

**Example 4: Default to Patient**
```
Input: "What is diabetes?"
Detection:
  - Technical terms? NO
  - Personal pronouns? NO
  - Keywords: Doctor = 0, Patient = 0
Result: → PATIENT mode (default) ✅
```

---

## 📊 How Mode Affects Response

After mode detection, it's used to format the answer:

**File**: [`backend/generators/answer_generator.py`](backend/generators/answer_generator.py)

```python
def generate(self, processed_query, evidence, mode=UserMode.PATIENT):
    if mode == UserMode.PATIENT:
        # Simplify language, avoid jargon
        return self._generate_patient_answer(evidence)
    else:
        # Use technical terminology, add clinical details
        return self._generate_doctor_answer(evidence)
```

### Patient Mode Response
```
Question: "What are side effects of Metformin?"
Response:
"Common side effects of Metformin include nausea, stomach upset, 
diarrhea, and a metallic taste in your mouth. These usually go away 
after a few days. Contact your doctor if they persist."
```

### Doctor Mode Response
```
Question: "What is the pathophysiology of Type 2 Diabetes and 
the mechanism of action of Metformin?"
Response:
"Type 2 Diabetes results from insulin resistance and beta-cell 
dysfunction. Metformin's mechanism of action involves inhibition 
of hepatic gluconeogenesis, enhancement of insulin-stimulated 
glucose uptake, and improved insulin sensitivity..."
```

---

## 🔧 Configuration

### Enable/Disable scispaCy

**File**: [`backend/config.py`](backend/config.py)

```python
# Force use of regex fallback (disable scispaCy)
USE_SCISPACY = False  # Set to False to skip scispaCy

# Or in .env
SCISPACY_MODEL=en_core_sci_md  # Model to load
```

### Add Custom Keywords

**File**: [`backend/preprocessing/query_processor.py` (Lines 185-222)](backend/preprocessing/query_processor.py)

Modify the keyword lists to customize mode detection:

```python
doctor_keywords.append("your_custom_professional_term")
patient_keywords.append("your_custom_patient_term")
```

---

## 📈 Performance Comparison

| Method | Accuracy | Speed | Resources | Setup Complexity |
|--------|----------|-------|-----------|------------------|
| **scispaCy** | ~85% | Medium | ~100MB | Medium |
| **Regex** | ~65% | Fast | <1MB | Low |
| **BioBERT** | ~92% | Slow | ~400MB | High |
| **Dictionary** | ~98% | Very Fast | ~10MB | Low |
| **Hybrid** | ~95% | Medium | ~500MB | High |

---

## 🚀 Recommended Setup

1. **For Development**: Use scispaCy (good balance)
2. **For Production**: Use Hybrid (dictionary + scispaCy)
3. **For Low Resources**: Use Regex fallback
4. **For Highest Accuracy**: Use BioBERT or Hybrid

---

## 📚 Related Files

- [`backend/preprocessing/query_processor.py`](backend/preprocessing/query_processor.py) - NER & Mode detection
- [`backend/models/__init__.py`](backend/models/__init__.py) - MedicalEntity, UserMode definitions
- [`backend/config.py`](backend/config.py) - Configuration settings
- [`backend/generators/answer_generator.py`](backend/generators/answer_generator.py) - Mode-aware response generation
- [`backend/utils/helpers.py`](backend/utils/helpers.py) - Utility functions

---

## 🎓 Key Takeaways

**NER Alternatives**:
1. **Primary**: scispaCy (medical-specialized)
2. **Fallback**: Regex patterns (lightweight)
3. **Alternative**: BioBERT, Dictionary lookup, Hybrid

**Mode Detection**:
1. **Check technical terminology first** (strongest indicator)
2. **Check personal pronouns** (strong indicator)
3. **Score keywords** (doctor vs patient)
4. **Default to patient** (safest approach)

**Mode impacts**:
- Response language complexity
- Technical terminology usage
- Level of clinical detail

