import random
from typing import List, Tuple, Optional

class MazeGenerator:
    def __init__(
        self, width: int=11, height: int=11, seed: Optional[int] = None
    ) -> None:

    self.width: int = width if width % 2 != 0 else width + 1
    self.height: int = height if height % 2 != 0 else height + 1
    if seed is not None
        random.seed(seed)