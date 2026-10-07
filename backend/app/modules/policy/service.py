"""Servicio de emisión contractual y outbox transaccional (Placeholder para HU-WEB-05)."""
from app.modules.policy.models import PolicyIssueRequest, PolicyRecord


class PolicyService:
    def issue_policy(self, request: PolicyIssueRequest) -> PolicyRecord:
        """Emite póliza de forma atómica y genera evento outbox (HU-WEB-05 / TC-S1-07).

        A ser implementado durante HU-WEB-05.
        """
        raise NotImplementedError("issue_policy pendiente de implementación en HU-WEB-05")


policy_service = PolicyService()
