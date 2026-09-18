class GWRException(Exception):
    code = "GWR_ERROR"
    def __init__(self, message: str, *, details=None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class NotFound(GWRException): code = "NOT_FOUND"
class ValidationError(GWRException): code = "VALIDATION_ERROR"
class AuthorityDenied(GWRException): code = "AUTHORITY_DENIED"
class ApprovalRequired(GWRException): code = "APPROVAL_REQUIRED"
class ApprovalMismatch(GWRException): code = "APPROVAL_MISMATCH"
class StaleVersion(GWRException): code = "STALE_VERSION"
class IdempotencyConflict(GWRException): code = "IDEMPOTENCY_CONFLICT"
class InvalidTransition(GWRException): code = "INVALID_TRANSITION"
class GateBlocked(GWRException): code = "GATE_BLOCKED"
class LoopGuardTriggered(GWRException): code = "LOOP_GUARD_TRIGGERED"
