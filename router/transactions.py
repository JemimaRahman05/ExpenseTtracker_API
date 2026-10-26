from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Annotated, Optional, Literal
from datetime import date as date_type
from database import SessionLocal
from models import Transactions
from fastapi.responses import JSONResponse
from router.auth import get_current_user
from fastapi.encoders import jsonable_encoder

router = APIRouter(tags=['transactions'])

class Transaction(BaseModel):
    title : str = Field(min_length=1)
    amount : float = Field(gt=0)
    type : Literal['income', 'expense']
    category : str = Field(min_length=1)
    date : date_type = Field(default_factory=date_type.today)

class TransactionUpdate(BaseModel):
    title : Optional[str] = Field(default=None, min_length=1)
    amount : Optional[float] = Field(default=None, gt=0)
    type : Optional[Literal['income', 'expense']] = Field(default=None)
    category : Optional[str] = Field(default=None, min_length=1)
    date : Optional[date_type] = Field(default=None)

class TransactionResponse(BaseModel):
    id : int
    title : str
    amount : float
    type : str
    category : str
    date : date_type
    owner_id : int


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.post('/transactions')
def create_transaction(user: user_dependency, db : db_dependency, new_transaction : Transaction):

    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    transaction_model = Transactions(**new_transaction.model_dump(), owner_id = user.get('id'))
    db.add(transaction_model)
    db.commit()
    db.refresh(transaction_model)

    return JSONResponse(status_code=201, content={'message' : 'Transaction created successfully', 'transaction' : jsonable_encoder(transaction_model)})

@router.get('/transactions')
def read_transactions(user: user_dependency, db : db_dependency):

    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    return db.query(Transactions).filter(Transactions.owner_id == user.get('id')).all()

@router.get('/transactions/filter')
def filter_transactions(user: user_dependency, db : db_dependency,type : Optional[Literal['income', 'expense']] = Query(default=None),category : Optional[str] = Query(default=None),minimum_amount : Optional[float] = Query(default=None, ge=0),maximum_amount : Optional[float] = Query(default=None, ge=0)):

    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    if minimum_amount is not None and maximum_amount is not None and minimum_amount > maximum_amount:
        raise HTTPException(status_code=400, detail='minimum_amount cannot be greater than maximum_amount')

    query = db.query(Transactions).filter(Transactions.owner_id == user.get('id'))

    if type is not None:
        query = query.filter(Transactions.type == type)
    if category is not None:
        query = query.filter(Transactions.category.ilike(category))
    if minimum_amount is not None:
        query = query.filter(Transactions.amount >= minimum_amount)
    if maximum_amount is not None:
        query = query.filter(Transactions.amount <= maximum_amount)

    return query.all()


@router.get('/transactions/{transaction_id}')
def read_specific_transaction(user: user_dependency, db : db_dependency, transaction_id : int):

    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    specific_transaction = db.query(Transactions).filter(Transactions.owner_id == user.get('id')).filter(Transactions.id == transaction_id).first()
    if specific_transaction is not None:
        return specific_transaction
    else:
        raise HTTPException(status_code=404, detail='Transaction not found')


@router.put('/transactions/{transaction_id}')
def update_transaction(user: user_dependency, db : db_dependency, transaction_id : int, update_transaction : TransactionUpdate):

    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    transaction = db.query(Transactions).filter(Transactions.owner_id == user.get('id')).filter(Transactions.id == transaction_id).first()
    if transaction is None:
        raise HTTPException(status_code=404, detail='Transaction not found')

    update_data = update_transaction.model_dump(exclude_unset=True)

    for key,value in update_data.items():
        setattr(transaction,key,value)
    db.commit()
    db.refresh(transaction)
    return JSONResponse(status_code=200, content={'message' : 'Transaction updated successfully', 'transaction' : jsonable_encoder(transaction)})


@router.delete('/transactions/{transaction_id}')
def delete_transaction(user: user_dependency, db : db_dependency, transaction_id : int):

    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')

    transaction = db.query(Transactions).filter(Transactions.owner_id == user.get('id')).filter(Transactions.id == transaction_id).first()
    if transaction is None:
        raise HTTPException(status_code=404, detail='Transaction not found')

    db.query(Transactions).filter(Transactions.owner_id == user.get('id')).filter(Transactions.id == transaction_id).delete()
    db.commit()
    return JSONResponse(status_code=200, content={'message' : 'Transaction deleted successfully'})
