"""
Integration Example: Recursive Dialogue Engine + Information Retrieval

Demonstrates how the dialogue engine can autonomously search for and validate
external information when it encounters knowledge gaps.

The system:
1. Detects when it needs external information
2. Searches multiple sources
3. Validates what it finds using 6-dimensional coherence
4. Integrates only high-confidence information into dialogue
5. Rejects misinformation automatically
"""

import numpy as np
from typing import Optional, Callable
from information_retrieval import InformationRetriever, InformationNeed
from external_data_validator import ValidationParams

#Note: Full dialogue system integration would require dialogue_system.py
# This is a simplified demonstration

class IntelligentDialogueAgent:
    """
    Dialogue agent with autonomous information retrieval

    When the agent encounters a question it can't answer with high confidence,
    it automatically searches external sources and validates them.
    """

    def __init__(self,
                 confidence_threshold: float = 0.7,
                 validation_params: Optional[ValidationParams] = None):
        """
        Initialize intelligent dialogue agent

        Args:
            confidence_threshold: Minimum confidence to accept external info
            validation_params: Parameters for truth validation
        """
        # Information retrieval system
        self.retriever = InformationRetriever(validation_params=validation_params)

        # Confidence threshold
        self.confidence_threshold = confidence_threshold

        # Internal knowledge base (embeddings of known facts)
        self.internal_knowledge: dict = {}

        # Conversation history
        self.conversation_history = []

    def process_query(self, query: str) -> dict:
        """
        Process a user query with autonomous information retrieval

        Args:
            query: User's question or statement

        Returns:
            Response dict with content, confidence, sources
        """
        print(f"\n{'='*70}")
        print(f"USER QUERY: '{query}'")
        print(f"{'='*70}")

        # 1. Check internal knowledge first
        internal_answer = self._check_internal_knowledge(query)

        if internal_answer and internal_answer['confidence'] >= self.confidence_threshold:
            print(f"✓ Answering from internal knowledge (confidence: {internal_answer['confidence']:.3f})")
            response = internal_answer
        else:
            # 2. Need external information
            print(f"⚠ Internal knowledge insufficient, searching external sources...")

            # Autonomous search
            validated_info = self.retriever.autonomous_search(
                query,
                confidence_threshold=self.confidence_threshold
            )

            if validated_info:
                # Successfully found and validated external information
                response = {
                    'content': validated_info.content,
                    'confidence': validated_info.truth_score,
                    'uncertainty': validated_info.uncertainty,
                    'sources': [s.name for s in validated_info.sources],
                    'evidence_count': len(validated_info.evidence),
                    'type': 'external'
                }

                # Learn from validated information
                self._add_to_internal_knowledge(query, validated_info)

                print(f"✓ External information validated and integrated")
            else:
                # Could not find high-confidence answer
                response = {
                    'content': "I couldn't find reliable information about that with sufficient confidence.",
                    'confidence': 0.0,
                    'uncertainty': 1.0,
                    'sources': [],
                    'type': 'unknown'
                }
                print(f"✗ No high-confidence answer available")

        # 3. Log conversation
        self.conversation_history.append({
            'query': query,
            'response': response
        })

        return response

    def _check_internal_knowledge(self, query: str) -> Optional[dict]:
        """Check if we already know the answer"""
        query_lower = query.lower()

        # Check if query matches anything in knowledge base
        for known_query, info in self.internal_knowledge.items():
            if known_query.lower() in query_lower or query_lower in known_query.lower():
                return {
                    'content': info['content'],
                    'confidence': info['confidence'],
                    'uncertainty': info['uncertainty'],
                    'sources': info['sources'],
                    'type': 'internal'
                }

        # No match found
        return None

    def _add_to_internal_knowledge(self, query: str, validated_info):
        """Add validated information to internal knowledge base"""
        self.internal_knowledge[query] = {
            'content': validated_info.content,
            'confidence': validated_info.truth_score,
            'uncertainty': validated_info.uncertainty,
            'sources': [s.name for s in validated_info.sources]
        }

    def show_knowledge_base(self):
        """Display current knowledge base"""
        print(f"\n{'='*70}")
        print(f"KNOWLEDGE BASE: {len(self.internal_knowledge)} facts")
        print(f"{'='*70}")

        for query, info in self.internal_knowledge.items():
            print(f"\nQuery: '{query}'")
            print(f"  Confidence: {info['confidence']:.3f}")
            print(f"  Uncertainty: {info['uncertainty']:.3f}")
            print(f"  Sources: {', '.join(info['sources'])}")
            print(f"  Content: {info['content'][:100]}...")

    def show_conversation_history(self):
        """Display conversation history"""
        print(f"\n{'='*70}")
        print(f"CONVERSATION HISTORY: {len(self.conversation_history)} exchanges")
        print(f"{'='*70}")

        for i, exchange in enumerate(self.conversation_history, 1):
            print(f"\n{i}. Q: {exchange['query']}")
            resp = exchange['response']
            print(f"   A: (confidence: {resp['confidence']:.3f}) {resp['content'][:80]}...")
            if resp['sources']:
                print(f"   Sources: {', '.join(resp['sources'])}")


def demo_autonomous_dialogue():
    """Demonstrate autonomous information retrieval in dialogue"""

    print("="*70)
    print("AUTONOMOUS DIALOGUE WITH INFORMATION RETRIEVAL")
    print("="*70)
    print("\nAgent can autonomously search for and validate information")
    print("when needed, while rejecting unreliable sources.\n")

    # Create agent with mock data for demo
    validation_params = ValidationParams(
        truth_threshold=0.55,
        max_uncertainty=0.35
    )

    agent = IntelligentDialogueAgent(
        confidence_threshold=0.65,
        validation_params=validation_params
    )

    # Force mock data for demo
    agent.retriever._use_mock = True

    # Scenario 1: Question requiring external lookup
    response1 = agent.process_query("What is quantum entanglement?")
    print(f"\nRESPONSE:")
    print(f"  Content: {response1['content'][:150]}...")
    print(f"  Confidence: {response1['confidence']:.3f}")
    print(f"  Sources: {', '.join(response1['sources'])}")
    print(f"  Evidence: {response1.get('evidence_count', 0)} pieces")

    # Scenario 2: Same question again (should use internal knowledge)
    response2 = agent.process_query("Tell me about quantum entanglement")
    print(f"\nRESPONSE:")
    print(f"  Content: {response2['content'][:150]}...")
    print(f"  Confidence: {response2['confidence']:.3f}")
    print(f"  Type: {response2['type']} (cached from previous search)")

    # Scenario 3: Different question
    response3 = agent.process_query("What causes climate change?")
    print(f"\nRESPONSE:")
    print(f"  Content: {response3['content'][:150]}...")
    print(f"  Confidence: {response3['confidence']:.3f}")
    print(f"  Sources: {', '.join(response3['sources'])}")

    # Scenario 4: Unreliable information (should reject or warn)
    # In real scenario, this would trigger searches that return low-confidence results
    response4 = agent.process_query("Some obscure conspiracy theory")
    print(f"\nRESPONSE:")
    print(f"  Content: {response4['content']}")
    print(f"  Confidence: {response4['confidence']:.3f}")

    # Show what the agent learned
    agent.show_knowledge_base()

    # Show conversation history
    agent.show_conversation_history()

    return agent


def demo_dialogue_with_validation():
    """
    Demonstrate how validation prevents misinformation

    Shows the difference between accepting all information vs. validating it
    """

    print("\n" + "="*70)
    print("DEMONSTRATION: VALIDATION PREVENTS MISINFORMATION")
    print("="*70)

    # Simulate two systems: one that validates, one that doesn't
    print("\n--- System A: No Validation (accepts everything) ---")
    print("Query: 'Is the earth flat?'")
    print("Response: 'According to randomblog.com, the earth is flat.'")
    print("❌ PROBLEM: Misinformation accepted without scrutiny\n")

    print("--- System B: With Validation (our system) ---")
    print("Query: 'Is the earth flat?'")
    print("Searching...")
    print("  Found: randomblog.com (Truth: 0.25) - REJECTED")
    print("  Found: nasa.gov (Truth: 0.95) - ACCEPTED")
    print("  Found: wikipedia.org (Truth: 0.85) - ACCEPTED")
    print("Response: 'Multiple reliable sources confirm earth is spherical.'")
    print("✓ SUCCESS: Only validated, high-confidence information used\n")

    print("="*70)
    print("KEY INSIGHT")
    print("="*70)
    print("""
The validation framework provides automatic quality control:
- Low-credibility sources are filtered out
- Contradictory information is identified
- Multiple sources must corroborate
- Uncertainty is quantified
- Only high-confidence facts enter the system

This prevents the dialogue engine from being corrupted by misinformation.
    """)


def example_integration_code():
    """Show example code for integration"""

    print("="*70)
    print("INTEGRATION EXAMPLE CODE")
    print("="*70)
    print("""
# Integrate with existing recursive dialogue engine

from dialogue_system import RecursiveDialogueEngine, DialogueConfig
from information_retrieval import InformationRetriever
from external_data_validator import ValidationParams

# Create dialogue engine
dialogue_config = DialogueConfig(
    state_dims=256,
    vocab_size=1000,
    engine_optimization='fft'
)

dialogue_engine = RecursiveDialogueEngine(dialogue_config)

# Create retrieval system with validation
validation_params = ValidationParams(
    truth_threshold=0.7,  # High confidence required
    max_uncertainty=0.25   # Low uncertainty required
)

retriever = InformationRetriever(validation_params=validation_params)

# Define listener with autonomous lookup
def intelligent_listener(t, mu):
    # Detect if dialogue needs external information
    # (e.g., entropy stuck, low coherence, query detected)

    knowledge_gap_detected = detect_knowledge_gap(mu)

    if knowledge_gap_detected:
        # Formulate query from dialogue state
        query = extract_query_from_state(mu)

        # Autonomous search with validation
        validated_info = retriever.autonomous_search(
            query,
            confidence_threshold=0.7
        )

        if validated_info:
            # High-confidence information found
            # Convert to input signal for dialogue engine
            return validated_info.embedding
        else:
            # No reliable information available
            # Signal uncertainty to dialogue engine
            return None

    # Normal listener feedback
    return standard_listener_feedback(t, mu)

# Run dialogue with intelligent listener
emissions = dialogue_engine.converse(
    n_steps=1000,
    listener_callback=intelligent_listener,
    verbose=True
)

# Result: Dialogue that can autonomously research topics
# while maintaining truth validation
    """)


if __name__ == "__main__":
    # Run demonstrations
    agent = demo_autonomous_dialogue()

    demo_dialogue_with_validation()

    example_integration_code()

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("""
✓ Created: Dialogue agent with autonomous information retrieval
✓ Demonstrates: Automatic search when knowledge gaps detected
✓ Shows: Validation prevents misinformation from entering system
✓ Provides: Integration example for recursive dialogue engine

The system can now:
1. Detect when it needs external information
2. Search multiple sources autonomously
3. Validate findings using 6-dimensional coherence analysis
4. Integrate only high-confidence, validated information
5. Maintain internal knowledge base from validated facts
6. Reject unreliable sources automatically

This enables dialogue systems that can learn from the world
while maintaining truth as a core constraint.
    """)
