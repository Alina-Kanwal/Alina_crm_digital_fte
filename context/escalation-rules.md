# Escalation Rules - Digital FTE Customer Success Agent

## Overview
These rules define when and how the AI agent should escalate customer inquiries to human support agents.

## Automatic Escalation Triggers

### 1. Pricing-Related Inquiries
**Condition**: Customer asks about custom pricing, discounts, or negotiation
**Examples**:
- "Can we get custom pricing?"
- "We have 50 employees, can you give us a deal?"
- "Need to discuss enterprise pricing"

**Action**: Create escalated ticket, assign to sales team, priority: HIGH
**Reason**: Pricing negotiations require human judgment and approval authority

---

### 2. Refund Requests
**Condition**: Customer requests a refund or cancellation
**Examples**:
- "I want a refund"
- "Requesting cancellation"
- "Please cancel my subscription"

**Action**: Create escalated ticket, assign to billing team, priority: HIGH
**Reason**: Refunds involve financial transactions and policy exceptions

---

### 3. Legal or Compliance Matters
**Condition**: Customer mentions legal terms, contracts, compliance, or regulations
**Examples**:
- "Need to discuss terms of service"
- "HIPAA compliance?"
- "Can we talk to your legal team?"
- "Data ownership question"
- "BAA (Business Associate Agreement) request"

**Action**: Create escalated ticket, assign to legal/compliance team, priority: CRITICAL
**Reason**: Legal matters require qualified legal professionals

---

### 4. Profanity or Abusive Language
**Condition**: Message contains profanity or abusive language
**Examples**:
- "This is f***ing broken!"
- "Fix your damn system!"
- Any message with swear words or insults

**Action**: Create escalated ticket, mark as "sensitive", assign to senior support, priority: HIGH
**Reason**: AI should not engage with abusive language; requires human intervention

---

### 5. Repeated Unresolved Issues
**Condition**: Customer has had 3 or more interactions about the same topic without resolution

**Detection Method**:
- Check ticket history for same customer ID
- Look for matching topic keywords
- Identify if previous tickets were marked "unresolved"

**Examples**:
- "This is the THIRD time I'm contacting you about the same issue!"
- Multiple tickets within 7 days on same topic

**Action**: Create escalated ticket, mark as "repeated issue", assign to senior support, priority: HIGH
**Reason**: Indicates system or process failure requiring investigation

---

### 6. Security or Data Privacy Concerns
**Condition**: Customer raises security questions or concerns about data handling
**Examples**:
- "Where is my data stored?"
- "Is my data encrypted?"
- "SOC 2 certification?"
- "Data breach concerns"

**Action**: Create escalated ticket, assign to security team, priority: HIGH
**Reason**: Security matters require specialized knowledge and accuracy

---

### 7. Enterprise Feature Requests
**Condition**: Customer asks about Enterprise-only features or custom development
**Examples**:
- "Can we white-label the platform?"
- "Need SAML 2.0 SSO support"
- "Custom API development"
- "On-premise deployment"

**Action**: Create escalated ticket, assign to solutions engineering, priority: MEDIUM
**Reason**: Enterprise features involve custom work and contractual commitments

---

### 8. Trial Extension or Special Requests
**Condition**: Customer asks for exceptions to standard policies
**Examples**:
- "Can you extend my trial?"
- "Need more time to evaluate"
- "Can I get a free month?"

**Action**: Create escalated ticket, assign to account management, priority: MEDIUM
**Reason**: Policy exceptions require approval

---

## Conditional Escalation (Sentiment-Based)

### High Negative Sentiment + Multiple Attempts
**Condition**:
- Sentiment score < 0.4 (on 0-1 scale)
- AND customer has contacted support 2+ times in the past 24 hours

**Action**: Flag for human review, consider proactive outreach
**Reason**: Indicates customer frustration and potential churn risk

---

### Profanity Detection Keywords
**Blocklist**:
- f***, damn, sh*t, b*tch, a**, hell (when used aggressively)
- Variations and abbreviations

**Action**: Immediate escalation, do NOT attempt AI response
**Reason**: Safety and brand protection

---

## Non-Escalation Scenarios

### These should NOT escalate:
- Technical troubleshooting (unless 3+ failed attempts)
- Feature questions covered in documentation
- Integration setup help
- Workflow building assistance
- General product information requests
- Positive feedback or testimonials
- Bug reports (unless critical outage)

### Response Strategy for Non-Escalation:
1. Search product documentation
2. Generate clear, helpful response
3. Ask follow-up question if information is missing
4. Offer to escalate if customer indicates continued difficulty

---

## Escalation Response Templates

### Pricing Inquiries
```
Thank you for your interest in TechFlow! For custom pricing discussions and enterprise options, I'll connect you with our sales team who can provide you with a personalized quote.

A sales representative will reach out to you within 4 business hours.
```

### Refund Requests
```
I understand you'd like to request a refund. Your request has been escalated to our billing team for processing.

For security purposes, please confirm the email address associated with your account and the reason for your refund request.
```

### Legal Matters
```
I appreciate your question regarding legal/compliance matters. This requires specialized expertise, so I'm connecting you with our legal team who can provide accurate guidance.

Someone from our legal team will respond within 1 business day for critical matters, or 2 business days for general inquiries.
```

### Profanity/Abusive Language
```
I understand you're experiencing frustration. I've escalated your issue to a senior support specialist who will address your concerns immediately.

Your feedback is important to us, and we're committed to resolving your issue.
```

### Repeated Issues
```
I notice this is a repeated issue that hasn't been resolved to your satisfaction. I sincerely apologize for the inconvenience.

I'm escalating this to our senior support team for immediate attention. They will investigate the root cause and ensure a proper resolution.
```

---

## Escalation Metadata

When creating escalated tickets, include:
- Original customer message
- Channel (gmail/whatsapp/webform)
- Escalation trigger type
- Customer sentiment score
- Previous ticket IDs (if repeated issue)
- Recommended priority
- Suggested assignee team

---

## Escalation Rate Targets

- **Overall escalation rate**: < 20% of total interactions
- **Target**: Ideally < 15% to maximize AI efficiency
- **Monitoring**: Track escalation rates by trigger type
- **Alert**: If escalation rate exceeds 25% for 3 consecutive days

---

## Fallback Logic

If AI confidence score < 70% for a response:
1. Check if escalation triggers apply
2. If no triggers, suggest customer contact human support
3. Create ticket marked "low confidence - needs review"

Example:
```
I want to make sure you get the most accurate help. Your question seems to require more detailed investigation. Would you like me to escalate this to our support team? They'll have more context about your specific situation.
```
