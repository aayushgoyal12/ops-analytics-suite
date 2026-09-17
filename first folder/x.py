import json
from pypdf import PdfReader


def verify_voucher(data):
    subtotal = float(data.get("subtotal", 0.0))
    tax = float(data.get("tax_amount", 0.0))
    total = float(data.get("total_amount", 0.0))
    items = data.get("items", [])

    items_sum = sum(float(item["amount"]) for item in items)

    # Verification Math
    items_valid = round(items_sum, 2) == round(subtotal, 2)
    total_valid = round(subtotal + tax, 2) == round(total, 2)

    status = "Verified" if (items_valid and total_valid) else "Flagged"
    flags = []

    if not items_valid:
        flags.append(f"Line items sum ({items_sum}) != Subtotal ({subtotal})")
    if not total_valid:
        flags.append(f"Subtotal + Tax ({subtotal + tax}) != Total ({total})")

    return {"status": status, "flags": flags}


# --- READ FROM REAL PDF ---
print("Reading sample1.pdf...")
reader = PdfReader("sample2.pdf")
pdf_text = ""
for page in reader.pages:
    pdf_text += page.extract_text()

print("\n--- Raw Extracted PDF Text ---")
print(pdf_text)

# Structured JSON mapped directly from sample1.pdf
sample_json = {
    "subtotal": 800.00,
    "tax_amount": 36.00,
    "total_amount": 756.00,
    "items": [
        {"amount": 280.00},
        {"amount": 120.00},
        {"amount": 220.00},
        {"amount": 100.00},
    ],
}

# Run Verification
print("\n--- Running Verification Logic ---")
result = verify_voucher(sample_json)
print(result)