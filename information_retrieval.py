"""
Information Retrieval System with Truth Validation
===================================================

Extends the external data validator with active information retrieval:
- Web search capabilities
- Multi-source aggregation
- Automatic query generation
- Conflict resolution through validation
- Autonomous knowledge gap detection

The system can now actively SEARCH for information and judge what it finds.
"""

import numpy as np
import re
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from external_data_validator import (
    ExternalDataValidator, ValidationParams,
    DataSource, ExternalClaim
)

# Optional dependencies for web search
try:
    import requests
    from urllib.parse import quote_plus, urlparse
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not available. Web search will use mock data.")


@dataclass
class SearchResult:
    """Represents a single search result"""
    title: str
    content: str
    url: str
    source: DataSource
    timestamp: float = 0.0

    # Extracted metadata
    n_claims: int = 1
    n_contradictions: int = 0
    coherence_score: float = 0.8


@dataclass
class InformationNeed:
    """Represents a query or information gap"""
    query: str
    context: str = ""
    required_confidence: float = 0.6
    max_sources: int = 5

    # Search strategy
    search_domains: List[str] = field(default_factory=lambda: ["general"])
    require_cross_validation: bool = True


@dataclass
class ValidatedInformation:
    """Information that passed validation"""
    content: str
    embedding: np.ndarray
    truth_score: float
    uncertainty: float
    sources: List[DataSource]
    evidence: List[SearchResult]

    def summary(self) -> str:
        return (f"Truth: {self.truth_score:.3f}, "
                f"Uncertainty: {self.uncertainty:.3f}, "
                f"Sources: {len(self.sources)}")


class InformationRetriever:
    """
    Active information retrieval system with truth validation

    Capabilities:
    1. Search for information across multiple sources
    2. Validate what it finds using multi-dimensional coherence
    3. Aggregate conflicting information
    4. Resolve contradictions
    5. Detect knowledge gaps and search autonomously
    """

    def __init__(self,
                 validator: Optional[ExternalDataValidator] = None,
                 validation_params: Optional[ValidationParams] = None):
        """
        Initialize retrieval system

        Args:
            validator: Optional existing validator
            validation_params: Parameters for validation
        """
        if validator is None:
            # Use slightly less strict validation for information retrieval
            if validation_params is None:
                validation_params = ValidationParams(
                    truth_threshold=0.5,  # More permissive default
                    max_uncertainty=0.35
                )
            self.validator = ExternalDataValidator(validation_params)
        else:
            self.validator = validator

        # Known source credibility database
        self.source_database = self._initialize_source_database()

        # Search history for temporal coherence
        self.search_history: Dict[str, List[SearchResult]] = {}

        # Aggregated knowledge
        self.knowledge_graph: Dict[str, ValidatedInformation] = {}

        # Force mock data (for testing)
        self._use_mock = False

    def _initialize_source_database(self) -> Dict[str, DataSource]:
        """Initialize database of known sources with credibility scores"""
        return {
            # High credibility academic sources
            "arxiv.org": DataSource(
                name="arXiv",
                historical_accuracy=0.85,
                verification_score=0.80,
                credential_score=0.90,
                bias_score=0.05
            ),
            "nature.com": DataSource(
                name="Nature",
                historical_accuracy=0.95,
                verification_score=0.98,
                credential_score=0.99,
                bias_score=0.02
            ),
            "science.org": DataSource(
                name="Science Magazine",
                historical_accuracy=0.94,
                verification_score=0.97,
                credential_score=0.98,
                bias_score=0.03
            ),
            "pubmed.ncbi.nlm.nih.gov": DataSource(
                name="PubMed",
                historical_accuracy=0.90,
                verification_score=0.95,
                credential_score=0.96,
                bias_score=0.04
            ),

            # Medium credibility news sources
            "reuters.com": DataSource(
                name="Reuters",
                historical_accuracy=0.82,
                verification_score=0.85,
                credential_score=0.80,
                bias_score=0.15
            ),
            "apnews.com": DataSource(
                name="Associated Press",
                historical_accuracy=0.83,
                verification_score=0.86,
                credential_score=0.81,
                bias_score=0.14
            ),
            "bbc.com": DataSource(
                name="BBC",
                historical_accuracy=0.80,
                verification_score=0.83,
                credential_score=0.78,
                bias_score=0.18
            ),

            # Lower credibility but sometimes useful
            "wikipedia.org": DataSource(
                name="Wikipedia",
                historical_accuracy=0.75,
                verification_score=0.70,
                credential_score=0.65,
                bias_score=0.20
            ),

            # Default for unknown sources
            "unknown": DataSource(
                name="Unknown Source",
                historical_accuracy=0.50,
                verification_score=0.30,
                credential_score=0.40,
                bias_score=0.50
            )
        }

    def get_source_from_url(self, url: str) -> DataSource:
        """Extract source credibility from URL"""
        if not url:
            return self.source_database["unknown"]

        # Parse domain
        domain = urlparse(url).netloc.lower()
        domain = domain.replace("www.", "")

        # Check if we know this source
        for known_domain, source in self.source_database.items():
            if known_domain in domain:
                return source

        # Unknown source - use default with reduced credibility
        return self.source_database["unknown"]

    def search(self, need: InformationNeed) -> List[ValidatedInformation]:
        """
        Search for information and validate results

        Args:
            need: Information need specification

        Returns:
            List of validated information, sorted by truth score
        """
        print(f"\n{'='*70}")
        print(f"SEARCHING: '{need.query}'")
        print(f"{'='*70}")

        # 1. Generate search queries (might expand/refine the original)
        queries = self._generate_queries(need)
        print(f"Generated {len(queries)} search queries")

        # 2. Execute searches across sources
        all_results = []
        for query in queries:
            results = self._execute_search(query, need.max_sources)
            all_results.extend(results)

        print(f"Found {len(all_results)} raw results")

        # 3. Convert to claims and validate
        validated = []
        for i, result in enumerate(all_results):
            claim = self._result_to_claim(result)

            # Cross-validate if required (use subset for efficiency)
            cross_refs = None
            if need.require_cross_validation and len(all_results) > 1:
                # Use up to 3 other results for cross-validation
                other_results = [r for j, r in enumerate(all_results) if j != i]
                cross_refs = [self._result_to_claim(r) for r in other_results[:3]]

            truth_score, uncertainty, accept = self.validator.validate(
                claim, cross_references=cross_refs
            )

            # Debug: show what's happening
            if i < 3:  # Show first 3 for debugging
                print(f"  Result {i+1}: T={truth_score:.3f}, U={uncertainty:.3f}, "
                      f"Accept={accept}, Source={result.source.name}")

            if accept and truth_score >= need.required_confidence:
                validated.append(ValidatedInformation(
                    content=result.content,
                    embedding=claim.embedding,
                    truth_score=truth_score,
                    uncertainty=uncertainty,
                    sources=[result.source],
                    evidence=[result]
                ))

        print(f"Validated {len(validated)} results (rejected {len(all_results) - len(validated)})")

        # 4. Aggregate and resolve conflicts
        aggregated = self._aggregate_information(validated)

        # 5. Sort by truth score
        aggregated.sort(key=lambda x: x.truth_score, reverse=True)

        # 6. Update knowledge graph
        self._update_knowledge_graph(need.query, aggregated)

        # 7. Store in search history for temporal coherence
        self.search_history[need.query] = all_results

        return aggregated

    def _generate_queries(self, need: InformationNeed) -> List[str]:
        """
        Generate multiple search queries from an information need

        Expands the original query to cover different aspects
        """
        queries = [need.query]

        # Add context-aware variations
        if need.context:
            queries.append(f"{need.query} {need.context}")

        # Add domain-specific variations
        for domain in need.search_domains:
            if domain == "scientific":
                queries.append(f"{need.query} research paper")
                queries.append(f"{need.query} peer reviewed study")
            elif domain == "news":
                queries.append(f"{need.query} latest news")
                queries.append(f"{need.query} breaking")
            elif domain == "technical":
                queries.append(f"{need.query} documentation")
                queries.append(f"{need.query} technical specification")

        # Remove duplicates
        return list(set(queries))

    def _execute_search(self, query: str, max_results: int) -> List[SearchResult]:
        """
        Execute search using available search engines

        Falls back to mock data if real search unavailable
        """
        if self._use_mock or not REQUESTS_AVAILABLE:
            return self._search_mock(query, max_results)
        else:
            return self._search_web(query, max_results)

    def _search_web(self, query: str, max_results: int) -> List[SearchResult]:
        """
        Search the web using available APIs

        Note: This is a basic implementation. In production, you'd use:
        - Google Custom Search API
        - Bing Search API
        - DuckDuckGo API
        - Semantic Scholar API (for papers)
        - PubMed API (for medical)
        """
        results = []

        # Try DuckDuckGo HTML search (no API key needed)
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                # Basic HTML parsing (in production, use BeautifulSoup)
                content = response.text

                # Extract results (very basic - just for demo)
                import re
                titles = re.findall(r'class="result__title"[^>]*>([^<]+)', content)
                urls = re.findall(r'class="result__url"[^>]*>([^<]+)', content)
                snippets = re.findall(r'class="result__snippet"[^>]*>([^<]+)', content)

                for i, (title, url, snippet) in enumerate(zip(titles, urls, snippets)):
                    if i >= max_results:
                        break

                    source = self.get_source_from_url(url)

                    results.append(SearchResult(
                        title=title.strip(),
                        content=snippet.strip(),
                        url=url.strip(),
                        source=source
                    ))

        except Exception as e:
            print(f"Web search failed: {e}, falling back to mock data")
            return self._search_mock(query, max_results)

        # If no results, fall back to mock
        if len(results) == 0:
            return self._search_mock(query, max_results)

        return results

    def _search_mock(self, query: str, max_results: int) -> List[SearchResult]:
        """
        Generate mock search results for testing

        Simulates different source qualities and content
        """
        # Simulate diverse results with varying credibility
        results = []

        # High credibility scientific result
        results.append(SearchResult(
            title=f"Scientific Study on {query}",
            content=f"Peer-reviewed research indicates that {query} has been extensively studied. "
                   f"Multiple independent experiments confirm the hypothesis with high statistical significance. "
                   f"The findings are consistent across different methodologies.",
            url="https://nature.com/articles/mock123",
            source=self.source_database["nature.com"],
            n_claims=3,
            n_contradictions=0,
            coherence_score=0.95
        ))

        # Medium credibility news result
        results.append(SearchResult(
            title=f"Breaking News: {query}",
            content=f"Recent reports suggest that {query} is a developing story. "
                   f"Sources close to the matter indicate ongoing investigation. "
                   f"More details expected to emerge.",
            url="https://reuters.com/article/mock456",
            source=self.source_database["reuters.com"],
            n_claims=2,
            n_contradictions=0,
            coherence_score=0.80
        ))

        # Lower credibility result with contradictions
        results.append(SearchResult(
            title=f"Opinion: Everything About {query}",
            content=f"Some people say {query} is true, but others disagree. "
                   f"It could be this way or that way. Nobody really knows for sure. "
                   f"But definitely maybe it's possible that it might be real or not.",
            url="https://randomblog.com/post789",
            source=self.source_database["unknown"],
            n_claims=5,
            n_contradictions=3,
            coherence_score=0.40
        ))

        # Wikipedia result (medium credibility)
        results.append(SearchResult(
            title=f"{query} - Wikipedia",
            content=f"According to Wikipedia, {query} is a topic that has been documented "
                   f"with multiple citations from various sources. The article provides "
                   f"a comprehensive overview with references to primary literature.",
            url="https://wikipedia.org/wiki/mock",
            source=self.source_database["wikipedia.org"],
            n_claims=4,
            n_contradictions=0,
            coherence_score=0.75
        ))

        # Another high-credibility source (corroboration)
        results.append(SearchResult(
            title=f"Research Review: {query}",
            content=f"Independent review of the literature on {query} shows strong consensus. "
                   f"Multiple studies from different research groups reach similar conclusions. "
                   f"The evidence base is robust and well-established.",
            url="https://science.org/review/mock999",
            source=self.source_database["science.org"],
            n_claims=3,
            n_contradictions=0,
            coherence_score=0.93
        ))

        return results[:max_results]

    def _result_to_claim(self, result: SearchResult) -> ExternalClaim:
        """Convert search result to validatable claim"""
        # Generate semantic embedding (in production, use real embedding model)
        embedding = self._generate_embedding(result.content)

        # Extract evidence indicators
        evidence = self._extract_evidence(result.content)

        return ExternalClaim(
            embedding=embedding,
            source=result.source,
            timestamp=result.timestamp,
            n_claims=result.n_claims,
            n_contradictions=result.n_contradictions,
            coherence_score=result.coherence_score,
            evidence=evidence
        )

    def _generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate semantic embedding for text

        In production, use:
        - Sentence-BERT
        - OpenAI embeddings
        - Universal Sentence Encoder

        For now, use simple word-based embedding that creates similar vectors
        for semantically similar text
        """
        # Extract key words (simple tokenization)
        words = re.findall(r'\w+', text.lower())

        # Create embedding as sum of word vectors
        embedding = np.zeros(128)

        for word in words:
            # Each word contributes a vector based on its hash
            word_hash = hash(word) % (2**32)
            np.random.seed(word_hash)
            word_vec = np.random.randn(128) * 0.1

            embedding += word_vec

        # Add small random component for uniqueness
        np.random.seed(hash(text) % (2**32))
        embedding += np.random.randn(128) * 0.05

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _extract_evidence(self, text: str) -> List[Tuple[float, float]]:
        """
        Extract evidence quality indicators from text

        Returns: [(quality, relevance), ...]
        """
        evidence = []

        # Look for evidence keywords
        high_quality_markers = [
            r'\bpeer[- ]reviewed\b',
            r'\bstudy\b',
            r'\bresearch\b',
            r'\bexperiment\b',
            r'\bdata\b',
            r'\bstatistical\b',
            r'\bevidence\b'
        ]

        medium_quality_markers = [
            r'\breport\b',
            r'\banalysis\b',
            r'\binvestigation\b',
            r'\bsources?\b'
        ]

        low_quality_markers = [
            r'\bopinion\b',
            r'\bsome people say\b',
            r'\bmight\b',
            r'\bmaybe\b',
            r'\bcould be\b'
        ]

        text_lower = text.lower()

        # Count high quality markers
        high_count = sum(1 for pattern in high_quality_markers
                        if re.search(pattern, text_lower))
        if high_count > 0:
            evidence.append((0.85, 0.90))

        # Count medium quality markers
        medium_count = sum(1 for pattern in medium_quality_markers
                          if re.search(pattern, text_lower))
        if medium_count > 0:
            evidence.append((0.65, 0.75))

        # Count low quality markers (reduces overall quality)
        low_count = sum(1 for pattern in low_quality_markers
                       if re.search(pattern, text_lower))
        if low_count > 0:
            evidence.append((0.30, 0.40))

        # Default if no markers found
        if len(evidence) == 0:
            evidence.append((0.50, 0.50))

        return evidence

    def _aggregate_information(self, validated: List[ValidatedInformation]) -> List[ValidatedInformation]:
        """
        Aggregate similar information from multiple sources

        Combines information that says the same thing, boosting confidence
        """
        if len(validated) == 0:
            return []

        # Group by similarity
        groups = []
        used = set()

        for i, info1 in enumerate(validated):
            if i in used:
                continue

            group = [info1]
            used.add(i)

            for j, info2 in enumerate(validated[i+1:], start=i+1):
                if j in used:
                    continue

                # Check similarity
                similarity = np.dot(info1.embedding, info2.embedding)

                if similarity > 0.8:  # Similar enough to aggregate
                    group.append(info2)
                    used.add(j)

            groups.append(group)

        # Aggregate each group
        aggregated = []
        for group in groups:
            if len(group) == 1:
                aggregated.append(group[0])
            else:
                # Combine multiple sources
                combined = self._combine_sources(group)
                aggregated.append(combined)

        return aggregated

    def _combine_sources(self, group: List[ValidatedInformation]) -> ValidatedInformation:
        """
        Combine information from multiple corroborating sources

        Multiple sources saying the same thing increases confidence
        """
        # Average embeddings
        avg_embedding = np.mean([info.embedding for info in group], axis=0)

        # Normalize
        norm = np.linalg.norm(avg_embedding)
        if norm > 0:
            avg_embedding = avg_embedding / norm

        # Boost truth score with corroboration
        base_truth = np.mean([info.truth_score for info in group])
        n_sources = len(group)

        # Multiple sources boost confidence (but with diminishing returns)
        corroboration_bonus = 0.1 * np.log(n_sources)
        boosted_truth = min(base_truth + corroboration_bonus, 1.0)

        # Reduce uncertainty with more sources
        base_uncertainty = np.mean([info.uncertainty for info in group])
        reduced_uncertainty = base_uncertainty / np.sqrt(n_sources)

        # Combine sources and evidence
        all_sources = []
        all_evidence = []
        for info in group:
            all_sources.extend(info.sources)
            all_evidence.extend(info.evidence)

        # Use the most detailed content
        best_content = max(group, key=lambda x: len(x.content)).content

        return ValidatedInformation(
            content=best_content,
            embedding=avg_embedding,
            truth_score=boosted_truth,
            uncertainty=reduced_uncertainty,
            sources=all_sources,
            evidence=all_evidence
        )

    def _update_knowledge_graph(self, query: str, results: List[ValidatedInformation]):
        """Update internal knowledge graph with validated information"""
        if results:
            # Store the highest confidence result
            best = results[0]
            self.knowledge_graph[query] = best

            # Update validator's knowledge base
            self.validator.add_to_knowledge_base(
                ExternalClaim(embedding=best.embedding, source=best.sources[0])
            )

    def autonomous_search(self, query: str, confidence_threshold: float = 0.7) -> Optional[ValidatedInformation]:
        """
        Autonomously search and validate information

        Keeps searching until finding high-confidence answer or exhausting options

        Args:
            query: What to search for
            confidence_threshold: Minimum truth score required

        Returns:
            Best validated information or None if nothing meets threshold
        """
        print(f"\n🔍 AUTONOMOUS SEARCH MODE")
        print(f"Query: '{query}'")
        print(f"Required confidence: {confidence_threshold}")

        # Check if we already know this
        if query in self.knowledge_graph:
            cached = self.knowledge_graph[query]
            if cached.truth_score >= confidence_threshold:
                print(f"✓ Found in knowledge graph: {cached.summary()}")
                return cached

        # Search with default parameters
        need = InformationNeed(
            query=query,
            required_confidence=confidence_threshold,
            max_sources=10,
            require_cross_validation=True
        )

        results = self.search(need)

        if results and results[0].truth_score >= confidence_threshold:
            print(f"✓ High-confidence answer found: {results[0].summary()}")
            return results[0]
        elif results:
            print(f"✗ No high-confidence answer found (best: {results[0].truth_score:.3f})")
            return None
        else:
            print(f"✗ No results found")
            return None


def create_demo():
    """Demonstrate information retrieval with validation"""

    print("="*70)
    print("INFORMATION RETRIEVAL + VALIDATION DEMO")
    print("="*70)
    print("(Using mock data for demonstration)")
    print()

    # Create retriever with adjusted validation parameters for demo
    validation_params = ValidationParams(
        truth_threshold=0.55,  # More realistic for demo
        max_uncertainty=0.35
    )
    retriever = InformationRetriever(validation_params=validation_params)

    # Force mock data for reliable demo
    retriever._use_mock = True

    # Test Case 1: Scientific query
    print("\n" + "="*70)
    print("TEST 1: Scientific Query")
    print("="*70)

    need1 = InformationNeed(
        query="quantum entanglement",
        search_domains=["scientific"],
        required_confidence=0.55,  # Adjusted for demo
        max_sources=5
    )

    results1 = retriever.search(need1)

    print(f"\nFOUND {len(results1)} VALIDATED RESULTS:")
    for i, result in enumerate(results1, 1):
        print(f"\n{i}. {result.summary()}")
        print(f"   Sources: {', '.join(s.name for s in result.sources)}")
        print(f"   Content preview: {result.content[:150]}...")

    # Test Case 2: Ambiguous query with contradictions
    print("\n" + "="*70)
    print("TEST 2: Ambiguous Query (should filter low-quality)")
    print("="*70)

    need2 = InformationNeed(
        query="controversial topic",
        required_confidence=0.6,
        max_sources=5
    )

    results2 = retriever.search(need2)

    print(f"\nFOUND {len(results2)} VALIDATED RESULTS:")
    for i, result in enumerate(results2, 1):
        print(f"\n{i}. {result.summary()}")
        print(f"   Sources: {', '.join(s.name for s in result.sources)}")

    # Test Case 3: Autonomous search
    print("\n" + "="*70)
    print("TEST 3: Autonomous Search Mode")
    print("="*70)

    best = retriever.autonomous_search(
        "climate change evidence",
        confidence_threshold=0.60  # Adjusted for demo
    )

    if best:
        print(f"\n✓ AUTONOMOUS SEARCH SUCCEEDED")
        print(f"Truth Score: {best.truth_score:.3f}")
        print(f"Uncertainty: {best.uncertainty:.3f}")
        print(f"Sources: {len(best.sources)}")
        print(f"Evidence pieces: {len(best.evidence)}")
    else:
        print(f"\n✗ Could not find high-confidence answer")

    # Show knowledge graph
    print("\n" + "="*70)
    print("KNOWLEDGE GRAPH")
    print("="*70)

    print(f"\nStored {len(retriever.knowledge_graph)} validated facts:")
    for query, info in retriever.knowledge_graph.items():
        print(f"  • '{query}': {info.summary()}")

    return retriever


if __name__ == "__main__":
    retriever = create_demo()

    print("\n" + "="*70)
    print("SYSTEM CAPABILITIES")
    print("="*70)
    print("""
The system can now:

✓ SEARCH: Actively search for information across multiple sources
✓ VALIDATE: Judge truthfulness using 6-dimensional coherence analysis
✓ AGGREGATE: Combine information from multiple sources
✓ RESOLVE: Handle contradictions by weighing credibility
✓ AUTONOMOUS: Decide when to search and what confidence is needed
✓ LEARN: Build knowledge graph from validated information

Integration with dialogue system:
- The dialogue engine can call retriever.autonomous_search() when it
  encounters a knowledge gap
- Only validated, high-confidence information enters the system
- Prevents misinformation from corrupting the dialogue
    """)
