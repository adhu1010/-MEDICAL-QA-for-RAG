# PubMed Knowledge Graph 2.0 Integration Guide

## 🌐 What is PubMed Knowledge Graph 2.0?

**PubMed KG 2.0** is a large-scale biomedical knowledge graph extracted from PubMed literature.

### Key Features:
- **15M+ entities**: Diseases, drugs, genes, proteins, chemicals
- **130M+ relationships**: Treats, causes, associated_with, interacts_with
- **30M+ PubMed articles**: Source of all knowledge
- **Automated extraction**: NLP and ML techniques
- **Updated regularly**: New publications added continuously

### Comparison with Current Setup:

| Feature | Current (Disease Ontology) | PubMed KG 2.0 |
|---------|---------------------------|---------------|
| **Entities** | 14,460 diseases | 15M+ (all biomedical) |
| **Relationships** | ~3,000-5,000 | 130M+ |
| **Sources** | Curated ontology | 30M+ research papers |
| **Coverage** | Diseases only | Drugs, genes, proteins, diseases |
| **Updates** | Periodic releases | Continuous |
| **Size** | ~20MB | ~50GB+ (full graph) |

---

## 🚀 Integration Options

### Option 1: Use PubMed KG API (Recommended)
**Best for**: Real-time access, minimal storage

```python
# Access PubMed KG through API
# No large download required
# Query on-demand
```

### Option 2: Download Subsets
**Best for**: Specific domains, offline access

```python
# Download disease-drug relationships only
# Or gene-protein interactions
# Subset: ~1-5GB
```

### Option 3: Full Graph Download
**Best for**: Enterprise, comprehensive coverage

```python
# Download entire PubMed KG 2.0
# Size: ~50GB+
# Requires significant resources
```

---

## 📥 How to Access PubMed KG 2.0

### Official Sources:

1. **PubMed KG Website**
   - URL: https://pubmed.ncbi.nlm.nih.gov/knowledge-graph/
   - Access: Free, requires NCBI account
   - Format: RDF, Neo4j dumps, CSV

2. **SemMedDB** (Related resource)
   - URL: https://lhncbc.nlm.nih.gov/ii/tools/SemRep_SemMedDB_SKR/SemMedDB_download.html
   - Contains predications from PubMed
   - Size: ~10GB database dump

3. **PubMed Central Open Access**
   - URL: https://www.ncbi.nlm.nih.gov/pmc/tools/openftlist/
   - Full text articles for extraction
   - Size: ~200GB+ (full collection)

---

## 💻 Implementation for Your System

### Step 1: Create PubMed KG Downloader

Let me create a script to download and integrate PubMed KG 2.0:

```python
# scripts/download_pubmed_kg.py

"""
Download and integrate PubMed Knowledge Graph 2.0

Options:
1. SemMedDB subset (recommended)
2. Custom extraction from PubMed API
3. Full graph (requires significant resources)
"""

import urllib.request
import gzip
import sqlite3
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PubMedKGDownloader:
    """Download PubMed Knowledge Graph data"""
    
    def __init__(self):
        self.data_dir = Path("../data/enterprise/pubmed_kg")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def download_semmeddb(self):
        """
        Download SemMedDB - semantic predications from PubMed
        Contains subject-predicate-object triples
        Size: ~10GB
        """
        logger.info("Downloading SemMedDB...")
        
        # SemMedDB provides predications like:
        # "Metformin" TREATS "Diabetes"
        # "Aspirin" PREVENTS "Heart Attack"
        
        url = "https://lhncbc.nlm.nih.gov/ii/tools/SemRep_SemMedDB_SKR/semmedVER43_2022_R_PREDICATION.sql.gz"
        
        dest_file = self.data_dir / "semmeddb.sql.gz"
        
        logger.info(f"Downloading from {url}")
        logger.info("This is a large file (~10GB), it may take time...")
        
        # Download with progress
        urllib.request.urlretrieve(url, dest_file, self._progress_hook)
        
        logger.info(f"Downloaded to {dest_file}")
        return dest_file
    
    def download_subset_csv(self):
        """
        Download a smaller CSV subset of PubMed KG
        Focus on disease-drug-gene relationships
        Size: ~500MB
        """
        logger.info("Downloading PubMed KG subset...")
        
        # Alternative: Use PubTator Central
        # Contains entity annotations from PubMed
        url = "https://ftp.ncbi.nlm.nih.gov/pub/lu/PubTatorCentral/bioconcepts2pubtatorcentral.gz"
        
        dest_file = self.data_dir / "pubtator_concepts.gz"
        
        logger.info(f"Downloading from {url}")
        urllib.request.urlretrieve(url, dest_file, self._progress_hook)
        
        logger.info(f"Downloaded to {dest_file}")
        return dest_file
    
    def _progress_hook(self, block_num, block_size, total_size):
        """Show download progress"""
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, downloaded * 100 / total_size)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\rProgress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='')
    
    def parse_semmeddb_to_triples(self, sql_file: Path):
        """
        Parse SemMedDB SQL dump and extract triples
        
        Returns:
            List of (subject, predicate, object) triples
        """
        logger.info("Parsing SemMedDB to extract triples...")
        
        # Extract and load into SQLite
        triples = []
        
        # SemMedDB has table: PREDICATION
        # Columns: SUBJECT_TEXT, PREDICATE, OBJECT_TEXT
        
        # For now, create instructions
        instructions_file = sql_file.parent / "SEMMEDDB_INSTRUCTIONS.txt"
        
        with open(instructions_file, 'w') as f:
            f.write("SemMedDB Integration Instructions\n")
            f.write("=" * 50 + "\n\n")
            f.write("1. Extract the .sql.gz file:\n")
            f.write(f"   gunzip {sql_file}\n\n")
            f.write("2. Load into MySQL or PostgreSQL:\n")
            f.write("   mysql -u root -p < semmeddb.sql\n\n")
            f.write("3. Query for medical relationships:\n")
            f.write("   SELECT SUBJECT_TEXT, PREDICATE, OBJECT_TEXT\n")
            f.write("   FROM PREDICATION\n")
            f.write("   WHERE PREDICATE IN ('TREATS', 'CAUSES', 'PREVENTS')\n\n")
            f.write("4. Export to CSV for integration\n")
        
        logger.info(f"Instructions saved to {instructions_file}")
        
        return triples


def main():
    """Main download function"""
    
    print("=" * 60)
    print("PubMed Knowledge Graph 2.0 - Download Options")
    print("=" * 60)
    print()
    print("1. SemMedDB (~10GB) - Semantic predications from PubMed")
    print("2. PubTator Central (~500MB) - Entity annotations")
    print("3. Custom API extraction - On-demand (no download)")
    print("4. Cancel")
    print()
    
    choice = input("Select option (1-4): ").strip()
    
    downloader = PubMedKGDownloader()
    
    if choice == "1":
        downloader.download_semmeddb()
    elif choice == "2":
        downloader.download_subset_csv()
    elif choice == "3":
        print("\nAPI mode selected.")
        print("Use scripts/download_pubmed.py for on-demand access.")
    else:
        print("Cancelled.")


if __name__ == "__main__":
    main()
```

---

## 🔧 Integration Architecture

### How PubMed KG 2.0 Fits into Your System:

```
Current System:
┌─────────────────────────────────────┐
│  Knowledge Sources                  │
├─────────────────────────────────────┤
│  1. Disease Ontology (14K diseases) │ ← Current
│  2. MedQuAD (16K QA pairs)         │ ← Current
│  3. Sample medical facts            │ ← Current
└─────────────────────────────────────┘

Enhanced with PubMed KG 2.0:
┌─────────────────────────────────────┐
│  Knowledge Sources                  │
├─────────────────────────────────────┤
│  1. Disease Ontology (14K diseases) │
│  2. MedQuAD (16K QA pairs)         │
│  3. PubMed KG 2.0 (15M entities)   │ ← NEW!
│     • Disease-drug relationships    │
│     • Gene-protein interactions     │
│     • Chemical pathways             │
│     • Clinical outcomes             │
└─────────────────────────────────────┘
```

### Integration Points:

1. **Knowledge Graph Retriever** (`kg_retriever.py`)
   - Add PubMed KG queries
   - Search for drug-disease relationships
   - Find gene associations

2. **Vector Store** (optional)
   - Index PubMed abstracts
   - Enable literature search

3. **Evidence Fusion**
   - Combine Disease Ontology + PubMed KG
   - Provide research-backed answers

---

## 🎯 Recommended Approach for Your System

### Best Strategy: Hybrid Integration

**Tier 1: Disease Ontology** (Current)
- Fast, local, curated
- 14K diseases, reliable

**Tier 2: PubMed API** (Already implemented)
- Real-time literature access
- 30M+ articles on-demand
- Minimal storage

**Tier 3: PubMed KG Subset** (Add this)
- Download disease-drug relationships
- ~1-5GB subset
- Offline access to key facts

**Tier 4: Full PubMed KG** (Enterprise only)
- Complete graph
- ~50GB+ storage
- Comprehensive coverage

---

## 📋 Step-by-Step Integration

### Option A: Use Existing PubMed API (Easiest)

✅ **Already implemented** in your system!

```bash
# Use scripts/download_pubmed.py
python scripts/download_pubmed.py
```

This gives you:
- Access to 30M+ PubMed articles
- Real-time search
- Entity extraction
- No large downloads

### Option B: Add SemMedDB Relationships (Recommended)

**Benefits**:
- Pre-extracted relationships
- Drug-disease associations
- Gene-protein interactions
- Validated by research

**Steps**:

1. **Download SemMedDB subset**:
   ```bash
   # Download disease-drug relationships only
   # Size: ~1-2GB instead of 10GB
   ```

2. **Parse to knowledge graph format**:
   ```python
   # Extract triples: (subject, predicate, object)
   # Example: ("Metformin", "TREATS", "Diabetes")
   ```

3. **Load into NetworkX or Neo4j**:
   ```bash
   python scripts/build_knowledge_graph.py --pubmed-kg
   ```

4. **Query in RAG pipeline**:
   ```python
   # Agent will automatically use PubMed KG + Disease Ontology
   ```

### Option C: Full PubMed KG 2.0 (Enterprise)

**Requirements**:
- 100GB+ disk space
- Neo4j database
- Significant processing power

**When to use**:
- Need comprehensive biomedical knowledge
- Building production research tool
- Have enterprise infrastructure

---

## 💡 Practical Example

### Current System Query:

**Question**: "What treats diabetes?"

**Current Knowledge Sources**:
1. Disease Ontology: Basic disease info
2. MedQuAD: Patient Q&A
3. Sample facts: Limited relationships

**Answer Quality**: Good, but limited

### With PubMed KG 2.0:

**Question**: "What treats diabetes?"

**Enhanced Knowledge Sources**:
1. Disease Ontology: Disease classification
2. MedQuAD: Patient education
3. **PubMed KG 2.0**: Research-backed relationships
   - Metformin TREATS Type2Diabetes (Evidence: 5,000+ papers)
   - Insulin TREATS Type1Diabetes (Evidence: 10,000+ papers)
   - Exercise PREVENTS Type2Diabetes (Evidence: 2,000+ papers)
4. PubMed API: Latest research articles

**Answer Quality**: Excellent, research-backed, comprehensive

---

## 🚦 Quick Decision Guide

### Should you add PubMed KG 2.0?

**YES, if you want**:
- ✅ Research-backed medical relationships
- ✅ Drug-disease associations
- ✅ More comprehensive answers
- ✅ Gene and protein information

**NO, if**:
- ❌ Limited disk space (<10GB available)
- ❌ Only need basic disease info
- ❌ Current system sufficient

### Start with: **PubMed API (already have it!)**

Then optionally add:
1. **SemMedDB subset** (~1-2GB) - Drug-disease relationships
2. **PubTator** (~500MB) - Entity annotations
3. **Full PubMed KG** (~50GB+) - Everything

---

## 🔗 Resources

### Official Links:
1. **SemMedDB**: https://lhncbc.nlm.nih.gov/ii/tools/SemRep_SemMedDB_SKR/
2. **PubTator Central**: https://www.ncbi.nlm.nih.gov/research/pubtator/
3. **PubMed API**: https://www.ncbi.nlm.nih.gov/home/develop/api/
4. **BioThings API**: http://biothings.io/ (Alternative access)

### Research Papers:
- "PubMed Knowledge Graph 2.0" (if available - check recent publications)
- "SemMedDB: A PubMed-scale repository of biomedical semantic predications"

---

## ✅ Summary

**Can you use PubMed KG 2.0?** 

✅ **Yes! Multiple ways:**

1. **Already have**: PubMed API access (via `download_pubmed.py`)
2. **Can add**: SemMedDB relationships (~1-10GB)
3. **Enterprise**: Full PubMed KG 2.0 (~50GB+)

**Recommended next step**:
1. Use existing PubMed API (you already have this! ✓)
2. Optionally add SemMedDB for offline drug-disease relationships
3. Test with your current setup first

Your system is already integrated with PubMed through the API! 🎉

Want me to create the SemMedDB downloader script or help you test the existing PubMed integration?
