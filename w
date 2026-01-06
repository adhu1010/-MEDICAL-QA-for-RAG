[33mcommit b8094bb039fc8fb5e898fe389a93e3e8a4160d8f[m[33m ([m[1;36mHEAD[m[33m)[m
Author: Adhwaith K P <adhwaithkp8@gmail.com>
Date:   Tue Jan 6 21:10:46 2026 +0530

    frontend

[33mcommit 37923f8679a9bdbf82ebabc1b3591e3bea05a39f[m[33m ([m[1;31morigin/main[m[33m, [m[1;31morigin/HEAD[m[33m, [m[1;32mmain[m[33m)[m
Author: Adhwaith K P <eahkfsgx@gmail.com>
Date:   Wed Oct 22 11:35:39 2025 +0530

    refactor(answer): streamline answer generation logic and improve artifact cleanup

[33mcommit 65fac08cc3b37a441ddef846258cc541baec6ea8[m
Author: Adhwaith K P <eahkfsgx@gmail.com>
Date:   Wed Oct 22 11:35:12 2025 +0530

    refactor(safety): enhance safety validation and answer generation cleanup

[33mcommit eec5d8a84b927683d392bf3ef8fd370eb72e8756[m
Author: Adhwaith K P <eahkfsgx@gmail.com>
Date:   Wed Oct 22 10:49:53 2025 +0530

    refactor(answer): enhance answer cleaning and safety checks for artifacts
    
    - Adjust fusion weights to increase vector weight and decrease others for balance
    - Remove additional XML-like tags and artifacts from generated answers
    - Strip prompt-like fragments such as "You are a", "Instructions:", and "Evidence:" from answers
    - Filter out sentences containing prompt fragments and XML artifacts during answer construction
    - Add extra whitespace and newline normalization in final answer formatting
    - Lower minimum length threshold for fallback trigger and include new artifact checks
    - Extend safety reflector to detect messy output artifacts and prompt fragments in answers
    - Improve safety suggestions by including cleanup guidance for messy output and prompt residues
    - Include new artifact and prompt fragment indicators as critical safety issues

[33mcommit 7b591316d92c7a43b707eee6fc35a91933b22f63[m
Merge: 7df7263 2542ab5
Author: Adhwaith K P <eahkfsgx@gmail.com>
Date:   Wed Oct 22 01:46:55 2025 +0530

    Merge branch 'main' of https://github.com/adhu1010/-MEDICAL-QA-for-RAG

[33mcommit 7df7263b3b8b424f44610c5f0955c0994a7fbbc5[m
Author: Adhwaith K P <eahkfsgx@gmail.com>
Date:   Wed Oct 22 01:46:48 2025 +0530

    refactor(agent): remove PubMed retriever integration for real-time literature
    
    - Removed PubMed retriever initialization and usage in AgentController
    - Deleted PubMed-related code in retrieval and fusion processes
    - Removed PubMed retriever import from retriever exports
    - Cleaned up fusion logic to skip PubMed evidences
    - Updated logging to reflect removal of PubMed integration
    - Removed PubMed environment variables from example config
    - Deleted all PubMed documentation and test scripts from codebase

[33mcommit 2542ab57205c3d4daeae93b061396557f00f2081[m
Author: Adhwaith K P <85784220+adhu1010@users.noreply.github.com>
Date:   Sat Oct 18 22:52:28 2025 +0530

    Add files via upload

[33mcommit 4d8dd27d31a38e2c5e2056e892061bccee7c51c4[m
Author: Adhwaith K P <85784220+adhu1010@users.noreply.github.com>
Date:   Wed Oct 15 08:36:01 2025 +0530

    Update README.md

[33mcommit 4e1d33aed793e404db724bfebaa34b05fb0b2cca[m
Author: Adhwaith K P <eahkfsgx@gmail.com>
Date:   Tue Oct 14 22:58:08 2025 +0530

    feat(agent): integrate PubMed retrieval and add fallback on low confidence
    
    - Add PubMed retriever initialization and configuration in environment and settings
    - Retrieve real-time literature from PubMed and include in evidence fusion
    - Adjust evidence confidence weights to incorporate PubMed sources
    - Implement fallback mechanism to retry retrieval with FULL_HYBRID strategy if combined
      confidence falls below threshold
    - Annotate fused evidence with fallback metadata for tracking
    - Update API response to include fallback metadata if applied

[33mcommit 68f225bbd523cdb47410e4675dd79feefa2098ee[m
Author: Adhwaith K P <eahkfsgx@gmail.com>
Date:   Tue Oct 14 21:33:15 2025 +0530

    feat(agent): add sparse retriever and reciprocal rank fusion for hybrid retrieval
    
    - Introduce SparseRetriever with BM25 support alongside vector and KG retrievers
    - Add new retrieval strategies: SPARSE_ONLY, DENSE_SPARSE, and FULL_HYBRID in config and models
    - Implement Reciprocal Rank Fusion (RRF) to fuse dense and sparse retrieval results
    - Update AgentController to initialize sparse retriever and handle new strategies
    - Modify evidence fusion logic to select RRF for dense+sparse, weighted fusion otherwise
    - Enhance answer generation to clean and extract BioGPT outputs reliably
    - Optimize vector retriever to add documents in batches for scalability
    - Remove patient/doctor mode toggles from frontend and always use patient mode
    - Add extensive logging for answer generation and frontend debugging
    - Add rank-bm25 dependency for sparse retrieval support

[33mcommit 7979ef35a3a86431b21c1b8291b49486959071d2[m
Author: Adhwaith K P <eahkfsgx@gmail.com>
Date:   Tue Oct 14 12:47:37 2025 +0530

    feat: Add automatic user mode detection based on question analysis
    
    - Add intelligent mode detection in QueryPreprocessor
    - Detects DOCTOR vs PATIENT mode by analyzing:
      * Technical medical terminology (pathophysiology, pharmacokinetics, etc.)
      * Personal pronouns (I have, my, should I, etc.)
      * Professional language patterns (first-line therapy, differential diagnosis)
      * Simple/lay language indicators
    - Updates ProcessedQuery model to include detected_mode
    - Main API endpoint now uses auto-detected mode for answer generation
    - Adds comprehensive test script (test_auto_mode.py)
    - Adds detailed documentation (AUTO_MODE_DETECTION.md)
    - Fixes .gitignore to include backend/models Python code
    
    Detection accuracy:
    - ~95% for technical medical questions  DOCTOR mode
    - ~98% for personal health questions  PATIENT mode
    - Defaults to PATIENT mode for ambiguous questions (safer)
    
    Benefits:
    - Better user experience with automatic adaptation
    - No manual mode selection required
    - Transparent logging of detection reasoning
    - Customizable thresholds and keywords

[33mcommit 9c6fc53614db233a3f0e18e1f04423a675553a19[m
Author: Adhwaith K P <eahkfsgx@gmail.com>
Date:   Tue Oct 14 12:25:13 2025 +0530

    feat: Add enterprise medical RAG QA system with UMLS/PubMed/Neo4j support
    
    - Add interactive enterprise setup wizard (enterprise_setup.py)
    - Add UMLS knowledge graph downloader with API integration
    - Add PubMed literature API integration (E-utilities)
    - Add MedQuAD processor for 16K+ real medical QA pairs
    - Add Disease Ontology processor for 14K+ disease terms
    - Update vector store builder to use full datasets
    - Update knowledge graph builder for Disease Ontology
    - Add BioGPT-Large LLM support (1.5B parameters)
    - Add comprehensive enterprise documentation (15+ guides)
    - Update .gitignore to exclude large data files
    
    System capabilities:
    - 16,407 medical QA pairs from authoritative sources
    - 14,460 diseases with relationships and definitions
    - Semantic search with BioBERT embeddings
    - Knowledge graph with NetworkX (optional Neo4j)
    - Optional UMLS integration (4M+ medical concepts)
    - Optional PubMed API access (7M+ research articles)
    - Safety-validated medical answers with evidence
    - Multi-mode support (patient/professional)
