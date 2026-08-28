class DatasetEntry:
    def __init__(
        self,
        uid: int,
        pool: str,
        prompt: str,
        weight: int,
        sensitivity: str,
        enabled: bool = True,
        flags: str = "",
        approved: bool = True,
        rejected: bool = False,
        rejection_reason: str = "",
    ):
        self.uid = uid
        self.pool = pool
        self.prompt = prompt
        self.weight = weight
        self.sensitivity = sensitivity
        self.enabled = enabled
        self.flags = flags
        self.approved = approved
        self.rejected = rejected
        self.rejection_reason = rejection_reason


ERROR_MARIA_DB = -1
ERROR_ENTRY_EXISTS = -2
