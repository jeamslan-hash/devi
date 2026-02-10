import sqlite3
from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox

DB_NAME = "abone_dlo.db"


class AboneDloApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Jesyon Abone Dlo")
        self.root.geometry("1100x700")

        self.conn = sqlite3.connect(DB_NAME)
        self.conn.row_factory = sqlite3.Row
        self._create_table()

        self.selected_id = None

        self._build_ui()
        self.load_data()

    def _create_table(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS abone (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                non TEXT NOT NULL,
                siyati TEXT NOT NULL,
                telefon TEXT,
                adres TEXT,
                nimewo_konte TEXT UNIQUE,
                dat_enskripsyon TEXT,
                balans REAL DEFAULT 0,
                estati TEXT DEFAULT 'aktif'
            )
            """
        )
        self.conn.commit()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        form = ttk.LabelFrame(main, text="Fòm Abone", padding=10)
        form.pack(fill=tk.X, pady=(0, 10))

        self.entries = {}

        fields = [
            ("non", "Non"),
            ("siyati", "Siyati"),
            ("telefon", "Telefòn"),
            ("adres", "Adrès"),
            ("nimewo_konte", "Nimewo Kontè"),
            ("dat_enskripsyon", "Dat Enskripsyon (YYYY-MM-DD)"),
            ("balans", "Balans"),
            ("estati", "Estati (aktif/inaktif)"),
        ]

        for i, (key, label) in enumerate(fields):
            r, c = divmod(i, 2)
            ttk.Label(form, text=label).grid(row=r, column=c * 2, sticky=tk.W, padx=6, pady=6)
            entry = ttk.Entry(form, width=35)
            entry.grid(row=r, column=c * 2 + 1, sticky=tk.EW, padx=6, pady=6)
            self.entries[key] = entry

        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(3, weight=1)

        if not self.entries["dat_enskripsyon"].get():
            self.entries["dat_enskripsyon"].insert(0, str(date.today()))
        self.entries["estati"].insert(0, "aktif")
        self.entries["balans"].insert(0, "0")

        btns = ttk.Frame(main)
        btns.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(btns, text="Ajoute", command=self.add_abone).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Mete Ajou", command=self.update_abone).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Efase", command=self.delete_abone).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Netwaye", command=self.clear_form).pack(side=tk.LEFT, padx=4)

        self.search_var = tk.StringVar()
        ttk.Label(btns, text="Chèche:").pack(side=tk.LEFT, padx=(20, 4))
        search_entry = ttk.Entry(btns, textvariable=self.search_var, width=35)
        search_entry.pack(side=tk.LEFT, padx=4)
        search_entry.bind("<KeyRelease>", lambda _e: self.load_data())

        columns = (
            "id",
            "non",
            "siyati",
            "telefon",
            "adres",
            "nimewo_konte",
            "dat_enskripsyon",
            "balans",
            "estati",
        )

        table_wrap = ttk.Frame(main)
        table_wrap.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            width = 130 if col not in ("adres",) else 220
            self.tree.column(col, width=width, anchor=tk.W)

        yscroll = ttk.Scrollbar(table_wrap, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def get_form_data(self):
        data = {k: v.get().strip() for k, v in self.entries.items()}

        if not data["non"] or not data["siyati"]:
            raise ValueError("Non ak Siyati obligatwa.")

        try:
            data["balans"] = float(data["balans"] or 0)
        except ValueError as exc:
            raise ValueError("Balans dwe yon nimewo.") from exc

        return data

    def add_abone(self):
        try:
            data = self.get_form_data()
            self.conn.execute(
                """
                INSERT INTO abone(non, siyati, telefon, adres, nimewo_konte, dat_enskripsyon, balans, estati)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["non"],
                    data["siyati"],
                    data["telefon"],
                    data["adres"],
                    data["nimewo_konte"],
                    data["dat_enskripsyon"],
                    data["balans"],
                    data["estati"] or "aktif",
                ),
            )
            self.conn.commit()
            self.load_data()
            self.clear_form()
            messagebox.showinfo("Siksè", "Abone a anrejistre.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Erè", "Nimewo kontè sa a deja egziste.")
        except ValueError as exc:
            messagebox.showerror("Erè", str(exc))

    def update_abone(self):
        if self.selected_id is None:
            messagebox.showwarning("Atansyon", "Tanpri chwazi yon abone nan lis la.")
            return

        try:
            data = self.get_form_data()
            self.conn.execute(
                """
                UPDATE abone
                SET non=?, siyati=?, telefon=?, adres=?, nimewo_konte=?, dat_enskripsyon=?, balans=?, estati=?
                WHERE id=?
                """,
                (
                    data["non"],
                    data["siyati"],
                    data["telefon"],
                    data["adres"],
                    data["nimewo_konte"],
                    data["dat_enskripsyon"],
                    data["balans"],
                    data["estati"] or "aktif",
                    self.selected_id,
                ),
            )
            self.conn.commit()
            self.load_data()
            messagebox.showinfo("Siksè", "Done yo mete ajou.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Erè", "Nimewo kontè sa a deja ekziste.")
        except ValueError as exc:
            messagebox.showerror("Erè", str(exc))

    def delete_abone(self):
        if self.selected_id is None:
            messagebox.showwarning("Atansyon", "Tanpri chwazi yon abone pou efase.")
            return

        if not messagebox.askyesno("Konfimasyon", "Èske ou vle efase abone sa a?"):
            return

        self.conn.execute("DELETE FROM abone WHERE id=?", (self.selected_id,))
        self.conn.commit()
        self.load_data()
        self.clear_form()
        messagebox.showinfo("Siksè", "Abone a efase.")

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        q = self.search_var.get().strip()
        if q:
            rows = self.conn.execute(
                """
                SELECT * FROM abone
                WHERE non LIKE ? OR siyati LIKE ? OR telefon LIKE ? OR nimewo_konte LIKE ?
                ORDER BY id DESC
                """,
                (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"),
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM abone ORDER BY id DESC").fetchall()

        for row in rows:
            self.tree.insert("", tk.END, values=tuple(row))

    def on_select(self, _event):
        selected = self.tree.selection()
        if not selected:
            return

        vals = self.tree.item(selected[0], "values")
        self.selected_id = int(vals[0])

        keys = [
            "non",
            "siyati",
            "telefon",
            "adres",
            "nimewo_konte",
            "dat_enskripsyon",
            "balans",
            "estati",
        ]

        for idx, key in enumerate(keys, start=1):
            self.entries[key].delete(0, tk.END)
            self.entries[key].insert(0, vals[idx])

    def clear_form(self):
        self.selected_id = None
        for e in self.entries.values():
            e.delete(0, tk.END)
        self.entries["dat_enskripsyon"].insert(0, str(date.today()))
        self.entries["balans"].insert(0, "0")
        self.entries["estati"].insert(0, "aktif")


def main():
    root = tk.Tk()
    AboneDloApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
