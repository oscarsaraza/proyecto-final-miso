"""Router BFF del asegurado en la app móvil: su billetera de pólizas (HU-MOV-04)."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import require_roles
from app.modules.identity.service import InvalidTokenError, insured_auth_service
from app.modules.policy.models import InsuredPolicies
from app.modules.policy.service import policy_service

router = APIRouter(prefix="/insured", tags=["Asegurado"])

require_insured = require_roles(["insured"])


@router.get("/policies", response_model=InsuredPolicies)
async def my_policies(claims: Dict[str, Any] = Depends(require_insured), db: AsyncSession = Depends(get_db_session)):
    """Pólizas vigentes del titular del token; no recibe identificadores del cliente."""
    try:
        account = await insured_auth_service.account_for_access(db, claims)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión revocada o vencida.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    policies = await policy_service.active_for_holder(db, account.document_number, account.full_name)
    return InsuredPolicies(policies=policies)
