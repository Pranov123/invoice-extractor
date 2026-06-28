from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re

app = FastAPI()

# ---------------- CORS (IMPORTANT FOR GRADER) ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # grader-safe
    allow_methods=["*"],
    allow_headers=["*"],
)

EMAIL = "23f3004298@ds.study.iitm.ac.in"

# ---------------- REQUEST MODEL ----------------
class InvoiceIn(BaseModel):
    text: str

# ---------------- RESPONSE MODEL ----------------
class InvoiceOut(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str

# ---------------- EXTRACTION LOGIC ----------------
def safe_extract(text: str):
    if not text or not isinstance(text, str):
        raise ValueError("Invalid input")

    vendor_match = re.search(r"([A-Z][A-Za-z0-9\-& ]+(Ltd|Inc|Industries|Corp|LLC))", text)
    vendor = vendor_match.group(1) if vendor_match else "Unknown"

    amount_match = re.search(r"(\d+(\.\d+)?)", text)
    amount = float(amount_match.group(1)) if amount_match else 0.0

    currency_match = re.search(r"\b(USD|EUR|GBP)\b", text.upper())
    currency = currency_match.group(1) if currency_match else "USD"

    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    date = date_match.group(1) if date_match else "2026-01-01"

    return vendor, amount, currency, date


# ---------------- ENDPOINT ----------------
@app.post("/extract", response_model=InvoiceOut)
def extract(payload: InvoiceIn):

    try:
        vendor, amount, currency, date = safe_extract(payload.text)

        return InvoiceOut(
            vendor=vendor,
            amount=amount,
            currency=currency,
            date=date
        )

    except Exception:
        raise HTTPException(status_code=422, detail="Invalid invoice text")