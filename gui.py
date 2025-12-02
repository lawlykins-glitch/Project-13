#Lawkins
#12/02/2025
#Project12
import os
import csv
import locale
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from datetime import datetime

import db
from business import DailySales, DATE_FORMAT

# Locale for currency formatting with a safe fallback.
try:
    locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_ALL, "")


class SalesApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Sales Data Studio")
        self.master.geometry("840x640")
        self.master.minsize(720, 560)

        self._configure_style()

        self.date_var = tk.StringVar()
        self.region_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.id_var = tk.StringVar()

        self.start_date_var = tk.StringVar()
        self.end_date_var = tk.StringVar()
        self.filter_region_var = tk.StringVar(value="All regions")

        self.total_var = tk.StringVar(value="$0.00")
        self.avg_var = tk.StringVar(value="$0.00")
        self.count_var = tk.StringVar(value="0")
        self.top_day_var = tk.StringVar(value="—")

        self.regions = self._load_regions()
        self._build_layout()

    def _configure_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f7f7fb")
        style.configure("TLabel", background="#f7f7fb", font=("Helvetica", 11))
        style.configure("Header.TLabel", font=("Helvetica", 16, "bold"))
        style.configure("Accent.TButton", padding=6, relief="flat", background="#1f7a8c", foreground="white")
        style.map("Accent.TButton",
                  background=[("active", "#13677a"), ("pressed", "#0f5666")],
                  foreground=[("disabled", "#d9d9d9")])

    def _build_layout(self):
        notebook = ttk.Notebook(self.master)
        notebook.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        self.lookup_frame = ttk.Frame(notebook, padding=18)
        self.analytics_frame = ttk.Frame(notebook, padding=18)

        notebook.add(self.lookup_frame, text="Lookup & Update")
        notebook.add(self.analytics_frame, text="Analytics & Export")

        self._build_lookup_tab()
        self._build_analytics_tab()

    def _build_lookup_tab(self):
        header = ttk.Label(self.lookup_frame, text="Update existing sales records", style="Header.TLabel")
        header.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))

        prompt = ttk.Label(self.lookup_frame, text="Enter a date (YYYY-MM-DD) and region code to load a sale.")
        prompt.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 12))

        self._add_labeled_entry(self.lookup_frame, "Date:", self.date_var, 2)
        self._add_labeled_entry(self.lookup_frame, "Region:", self.region_var, 3)
        self._add_labeled_entry(self.lookup_frame, "Amount:", self.amount_var, 4)
        self.id_entry = self._add_labeled_entry(self.lookup_frame, "ID:", self.id_var, 5, readonly=True)

        btn = ttk.Button(self.lookup_frame, text="Get Amount", command=self.get_sales)
        btn.grid(row=3, column=3, padx=(12, 0), sticky="w")

        # keep an empty spacer column so the button does not overlap the entry field
        self.lookup_frame.columnconfigure(3, minsize=120)

        actions = ttk.Frame(self.lookup_frame, padding=(0, 12))
        actions.grid(row=6, column=0, columnspan=3, sticky="w")

        update_btn = ttk.Button(actions, text="Save Changes", style="Accent.TButton", command=self.update_amount)
        update_btn.pack(side=tk.LEFT, padx=(0, 10))

        exit_btn = ttk.Button(actions, text="Exit", command=self.on_close)
        exit_btn.pack(side=tk.LEFT)

    def _build_analytics_tab(self):
        header = ttk.Label(self.analytics_frame, text="Explore trends, filter data, and export snapshots", style="Header.TLabel")
        header.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))

        self._add_labeled_entry(self.analytics_frame, "Start date:", self.start_date_var, 1)
        self._add_labeled_entry(self.analytics_frame, "End date:", self.end_date_var, 2)

        ttk.Label(self.analytics_frame, text="Region filter:").grid(row=3, column=0, sticky="e", pady=4, padx=(0, 10))
        region_codes = ["All regions"] + sorted(self.regions.keys())
        self.region_dropdown = ttk.Combobox(self.analytics_frame, textvariable=self.filter_region_var,
                                            values=region_codes, state="readonly", width=22)
        self.region_dropdown.grid(row=3, column=1, sticky="w", pady=4)

        run_btn = ttk.Button(self.analytics_frame, text="Run Analysis", style="Accent.TButton", command=self.run_summary)
        run_btn.grid(row=1, column=3, rowspan=2, padx=(12, 0), sticky="ew")

        export_btn = ttk.Button(self.analytics_frame, text="Export Filtered CSV", command=self.export_filtered_csv)
        export_btn.grid(row=3, column=3, padx=(12, 0), sticky="ew")

        self.analytics_frame.columnconfigure(2, weight=1)
        self.analytics_frame.columnconfigure(3, weight=1)

        # Summary cards
        cards = ttk.Frame(self.analytics_frame, padding=(0, 14))
        cards.grid(row=4, column=0, columnspan=4, sticky="ew")
        for idx, (label, var) in enumerate([
            ("Total amount", self.total_var),
            ("Average amount", self.avg_var),
            ("Records", self.count_var),
            ("Best day", self.top_day_var),
        ]):
            card = ttk.Frame(cards, relief="ridge", padding=10)
            card.grid(row=0, column=idx, padx=6, sticky="ew")
            ttk.Label(card, text=label, font=("Helvetica", 10, "bold")).pack(anchor="w")
            ttk.Label(card, textvariable=var, font=("Helvetica", 14)).pack(anchor="w", pady=(4, 0))
            cards.columnconfigure(idx, weight=1)

        # Region breakdown
        ttk.Label(self.analytics_frame, text="Totals by region", font=("Helvetica", 12, "bold")).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(6, 4))
        region_frame, self.region_tree = self._build_tree(self.analytics_frame, ["Code", "Region", "Total", "Count"])
        region_frame.grid(row=6, column=0, columnspan=2, sticky="nsew", pady=(0, 10))

        # Quarter breakdown
        ttk.Label(self.analytics_frame, text="Totals by quarter", font=("Helvetica", 12, "bold")).grid(
            row=5, column=2, columnspan=2, sticky="w", pady=(6, 4))
        quarter_frame, self.quarter_tree = self._build_tree(self.analytics_frame, ["Quarter", "Total"])
        quarter_frame.grid(row=6, column=2, columnspan=2, sticky="nsew", pady=(0, 10))

        self.analytics_frame.rowconfigure(6, weight=1)
        self.analytics_frame.columnconfigure(1, weight=1)
        self.analytics_frame.columnconfigure(2, weight=1)
        self.analytics_frame.columnconfigure(3, weight=1)

        ttk.Label(self.analytics_frame, text="Use the filters above to slice the data. Export produces a CSV with ID, date, region, and amount for the current slice.").grid(
            row=7, column=0, columnspan=4, sticky="w", pady=(6, 0))

    def _build_tree(self, parent, columns):
        frame = ttk.Frame(parent)
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        return frame, tree

    def _add_labeled_entry(self, parent, label_text, text_var, row, readonly=False):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=(0, 10), pady=4, sticky="e")
        entry_state = "readonly" if readonly else "normal"
        entry = ttk.Entry(parent, textvariable=text_var, width=26, state=entry_state)
        entry.grid(row=row, column=1, pady=4, sticky="w", columnspan=2)
        return entry

    def _load_regions(self):
        try:
            regions = db.get_regions()
            region_list = []
            if hasattr(regions, "_Regions__VALID_REGIONS"):
                region_list = getattr(regions, "_Regions__VALID_REGIONS")
            return {region.code: region for region in region_list}
        except Exception:
            messagebox.showerror("Database error", "Unable to load regions from the database.")
            return {}

    def _set_id_value(self, value):
        self.id_entry.config(state="normal")
        self.id_var.set(value)
        self.id_entry.config(state="readonly")

    def _clear_loaded_sale(self):
        self.amount_var.set("")
        self._set_id_value("")

    def _parse_date_text(self, text, allow_blank=False, label="Date"):
        value = text.strip()
        if not value:
            return None if allow_blank else False
        try:
            dt = datetime.strptime(value, DATE_FORMAT)
            return dt.strftime(DATE_FORMAT)
        except ValueError:
            messagebox.showerror("Invalid date", f"{label} must be valid and in YYYY-MM-DD format.")
            return False

    def get_sales(self):
        date_value = self._parse_date_text(self.date_var.get(), label="Date")
        region_code = self.region_var.get().strip()

        if date_value is False:
            return
        if not date_value or not region_code:
            messagebox.showwarning("Missing data", "Enter both a date and a region code.")
            return

        if self.regions and region_code not in self.regions:
            valid_codes = ", ".join(sorted(self.regions.keys()))
            messagebox.showerror("Invalid region", f"Region must be one of: {valid_codes}.")
            return

        try:
            data = db.get_sales(date_value, region_code)
        except Exception:
            messagebox.showerror("Database error", "Unable to retrieve sales data.")
            return

        if data is None:
            self._clear_loaded_sale()
            messagebox.showinfo("Not found", "No sales amount for the date and region entered.")
            return

        self.amount_var.set(f"{data.amount}")
        self._set_id_value(str(data.id))

        self.date_var.set(date_value)
        self.region_var.set(data.region.code)

    def update_amount(self):
        sale_id = self.id_var.get().strip()
        if not sale_id:
            messagebox.showwarning("No sale loaded", "Retrieve a sale before updating the amount.")
            return

        try:
            amount = float(self.amount_var.get())
        except ValueError:
            messagebox.showerror("Invalid amount", "Enter a numeric sales amount.")
            return

        if amount <= 0:
            messagebox.showerror("Invalid amount", "Amount must be greater than zero.")
            return

        data = DailySales()
        data.id = int(sale_id)
        data.amount = amount

        try:
            db.update_sales_amount(data)
        except Exception:
            messagebox.showerror("Database error", "Unable to update the sales amount.")
            return

        messagebox.showinfo("Updated", "Sales amount updated successfully.")

    def _clear_tree(self, tree):
        for child in tree.get_children():
            tree.delete(child)

    def _format_currency(self, value):
        try:
            return locale.currency(value, grouping=True)
        except Exception:
            return f"${value:,.2f}"

    def run_summary(self):
        start = self._parse_date_text(self.start_date_var.get(), allow_blank=True, label="Start date")
        end = self._parse_date_text(self.end_date_var.get(), allow_blank=True, label="End date")
        if start is False or end is False:
            return

        if start and end:
            try:
                if datetime.strptime(start, DATE_FORMAT) > datetime.strptime(end, DATE_FORMAT):
                    messagebox.showerror("Invalid range", "Start date must be before or equal to end date.")
                    return
            except ValueError:
                return

        region_choice = self.filter_region_var.get().strip()
        region_filter = None if region_choice in ("", "All regions") else region_choice

        try:
            summary = db.get_sales_summary(start, end, region_filter)
        except Exception:
            messagebox.showerror("Database error", "Unable to build the summary with the current filters.")
            return

        total = summary.get("total") or 0
        avg = summary.get("average") or 0
        count = summary.get("count") or 0
        top_day = summary.get("top_day")

        self.total_var.set(self._format_currency(total))
        self.avg_var.set(self._format_currency(avg) if count else "$0.00")
        self.count_var.set(str(count))
        if top_day:
            self.top_day_var.set(f"{top_day['salesDate']} ({self._format_currency(top_day['total'])})")
        else:
            self.top_day_var.set("—")

        self._clear_tree(self.region_tree)
        for row in summary.get("regions", []):
            self.region_tree.insert("", tk.END, values=(
                row["code"],
                row["name"],
                self._format_currency(row["total"]),
                row["count"]
            ))

        self._clear_tree(self.quarter_tree)
        for row in summary.get("quarters", []):
            self.quarter_tree.insert("", tk.END, values=(
                int(row["quarter"]),
                self._format_currency(row["total"])
            ))

    def export_filtered_csv(self):
        start = self._parse_date_text(self.start_date_var.get(), allow_blank=True, label="Start date")
        end = self._parse_date_text(self.end_date_var.get(), allow_blank=True, label="End date")
        if start is False or end is False:
            return

        region_choice = self.filter_region_var.get().strip()
        region_filter = None if region_choice in ("", "All regions") else region_choice

        try:
            data = db.get_sales_filtered(start, end, region_filter)
        except Exception:
            messagebox.showerror("Database error", "Unable to retrieve filtered data for export.")
            return

        if data.count == 0:
            messagebox.showinfo("No data", "No sales match the current filters.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Save filtered sales as CSV"
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Date", "Region Code", "Region Name", "Amount", "Quarter"])
                for sale in data:
                    sales_date = sale.salesDate.strftime(DATE_FORMAT) if hasattr(sale.salesDate, "strftime") else sale.salesDate
                    writer.writerow([
                        sale.id,
                        sales_date,
                        sale.region.code,
                        sale.region.name,
                        f"{sale.amount:.2f}",
                        sale.quarter,
                    ])
        except OSError:
            messagebox.showerror("File error", "Unable to write to the chosen file path.")
            return

        messagebox.showinfo("Export complete", f"Saved {data.count} rows to\n{filepath}")

    def on_close(self):
        db.close()
        self.master.destroy()


def main():
    # ensure the SQLite file is found when running from other directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    db.connect()

    root = tk.Tk()
    app = SalesApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
