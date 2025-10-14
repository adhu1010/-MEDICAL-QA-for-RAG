"""
PubMed Central API Integration

This script provides real-time access to PubMed medical literature
using the NCBI E-utilities API.

Features:
- Search PubMed for relevant medical articles
- Fetch abstracts and metadata
- Optional: Generate embeddings for vector store
- Rate limiting and API key support

API Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25501/
"""

import os
import json
import urllib.request
import urllib.parse
from pathlib import Path
import logging
from typing import List, Dict, Optional
import time
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PubMedAPI:
    """Interface to PubMed E-utilities API"""
    
    def __init__(self, email: str, api_key: Optional[str] = None):
        self.email = email
        self.api_key = api_key
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        
        # Rate limits: 3 req/sec without key, 10 req/sec with key
        self.rate_limit = 0.1 if api_key else 0.34
        
        self.data_dir = Path("../data/enterprise/pubmed")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def search(self, query: str, max_results: int = 100) -> List[str]:
        """Search PubMed and return list of PMIDs"""
        logger.info(f"Searching PubMed: '{query}'")
        
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'json',
            'email': self.email
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        url = f"{self.base_url}/esearch.fcgi"
        query_url = url + '?' + urllib.parse.urlencode(params)
        
        try:
            with urllib.request.urlopen(query_url) as response:
                data = json.loads(response.read().decode())
                pmids = data.get('esearchresult', {}).get('idlist', [])
                logger.info(f"Found {len(pmids)} articles")
                return pmids
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def fetch_abstracts(self, pmids: List[str]) -> List[Dict]:
        """Fetch abstracts for given PMIDs"""
        logger.info(f"Fetching {len(pmids)} abstracts...")
        
        articles = []
        
        # Process in batches of 200 (API limit)
        batch_size = 200
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i+batch_size]
            
            params = {
                'db': 'pubmed',
                'id': ','.join(batch),
                'retmode': 'xml',
                'email': self.email
            }
            
            if self.api_key:
                params['api_key'] = self.api_key
            
            url = f"{self.base_url}/efetch.fcgi"
            query_url = url + '?' + urllib.parse.urlencode(params)
            
            try:
                with urllib.request.urlopen(query_url) as response:
                    xml_data = response.read().decode()
                    batch_articles = self._parse_pubmed_xml(xml_data)
                    articles.extend(batch_articles)
                    
                    logger.info(f"Fetched batch {i//batch_size + 1}: {len(batch_articles)} articles")
            except Exception as e:
                logger.error(f"Fetch failed for batch: {e}")
            
            time.sleep(self.rate_limit)
        
        return articles
    
    def _parse_pubmed_xml(self, xml_data: str) -> List[Dict]:
        """Parse PubMed XML response"""
        articles = []
        
        try:
            root = ET.fromstring(xml_data)
            
            for article_elem in root.findall('.//PubmedArticle'):
                try:
                    # Extract PMID
                    pmid_elem = article_elem.find('.//PMID')
                    pmid = pmid_elem.text if pmid_elem is not None else ''
                    
                    # Extract title
                    title_elem = article_elem.find('.//ArticleTitle')
                    title = title_elem.text if title_elem is not None else ''
                    
                    # Extract abstract
                    abstract_parts = []
                    for abstract_elem in article_elem.findall('.//AbstractText'):
                        text = abstract_elem.text or ''
                        abstract_parts.append(text)
                    abstract = ' '.join(abstract_parts)
                    
                    # Extract journal
                    journal_elem = article_elem.find('.//Journal/Title')
                    journal = journal_elem.text if journal_elem is not None else ''
                    
                    # Extract publication year
                    year_elem = article_elem.find('.//PubDate/Year')
                    year = year_elem.text if year_elem is not None else ''
                    
                    # Extract MeSH keywords
                    keywords = []
                    for mesh_elem in article_elem.findall('.//MeshHeading/DescriptorName'):
                        if mesh_elem.text:
                            keywords.append(mesh_elem.text)
                    
                    if title and abstract:
                        articles.append({
                            'pmid': pmid,
                            'title': title,
                            'abstract': abstract,
                            'journal': journal,
                            'year': year,
                            'keywords': keywords
                        })
                except Exception as e:
                    logger.warning(f"Failed to parse article: {e}")
                    continue
        except Exception as e:
            logger.error(f"XML parsing failed: {e}")
        
        return articles
    
    def download_medical_topics(self, topics: List[str], articles_per_topic: int = 50):
        """Download articles for multiple medical topics"""
        logger.info(f"Downloading articles for {len(topics)} medical topics")
        
        all_articles = []
        
        for topic in topics:
            logger.info(f"\nProcessing topic: {topic}")
            
            # Search for topic
            pmids = self.search(f"{topic}[Title/Abstract]", max_results=articles_per_topic)
            
            if not pmids:
                continue
            
            # Fetch abstracts
            articles = self.fetch_abstracts(pmids)
            
            # Add topic tag
            for article in articles:
                article['topic'] = topic
            
            all_articles.extend(articles)
            
            time.sleep(self.rate_limit)
        
        # Save to JSON
        output_file = self.data_dir / "pubmed_articles.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Downloaded {len(all_articles)} total articles")
        logger.info(f"Saved to: {output_file}")
        logger.info("=" * 60)
        
        return all_articles


def download_pubmed_for_medical_domains(email: str, api_key: Optional[str] = None):
    """Download PubMed articles for common medical domains"""
    
    api = PubMedAPI(email, api_key)
    
    # Medical topics to download
    medical_topics = [
        # Chronic diseases
        "diabetes mellitus treatment",
        "hypertension management",
        "cancer therapy",
        "asthma treatment",
        
        # Infectious diseases
        "pneumonia diagnosis",
        "influenza prevention",
        "antibiotic resistance",
        
        # Mental health
        "depression treatment",
        "anxiety disorders",
        
        # Common conditions
        "headache diagnosis",
        "back pain management",
        "arthritis treatment",
        
        # Preventive care
        "vaccination guidelines",
        "preventive screening",
        "health promotion"
    ]
    
    articles = api.download_medical_topics(medical_topics, articles_per_topic=30)
    
    return articles


def main():
    """Main entry point"""
    import sys
    
    print("=" * 60)
    print("PubMed Medical Literature Downloader")
    print("=" * 60)
    
    # Get email from environment or user input
    email = os.getenv('PUBMED_EMAIL')
    
    if not email:
        print("\nNCBI requires an email address for API access.")
        email = input("Enter your email: ").strip()
    
    if not email:
        print("❌ No email provided. Exiting.")
        sys.exit(1)
    
    # Get API key (optional)
    api_key = os.getenv('PUBMED_API_KEY')
    
    if not api_key:
        has_key = input("\nDo you have an NCBI API key? (y/n) [n]: ").lower().strip()
        if has_key == 'y':
            api_key = input("Enter API key: ").strip()
    
    try:
        articles = download_pubmed_for_medical_domains(email, api_key)
        
        print(f"\n✓ Successfully downloaded {len(articles)} articles")
        print("\nNext steps:")
        print("1. Run: python scripts/build_vector_store.py --pubmed")
        print("   (This will add PubMed articles to vector store)")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Download cancelled by user.")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise


if __name__ == "__main__":
    main()
