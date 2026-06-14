import datetime
from pathlib import Path

class ProcessResult:
    def __init__(self):
        self.algorithm: str = ""
        self.startDateTime: datetime.datetime | None = None
        self.endDateTime: datetime.datetime | None = None
        self.heightPixels: int = -1
        self.widthPixels: int = -1
        self.numIterations: int = -1
        self.finalOutputPath: Path | None = None