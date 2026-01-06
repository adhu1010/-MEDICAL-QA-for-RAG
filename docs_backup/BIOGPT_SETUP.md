# BioGPT Setup Guide

## 🤖 What is BioGPT?

**BioGPT** is a large language model specifically pre-trained on **biomedical literature** (PubMed abstracts). It's designed for medical and healthcare applications.

### Key Features:
- ✅ **Medical-Specific**: Trained on 15M PubMed abstracts
- ✅ **Large Model**: 1.5 billion parameters
- ✅ **Accurate**: Better than general LLMs for medical tasks
- ✅ **Research-Grade**: Published by Microsoft Research

---

## 📦 Installation Status

### Requirements:
- ✅ **transformers** library - Installed
- ✅ **torch** (PyTorch) - Installed
- ✅ **sacremoses** - Installed
- ✅ **Disk Space**: ~6.5 GB required

### Download Progress:
Currently downloading BioGPT-Large model (~6.3 GB)

**Download Speed**: ~11 MB/s  
**Estimated Time**: 8-10 minutes  
**Progress**: Check terminal for progress bar

---

## 🚀 After BioGPT Downloads

### What Happens Next:

1. **Automatic Integration**: The server will auto-reload with BioGPT
2. **Better Answers**: Medical-specific language generation
3. **Higher Quality**: More coherent and accurate responses

### Expected Improvements:

**Before (Evidence-Based Fallback)**:
```
Answer: Common side effects of Metformin include nausea, vomiting, 
stomach upset, diarrhea, weakness. Metformin is the first-line 
medication for type 2 diabetes...
```
✅ Accurate but concatenated evidence

**After (BioGPT)**:
```
Answer: Metformin, the first-line medication for type 2 diabetes, 
commonly causes gastrointestinal side effects. Patients may experience 
nausea, vomiting, diarrhea, and stomach upset, which typically resolve 
with continued use. In rare cases, lactic acidosis may occur, requiring 
immediate medical attention.
```
✅ Coherent, well-structured medical explanation

---

## ⚙️ Configuration

### Current Settings:
```python
# backend/config.py
llm_model = "microsoft/BioGPT-Large"  # 6.3 GB
llm_temperature = 0.3  # Conservative for medical accuracy
llm_max_tokens = 512  # Maximum answer length
```

### Model Details:
- **Architecture**: GPT-2 based (Causal Language Model)
- **Parameters**: 1.5 billion
- **Training Data**: 15M PubMed abstracts
- **Context Length**: 1024 tokens
- **Output Quality**: Medical research grade

---

## 🔍 How It Works

### Generation Pipeline:

```
User Question: "What are the side effects of Metformin?"
     ↓
[Vector Retrieval] → Find relevant medical evidence
     ↓
[Evidence Fusion] → Combine top 5 sources
     ↓
[Prompt Creation] → Format for BioGPT
     ↓
┌─────────────────────────────────────────┐
│  BioGPT PROMPT:                         │
│  ─────────────────                      │
│  Based on the following evidence from   │
│  medical literature, provide a detailed │
│  answer:                                │
│                                         │
│  Question: What are the side effects?   │
│                                         │
│  Evidence:                              │
│  [1] Common side effects include...    │
│  [2] Meta-analysis shows...             │
│  [3] Gastrointestinal disturbances...  │
│                                         │
│  Answer:                                │
└─────────────────────────────────────────┘
     ↓
[BioGPT Generation] → Medical language model
     ↓
[Safety Validation] → Check for hallucinations
     ↓
[Final Answer] → Display to user
```

---

## 📊 Performance Comparison

### Model Comparison:

| Model | Size | Training Data | Medical Accuracy | Speed |
|-------|------|---------------|------------------|-------|
| **Evidence Fallback** | 0 MB | N/A | ⭐⭐⭐⭐ (High) | ⚡⚡⚡ Fast |
| **FLAN-T5-small** | 300 MB | General web | ⭐ (Poor) | ⚡⚡⚡ Fast |
| **FLAN-T5-base** | 900 MB | General web | ⭐⭐ (Fair) | ⚡⚡ Medium |
| **BioGPT-Large** | 6.3 GB | PubMed (Medical) | ⭐⭐⭐⭐⭐ (Excellent) | ⚡ Slower |
| **GPT-4 (API)** | Cloud | Multi-domain | ⭐⭐⭐⭐⭐ (Excellent) | ⚡⚡ Medium |

---

## 🎯 When to Use BioGPT

### Best For:
✅ Medical question answering  
✅ Clinical documentation  
✅ Patient education materials  
✅ Medical research summaries  
✅ Drug information explanations  

### Not Ideal For:
❌ Real-time high-volume applications (slower)  
❌ General conversation (overly medical)  
❌ Non-medical domains  

---

## 🔧 Troubleshooting

### If Download Fails:

**Error**: "No space left on device"
```bash
# Check free space
dir C:\Users\eahkf\.cache\huggingface

# Need at least 7 GB free
# Delete unused files to free space
```

**Error**: "Connection timeout"
```bash
# Retry the download
python test_biogpt.py
```

**Error**: "Out of memory" during generation
```bash
# Reduce max_tokens in backend/config.py
llm_max_tokens = 256  # Instead of 512
```

---

## 📝 Testing BioGPT

### After Download Completes:

1. **Test script** will automatically run
2. **Check output** for quality
3. **Restart backend** server:
   ```bash
   # Server should auto-reload
   # Or manually restart:
   python scripts/run.py
   ```

4. **Test in frontend**:
   - Open http://localhost:3000
   - Ask: "What are the side effects of Metformin?"
   - Compare answer quality

---

## ⚡ Performance Tips

### Speed Up Generation:

1. **Reduce temperature** (more deterministic):
   ```python
   llm_temperature = 0.1  # Instead of 0.3
   ```

2. **Reduce max tokens** (shorter answers):
   ```python
   llm_max_tokens = 256  # Instead of 512
   ```

3. **Use GPU** (if available):
   ```python
   # Model will automatically use CUDA if available
   # Check: torch.cuda.is_available()
   ```

---

## 🎓 Citation

If you use BioGPT in research:

```bibtex
@article{luo2022biogpt,
  title={BioGPT: generative pre-trained transformer for biomedical text generation and mining},
  author={Luo, Renqian and Sun, Liai and Xia, Yingce and Qin, Tao and Zhang, Sheng and Poon, Hoifung and Liu, Tie-Yan},
  journal={Briefings in Bioinformatics},
  year={2022}
}
```

---

## ✅ Summary

**BioGPT** will give you:
- ✅ Medical-grade language generation
- ✅ Coherent, well-structured answers
- ✅ Better synthesis of evidence
- ✅ Professional medical writing style

**Download Status**: In progress (~8-10 minutes)  
**Next Step**: Wait for download, then test the quality!  
**Fallback**: System will continue using evidence-based answers if BioGPT fails
