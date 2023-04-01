import dataclasses
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclasses.dataclass
class Image:
    path: Path
    size: int
    last_updated_at: datetime
    dimensions: (int, int)

    thumbnail: Optional[bytes]
    rank: int
