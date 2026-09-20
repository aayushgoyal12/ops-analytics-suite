from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_sample_invoice(filename="sample_invoice.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    
    # Header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(200, 750, "TAX INVOICE")
    
    # Vendor Details
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 700, "Vendor Name: Acme Solutions Pvt Ltd")
    c.setFont("Helvetica", 10)
    c.drawString(50, 685, "GSTIN: 07AAAAA0000A1Z5")
    c.drawString(50, 670, "Date: 2026-09-20")
    c.drawString(50, 655, "Invoice No: INV-2026-001")
    
    # Divider
    c.line(50, 640, 550, 640)
    
    # Item Details
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 610, "Description")
    c.drawString(300, 610, "Qty")
    c.drawString(400, 610, "Amount (INR)")
    
    c.setFont("Helvetica", 10)
    c.drawString(50, 585, "Software Consulting Services")
    c.drawString(300, 585, "1")
    c.drawString(400, 585, "10,000.00")
    
    # Divider
    c.line(50, 560, 550, 560)
    
    # Totals
    c.setFont("Helvetica", 10)
    c.drawString(300, 530, "Taxable Value:")
    c.drawString(450, 530, "10,000.00")
    
    c.drawString(300, 510, "GST (18%):")
    c.drawString(450, 510, "1,800.00")
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(300, 485, "Total Amount:")
    c.drawString(450, 485, "11,800.00")
    
    c.save()
    print(f"File saved as {filename}")

if __name__ == "__main__":
    create_sample_invoice()