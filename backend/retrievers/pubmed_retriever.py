"""
PubMed Real-Time Retriever

Dynamically fetches relevant medical literature from PubMed API
based on the user's query. Provides evidence-based citations.
"""
import urllib.request
import urllib.parse
import json
import time
import xml.etree.ElementTree as ET
from typing import List, Optional
from loguru import logger

from backend.models import ProcessedQuery, RetrievedEvidence
from backend.config import settings


class PubMedRetriever:
    """
    Real-time retriever for PubMed medical literature.
    Fetches abstracts dynamically using NCBI E-utilities API.
    """
    
    def __init__(
        self,
        email: Optional[str] = None,
        api_key: Optional[str] = None,
        max_results: int = 5
    ):
        """
        Initialize PubMed retriever
        
        Args:
            email: Email for NCBI API (required)
            api_key: NCBI API key (optional, for higher rate limits)
            max_results: Maximum articles to retrieve per query
        """
        self.email = email or settings.pubmed_email
        self.api_key = api_key or settings.pubmed_api_key
        self.max_results = max_results
        
        # API endpoints
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.search_url = f"{self.base_url}/esearch.fcgi"
        self.fetch_url = f"{self.base_url}/efetch.fcgi"
        
        # Rate limiting: 3 req/sec without key, 10 req/sec with key
        self.rate_limit = 0.1 if self.api_key else 0.34
        
        # Validate configuration
        if not self.email:
            logger.warning(
                "PubMed email not configured. Set PUBMED_EMAIL in .env file. "
                "PubMed retrieval will be disabled."
            )
            self.enabled = False
        else:
            self.enabled = True
            logger.info(
                f"PubMed retriever initialized (email={self.email}, "
                f"rate={'10 req/s' if self.api_key else '3 req/s'})"
            )
    
    def _build_query(self, query: ProcessedQuery) -> str:
        """
        Build optimized PubMed search query from processed query
        
        Args:
            query: ProcessedQuery object
            
        Returns:
            PubMed search string
        """
        # Start with normalized question
        search_terms = [query.normalized_question]
        
        # Add entity terms for better matching
        if query.entities:
            entity_terms = [entity.text for entity in query.entities]
            search_terms.extend(entity_terms)
        
        # Combine into PubMed query
        # Use [Title/Abstract] field for relevance
        query_string = " ".join(search_terms)
        pubmed_query = f"({query_string})[Title/Abstract]"
        
        logger.debug(f"Built PubMed query: {pubmed_query}")
        return pubmed_query
    
    def _search_pubmed(self, query_string: str) -> List[str]:
        """
        Search PubMed and return PMIDs
        
        Args:
            query_string: PubMed search query
            
        Returns:
            List of PMIDs
        """
        params = {
            'db': 'pubmed',
            'term': query_string,
            'retmax': self.max_results,
            'retmode': 'json',
            'email': self.email,
            'sort': 'relevance'  # Sort by relevance
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        url = self.search_url + '?' + urllib.parse.urlencode(params)
        
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
                pmids = data.get('esearchresult', {}).get('idlist', [])
                
                logger.info(f"PubMed search found {len(pmids)} articles")
                return pmids
                
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return []
    
    def _fetch_abstracts(self, pmids: List[str]) -> List[dict]:
        """
        Fetch article abstracts for given PMIDs
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            List of article dictionaries
        """
        if not pmids:
            return []
        
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml',
            'email': self.email
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        url = self.fetch_url + '?' + urllib.parse.urlencode(params)
        
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                xml_data = response.read().decode()
                articles = self._parse_pubmed_xml(xml_data)
                
                logger.info(f"Fetched {len(articles)} PubMed abstracts")
                return articles
                
        except Exception as e:
            logger.error(f"PubMed fetch failed: {e}")
            return []
    
    def _parse_pubmed_xml(self, xml_data: str) -> List[dict]:
        """
        Parse PubMed XML response into structured articles
        
        Args:
            xml_data: XML string from PubMed API
            
        Returns:
            List of article dictionaries
        """
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
                    title = ''.join(title_elem.itertext()) if title_elem is not None else ''
                    
                    # Extract abstract (combine all parts)
                    abstract_parts = []
                    for abstract_elem in article_elem.findall('.//AbstractText'):
                        # Get label if exists (Background, Methods, Results, etc.)
                        label = abstract_elem.get('Label', '')
                        text = ''.join(abstract_elem.itertext()) if abstract_elem.text else ''
                        
                        if label:
                            abstract_parts.append(f"{label}: {text}")
                        else:
                            abstract_parts.append(text)
                    
                    abstract = ' '.join(abstract_parts)
                    
                    # Extract journal
                    journal_elem = article_elem.find('.//Journal/Title')
                    journal = journal_elem.text if journal_elem is not None else ''
                    
                    # Extract year
                    year_elem = article_elem.find('.//PubDate/Year')
                    year = year_elem.text if year_elem is not None else ''
                    
                    # Extract authors (first 3)
                    authors = []
                    for author_elem in article_elem.findall('.//Author')[:3]:
                        last_name = author_elem.findtext('LastName', '')
                        initials = author_elem.findtext('Initials', '')
                        if last_name:
                            authors.append(f"{last_name} {initials}".strip())
                    
                    # Only include if has title and abstract
                    if title and abstract:
                        articles.append({
                            'pmid': pmid,
                            'title': title,
                            'abstract': abstract,
                            'journal': journal,
                            'year': year,
                            'authors': authors
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to parse article: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"XML parsing failed: {e}")
        
        return articles
    
    def _calculate_relevance(self, article: dict, query: ProcessedQuery) -> float:
        """
        Calculate relevance score for an article
        
        Args:
            article: Article dictionary
            query: ProcessedQuery
            
        Returns:
            Relevance score (0-1)
        """
        # Simple relevance based on entity matching
        score = 0.7  # Base score for PubMed relevance ranking
        
        # Boost if entities appear in title/abstract
        if query.entities:
            text_lower = (article['title'] + ' ' + article['abstract']).lower()
            
            for entity in query.entities:
                if entity.text.lower() in text_lower:
                    score += 0.1
        
        # Cap at 0.95 (reserve 1.0 for KG facts)
        return min(score, 0.95)
    
    def retrieve(
        self,
        query: ProcessedQuery,
        top_k: int = None
    ) -> List[RetrievedEvidence]:
        """
        Retrieve relevant PubMed articles for a query
        
        Args:
            query: ProcessedQuery object
            top_k: Number of articles to return (default: self.max_results)
            
        Returns:
            List of RetrievedEvidence from PubMed
        """
        if not self.enabled:
            logger.warning("PubMed retriever disabled (no email configured)")
            return []
        
        top_k = top_k or self.max_results
        
        logger.info(f"Retrieving PubMed articles for: {query.original_question}")
        
        # Build search query
        pubmed_query = self._build_query(query)
        
        # Search PubMed
        pmids = self._search_pubmed(pubmed_query)
        
        if not pmids:
            logger.info("No PubMed articles found")
            return []
        
        # Fetch abstracts
        time.sleep(self.rate_limit)  # Rate limiting
        articles = self._fetch_abstracts(pmids)
        
        # Convert to RetrievedEvidence
        evidences = []
        for article in articles[:top_k]:
            # Calculate relevance
            confidence = self._calculate_relevance(article, query)
            
            # Format citation
            authors_str = ", ".join(article['authors']) if article['authors'] else "Authors"
            if len(article['authors']) > 3:
                authors_str += " et al."
            
            citation = f"{authors_str}. {article['journal']}. {article['year']}."
            
            # Create evidence content
            content = f"{article['title']}\n\n{article['abstract']}"
            
            evidence = RetrievedEvidence(
                source_type="pubmed",
                content=content,
                confidence=confidence,
                metadata={
                    "pmid": article['pmid'],
                    "title": article['title'],
                    "journal": article['journal'],
                    "year": article['year'],
                    "authors": article['authors'],
                    "citation": citation,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{article['pmid']}/"
                }
            )
            evidences.append(evidence)
        
        logger.info(f"Retrieved {len(evidences)} PubMed evidences")
        return evidences


# Singleton instance
_pubmed_retriever_instance = None


def get_pubmed_retriever() -> PubMedRetriever:
    """Get or create PubMedRetriever singleton"""
    global _pubmed_retriever_instance
    if _pubmed_retriever_instance is None:
        _pubmed_retriever_instance = PubMedRetriever()
    return _pubmed_retriever_instance
