# NER & Mode Detection - Complete Documentation Index

## 📚 Documentation Files

This section contains comprehensive documentation about Named Entity Recognition (NER) and Mode Detection in the Medical RAG QA system.

### Quick Start (5 minutes)
**[NER_MODE_SUMMARY.txt](NER_MODE_SUMMARY.txt)** ⭐ START HERE
- Executive summary of both NER and Mode Detection
- 14 key points covering everything
- File locations, testing commands, common issues
- Perfect for quick understanding

### Quick Reference (10 minutes)
**[NER_MODE_QUICK_REFERENCE.md](NER_MODE_QUICK_REFERENCE.md)** 
- Quick lookup guide
- Decision trees for mode detection
- Performance comparison table
- Testing commands with examples
- Common issues and solutions

### Visual Guide (15 minutes)
**[NER_MODE_VISUAL_GUIDE.md](NER_MODE_VISUAL_GUIDE.md)**
- Flowcharts and diagrams
- Processing pipelines
- Decision trees with examples
- Accuracy scenarios
- API testing examples

### Comprehensive Guide (30 minutes)
**[NER_AND_MODE_DETECTION.md](NER_AND_MODE_DETECTION.md)**
- Complete technical documentation
- All NER alternatives explained
- Detailed mode detection algorithm
- Code examples
- Configuration options
- Related files and dependencies

---

## 🎯 Choose Your Resource

### I want to understand NER alternatives
→ Read: [NER_AND_MODE_DETECTION.md](NER_AND_MODE_DETECTION.md) - Section "🎯 Alternative NER Solutions"

### I want to understand mode detection
→ Read: [NER_AND_MODE_DETECTION.md](NER_AND_MODE_DETECTION.md) - Section "👥 Mode Detection"

### I want to see a decision tree
→ Read: [NER_MODE_QUICK_REFERENCE.md](NER_MODE_QUICK_REFERENCE.md) - Section "🎯 Key Indicators"

### I want to see flowcharts
→ Read: [NER_MODE_VISUAL_GUIDE.md](NER_MODE_VISUAL_GUIDE.md) - Multiple pipeline diagrams

### I want a 2-minute overview
→ Read: [NER_MODE_SUMMARY.txt](NER_MODE_SUMMARY.txt) - Points 1-3

### I want to customize NER
→ Read: [NER_AND_MODE_DETECTION.md](NER_AND_MODE_DETECTION.md) - Section "🔧 Configuration"

### I want to customize Mode keywords
→ Read: [NER_MODE_QUICK_REFERENCE.md](NER_MODE_QUICK_REFERENCE.md) - Section "🛠️ How to Customize"

### I want to test the system
→ Read: [NER_MODE_QUICK_REFERENCE.md](NER_MODE_QUICK_REFERENCE.md) - Section "🔍 How to Test"

---

## 📋 Summary of Content

### NER (Named Entity Recognition)

**What it does**: Extracts medical entities (drugs, diseases, symptoms) from user questions

**Three implementation methods** (in priority order):
1. **scispaCy** (Primary) - 85% accurate, requires model (~40MB)
2. **Regex** (Fallback) - 65% accurate, no dependencies
3. **BioBERT/Dict/Hybrid** (Alternatives) - 92-98% accurate

**Location in code**: `backend/preprocessing/query_processor.py`
- Lines 36-107: scispaCy implementation
- Lines 109-170: Regex fallback

---

### Mode Detection

**What it does**: Automatically detects if user is a PATIENT or DOCTOR

**Detection algorithm** (4-step process):
1. Check for technical medical terminology → DOCTOR
2. Check for personal pronouns (I have, my, etc.) → PATIENT
3. Count keyword scores (doctor vs patient keywords)
4. Default to PATIENT (safety)

**Location in code**: `backend/preprocessing/query_processor.py`
- Lines 172-256: Mode detection implementation

---

## 🔗 Code References

### Primary Files
```
backend/preprocessing/query_processor.py
├─ Lines 25-75: QueryPreprocessor initialization
├─ Lines 67-107: extract_entities() - NER
├─ Lines 109-170: _simple_entity_extraction() - Regex fallback
├─ Lines 172-256: detect_user_mode() - Mode detection
├─ Lines 258-286: detect_query_type() - Query classification
├─ Lines 288-312: suggest_retrieval_strategy() - Strategy selection
├─ Lines 314-330: normalize_query() - Query normalization
├─ Lines 332-378: process_query() - Complete pipeline
└─ Lines 385-390: get_query_preprocessor() - Singleton

backend/models/__init__.py
├─ MedicalEntity: NER output model
├─ ProcessedQuery: Pipeline output
├─ UserMode: Enum (PATIENT, DOCTOR)
├─ QueryType: Enum (DEFINITION, COMPLEX, CONTEXTUAL)
└─ RetrievalStrategy: Enum (VECTOR_ONLY, KG_ONLY, HYBRID)

backend/generators/answer_generator.py
└─ Uses UserMode to format responses
```

---

## 📊 Quick Comparison

### NER Methods
| Method | Accuracy | Speed | Resources | Best For |
|--------|----------|-------|-----------|----------|
| scispaCy | 85% | Medium | ~100MB | Production (balanced) |
| Regex | 65% | Fast | <1MB | Low resources |
| BioBERT | 92% | Slow | ~400MB | High accuracy |
| Dictionary | 98% | V-Fast | ~10MB | Known terms only |

### Mode Detection Examples
| Question | Detection | Reason |
|----------|-----------|--------|
| "What is pathophysiology?" | DOCTOR | Technical term |
| "I have diabetes, is it safe?" | PATIENT | Personal pronoun |
| "What is diabetes?" | PATIENT | Default (no indicators) |
| "First-line therapy for HTN?" | DOCTOR | Professional keywords |

---

## 🚀 Getting Started

### 1. Quick Understanding (5 min)
```bash
# Read the executive summary
cat NER_MODE_SUMMARY.txt
```

### 2. Detailed Learning (30 min)
```bash
# Read comprehensive guide in order:
1. NER_AND_MODE_DETECTION.md (start here)
2. NER_MODE_QUICK_REFERENCE.md (practical reference)
3. NER_MODE_VISUAL_GUIDE.md (see diagrams)
```

### 3. Testing
```bash
# Test NER extraction
curl -X POST http://localhost:8000/api/preprocess \
  -H "Content-Type: application/json" \
  -d '{"question":"What are side effects of Metformin?"}'

# Test mode detection
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"I have diabetes, should I take Metformin?"}'
```

### 4. Customization
```bash
# Edit patterns and keywords in:
# backend/preprocessing/query_processor.py
# Lines 123-135 (NER patterns)
# Lines 185-222 (Mode keywords)
```

---

## ❓ Common Questions

**Q: What's the difference between NER and Mode Detection?**
A: NER extracts medical entities (what), Mode Detection identifies user type (who asking). Both work together.

**Q: Should I use scispaCy or Regex?**
A: Use scispaCy for production (85% accurate), Regex for low-resource environments (65% accurate).

**Q: How does mode affect the answer?**
A: PATIENT mode uses simple language, DOCTOR mode uses technical terminology.

**Q: Can I add custom entities?**
A: Yes! Add patterns to lines 123-135 in query_processor.py

**Q: Can I add custom keywords for mode?**
A: Yes! Add to doctor_keywords or patient_keywords (lines 185-222)

**Q: What if scispaCy fails?**
A: System automatically falls back to regex extraction.

---

## 📞 Support

If you need help:
1. Check **[NER_MODE_QUICK_REFERENCE.md](NER_MODE_QUICK_REFERENCE.md)** - Troubleshooting section
2. Review **[NER_MODE_VISUAL_GUIDE.md](NER_MODE_VISUAL_GUIDE.md)** - Flowcharts and examples
3. Study **[NER_AND_MODE_DETECTION.md](NER_AND_MODE_DETECTION.md)** - Complete reference
4. Check **[NER_MODE_SUMMARY.txt](NER_MODE_SUMMARY.txt)** - Point 13 (Common Issues)

---

## 📖 Document Structure

```
Medical RAG QA System
├── NER_MODE_INDEX.md (YOU ARE HERE)
│   └─ Navigation guide for all NER/Mode docs
├── NER_MODE_SUMMARY.txt
│   └─ 14-point executive summary
├── NER_MODE_QUICK_REFERENCE.md
│   └─ Quick lookup, testing, customization
├── NER_MODE_VISUAL_GUIDE.md
│   └─ Flowcharts, pipelines, examples
└── NER_AND_MODE_DETECTION.md
    └─ Comprehensive technical documentation
```

---

## 🎓 Learning Path

**Beginner** (New to the system)
1. Read: NER_MODE_SUMMARY.txt (5 min)
2. Read: NER_MODE_QUICK_REFERENCE.md (10 min)
3. Test: Run curl examples (5 min)

**Intermediate** (Want to customize)
1. Review: NER_MODE_QUICK_REFERENCE.md - Customization section
2. Modify: backend/preprocessing/query_processor.py (lines 123-135, 185-222)
3. Test: Verify changes work

**Advanced** (Want to extend)
1. Study: NER_AND_MODE_DETECTION.md - Alternative NER Solutions
2. Implement: BioBERT or Hybrid approach
3. Integrate: Update query_processor.py with new method

---

**Last Updated**: December 25, 2025  
**System**: Medical RAG QA v1.0  
**Status**: ✅ All components operational
