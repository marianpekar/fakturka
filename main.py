from sys import argv
from invoice import Invoice, Solver
from pdf_generator import PdfGenerator

if len(argv) < 2:
    print(f"Usage: {argv[0]} [template path]")
    exit(1)

invoice = Invoice(argv[1], Solver())
PdfGenerator().generate(invoice)