from fastmcp import FastMCP
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

# Initialize the MCP server
mcp = FastMCP("Legal Research Snippets")

# Helper function to load/save data
def load_snippets():
    if os.path.exists('legal_snippets.json'):
        with open('legal_snippets.json', 'r') as f:
            return json.load(f)
    return {"snippets": [], "next_id": 1}

def save_snippets(data):
    with open('legal_snippets.json', 'w') as f:
        json.dump(data, f, indent=2)

@mcp.tool()
def create_snippet(
    citation: str, 
    key_language: str, 
    tags: List[str], 
    context: str = "",
    case_type: str = "civil"
) -> Dict:
    """Create a new legal research snippet with metadata"""
    data = load_snippets()
    
    snippet = {
        "id": data["next_id"],
        "citation": citation,
        "key_language": key_language,
        "tags": tags,
        "context": context,
        "case_type": case_type,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    data["snippets"].append(snippet)
    data["next_id"] += 1
    save_snippets(data)
    
    return {"status": "success", "snippet_id": snippet["id"], "message": f"Created snippet {snippet['id']} for {citation}"}

@mcp.tool()
def search_snippets(query: str = "", tags: Optional[List[str]] = None) -> List[Dict]:
    """Search snippets by text content or tags"""
    data = load_snippets()
    results = []
    
    for snippet in data["snippets"]:
        # Text search
        if query and (query.lower() in snippet["citation"].lower() or 
                     query.lower() in snippet["key_language"].lower() or
                     query.lower() in snippet.get("context", "").lower()):
            results.append(snippet)
        # Tag search
        elif tags and any(tag in snippet["tags"] for tag in tags):
            results.append(snippet)
        # Return all if no search criteria
        elif not query and not tags:
            results.append(snippet)
    
    return results

@mcp.tool()
def get_snippet(snippet_id: int) -> Optional[Dict]:
    """Retrieve a specific snippet by ID"""
    data = load_snippets()
    for snippet in data["snippets"]:
        if snippet["id"] == snippet_id:
            return snippet
    return None

@mcp.tool()
def update_snippet(
    snippet_id: int,
    citation: Optional[str] = None,
    key_language: Optional[str] = None,
    tags: Optional[List[str]] = None,
    context: Optional[str] = None,
    case_type: Optional[str] = None
) -> Dict:
    """Update an existing snippet"""
    data = load_snippets()
    
    for snippet in data["snippets"]:
        if snippet["id"] == snippet_id:
            if citation: snippet["citation"] = citation
            if key_language: snippet["key_language"] = key_language
            if tags: snippet["tags"] = tags
            if context: snippet["context"] = context
            if case_type: snippet["case_type"] = case_type
            snippet["updated_at"] = datetime.now().isoformat()
            
            save_snippets(data)
            return {"status": "success", "message": f"Updated snippet {snippet_id}"}
    
    return {"status": "error", "message": f"Snippet {snippet_id} not found"}

@mcp.tool()
def delete_snippet(snippet_id: int) -> Dict:
    """Delete a snippet by ID"""
    data = load_snippets()
    original_count = len(data["snippets"])
    data["snippets"] = [s for s in data["snippets"] if s["id"] != snippet_id]
    
    if len(data["snippets"]) < original_count:
        save_snippets(data)
        return {"status": "success", "message": f"Deleted snippet {snippet_id}"}
    
    return {"status": "error", "message": f"Snippet {snippet_id} not found"}

@mcp.tool()
def list_tags() -> List[str]:
    """Get all unique tags from the snippet collection"""
    data = load_snippets()
    all_tags = set()
    for snippet in data["snippets"]:
        all_tags.update(snippet.get("tags", []))
    return sorted(list(all_tags))

@mcp.tool()
def export_snippets(format: str = "json") -> str:
    """Export all snippets in specified format (json or text)"""
    data = load_snippets()
    
    if format == "text":
        result = []
        for snippet in data["snippets"]:
            result.append(f"Citation: {snippet['citation']}\n")
            result.append(f"Key Language: {snippet['key_language']}\n")
            result.append(f"Tags: {', '.join(snippet['tags'])}\n")
            if snippet.get('context'):
                result.append(f"Context: {snippet['context']}\n")
            result.append(f"Created: {snippet['created_at']}\n")
            result.append("-" * 50 + "\n")
        return "".join(result)
    else:
        return json.dumps(data["snippets"], indent=2)

@mcp.resource("schema://legal_snippets")
def get_schema() -> str:
    """Provide information about the snippet data structure"""
    return """Legal Snippets Schema:
    
    - id: Unique identifier
    - citation: Case citation (e.g., "Smith v. Jones, 123 F.3d 456 (2nd Cir. 2023)")
    - key_language: Important legal text from the case
    - tags: List of categorization tags (e.g., ["contract", "damages", "breach"])
    - context: Additional notes and surrounding context
    - case_type: Type of case (civil, criminal, administrative, constitutional)
    - created_at: ISO timestamp of creation
    - updated_at: ISO timestamp of last update
    """

if __name__ == "__main__":
    mcp.run()