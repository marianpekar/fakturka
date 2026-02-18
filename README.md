# Fakturka

A Python script that generates a Czech invoice in PDF based on a plain text template, where `RRRR`, `MM`, and `DD` strings inside `${` and `}` tags are replaced with the current year, month, and day, respectively. An expression like `${DD.MM.RRRR+14}` is solved as you'd expect, 14 days are added to the current day. The script also sums the prices of items and generates a QR pay code.

Compare the example input `./templates/example.txt` with the example output `example_202602.pdf`

## Example usage

```
python main.py ./templates/example.txt
```