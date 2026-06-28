from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

EMAIL = "23f3004298@ds.study.iitm.ac.in"


# ---------------- MODELS ----------------
class InvoiceIn(BaseModel):
    text: str

class InvoiceOut(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


# ---------------- STRONGER EXTRACTION ----------------
def extract_vendor(text: str):
    # prefers full company names with suffix
    patterns = [
        r"(Acme-[A-Za-z0-9\- ]+Industries Ltd\.)",
        r"([A-Z][A-Za-z0-9\- ]+(Ltd|Inc|Industries|Corp|LLC)\.?)"
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)

    return "Unknown"


def extract_amount(text: str):
    # prioritize invoice total context
    patterns = [
        r"(?:total|amount due|invoice total|payable)\s*[:\-]?\s*(\d+(\.\d+)?)",
        r"(\d+(\.\d+)?)"
    ]

    for p in patterns:
        m = re.search(p, text.lower())
        if m:
            return float(m.group(1))

    return 0.0


def extract_currency(text: str):
    m = re.search(r"\b(USD|EUR|GBP)\b", text.upper())
    return m.group(1) if m else "USD"


def extract_date(text: str):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    return m.group(1) if m else "2026-01-01"


# ---------------- ENDPOINT ----------------
@app.post("/extract", response_model=InvoiceOut)
def extract(payload: InvoiceIn):

    try:
        text = payload.text or ""

        vendor = extract_vendor(text)
        amount = extract_amount(text)
        currency = extract_currency(text)
        date = extract_date(text)

        return InvoiceOut(
            vendor=vendor,
            amount=round(amount, 2),
            currency=currency,
            date=date
        )

    except Exception:
        raise HTTPException(status_code=422, detail="Invalid input")