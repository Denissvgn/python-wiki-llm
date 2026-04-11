from pydantic import BaseModel
from pathlib import Path

class WikiStorage(BaseModel):
    """Handles persistence of wiki pages."""
    base_path: Path
    
    def save_page(self, path: str, content: str):
        full_path = self.base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)
