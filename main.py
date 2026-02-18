from sys import argv
from fpdf import FPDF
from qrplatba import QRPlatbaGenerator
from datetime import datetime, timedelta
import locale
import re
import os

class Invoice:
    def __init__(self, template_path: str, solver: Solver):
        self.lines = self.__load(template_path, solver)

    def __load(self, template_path: str, solver: Solver):
        var_pattern = r"\$\{(.*?)\}"
        lines = []
        with open(template_path, 'r', encoding='utf-8') as file:
            for line in file:
                if re.search(var_pattern, line):
                    line = solver.solve(var_pattern, line)
                lines.append(line)
        return lines

class Solver:
    def solve(self, var_pattern: str, line: str):
        now = datetime.now()
        replacements = {
            "RRRR": str(now.year),
            "MM": f"{now.month:02}",
            "DD": f"{now.day:02}"
        }

        def replace(match):
            content = match.group(1)
            for key, value in replacements.items():
                content = content.replace(key, value)
            return content
        
        def solve_add_days_to_date_expr(line: str):
            expr_pattern = r"(\d{2})\.(\d{2})\.(\d{4})\+(\d+)"

            def solve_and_replace(match):
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))
                add_days = int(match.group(4))

                base_date = datetime(year, month, day)
                new_date = base_date + timedelta(days=add_days)

                return new_date.strftime("%d.%m.%Y")

            return re.sub(expr_pattern, solve_and_replace, line)
        
        line = re.sub(var_pattern, replace, line)
        line = solve_add_days_to_date_expr(line)
        return line

class PdfGenerator:
    def generate(self, invoice):
        locale.setlocale(locale.LC_ALL, "cs_CZ.UTF-8")

        pdf = FPDF()
        pdf.add_page()
        pdf.add_font("DejaVu", "", "./fonts/dejavu-sans/ttf/DejaVuSans.ttf")
        pdf.add_font("DejaVu", "B", "./fonts/dejavu-sans/ttf/DejaVuSans-Bold.ttf")

        output_name = invoice.lines.pop().lstrip("=>").strip()

        # Title
        title = invoice.lines[0].rstrip('\n')
        pdf.set_font("DejaVu", "B", 20)
        pdf.set_text_color(64)
        pdf.cell(0, 15, title, align="R")
        pdf.set_text_color(0)
        pdf.set_line_width(1)
        pdf.set_draw_color(92)
        pdf.line(106, 10, 198, 10)
        pdf.ln(25)

        qr_pay_account = ""
        qr_pay_variable = ""
        qr_pay_due_date = ""
        
        # Header
        header_lines = invoice.lines[: invoice.lines.index("---\n")]
        supplier_line_idx = header_lines.index("DODAVATEL\n")
        customer_line_idx = header_lines.index("ODBĚRATEL\n")
        left_lines = header_lines[supplier_line_idx : customer_line_idx]
        right_lines = header_lines[customer_line_idx :]
        for i in range(max(len(left_lines), len(right_lines))):
            left = left_lines[i].rstrip('\n') if i < len(left_lines) else ""
            right = right_lines[i].rstrip('\n') if i < len(right_lines) else ""

            if i == 2:
               pdf.set_font("DejaVu", "B", 10)
            else:
               pdf.set_font("DejaVu", "", 10)
            
            if "=" in left:
                left_left, left_right = left.split("=", 1)

                if left_left.strip() == "Bankovní účet":
                    qr_pay_account = left_right.strip()
                elif left_left.strip() == "Variabilní symbol":
                    qr_pay_variable = left_right.strip()
                    
                pdf.cell(45, 6, left_left)
                pdf.cell(45, 6, left_right, align="R")
            else:
                pdf.cell(90, 6, left)

            pdf.cell(6, 6,"")

            if "=" in right:
                right_left, right_right = right.split("=", 1)

                if right_left.strip() == "Datum splatnosti":
                    qr_pay_due_date = right_right.strip()

                pdf.cell(45, 6, right_left)
                pdf.cell(45, 6, right_right, align="R")
            else:
                pdf.cell(90, 6, right)

            pdf.ln(6)

        # Items
        items_start_idx = invoice.lines.index("---\n")
        items_end_idx = invoice.lines.index("---\n", items_start_idx + 1)
        item_lines = invoice.lines[items_start_idx + 1 : items_end_idx]

        total = 0.0
        pdf.cell(185, 8, "CENA", align="R")
        pdf.set_line_width(0.25)
        pdf.set_draw_color(192)
        y = pdf.get_y() + 7
        pdf.line(10, y, 195, y)
        for line in item_lines:
            line = line.rstrip('\n')
            if "=" in line:
                item, amount_str = line.split("=", 1)
                item = item.strip()
                amount_str = amount_str.strip().replace(" ", "").replace(",", ".").replace("Kč", "")
                amount = float(amount_str)
                total += amount
                pdf.cell(125, 8, item)
                pdf.cell(60, 8, locale.format_string("%.2f Kč", amount, grouping=True), align="R")
                pdf.ln(8)
            else:
                pdf.cell(125, 8, line)
                pdf.ln(8)

        y = pdf.get_y()
        pdf.line(10, y - 7, 195, y - 7)

        pdf.set_line_width(0.6)
        pdf.set_draw_color(64)
        pdf.line(106, y + 5, 195, y + 5)

        pdf.ln(10)

        # Total
        pdf.set_font("DejaVu", "B", 16)
        pdf.cell(125, 6, "")
        pdf.set_text_color(64)
        pdf.cell(60, 6, locale.format_string("%.2f Kč", total, grouping=True), align="R")

        pdf.ln(5)

        generator = QRPlatbaGenerator(qr_pay_account, total, x_vs=qr_pay_variable, message=title, due_date=qr_pay_due_date)
        qr_pay_img = generator.make_image(box_size=20, border=4)
        qr_pay_img.save('qr.svg')
        pdf.image('qr.svg', w=40)
        os.remove('qr.svg')

        # Footer
        pdf.set_y(-25)
        pdf.set_font("DejaVu", "", 8)
        footer = invoice.lines[-1].rstrip('\n')
        pdf.cell(0, 5, footer)

        pdf.output(output_name)
        print(f"PDF generated: {output_name}")


if len(argv) < 2:
    print(f"Usage: {argv[0]} [template path]")
    exit(1)

invoice = Invoice(argv[1], Solver())
PdfGenerator().generate(invoice)