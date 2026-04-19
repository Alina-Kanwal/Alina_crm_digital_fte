"""
Model Context Protocol (MCP) Server for Digital FTE CRM.
Exposes CRM tools and resources to external AI models (like Claude or other Digital FTEs).
"""
import logging
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from src.database.connection import get_db
from src.models.customer import Customer
from src.models.support_ticket import SupportTicket
from src.models.conversation_thread import ConversationThread

# Configure logging
logger = logging.getLogger(__name__)

# Initialize FastAPI app for MCP
app = FastAPI(
    title="Digital FTE CRM MCP Server",
    description="Model Context Protocol server for secure CRM data access",
    version="1.0.0"
)

# --- MCP Protocol Schemas ---

class MCPResource(BaseModel):
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None

class MCPTool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]

class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any]

# --- Tool Implementations ---

@app.get("/tools")
async def list_tools() -> List[MCPTool]:
    """List available CRM tools for the MCP server."""
    return [
        MCPTool(
            name="get_customer_profile",
            description="Retrieve a complete customer profile by email or phone",
            input_schema={
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "phone": {"type": "string"}
                }
            }
        ),
        MCPTool(
            name="get_recent_tickets",
            description="List the most recent support tickets for a customer",
            input_schema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["customer_id"]
            }
        ),
        MCPTool(
            name="search_conversations",
            description="Search conversation history across all channels for a keyword",
            input_schema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "query": {"type": "string"}
                },
                "required": ["customer_id", "query"]
            }
        )
    ]

@app.post("/tools/get_customer_profile")
async def get_customer_profile(params: Dict[str, str], db: Session = Depends(get_db)):
    """MCP Tool: Retrieve customer profile."""
    email = params.get("email")
    phone = params.get("phone")
    
    if not email and not phone:
        raise HTTPException(status_code=400, detail="Missing email or phone")
    
    query = db.query(Customer)
    if email:
        query = query.filter(Customer.email == email)
    elif phone:
        query = query.filter(Customer.phone == phone)
        
    customer = query.first()
    if not customer:
        return {"error": "Customer not found"}
        
    return customer.to_dict()

@app.post("/tools/get_recent_tickets")
async def get_recent_tickets(params: Dict[str, Any], db: Session = Depends(get_db)):
    """MCP Tool: List recent tickets."""
    customer_id = params.get("customer_id")
    limit = params.get("limit", 5)
    
    tickets = db.query(SupportTicket).filter(
        SupportTicket.customer_id == customer_id
    ).order_by(SupportTicket.created_at.desc()).limit(limit).all()
    
    return [t.to_dict() for t in tickets]

@app.get("/resources")
async def list_resources() -> List[MCPResource]:
    """List available CRM resources (e.g., active thread logs)."""
    return [
        MCPResource(
            uri="crm://customers/active",
            name="Active Customers",
            description="Listing of customers with active conversations in the last 24h",
            mime_type="application/json"
        )
    ]

@app.get("/")
async def mcp_root():
    """MCP Server details."""
    return {
        "mcp_server": "digital-fte-crm",
        "protocol_version": "1.0",
        "capabilities": ["tools", "resources"]
    }

# Entry point for running the server
if __name__ == "__main__":
    import uvicorn
    # MCP servers usually run on a specific port or via stdio
    # For this implementation, we'll use a standard HTTP port
    uvicorn.run(app, host="0.0.0.0", port=8001)
