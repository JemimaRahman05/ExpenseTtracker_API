from test.test_main import client, TestingSessionLocal
from fastapi import status
from models import Transactions
from datetime import date

def test_transaction():
    db=TestingSessionLocal()
    db.query(Transactions).filter(Transactions.id==99).delete()
    transaction=Transactions(
        id = 99,
        title = "Lunch",
        amount = 250.0,
        type = "expense",
        category = "Food",
        date = date(2026, 10, 1),
        owner_id = 1
    )
    db.add(transaction)
    db.commit()
    db.close()

def test_read_transactions():
    response=client.get('/transactions')
    assert response.status_code==status.HTTP_200_OK

def test_read_specific_transaction():
    response=client.get('/transactions/99')
    assert response.status_code==status.HTTP_200_OK

def test_create_transaction():
    request_data={
        "title": "Bus fare",
        "amount": 50,
        "type": "expense",
        "category": "Transport",
        "date": "2026-10-20"
    }
    response=client.post('/transactions',json=request_data)
    assert response.status_code==status.HTTP_201_CREATED

def test_update_transaction():
    request_data={
        "title": "Dinner"
    }
    response=client.put('/transactions/99',json=request_data)
    assert response.status_code==status.HTTP_200_OK

def test_delete_transaction():
    response=client.delete('/transactions/99')
    assert response.status_code==status.HTTP_200_OK
