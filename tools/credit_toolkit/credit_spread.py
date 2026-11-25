"""Automation #1 - document gathering & financial spreading (diagram steps R1 -> R3).

Pulls XBRL financials from SEC EDGAR and writes a credit spread workbook:
  * Summary sheet - latest-period credit metrics for every issuer
  * One sheet per issuer - 5 fiscal years + LTM, $mm, with credit ratios
  * Audit sheet - the exact XBRL concept / filing behind every number

Usage:
    python credit_spread.py T F CCL            # tickers or CIKs
    python credit_spread.py T --years 3 --out at_t_spread.xlsx
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from credit_toolkit.edgar import spread_issuer

ROWS = [  # (key, label, kind)
    ("revenue", "Revenue", "usd"),
    ("ebitda", "EBITDA (OI + D&A)", "usd"),
    ("ebitda_margin", "EBITDA margin", "pct"),
    ("operating_income", "Operating income", "usd"),
    ("d_and_a", "D&A", "usd"),
    ("interest_expense", "Interest expense", "usd"),
    ("net_income", "Net income", "usd"),
    ("cfo", "Cash from operations", "usd"),
    ("capex", "Capex", "usd"),
    ("fcf", "Free cash flow (CFO - capex)", "usd"),
    ("cash", "Cash & equivalents", "usd"),
    ("total_debt", "Total debt", "usd"),
    ("net_debt", "Net debt", "usd"),
    ("equity", "Shareholders' equity", "usd"),
    ("gross_leverage", "Gross leverage (Debt / EBITDA)", "x"),
    ("net_leverage", "Net leverage (Net debt / EBITDA)", "x"),
    ("interest_coverage", "Interest coverage (EBITDA / Interest)", "x"),
    ("fcf_to_debt", "FCF / Debt", "pct"),
    ("debt_to_capital", "Debt / Capital", "pct"),
]
FMT = {"usd": '#,##0;(#,##0);"-"', "pct": '0.0%;(0.0%);"-"', "x": '0.00"x";(0.00"x");"-"'}
HEADER_FILL = PatternFill("solid", fgColor="1F3864")
RATIO_FILL = PatternFill("solid", fgColor="EAF1FB")


def issuer_frame(result: dict) -> pd.DataFrame:
    cols = {}
    for p in result["periods"]:
        col = []
        for key, _, kind in ROWS:
            v = p.values.get(key)
            col.append(v / 1e6 if (v is not None and kind == "usd") else v)
        cols[p.label] = col
    return pd.DataFrame(cols, index=[label for _, label, _ in ROWS])


def write_workbook(results: list[dict], out: Path) -> None:
    summary, audit = [], []
    for r in results:
        latest = r["periods"][-1]
        v = latest.values
        summary.append({
            "Ticker": r["ticker"], "Issuer": r["name"], "Period": latest.label,
            "Revenue ($mm)": (v.get("revenue") or 0) / 1e6 or None,
            "EBITDA ($mm)": (v.get("ebitda") or 0) / 1e6 or None,
            "Total debt ($mm)": (v.get("total_debt") or 0) / 1e6 or None,
            "Gross lev (x)": v.get("gross_leverage"), "Net lev (x)": v.get("net_leverage"),
            "Int cov (x)": v.get("interest_coverage"), "FCF / Debt": v.get("fcf_to_debt"),
            "Debt / Cap": v.get("debt_to_capital"),
            "Data gaps": "; ".join(r["gaps"]) or "none",
        })
        for p in r["periods"]:
            for metric, src in p.sources.items():
                audit.append({"Ticker": r["ticker"], "Period": p.label, "Metric": metric, "Source": src})

    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        pd.DataFrame(summary).to_excel(xw, sheet_name="Summary", index=False)
        ws = xw.sheets["Summary"]
        fmts = {"D": FMT["usd"], "E": FMT["usd"], "F": FMT["usd"], "G": FMT["x"], "H": FMT["x"],
                "I": FMT["x"], "J": FMT["pct"], "K": FMT["pct"]}
        for col, f in fmts.items():
            for cell in ws[col][1:]:
                cell.number_format = f
        _style_header(ws)

        for r in results:
            name = r["ticker"][:31]
            df = issuer_frame(r)
            df.to_excel(xw, sheet_name=name, startrow=2)
            ws = xw.sheets[name]
            ws["A1"] = f"{r['name']} (CIK {r['cik']}) - $ millions - source: SEC EDGAR XBRL, pulled {date.today()}"
            ws["A1"].font = Font(bold=True, size=12)
            for i, (_, _, kind) in enumerate(ROWS):
                row = 4 + i
                for c in range(2, 2 + len(df.columns)):
                    cell = ws.cell(row=row, column=c)
                    cell.number_format = FMT[kind]
                    if kind != "usd":
                        cell.fill = RATIO_FILL
            _style_header(ws, header_row=3)
            ws.column_dimensions["A"].width = 40

        pd.DataFrame(audit).to_excel(xw, sheet_name="Audit", index=False)
        _style_header(xw.sheets["Audit"])
        xw.sheets["Audit"].column_dimensions["D"].width = 110


def _style_header(ws, header_row: int = 1) -> None:
    for cell in ws[header_row]:
        if cell.value is not None:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = HEADER_FILL
            cell.alignment = Alignment(horizontal="center", wrap_text=True)
    for i, col in enumerate(ws.columns, start=1):
        letter = get_column_letter(i)
        if ws.column_dimensions[letter].width in (None, 13):
            ws.column_dimensions[letter].width = 16
    ws.freeze_panes = ws.cell(row=header_row + 1, column=2)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("issuers", nargs="+", help="Tickers or CIKs")
    ap.add_argument("--years", type=int, default=5, help="Fiscal years to show (default 5)")
    ap.add_argument("--out", default=f"credit_spread_{date.today():%Y%m%d}.xlsx")
    args = ap.parse_args(argv)

    results, failed = [], []
    for ident in args.issuers:
        try:
            print(f"Spreading {ident} ...", end=" ", flush=True)
            r = spread_issuer(ident, years=args.years)
            results.append(r)
            v = r["periods"][-1].values
            lev, cov = v.get("gross_leverage"), v.get("interest_coverage")
            lev_s = f"{lev:.2f}x" if lev is not None else "n/a"
            cov_s = f"{cov:.1f}x" if cov is not None else "n/a"
            print(f"{r['name']} | {r['periods'][-1].label} | gross lev {lev_s} | int cov {cov_s}")
            for g in r["gaps"]:
                print(f"    ! data gap: {g}")
        except Exception as e:  # keep going on the rest of the list
            failed.append(ident)
            print(f"FAILED: {e}")
    if not results:
        return 1
    out = Path(args.out)
    write_workbook(results, out)
    print(f"\nWrote {out.resolve()}")
    if failed:
        print(f"Could not spread: {', '.join(failed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
