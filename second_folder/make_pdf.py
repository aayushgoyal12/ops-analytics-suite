import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

# Create sample pdf with tabular data
pdf_path = "second_folder/sample_test.pdf"
doc = SimpleDocTemplate(pdf_path, pagesize=letter)
elements = []

data = [
    ["Category", "Description", "Amount"],
    ["Audit Fee", "Statutory Audit", "25000"],
    ["Taxation", "ITR Filing", "12000"],
    ["GST", "Reconciliation", "18000"]
]

t = Table(data)
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.grey),
    ('GRID', (0,0), (-1,-1), 1, colors.black)
]))

elements.append(t)
doc.build(elements)
print("Test PDF Created Successfully!")