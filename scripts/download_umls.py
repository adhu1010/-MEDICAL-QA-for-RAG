"""
UMLS Knowledge Graph Downloader

This script helps download and process UMLS (Unified Medical Language System) data
for the Medical RAG QA system.

Prerequisites:
- UMLS license and API key from https://uts.nlm.nih.gov/
- MetamorphoSys tool (included in UMLS download)

UMLS provides comprehensive medical vocabularies including:
- SNOMED CT (clinical terms)
- RxNorm (medications)
- ICD-10/11 (diagnoses)
- LOINC (lab tests)
- CPT (procedures)
"""

import os
import json
import urllib.request
import urllib.parse
from pathlib import Path
import logging
from typing import List, Dict, Tuple
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UMLSDownloader:
    """Download and process UMLS data"""
    
    def __init__(self, api_key: str, version: str = "2024AA"):
        self.api_key = api_key
        self.version = version
        self.base_url = "https://uts-ws.nlm.nih.gov/rest"
        
        self.data_dir = Path("../data/enterprise/umls")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_tgt(self):
        """Get Ticket Granting Ticket for authentication"""
        url = "https://utslogin.nlm.nih.gov/cas/v1/api-key"
        
        data = urllib.parse.urlencode({'apikey': self.api_key}).encode()
        
        try:
            with urllib.request.urlopen(url, data) as response:
                tgt = response.read().decode()
                # Extract TGT from response
                return tgt
        except Exception as e:
            logger.error(f"Failed to get TGT: {e}")
            return None
    
    def get_service_ticket(self, tgt: str):
        """Get Service Ticket using TGT"""
        service = "http://umlsks.nlm.nih.gov"
        
        data = urllib.parse.urlencode({'service': service}).encode()
        
        try:
            with urllib.request.urlopen(tgt, data) as response:
                st = response.read().decode()
                return st
        except Exception as e:
            logger.error(f"Failed to get service ticket: {e}")
            return None
    
    def search_concept(self, term: str, ticket: str) -> Dict:
        """Search for a concept in UMLS"""
        url = f"{self.base_url}/search/current"
        params = {
            'string': term,
            'ticket': ticket
        }
        
        query_url = url + '?' + urllib.parse.urlencode(params)
        
        try:
            with urllib.request.urlopen(query_url) as response:
                data = json.loads(response.read().decode())
                return data
        except Exception as e:
            logger.error(f"Search failed for '{term}': {e}")
            return {}
    
    def get_concept_relations(self, cui: str, ticket: str) -> List[Dict]:
        """Get relationships for a concept (CUI)"""
        url = f"{self.base_url}/content/current/CUI/{cui}/relations"
        params = {'ticket': ticket}
        
        query_url = url + '?' + urllib.parse.urlencode(params)
        
        try:
            with urllib.request.urlopen(query_url) as response:
                data = json.loads(response.read().decode())
                return data.get('result', [])
        except Exception as e:
            logger.error(f"Failed to get relations for {cui}: {e}")
            return []
    
    def download_concepts_batch(self, terms: List[str]) -> List[Dict]:
        """Download concepts and their relationships for a batch of terms"""
        logger.info(f"Downloading {len(terms)} medical concepts from UMLS...")
        
        # Get authentication ticket
        tgt = self.get_tgt()
        if not tgt:
            logger.error("Authentication failed")
            return []
        
        concepts = []
        
        # Get initial service ticket
        ticket = self.get_service_ticket(tgt)
        if not ticket:
            logger.error("Failed to get initial service ticket")
            return []
        
        for i, term in enumerate(terms):
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(terms)}")
                # Get new service ticket periodically
                new_ticket = self.get_service_ticket(tgt)
                if new_ticket:
                    ticket = new_ticket
            
            # Search for concept
            results = self.search_concept(term, ticket)
            
            if not results or 'result' not in results:
                continue
            
            for result in results['result']['results'][:3]:  # Top 3 results
                cui = result.get('ui')
                name = result.get('name')
                
                if not cui:
                    continue
                
                # Get relationships
                time.sleep(0.1)  # Rate limiting
                relations = self.get_concept_relations(cui, ticket)
                
                concepts.append({
                    'cui': cui,
                    'name': name,
                    'search_term': term,
                    'relations': relations
                })
            
            time.sleep(0.2)  # Rate limiting
        
        logger.info(f"Downloaded {len(concepts)} concepts")
        return concepts
    
    def export_to_knowledge_graph(self, concepts: List[Dict], output_file: str):
        """Export UMLS concepts to knowledge graph format"""
        logger.info("Converting to knowledge graph format...")
        
        triples = []
        
        for concept in concepts:
            cui = concept['cui']
            name = concept['name']
            
            # Add concept definition
            triples.append({
                'subject': name,
                'predicate': 'UMLS_CUI',
                'object': cui
            })
            
            # Add relationships
            for relation in concept.get('relations', []):
                rel_type = relation.get('relatedIdName', 'RELATED_TO')
                related_cui = relation.get('relatedId', '')
                related_name = relation.get('relatedFromIdName', related_cui)
                
                triples.append({
                    'subject': name,
                    'predicate': rel_type,
                    'object': related_name
                })
        
        # Save as JSON
        output_path = self.data_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(triples, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(triples)} triples to {output_path}")
        return triples


def download_umls_for_medical_domains(api_key: str):
    """Download UMLS data for common medical domains"""
    
    downloader = UMLSDownloader(api_key)
    
    # Common medical terms to build knowledge graph
    medical_terms = [
        # Diseases
        "diabetes", "hypertension", "cancer", "asthma", "pneumonia",
        "arthritis", "influenza", "migraine", "depression", "anxiety",
        
        # Symptoms
        "fever", "pain", "nausea", "cough", "headache",
        "fatigue", "dizziness", "rash", "shortness of breath",
        
        # Medications
        "metformin", "insulin", "aspirin", "ibuprofen", "amoxicillin",
        "lisinopril", "atorvastatin", "levothyroxine",
        
        # Procedures
        "surgery", "biopsy", "chemotherapy", "physical therapy",
        "vaccination", "blood test", "x-ray", "mri", "ct scan",
        
        # Anatomy
        "heart", "lung", "liver", "kidney", "brain",
        "stomach", "intestine", "blood vessel"
    ]
    
    logger.info(f"Downloading UMLS data for {len(medical_terms)} medical terms")
    
    concepts = downloader.download_concepts_batch(medical_terms)
    
    # Export to knowledge graph format
    triples = downloader.export_to_knowledge_graph(concepts, "umls_knowledge_graph.json")
    
    logger.info("\n" + "=" * 60)
    logger.info("UMLS Download Complete!")
    logger.info("=" * 60)
    logger.info(f"Downloaded concepts: {len(concepts)}")
    logger.info(f"Knowledge triples: {len(triples)}")
    logger.info(f"Output: {downloader.data_dir / 'umls_knowledge_graph.json'}")
    
    return concepts, triples


def main():
    """Main entry point"""
    import sys
    
    print("=" * 60)
    print("UMLS Knowledge Graph Downloader")
    print("=" * 60)
    
    # Get API key from environment or user input
    api_key = os.getenv('UMLS_API_KEY')
    
    if not api_key:
        print("\nUMLS API Key not found in environment.")
        print("Get your API key from: https://uts.nlm.nih.gov/uts/profile")
        api_key = input("\nEnter UMLS API Key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Exiting.")
        sys.exit(1)
    
    try:
        download_umls_for_medical_domains(api_key)
    except KeyboardInterrupt:
        print("\n\n⚠️  Download cancelled by user.")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise


if __name__ == "__main__":
    main()
