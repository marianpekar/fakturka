from datetime import datetime, timedelta
from re import sub, search

class Invoice:
    def __init__(self, template_path: str, solver: Solver):
        self.lines = self.__load(template_path, solver)

    def __load(self, template_path: str, solver: Solver):
        var_pattern = r"\$\{(.*?)\}"
        lines = []
        with open(template_path, 'r', encoding='utf-8') as file:
            for line in file:
                if search(var_pattern, line):
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

            return sub(expr_pattern, solve_and_replace, line)
        
        line = sub(var_pattern, replace, line)
        line = solve_add_days_to_date_expr(line)
        return line