# Research Findings: Digital Full-Time Employee (Digital FTE) – AI Customer Success Agent

## Decision: Natural Language Processing Approach
**Chosen**: OpenAI's GPT-4o model with custom function tools for intent recognition and entity extraction
**Rationale**: Provides state-of-the-art language understanding capabilities specifically tuned for complex customer service interactions. The function tools allow precise control over specialized capabilities like sentiment analysis and escalation triggering while leveraging GPT-4o's strong reasoning abilities.
**Alternatives considered**:
- spaCy with custom NER models (less capable for nuanced understanding)
- Hugging Face transformers (good but requires more infrastructure management)
- AWS Comprehend/Azure Cognitive Services (good but less flexible for custom logic)

## Decision: Knowledge Base Confidence Threshold
**Chosen**: For low-confidence answers (<70% confidence), the system should either search broader documentation sources or initiate escalation to human agents
**Rationale**: Balances the need to provide helpful responses with the risk of giving incorrect information. A 70% threshold ensures reasonably confident answers while providing a clear escalation path for uncertain cases.
**Alternatives considered**:
- 50% threshold (too risky for incorrect information)
- 80% threshold (might escalate too frequently, frustrating customers)
- Dynamic threshold based on query type (adds complexity without clear benefit)

## Decision: Escalation Criteria for Repeated Unresolved Queries
**Chosen**: Escalation triggers after 3 interactions on the same topic without resolution OR when customer expresses dissatisfaction in 2 consecutive interactions
**Rationale**: Combines quantitative (interaction count) and qualitative (customer sentiment) measures to catch both stubborn issues and frustrated customers early.
**Alternatives considered**:
- Fixed number of interactions only (misses frustrated customers who escalate quickly)
- Sentiment analysis only (might miss genuinely complex issues that take time to resolve)
- Time-based thresholds (doesn't account for issue complexity)

## Decision: Language Support Level
**Chosen**: Primary support for English with basic handling of top 5 most common languages (Spanish, French, German, Portuguese, Italian) for simple queries; complex queries in non-English languages should be escalated
**Rationale**: Covers the majority of likely customer bases while setting clear boundaries for the AI's capabilities. Simple queries in supported languages can be handled, but complex technical discussions should involve human agents who can navigate language nuances better.
**Alternatives considered**:
- English only (too restrictive for global SaaS)
- Full multilingual support (significantly increases complexity and cost)
- Language detection with full translation dependency (introduces latency and accuracy concerns)

## Decision: Customer Identification Mechanism
**Chosen**: Use email address as primary identifier, with phone number (for WhatsApp) and cookies/session IDs (for web form) as secondary identifiers, linked in the PostgreSQL database
**Rationale**: Provides a reliable, consistent way to identify customers across channels while respecting the different identifier types naturally available in each channel. The database linkage enables maintaining conversation history.
**Alternatives considered**:
- Unified customer ID system requiring upfront registration (creates friction for support)
- Device fingerprinting (privacy concerns and unreliable across browsers/devices)
- Channel-specific separate histories (doesn't meet cross-channel continuity requirement)