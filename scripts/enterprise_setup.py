"""
Enterprise Setup for Medical RAG QA System

This script helps you configure:
1. Full UMLS Knowledge Graph (requires free NIH UMLS license)
2. PubMed Central embeddings (large download ~100GB+)
3. Neo4j database for persistent KG storage

Prerequisites:
- UMLS license from https://uts.nlm.nih.gov/uts/signup-login
- Neo4j installed (https://neo4j.com/download/)
- Sufficient disk space (~150GB+ recommended)
"""

import os
import json
import urllib.request
import zipfile
import subprocess
from pathlib import Path
from getpass import getpass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnterpriseSetup:
    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent
        self.data_dir = self.workspace_root / "data" / "enterprise"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = {
            "umls": {},
            "pubmed": {},
            "neo4j": {}
        }
    
    def welcome(self):
        """Display welcome message and prerequisites"""
        print("=" * 80)
        print("MEDICAL RAG QA - ENTERPRISE SETUP")
        print("=" * 80)
        print("\nThis setup will help you configure:")
        print("✓ Full UMLS Knowledge Graph")
        print("✓ PubMed Central embeddings")
        print("✓ Neo4j persistent storage")
        print("\n" + "=" * 80)
        print("PREREQUISITES CHECK")
        print("=" * 80)
        
        # Check disk space
        import shutil
        total, used, free = shutil.disk_usage(self.workspace_root)
        free_gb = free // (2**30)
        
        print(f"\n1. Disk Space: {free_gb} GB available")
        if free_gb < 150:
            print("   ⚠️  WARNING: Recommended 150GB+ free space")
            print("   ⚠️  You may need to skip PubMed embeddings or use external storage")
        else:
            print("   ✓ Sufficient disk space")
        
        print("\n2. UMLS License:")
        print("   Required: Free account at https://uts.nlm.nih.gov/uts/signup-login")
        print("   You'll need your UMLS API Key")
        
        print("\n3. Neo4j Database:")
        print("   Required: Neo4j installed locally or accessible remotely")
        print("   Download: https://neo4j.com/download/")
        
        input("\nPress Enter to continue or Ctrl+C to exit...")
    
    def setup_umls(self):
        """Setup UMLS Knowledge Graph"""
        print("\n" + "=" * 80)
        print("STEP 1: UMLS KNOWLEDGE GRAPH SETUP")
        print("=" * 80)
        
        print("\n📋 UMLS License Information:")
        print("1. Create free account: https://uts.nlm.nih.gov/uts/signup-login")
        print("2. Accept UMLS license agreement")
        print("3. Get your API key from profile settings")
        
        use_umls = input("\nDo you have a UMLS API key? (y/n): ").lower().strip()
        
        if use_umls != 'y':
            print("\n⚠️  Skipping UMLS setup. Using Disease Ontology instead.")
            print("   To use UMLS later, get API key and re-run this setup.")
            self.config['umls']['enabled'] = False
            self.config['umls']['fallback'] = 'disease_ontology'
            return False
        
        api_key = getpass("Enter your UMLS API Key: ").strip()
        
        if not api_key:
            print("❌ No API key provided. Using fallback data.")
            self.config['umls']['enabled'] = False
            return False
        
        self.config['umls']['enabled'] = True
        self.config['umls']['api_key'] = api_key
        
        # Choose UMLS version
        print("\n📦 UMLS Versions:")
        print("1. UMLS 2024AA (Latest - Recommended)")
        print("2. UMLS 2023AB")
        print("3. UMLS 2023AA")
        
        version_choice = input("Select version (1-3) [1]: ").strip() or "1"
        versions = {
            "1": "2024AA",
            "2": "2023AB", 
            "3": "2023AA"
        }
        umls_version = versions.get(version_choice, "2024AA")
        self.config['umls']['version'] = umls_version
        
        # Choose UMLS subsets
        print("\n📊 UMLS Data Subsets (to reduce size):")
        print("1. Full UMLS (~30GB) - All medical vocabularies")
        print("2. SNOMED CT + RxNorm (~5GB) - Diseases + Drugs")
        print("3. Essential Medical (~2GB) - Core medical concepts only")
        
        subset_choice = input("Select subset (1-3) [2]: ").strip() or "2"
        subsets = {
            "1": "full",
            "2": "snomed_rxnorm",
            "3": "essential"
        }
        self.config['umls']['subset'] = subsets.get(subset_choice, "snomed_rxnorm")
        
        # Download location
        print(f"\n📁 UMLS data will be downloaded to:")
        print(f"   {self.data_dir / 'umls'}")
        
        download_now = input("\nDownload UMLS now? (y/n) [y]: ").lower().strip() or 'y'
        
        if download_now == 'y':
            self._download_umls(api_key, umls_version)
        else:
            print("⏭️  UMLS download deferred. Run download_umls.py later.")
        
        return True
    
    def _download_umls(self, api_key, version):
        """Download UMLS data using API"""
        print(f"\n⬇️  Downloading UMLS {version}...")
        
        umls_dir = self.data_dir / "umls"
        umls_dir.mkdir(exist_ok=True)
        
        # UMLS download requires MetamorphoSys tool
        print("\n📖 UMLS Download Instructions:")
        print("1. Go to: https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html")
        print(f"2. Download UMLS {version} Full Release")
        print("3. Extract using MetamorphoSys tool (included in download)")
        print("4. Select subsets as configured above")
        print(f"5. Extract to: {umls_dir}")
        print("\n⚠️  Note: UMLS requires manual download due to license agreement.")
        print("   Automated download will be supported in future versions.")
        
        # Save instructions
        instructions_file = umls_dir / "DOWNLOAD_INSTRUCTIONS.txt"
        with open(instructions_file, 'w') as f:
            f.write(f"UMLS {version} Download Instructions\n")
            f.write("=" * 50 + "\n\n")
            f.write("1. Visit: https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html\n")
            f.write(f"2. Download: UMLS {version} Full Release\n")
            f.write("3. Extract using MetamorphoSys\n")
            f.write(f"4. Extract to: {umls_dir}\n")
            f.write("\nAPI Key (save securely): " + api_key[:10] + "..." + "\n")
        
        logger.info(f"Instructions saved to: {instructions_file}")
    
    def setup_pubmed(self):
        """Setup PubMed Central embeddings"""
        print("\n" + "=" * 80)
        print("STEP 2: PUBMED CENTRAL EMBEDDINGS SETUP")
        print("=" * 80)
        
        print("\n📊 PubMed Embedding Options:")
        print("1. Full PMC embeddings (~100GB) - All PubMed Central articles")
        print("2. Subset (Top journals, ~20GB) - High-impact journals only")
        print("3. On-demand (API-based) - Real-time retrieval (no download)")
        print("4. Skip - Use MedQuAD only")
        
        choice = input("\nSelect option (1-4) [3]: ").strip() or "3"
        
        if choice == "4":
            print("⏭️  Skipping PubMed embeddings.")
            self.config['pubmed']['enabled'] = False
            return False
        
        self.config['pubmed']['enabled'] = True
        
        if choice == "3":
            # On-demand API mode
            self.config['pubmed']['mode'] = 'api'
            print("\n✓ PubMed API mode configured")
            print("  Articles will be fetched on-demand using E-utilities API")
            
            email = input("Enter your email (for NCBI API): ").strip()
            self.config['pubmed']['email'] = email
            
            # Optional API key for higher rate limits
            has_api_key = input("Do you have an NCBI API key? (y/n) [n]: ").lower().strip()
            if has_api_key == 'y':
                api_key = getpass("Enter NCBI API key: ").strip()
                self.config['pubmed']['api_key'] = api_key
            
            return True
        
        elif choice in ["1", "2"]:
            # Prebuilt embeddings
            self.config['pubmed']['mode'] = 'prebuilt'
            self.config['pubmed']['subset'] = 'full' if choice == "1" else 'top_journals'
            
            size = "100GB" if choice == "1" else "20GB"
            print(f"\n⚠️  This will download ~{size} of data")
            
            # Check available space
            import shutil
            _, _, free = shutil.disk_usage(self.workspace_root)
            free_gb = free // (2**30)
            required_gb = 100 if choice == "1" else 20
            
            if free_gb < required_gb + 10:
                print(f"❌ Insufficient disk space. Need {required_gb}GB, have {free_gb}GB")
                print("   Consider using option 3 (API mode) instead")
                return False
            
            download_now = input(f"\nDownload {size} now? (y/n) [n]: ").lower().strip()
            
            if download_now == 'y':
                self._download_pubmed_embeddings(self.config['pubmed']['subset'])
            else:
                print("⏭️  PubMed download deferred.")
        
        return True
    
    def _download_pubmed_embeddings(self, subset):
        """Download prebuilt PubMed embeddings"""
        print(f"\n⬇️  Downloading PubMed {subset} embeddings...")
        
        pubmed_dir = self.data_dir / "pubmed_embeddings"
        pubmed_dir.mkdir(exist_ok=True)
        
        # Note: These URLs are placeholders - you would host these on cloud storage
        urls = {
            'full': 'https://example.com/pubmed_full_biobert_embeddings.tar.gz',
            'top_journals': 'https://example.com/pubmed_top_journals_embeddings.tar.gz'
        }
        
        print("\n📖 PubMed Embeddings Download:")
        print(f"   Due to size, embeddings should be downloaded separately")
        print(f"   Contact system administrator or use API mode")
        print(f"\n   Alternative: Use BioASQ or TREC-COVID prebuilt indices")
        
        # Save instructions
        instructions_file = pubmed_dir / "DOWNLOAD_INSTRUCTIONS.txt"
        with open(instructions_file, 'w') as f:
            f.write("PubMed Embeddings Download Instructions\n")
            f.write("=" * 50 + "\n\n")
            f.write("Option 1: Download prebuilt embeddings\n")
            f.write(f"  - Contact administrator for {subset} embeddings\n")
            f.write(f"  - Extract to: {pubmed_dir}\n\n")
            f.write("Option 2: Use existing indices\n")
            f.write("  - BioASQ: http://bioasq.org/\n")
            f.write("  - TREC-COVID: https://ir.nist.gov/trec-covid/\n")
        
        logger.info(f"Instructions saved to: {instructions_file}")
    
    def setup_neo4j(self):
        """Setup Neo4j database connection"""
        print("\n" + "=" * 80)
        print("STEP 3: NEO4J PERSISTENT STORAGE SETUP")
        print("=" * 80)
        
        print("\n📦 Neo4j Installation:")
        print("1. Download: https://neo4j.com/download/")
        print("2. Install Neo4j Community or Enterprise Edition")
        print("3. Start Neo4j server")
        
        has_neo4j = input("\nIs Neo4j installed and running? (y/n): ").lower().strip()
        
        if has_neo4j != 'y':
            print("\n⚠️  Neo4j not available. Using in-memory NetworkX graph.")
            print("   Install Neo4j for persistent, scalable storage.")
            self.config['neo4j']['enabled'] = False
            self.config['neo4j']['fallback'] = 'networkx'
            return False
        
        self.config['neo4j']['enabled'] = True
        
        # Get connection details
        print("\n🔧 Neo4j Connection Details:")
        
        uri = input("Neo4j URI [bolt://localhost:7687]: ").strip() or "bolt://localhost:7687"
        self.config['neo4j']['uri'] = uri
        
        username = input("Neo4j Username [neo4j]: ").strip() or "neo4j"
        self.config['neo4j']['username'] = username
        
        password = getpass("Neo4j Password: ").strip()
        self.config['neo4j']['password'] = password
        
        database = input("Database name [medical-kg]: ").strip() or "medical-kg"
        self.config['neo4j']['database'] = database
        
        # Test connection
        print("\n🔍 Testing Neo4j connection...")
        
        if self._test_neo4j_connection():
            print("✓ Neo4j connection successful!")
            return True
        else:
            print("❌ Neo4j connection failed. Check credentials and try again.")
            self.config['neo4j']['enabled'] = False
            return False
    
    def _test_neo4j_connection(self):
        """Test Neo4j database connection"""
        try:
            from neo4j import GraphDatabase
            
            driver = GraphDatabase.driver(
                self.config['neo4j']['uri'],
                auth=(self.config['neo4j']['username'], 
                      self.config['neo4j']['password'])
            )
            
            with driver.session(database=self.config['neo4j'].get('database')) as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                
            driver.close()
            return record['test'] == 1
            
        except ImportError:
            print("⚠️  neo4j package not installed. Run: pip install neo4j")
            return False
        except Exception as e:
            print(f"⚠️  Connection error: {e}")
            return False
    
    def save_configuration(self):
        """Save enterprise configuration to .env file"""
        print("\n" + "=" * 80)
        print("SAVING CONFIGURATION")
        print("=" * 80)
        
        env_file = self.workspace_root / ".env"
        env_enterprise_file = self.workspace_root / ".env.enterprise"
        
        # Create .env.enterprise with full config
        with open(env_enterprise_file, 'w') as f:
            f.write("# Enterprise Configuration for Medical RAG QA System\n")
            f.write("# Generated by enterprise_setup.py\n\n")
            
            # UMLS Configuration
            f.write("# UMLS Knowledge Graph\n")
            f.write(f"UMLS_ENABLED={str(self.config['umls'].get('enabled', False)).lower()}\n")
            if self.config['umls'].get('enabled'):
                f.write(f"UMLS_API_KEY={self.config['umls'].get('api_key', '')}\n")
                f.write(f"UMLS_VERSION={self.config['umls'].get('version', '2024AA')}\n")
                f.write(f"UMLS_SUBSET={self.config['umls'].get('subset', 'snomed_rxnorm')}\n")
                f.write(f"UMLS_DATA_PATH=data/enterprise/umls\n")
            else:
                f.write(f"UMLS_FALLBACK={self.config['umls'].get('fallback', 'disease_ontology')}\n")
            
            f.write("\n# PubMed Central Embeddings\n")
            f.write(f"PUBMED_ENABLED={str(self.config['pubmed'].get('enabled', False)).lower()}\n")
            if self.config['pubmed'].get('enabled'):
                f.write(f"PUBMED_MODE={self.config['pubmed'].get('mode', 'api')}\n")
                if self.config['pubmed']['mode'] == 'api':
                    f.write(f"PUBMED_EMAIL={self.config['pubmed'].get('email', '')}\n")
                    if 'api_key' in self.config['pubmed']:
                        f.write(f"PUBMED_API_KEY={self.config['pubmed']['api_key']}\n")
                else:
                    f.write(f"PUBMED_SUBSET={self.config['pubmed'].get('subset', 'top_journals')}\n")
                    f.write(f"PUBMED_EMBEDDINGS_PATH=data/enterprise/pubmed_embeddings\n")
            
            f.write("\n# Neo4j Database\n")
            f.write(f"NEO4J_ENABLED={str(self.config['neo4j'].get('enabled', False)).lower()}\n")
            if self.config['neo4j'].get('enabled'):
                f.write(f"NEO4J_URI={self.config['neo4j'].get('uri', 'bolt://localhost:7687')}\n")
                f.write(f"NEO4J_USERNAME={self.config['neo4j'].get('username', 'neo4j')}\n")
                f.write(f"NEO4J_PASSWORD={self.config['neo4j'].get('password', '')}\n")
                f.write(f"NEO4J_DATABASE={self.config['neo4j'].get('database', 'medical-kg')}\n")
            else:
                f.write(f"NEO4J_FALLBACK={self.config['neo4j'].get('fallback', 'networkx')}\n")
            
            f.write("\n# Vector Store\n")
            f.write("VECTOR_STORE=chromadb\n")
            f.write("EMBEDDING_MODEL=dmis-lab/biobert-base-cased-v1.2\n")
            
            f.write("\n# LLM Configuration\n")
            f.write("LLM_MODEL=microsoft/BioGPT-Large\n")
            f.write("LLM_MAX_TOKENS=512\n")
        
        print(f"✓ Configuration saved to: {env_enterprise_file}")
        
        # Update main .env if user confirms
        update_env = input("\nUpdate main .env file? (y/n) [y]: ").lower().strip() or 'y'
        
        if update_env == 'y':
            import shutil
            shutil.copy(env_enterprise_file, env_file)
            print(f"✓ Main .env updated")
        
        # Save JSON config for reference
        config_json = self.workspace_root / "config" / "enterprise_config.json"
        config_json.parent.mkdir(exist_ok=True)
        
        with open(config_json, 'w') as f:
            # Remove sensitive data for JSON
            safe_config = self.config.copy()
            if 'api_key' in safe_config.get('umls', {}):
                safe_config['umls']['api_key'] = '***HIDDEN***'
            if 'password' in safe_config.get('neo4j', {}):
                safe_config['neo4j']['password'] = '***HIDDEN***'
            
            json.dump(safe_config, f, indent=2)
        
        print(f"✓ Configuration reference saved to: {config_json}")
    
    def display_next_steps(self):
        """Display next steps after configuration"""
        print("\n" + "=" * 80)
        print("SETUP COMPLETE!")
        print("=" * 80)
        
        print("\n📋 Next Steps:\n")
        
        step = 1
        
        if self.config['umls'].get('enabled'):
            print(f"{step}. Download and extract UMLS data")
            print(f"   See: {self.data_dir / 'umls' / 'DOWNLOAD_INSTRUCTIONS.txt'}")
            step += 1
        
        if self.config['pubmed'].get('enabled') and self.config['pubmed'].get('mode') == 'prebuilt':
            print(f"{step}. Download PubMed embeddings")
            print(f"   See: {self.data_dir / 'pubmed_embeddings' / 'DOWNLOAD_INSTRUCTIONS.txt'}")
            step += 1
        
        print(f"{step}. Build vector store:")
        print(f"   python scripts/build_vector_store.py --enterprise")
        step += 1
        
        print(f"{step}. Build knowledge graph:")
        print(f"   python scripts/build_knowledge_graph.py --enterprise")
        step += 1
        
        print(f"{step}. Start the backend:")
        print(f"   python scripts/run.py")
        
        print("\n" + "=" * 80)
        print("📚 Documentation:")
        print("  - UMLS: https://www.nlm.nih.gov/research/umls/")
        print("  - PubMed API: https://www.ncbi.nlm.nih.gov/home/develop/api/")
        print("  - Neo4j: https://neo4j.com/docs/")
        print("=" * 80)
    
    def run(self):
        """Run the complete enterprise setup"""
        self.welcome()
        self.setup_umls()
        self.setup_pubmed()
        self.setup_neo4j()
        self.save_configuration()
        self.display_next_steps()


def main():
    """Main entry point"""
    setup = EnterpriseSetup()
    
    try:
        setup.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user.")
        print("   You can run this script again anytime to complete setup.")
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        raise


if __name__ == "__main__":
    main()
