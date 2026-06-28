from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

EMAIL = "23f3004298@ds.study.iitm.ac.in"


class InvoiceIn(BaseModel):
    text: str

class InvoiceOut(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


# ---------------- STRONG AMOUNT EXTRACTION ----------------
def extract_amount(text: str):

    # STEP 1: find all numbers
    numbers = [(m.group(), m.start()) for m in re.finditer(r"\d+(\.\d+)?", text)]

    if not numbers:
        return 0.0

    # STEP 2: look for keyword positions
    keywords = ["total", "amount", "due", "invoice", "payable"]

    keyword_positions = []
    lower_text = text.lower()

    for kw in keywords:
        idx = lower_text.find(kw)
        if idx != -1:
            keyword_positions.append(idx)

    # STEP 3: if keywords exist → pick closest number after them
    if keyword_positions:
        best_num = None
        best_dist = float("inf")

        for num, pos in numbers:
            for kp in keyword_positions:
                if pos >= kp:  # number appears after keyword
                    dist = pos - kp
                    if dist < best_dist:
                        best_dist = dist
                        best_num = num

        if best_num:
            return float(best_num)

    # STEP 4: fallback → last number (NOT first!)
    return float(numbers[-1][0])


# ---------------- OTHER FIELDS ----------------
def extract_vendor(text: str):
    m = re.search(r"([A-Z][A-Za-z0-9\-& ]+(Ltd|Inc|Industries|Corp|LLC)\.?)", text)
    return m.group(1) if m else "Unknown"


def extract_currency(text: str):
    m = re.search(r"\b(USD|EUR|GBP)\b", text.upper())
    return m.group(1) if m else "USD"


def extract_date(text: str):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    return m.group(1) if m else "2026-01-01"


@app.post("/extract", response_model=InvoiceOut)
def extract(payload: InvoiceIn):

    try:
        text = payload.text or ""

        return InvoiceOut(
            vendor=extract_vendor(text),
            amount=round(extract_amount(text), 2),
            currency=extract_currency(text),
            date=extract_date(text)
        )

    except Exception:
        raise HTTPException(status_code=422, detail="Invalid input")