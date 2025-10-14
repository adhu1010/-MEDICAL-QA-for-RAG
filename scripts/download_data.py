"""
Script to download and prepare medical datasets
"""
import os
import json
import requests
from pathlib import Path

try:
    from loguru import logger
except ImportError:
    class SimpleLogger:
        def info(self, msg): print(msg)
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    logger = SimpleLogger()

# Setup paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MEDQUAD_DIR = DATA_DIR / "medquad"
PUBMED_DIR = DATA_DIR / "pubmed"

# Create directories
DATA_DIR.mkdir(exist_ok=True)
MEDQUAD_DIR.mkdir(exist_ok=True)
PUBMED_DIR.mkdir(exist_ok=True)


def create_sample_medquad_data():
    """
    Create sample MedQuAD-style data for testing
    In production, download from: https://github.com/abachaa/MedQuAD
    """
    logger.info("Creating sample MedQuAD data")
    
    sample_qa_pairs = [
        {
            "question": "What are the side effects of Metformin?",
            "answer": "Common side effects of Metformin include nausea, vomiting, stomach upset, diarrhea, weakness, and a metallic taste in the mouth. Rarely, it may cause lactic acidosis, a serious condition. Always consult your doctor if you experience severe side effects.",
            "focus": "Metformin",
            "type": "side effects",
            "category": "Diabetes",
            "source": "NIH"
        },
        {
            "question": "What is Type 2 Diabetes?",
            "answer": "Type 2 diabetes is a chronic metabolic disorder characterized by high blood sugar levels due to insulin resistance and relative insulin deficiency. It typically develops in adulthood and is associated with obesity, lack of physical activity, and genetic factors.",
            "focus": "Type 2 Diabetes",
            "type": "definition",
            "category": "Diabetes",
            "source": "Mayo Clinic"
        },
        {
            "question": "What is the best antibiotic for sinus infection?",
            "answer": "Amoxicillin is commonly prescribed as a first-line antibiotic for bacterial sinusitis. However, doxycycline or macrolides (like azithromycin) may be alternatives for patients allergic to penicillin. The choice depends on the severity of infection and patient history.",
            "focus": "Sinusitis treatment",
            "type": "treatment",
            "category": "Infections",
            "source": "CDC Guidelines"
        },
        {
            "question": "How does Metformin work?",
            "answer": "Metformin works primarily by decreasing glucose production in the liver and improving insulin sensitivity in peripheral tissues. It also reduces glucose absorption in the intestines and may have beneficial effects on lipid metabolism.",
            "focus": "Metformin mechanism",
            "type": "mechanism",
            "category": "Diabetes",
            "source": "Medical Textbook"
        },
        {
            "question": "What are the symptoms of sinusitis?",
            "answer": "Common symptoms of sinusitis include facial pain or pressure, nasal congestion, thick nasal discharge (yellow or green), reduced sense of smell, cough, fatigue, and headache. Symptoms lasting more than 10 days may indicate bacterial infection.",
            "focus": "Sinusitis",
            "type": "symptoms",
            "category": "Infections",
            "source": "Mayo Clinic"
        }
    ]
    
    # Save as JSON
    output_file = MEDQUAD_DIR / "sample_qa_pairs.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_qa_pairs, f, indent=2)
    
    logger.info(f"Created {len(sample_qa_pairs)} sample QA pairs at {output_file}")
    
    return sample_qa_pairs


def create_sample_pubmed_data():
    """
    Create sample PubMed-style abstracts
    In production, use PubMed API: https://www.ncbi.nlm.nih.gov/pmc/tools/developers/
    """
    logger.info("Creating sample PubMed data")
    
    sample_abstracts = [
        {
            "pmid": "12345678",
            "title": "Efficacy and Safety of Metformin in Type 2 Diabetes",
            "abstract": "Metformin is the first-line medication for type 2 diabetes. This meta-analysis of 100 studies shows that metformin effectively reduces HbA1c levels by 1-2% and has cardiovascular benefits. Common side effects include gastrointestinal disturbances in 20-30% of patients, which usually resolve with continued use.",
            "authors": "Smith J, Johnson A, Williams B",
            "journal": "Diabetes Care",
            "year": 2022,
            "keywords": ["Metformin", "Type 2 Diabetes", "HbA1c", "Cardiovascular"]
        },
        {
            "pmid": "23456789",
            "title": "Antibiotic Treatment Guidelines for Acute Bacterial Sinusitis",
            "abstract": "Current guidelines recommend amoxicillin as first-line therapy for acute bacterial sinusitis in adults. Treatment duration should be 5-7 days for uncomplicated cases. Doxycycline or respiratory fluoroquinolones are alternatives for penicillin-allergic patients.",
            "authors": "Brown C, Davis E, Miller F",
            "journal": "Clinical Infectious Diseases",
            "year": 2023,
            "keywords": ["Sinusitis", "Antibiotics", "Amoxicillin", "Treatment Guidelines"]
        },
        {
            "pmid": "34567890",
            "title": "Mechanisms of Metformin Action Beyond Glucose Lowering",
            "abstract": "Recent research reveals that metformin has pleiotropic effects beyond glycemic control, including anti-inflammatory properties, potential anti-cancer effects, and cardiovascular protection through AMPK activation and modulation of gut microbiota.",
            "authors": "Garcia H, Martinez I, Lopez J",
            "journal": "Nature Medicine",
            "year": 2023,
            "keywords": ["Metformin", "AMPK", "Mechanism", "Inflammation"]
        }
    ]
    
    # Save as JSON
    output_file = PUBMED_DIR / "sample_abstracts.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_abstracts, f, indent=2)
    
    logger.info(f"Created {len(sample_abstracts)} sample abstracts at {output_file}")
    
    return sample_abstracts


def create_readme():
    """Create README for data directory"""
    readme_content = """# Medical Data Directory

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
"""
    
    readme_file = DATA_DIR / "README.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    logger.info(f"Created data README at {readme_file}")


def main():
    """Main data preparation function"""
    logger.info("Starting data preparation")
    
    # Create sample datasets
    medquad_data = create_sample_medquad_data()
    pubmed_data = create_sample_pubmed_data()
    
    # Create README
    create_readme()
    
    logger.info("Data preparation complete")
    logger.info(f"MedQuAD samples: {len(medquad_data)}")
    logger.info(f"PubMed samples: {len(pubmed_data)}")
    logger.info("\n⚠️ Note: These are sample datasets. For production, download full datasets.")


if __name__ == "__main__":
    main()
