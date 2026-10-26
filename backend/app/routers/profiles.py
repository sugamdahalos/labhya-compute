from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session as Session_DB, select
from app.db import get_session
from app.models import User, Host, Renter, GPU, Transaction, Wallet
from app.auth_utils import get_current_user
from app.routers.wallets import make_transaction_response

hosts_router = APIRouter(prefix="/api/hosts", tags=["Hosts"])
renters_router = APIRouter(prefix="/api/renters", tags=["Renters"])
transactions_router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

@hosts_router.get("/")
def get_current_host_profile(user: User = Depends(get_current_user), db: Session_DB = Depends(get_session)):
    stmt = select(Host).where(Host.user_id == user.id)
    host = db.exec(stmt).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host profile not found")
    
    wallet = host.get_wallet(db)
    return {
        "id": str(host.id),
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": "HOST"
        },
        "wallet": {
            "balance": str(wallet.balance)
        }
    }

@hosts_router.get("/{host_id}/gpus/")
def get_host_gpus(host_id: uuid.UUID, db: Session_DB = Depends(get_session)):
    stmt = select(GPU).where(GPU.host_id == host_id)
    gpus = db.exec(stmt).all()
    return {"results": gpus}

@renters_router.get("/")
def get_current_renter_profile(user: User = Depends(get_current_user), db: Session_DB = Depends(get_session)):
    stmt = select(Renter).where(Renter.user_id == user.id)
    renter = db.exec(stmt).first()
    if not renter:
        raise HTTPException(status_code=404, detail="Renter profile not found")
    
    wallet = renter.get_wallet(db)
    return {
        "id": str(renter.id),
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": "RENTER"
        },
        "wallet": {
            "balance": str(wallet.balance)
        }
    }

@transactions_router.get("/")
def get_user_transactions(user: User = Depends(get_current_user), db: Session_DB = Depends(get_session)):
    wallet = None
    stmt_renter = select(Renter).where(Renter.user_id == user.id)
    renter = db.exec(stmt_renter).first()
    if renter:
        wallet = renter.get_wallet(db)
    else:
        stmt_host = select(Host).where(Host.user_id == user.id)
        host = db.exec(stmt_host).first()
        if host:
            wallet = host.get_wallet(db)
            
    if not wallet:
        return {"results": []}
        
    stmt_txs = select(Transaction).where(Transaction.wallet_id == wallet.id).order_by(Transaction.created_at.desc())
    txs = db.exec(stmt_txs).all()
    return {"results": [make_transaction_response(tx, db) for tx in txs]}
