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
    import re

    candidates = []

    keywords_positive = ["total", "due", "amount", "payable"]
    keywords_negative = ["invoice", "id", "ref", "no"]

    text_lower = text.lower()

    for match in re.finditer(r"\d+(\.\d+)?", text):
        num_str = match.group()
        pos = match.start()

        score = 0

        # ---- decimal bonus ----
        if "." in num_str:
            score += 5

        value = float(num_str)

        # ---- penalize large integers (VERY IMPORTANT) ----
        if "." not in num_str and value >= 1000:
            score -= 8

        # ---- keyword scoring (window-based) ----
        window = text_lower[max(0, pos-25): pos+25]

        for kw in keywords_positive:
            if kw in window:
                score += 10

        for kw in keywords_negative:
            if kw in window:
                score -= 10

        candidates.append((score, value))

    # pick highest score
    candidates.sort(reverse=True, key=lambda x: x[0])

    return candidates[0][1] if candidates else 0.0


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