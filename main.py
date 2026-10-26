from fastapi import FastAPI
import models
from database import engine
from router import auth, transactions

app = FastAPI(title='Personal Expense Tracker API')

models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(transactions.router)


@app.get('/')
def root():
    return {'message': 'Expense Tracker API is running. Visit /docs'}
