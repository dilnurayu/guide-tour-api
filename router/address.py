from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Address
from db.schemas import AddressCreate, AddressOut
from db.get_db import get_async_session

router = APIRouter(prefix="/addresses", tags=["addresses"])

@router.get("/{address_id}", response_model=AddressOut)
async def get_address(
    address_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Address).where(Address.address_id == address_id)
    )
    address = result.scalar_one_or_none()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found.")
    return address

@router.get("/", response_model=list[AddressOut])
async def list_addresses(
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Address))
    addresses = result.scalars().all()
    return addresses