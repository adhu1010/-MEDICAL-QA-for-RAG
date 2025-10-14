# Medical Data Directory

## Data Sources

### MedQuAD
Medical Question Answering Dataset from NIH, Mayo Clinic, and other trusted sources.
- **Official Repository**: https://github.com/abachaa/MedQuAD
- **Format**: JSON with question-answer pairs
- **Categories**: Diseases, Treatments, Medications, Symptoms

### PubMed Abstracts
Biomedical literature from PubMed Central.
- **API**: https://www.ncbi.nlm.nih.gov/home/develop/api/
- **Format**: JSON with PMID, title, abstract, metadata
- **Usage**: Evidence-based retrieval

### UMLS (Unified Medical Language System)
Medical terminology and ontology for knowledge graph construction.
- **Source**: https://www.nlm.nih.gov/research/umls/
- **License Required**: Yes (free for research)
- **Format**: RRF files, can be loaded into Neo4j or NetworkX

## Sample Data

The `sample_*` files are for testing and demonstration. Replace with actual data for production use.

## Download Instructions

1. **MedQuAD**: Clone from GitHub
   ```bash
   git clone https://github.com/abachaa/MedQuAD.git data/medquad_full
   ```

2. **PubMed**: Use the Entrez API
   ```python
   from Bio import Entrez
   # Configure API and download abstracts
   ```

3. **UMLS**: Register and download from NLM
   - Requires UMLS Terminology Services account
   - Download Metathesaurus files

## Data Privacy

⚠️ Do not commit actual medical data to version control.
- Use `.gitignore` to exclude data files
- Only sample/synthetic data should be in repository
