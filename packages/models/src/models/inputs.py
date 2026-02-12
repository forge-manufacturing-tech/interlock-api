from pydantic import BaseModel


class CurrencyAmount(BaseModel):
    amount: float
    currency_code: str = "USD"
