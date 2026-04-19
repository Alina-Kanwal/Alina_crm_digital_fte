"""
Customer identification service.
Handles customer identification across channels using identifiers
(email, phone) and semantic similarity using pgvector embeddings.
Enables cross-channel context by accurately linking messages from different apps.
"""
import logging
from typing import Dict, Optional, Any, List, Tuple
from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.models.customer import Customer
from src.utils.embeddings import generate_embedding, cosine_similarity
import numpy as np
import uuid
import re

logger = logging.getLogger(__name__)

# Minimum similarity threshold to consider two customer interactions as the same user
# 0.95+ is required to meet the 97%+ accuracy target for complex cross-channel identification
SIMILARITY_THRESHOLD = 0.95


class CustomerIdentifierService:
    """Service to identify customers across multiple channels."""

    def __init__(self, threshold: float = SIMILARITY_THRESHOLD):
        """
        Initialize the customer identifier service.

        Args:
            threshold: Similarity threshold for pgvector matching
        """
        self.threshold = threshold
        logger.info(f"Customer identification service initialized (threshold={threshold})")

    async def identify_customer(self, 
                                normalized_message: Dict[str, Any], 
                                correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Identify existing customer or create a new one based on normalized message.

        Matches by:
        1. Explicit identifiers (email, phone number)
        2. pgvector similarity matching (>95% threshold)

        Args:
            normalized_message: Parsed and normalized message from channel
            correlation_id: (Optional) Trace ID

        Returns:
            Customer information dictionary
        """
        tag = f"[{correlation_id}] " if correlation_id else ""
        logger.debug(f"{tag}Identifying customer for current message")

        # Extract identifiers from normalized message
        email = normalized_message.get('sender', '').lower() if '@' in normalized_message.get('sender', '') else None
        phone = normalized_message.get('sender', '').strip() if self._looks_like_phone_number(normalized_message.get('sender', '')) else None
        name = normalized_message.get('metadata', {}).get('name', '')
        if not phone and 'whatsapp' in normalized_message.get('sender', '').lower():
            phone_match = re.search(r'\+?\d+', normalized_message.get('sender', ''))
            if phone_match:
                phone = phone_match.group(0).strip()

        db = SessionLocal()
        try:
            # 1. Direct identifier matching (Priority: Email, then Phone)
            if email:
                customer = db.query(Customer).filter(Customer.email == email).first()
                if customer:
                    logger.info(f"{tag}Customer identified by email matching: {email} (ID: {customer.id})")
                    return customer.to_dict()

            if phone:
                customer = db.query(Customer).filter(Customer.phone == phone).first()
                if customer:
                    logger.info(f"{tag}Customer identified by phone matching: {phone} (ID: {customer.id})")
                    # Update email if we found one in this message
                    if email and not customer.email:
                        customer.email = email
                        logger.info(f"{tag}Updating customer {customer.id} email with: {email}")
                        db.commit()
                    return customer.to_dict()

            # 2. Semantic similarity matching using pgvector (Fallback)
            # This handles cases where people switch channels or names without previous direct link
            logger.debug(f"{tag}No direct identifier match found, trying semantic similarity")
            
            # Create a profile string for current customer interaction
            profile_text = f"Email: {email or 'Unknown'} | Phone: {phone or 'Unknown'} | Name: {name or 'Unknown'}"
            current_embedding = await generate_embedding(profile_text)

            if current_embedding:
                # High-performance search using native pgvector <=> operator (cosine distance)
                # 1 - distance = similarity. We find the top match above the threshold.
                from src.utils.embeddings import embedding_to_vector_str
                vector_str = embedding_to_vector_str(current_embedding)
                
                from sqlalchemy import text
                stmt = text(f"""
                    SELECT id, email, phone, (1 - (embedding <=> :query_vec)) as similarity
                    FROM customers
                    WHERE embedding IS NOT NULL
                    AND (1 - (embedding <=> :query_vec)) >= :threshold
                    ORDER BY similarity DESC
                    LIMIT 1
                """)
                
                result = db.execute(stmt, {
                    "query_vec": vector_str,
                    "threshold": self.threshold
                }).first()

                if result:
                    customer_id, match_email, match_phone, score = result
                    logger.info(f"{tag}Customer identified by high-perf semantic similarity ({score:.4f}): {customer_id}")
                    
                    # Fetch the full object to update if needed
                    best_match = db.query(Customer).get(customer_id)
                    if best_match:
                        # Update record with new identifiers if available
                        updated = False
                        if email and not best_match.email:
                            best_match.email = email; updated = True
                        if phone and not best_match.phone:
                            best_match.phone = phone; updated = True
                        if updated:
                            db.commit()
                        return best_match.to_dict()

            # 3. Create new customer record if no match
            logger.info(f"{tag}No previous customer found, creating new record")
            new_customer = Customer(
                email=email or f"anonymous-{uuid.uuid4().hex[:8]}@temporary.com",
                phone=phone,
                first_name=name.split(' ')[0] if name else None,
                last_name=' '.join(name.split(' ')[1:]) if name and ' ' in name else None,
                embedding=current_embedding,
                is_active=True
            )
            db.add(new_customer)
            db.commit()
            db.refresh(new_customer)

            logger.info(f"{tag}Successfully created new customer with ID: {new_customer.id}")
            return new_customer.to_dict()

        except Exception as e:
            logger.error(f"{tag}Error during customer identification: {e}", exc_info=True)
            db.rollback()
            # Return basic anonymous record as absolute fallback
            return {
                "id": str(uuid.uuid4()),
                "email": "error-fallback@temporary.com",
                "is_fallback": True,
                "error": str(e)
            }
        finally:
            db.close()

    def _looks_like_phone_number(self, text: str) -> bool:
        """Check if text looks like a phone number."""
        if not text:
            return False
        
        # Strip common formatting
        cleaned = text.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        # Handle whatsapp prefix if present
        if 'whatsapp' in cleaned.lower():
            cleaned = cleaned.lower().replace('whatsapp:', '')
        
        # Should be mostly digits and reasonable length
        return cleaned.isdigit() and 7 <= len(cleaned) <= 15