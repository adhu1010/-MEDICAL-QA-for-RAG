"""
Process downloaded MedQuAD dataset into usable format

This script processes the MedQuAD XML files from:
c:/Users/eahkf/AppData/Roaming/Qoder/User/globalStorage/alefragnani.project-manager/data/MedQuAD-master

And converts them to JSON format for the vector store.
"""

import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_medquad_directory():
    """Find the MedQuAD directory"""
    # Check common locations
    possible_paths = [
        Path("../data/MedQuAD-master"),
        Path("../../data/MedQuAD-master"),
        Path("c:/Users/eahkf/AppData/Roaming/Qoder/User/globalStorage/alefragnani.project-manager/data/MedQuAD-master"),
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"Found MedQuAD at: {path}")
            return path
    
    logger.error("MedQuAD directory not found!")
    logger.error("Expected location: data/MedQuAD-master")
    return None


def parse_medquad_xml(xml_path: Path):
    """Parse a single MedQuAD XML file to extract QA pairs"""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        qa_pairs = []
        
        # Extract document focus (disease/condition name)
        focus_elem = root.find('.//Focus')
        focus = focus_elem.text if focus_elem is not None else ''
        
        # Extract QAPairs
        for qa_pair in root.findall('.//QAPair'):
            question_elem = qa_pair.find('Question')
            answer_elem = qa_pair.find('Answer')
            
            if question_elem is not None and answer_elem is not None:
                question = question_elem.text
                answer = answer_elem.text
                
                if question and answer:
                    qa_pairs.append({
                        'question': question.strip(),
                        'answer': answer.strip(),
                        'focus': focus.strip() if focus else '',
                        'source_file': xml_path.stem
                    })
        
        return qa_pairs
    except Exception as e:
        logger.warning(f"Error parsing {xml_path}: {e}")
        return []


def process_medquad_category(category_path: Path, category_name: str):
    """Process all XML files in a MedQuAD category"""
    logger.info(f"Processing category: {category_name}")
    
    xml_files = list(category_path.glob("*.xml"))
    logger.info(f"  Found {len(xml_files)} XML files")
    
    all_qa_pairs = []
    
    for i, xml_file in enumerate(xml_files):
        if (i + 1) % 100 == 0:
            logger.info(f"  Progress: {i + 1}/{len(xml_files)}")
        
        qa_pairs = parse_medquad_xml(xml_file)
        
        # Add category information
        for qa in qa_pairs:
            qa['category'] = category_name
        
        all_qa_pairs.extend(qa_pairs)
    
    logger.info(f"  Extracted {len(all_qa_pairs)} QA pairs")
    return all_qa_pairs


def process_all_medquad():
    """Process all MedQuAD categories"""
    logger.info("=" * 60)
    logger.info("Processing MedQuAD Dataset")
    logger.info("=" * 60)
    
    # Find MedQuAD directory
    medquad_path = find_medquad_directory()
    
    if not medquad_path:
        logger.error("Cannot proceed without MedQuAD data")
        return []
    
    # MedQuAD categories
    categories = [
        ("1_CancerGov_QA", "Cancer"),
        ("2_GARD_QA", "Genetic and Rare Diseases"),
        ("3_GHR_QA", "Genetics Home Reference"),
        ("4_MPlus_Health_Topics_QA", "Health Topics"),
        ("5_NIDDK_QA", "Digestive and Kidney Diseases"),
        ("6_NINDS_QA", "Neurological Disorders"),
        ("7_SeniorHealth_QA", "Senior Health"),
        ("8_NHLBI_QA_XML", "Heart, Lung, and Blood"),
        ("9_CDC_QA", "CDC"),
        ("10_MPlus_ADAM_QA", "ADAM Encyclopedia"),
        ("11_MPlusDrugs_QA", "Drugs"),
        ("12_MPlusHerbsSupplements_QA", "Herbs and Supplements")
    ]
    
    all_qa_pairs = []
    category_stats = {}
    
    for dir_name, category_name in categories:
        category_path = medquad_path / dir_name
        
        if not category_path.exists():
            logger.warning(f"Category not found: {dir_name}")
            continue
        
        qa_pairs = process_medquad_category(category_path, category_name)
        all_qa_pairs.extend(qa_pairs)
        
        category_stats[category_name] = len(qa_pairs)
    
    # Save to JSON
    output_dir = Path("../data")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "medquad_processed.json"
    
    logger.info(f"\nSaving processed data to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_qa_pairs, f, indent=2, ensure_ascii=False)
    
    # Print statistics
    logger.info("\n" + "=" * 60)
    logger.info("Processing Complete!")
    logger.info("=" * 60)
    logger.info(f"Total QA pairs: {len(all_qa_pairs)}")
    logger.info("\nBreakdown by category:")
    for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {category}: {count} QA pairs")
    
    logger.info(f"\nOutput file: {output_file}")
    logger.info("=" * 60)
    
    return all_qa_pairs


def download_disease_ontology():
    """Download Disease Ontology for knowledge graph"""
    logger.info("\n" + "=" * 60)
    logger.info("Downloading Disease Ontology")
    logger.info("=" * 60)
    
    import urllib.request
    
    data_dir = Path("../data")
    data_dir.mkdir(exist_ok=True)
    
    url = "https://github.com/DiseaseOntology/HumanDiseaseOntology/raw/main/src/ontology/doid.obo"
    dest_path = data_dir / "disease_ontology.obo"
    
    if dest_path.exists():
        logger.info(f"Disease Ontology already exists: {dest_path}")
        return dest_path
    
    try:
        logger.info(f"Downloading from: {url}")
        
        def progress_hook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 / total_size)
                mb_downloaded = downloaded / (1024 * 1024)
                mb_total = total_size / (1024 * 1024)
                print(f"\rProgress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='')
        
        urllib.request.urlretrieve(url, str(dest_path), progress_hook)
        print()  # New line
        
        logger.info(f"✓ Downloaded to: {dest_path}")
        return dest_path
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return None


def parse_disease_ontology(obo_path: Path):
    """Parse Disease Ontology OBO file"""
    logger.info("Parsing Disease Ontology...")
    
    diseases = []
    current_term: dict = {}
    
    with open(obo_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            if line == "[Term]":
                if current_term and 'name' in current_term:
                    diseases.append(current_term)
                current_term = {'relationships': []}
            
            elif line.startswith("id:"):
                current_term['id'] = line.split("id:")[1].strip()
            
            elif line.startswith("name:"):
                current_term['name'] = line.split("name:")[1].strip()
            
            elif line.startswith("def:"):
                try:
                    definition = line.split('"')[1]
                    current_term['definition'] = definition
                except IndexError:
                    pass
            
            elif line.startswith("is_a:"):
                parent_id = line.split("is_a:")[1].split("!")[0].strip()
                current_term['relationships'].append({
                    'type': 'is_a',
                    'target': parent_id
                })
            
            elif line.startswith("synonym:"):
                if 'synonyms' not in current_term:
                    current_term['synonyms'] = []
                try:
                    synonym = line.split('"')[1]
                    current_term['synonyms'].append(synonym)
                except IndexError:
                    pass
    
    # Add last term
    if current_term and 'name' in current_term:
        diseases.append(current_term)
    
    logger.info(f"Parsed {len(diseases)} disease terms")
    
    # Save to JSON
    output_path = Path("../data/disease_ontology_processed.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(diseases, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved to: {output_path}")
    return diseases


def main():
    """Main processing function"""
    logger.info("\n" + "=" * 60)
    logger.info("Medical RAG QA - Data Processing")
    logger.info("=" * 60 + "\n")
    
    # Step 1: Process MedQuAD
    qa_pairs = process_all_medquad()
    
    if not qa_pairs:
        logger.error("No QA pairs processed. Check MedQuAD directory location.")
        return
    
    # Step 2: Download and parse Disease Ontology
    do_path = download_disease_ontology()
    
    if do_path and do_path.exists():
        diseases = parse_disease_ontology(do_path)
    else:
        logger.warning("Disease Ontology not available")
        diseases = []
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Data Processing Complete!")
    logger.info("=" * 60)
    logger.info(f"✓ MedQuAD QA pairs: {len(qa_pairs)}")
    logger.info(f"✓ Disease terms: {len(diseases)}")
    logger.info("\nNext steps:")
    logger.info("1. python scripts/build_vector_store.py")
    logger.info("2. python scripts/build_knowledge_graph.py")
    logger.info("3. python scripts/run.py")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
