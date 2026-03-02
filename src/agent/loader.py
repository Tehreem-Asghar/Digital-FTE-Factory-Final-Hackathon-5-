import json
from pathlib import Path
from typing import Dict, List, Any

class ContextLoader:
    """Loads and parses the SaaSFlow development dossier context files."""
    
    def __init__(self, context_dir: str = "context"):
        self.context_path = Path(context_dir)
        if not self.context_path.exists():
            raise FileNotFoundError(f"Context directory not found at {context_dir}")

    def load_markdown(self, filename: str) -> str:
        """Reads a markdown file from the context directory."""
        file_path = self.context_path / filename
        if not file_path.exists():
            return ""
        return file_path.read_text(encoding="utf-8")

    def load_tickets(self) -> List[Dict[str, Any]]:
        """Parses the sample-tickets.json file."""
        file_path = self.context_path / "sample-tickets.json"
        if not file_path.exists():
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_all_context(self) -> Dict[str, Any]:
        """Returns a dictionary containing all loaded context data."""
        return {
            "company_profile": self.load_markdown("company-profile.md"),
            "product_docs": self.load_markdown("product-docs.md"),
            "escalation_rules": self.load_markdown("escalation-rules.md"),
            "brand_voice": self.load_markdown("brand-voice.md"),
            "sample_tickets": self.load_tickets()
        }

if __name__ == "__main__":
    loader = ContextLoader()
    context = loader.get_all_context()
    print(f"Loaded {len(context['sample_tickets'])} tickets.")
    print(f"Company Profile Preview: {context['company_profile'][:50]}...")
