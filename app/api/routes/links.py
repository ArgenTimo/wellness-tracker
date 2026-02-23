"""Links routes - client/specialist invites and redeem."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser
from app.db.session import DbSession
from app.domain.schemas import (
    ClientInviteRequest,
    ClientInviteResponse,
    RedeemResponse,
    SpecialistInviteResponse,
)
from app.services.links_service import LinksService

router = APIRouter(prefix="/links", tags=["links"])


@router.post("/client-invite", response_model=ClientInviteResponse)
async def create_client_invite(
    current: CurrentUser,
    session: DbSession,
    body: ClientInviteRequest | None = None,
):
    """Create client invite. Returns token and URL. Multi-use by default."""
    single_use = (body and body.single_use) or False
    service = LinksService(session)
    token, url = await service.create_client_invite(current, single_use=single_use)
    return ClientInviteResponse(token=token, url=url)


@router.post("/specialist-invite", response_model=SpecialistInviteResponse)
async def create_specialist_invite(current: CurrentUser, session: DbSession):
    """Create specialist invite. Always single-use."""
    service = LinksService(session)
    token, url = await service.create_specialist_invite(current)
    return SpecialistInviteResponse(token=token, url=url)


@router.post("/redeem/{token}", response_model=RedeemResponse)
async def redeem_token(
    token: str,
    current: CurrentUser,
    session: DbSession,
):
    """
    Redeem invite token. Authenticated user is the redeemer.
    Returns status: linked | already_linked | ignored_self_redeem.
    """
    service = LinksService(session)
    try:
        status_result = await service.redeem_token(token, current)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return RedeemResponse(status=status_result)
