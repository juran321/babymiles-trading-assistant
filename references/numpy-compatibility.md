# NumPy Compatibility Fix for moomoo SDK

## Problem

moomoo SDK depends on pandas, which depends on numexpr. When NumPy 2.x is installed but numexpr was compiled against NumPy 1.x, importing moomoo crashes with:

```
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.4.4
```

## Solution

Upgrade pandas (which will pull in compatible numexpr):

```bash
pip install --upgrade pandas matplotlib --break-system-packages
```

If that fails, force reinstall:

```bash
pip install pandas --force-reinstall --break-system-packages
```

## Prevention

Always check imports before running analysis scripts:

```bash
PYTHONPATH=/usr/local/lib/python3.12/dist-packages python3 -c "from moomoo import OpenQuoteContext; print('OK')"
```

## Affected Scripts

- `scripts/analyze_stock.py`
- `scripts/quote/get_kline.py`
- Any script importing `moomoo` + `pandas`
