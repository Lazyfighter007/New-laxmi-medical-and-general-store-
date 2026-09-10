import os
import sqlite3
import tempfile
import webbrowser
from datetime import date, datetime
import tkinter as tk
from tkinter import ttk, messagebox

APP_NAME = "NEW LAXMI MEDICAL & GENERAL STORE"
STORE_ADDRESS = "GMR NAGAR, DOLAPETA, RAJAM"
STORE_PHONE = "96524 69782"
STORE_GSTIN = ""
# Store user data outside Program Files so the installed app can write to it.
DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "NewLaxmiMedicalStore")
os.makedirs(DATA_DIR, exist_ok=True)
DB = os.path.join(DATA_DIR, "medical_store.db")
CATEGORIES = [
    "Tablets & Capsules", "Liquid Orals / Syrups", "Powders & Granules",
    "Surgical Disposables", "Wound Care & Dressings", "Medical Equipment & Devices",
    "Inhalers & Aerosols", "Respiratory Fluids", "Intravenous (IV) Fluids",
    "Injectables", "Semisolids / Ointments", "Liquids & Drops",
    "Personal & Baby Care", "OTC Health & Wellness"
]


def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier TEXT, invoice_no TEXT, invoice_date TEXT, purchase_type TEXT,
        hsn TEXT, name TEXT NOT NULL, mfg TEXT, pack TEXT NOT NULL,
        batch TEXT NOT NULL, expiry TEXT NOT NULL,
        paid_packs INTEGER NOT NULL DEFAULT 0,
        free_packs INTEGER NOT NULL DEFAULT 0,
        stock_units INTEGER NOT NULL DEFAULT 0,
        purchase_price REAL NOT NULL DEFAULT 0,
        gst REAL NOT NULL DEFAULT 0,
        selling_price REAL NOT NULL DEFAULT 0,
        category TEXT, rack TEXT
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_no TEXT UNIQUE NOT NULL,
        bill_date TEXT NOT NULL,
        total REAL NOT NULL,
        paid REAL NOT NULL,
        change_amt REAL NOT NULL
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS bill_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_id INTEGER NOT NULL,
        medicine_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        batch TEXT,
        quantity_units INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        total REAL NOT NULL
    )""")
    con.commit()
    return con


def pack_units(pack):
    import re
    m = re.search(r"(\d+(?:\.\d+)?)\s*S\b", (pack or "").upper())
    return float(m.group(1)) if m else 1.0


def parse_expiry(v):
    v = (v or "").strip()
    if not v:
        return None
    try:
        if len(v) == 5 and v[2] == "/":
            mm, yy = map(int, v.split("/"))
            return date(2000 + yy, mm, 1)
        return datetime.strptime(v, "%Y-%m-%d").date()
    except ValueError:
        return None


def expiry_status(expiry):
    d = parse_expiry(expiry)
    if not d:
        return "INVALID"
    today = date.today()
    if d < today.replace(day=1):
        return "EXPIRED"
    # Four calendar months from the current month.
    month = today.month - 1 + 4
    year = today.year + month // 12
    month = month % 12 + 1
    limit = date(year, month, 1)
    return "EXPIRING" if d <= limit else "OK"


def money(v):
    return f"₹{v:,.2f}"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1280x760")
        self.minsize(1100, 680)
        self.cart = []
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._style()
        self._header()
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.dashboard_tab()
        self.inventory_tab()
        self.billing_tab()
        self.sales_tab()
        self.refresh_all()

    def _style(self):
        st = ttk.Style(self)
        try: st.theme_use("clam")
        except tk.TclError: pass
        st.configure("Title.TLabel", font=("Segoe UI", 19, "bold"))
        st.configure("Card.TLabel", font=("Segoe UI", 22, "bold"))
        st.configure("Treeview", rowheight=28)

    def _header(self):
        f = ttk.Frame(self, padding=12); f.pack(fill="x")
        ttk.Label(f, text=APP_NAME, style="Title.TLabel").pack(side="left")
        ttk.Button(f, text="Refresh", command=self.refresh_all).pack(side="right")

    def dashboard_tab(self):
        tab = ttk.Frame(self.tabs, padding=12); self.tabs.add(tab, text="Dashboard")
        cards = ttk.Frame(tab); cards.pack(fill="x")
        self.card_vars = {}
        for key, label in [("meds","Medicines"),("stock","Total Units"),("low","Low Stock"),("expiry","Expiring ≤ 4 Months"),("expired","Expired")]:
            box = ttk.LabelFrame(cards, text=label, padding=15); box.pack(side="left",fill="both",expand=True,padx=4)
            v=tk.StringVar(value="0"); self.card_vars[key]=v; ttk.Label(box,textvariable=v,style="Card.TLabel").pack()
        sec=ttk.LabelFrame(tab,text="Expiry alerts — next 4 months",padding=10);sec.pack(fill="both",expand=True,pady=(16,0))
        cols=("name","batch","stock","expiry","status")
        self.exp_tree=ttk.Treeview(sec,columns=cols,show="headings")
        for c,h,w in [("name","Medicine",270),("batch","Batch",120),("stock","Stock",170),("expiry","Expiry",120),("status","Status",120)]:
            self.exp_tree.heading(c,text=h);self.exp_tree.column(c,width=w)
        self.exp_tree.pack(fill="both",expand=True)

    def inventory_tab(self):
        tab=ttk.Frame(self.tabs,padding=10);self.tabs.add(tab,text="Inventory")
        top=ttk.Frame(tab);top.pack(fill="x")
        ttk.Label(top,text="Purchase-bill style inventory. 10S × 1 pack = 10 units; free packs are included in total stock.").pack(side="left")
        ttk.Button(top,text="+ Add Inventory",command=self.open_purchase).pack(side="right")
        bar=ttk.Frame(tab);bar.pack(fill="x",pady=10)
        self.inv_search=tk.StringVar(); ttk.Label(bar,text="Search:").pack(side="left"); ttk.Entry(bar,textvariable=self.inv_search,width=40).pack(side="left",padx=6); self.inv_search.trace_add("write",lambda *_:self.load_inventory())
        cols=("category","hsn","name","mfg","pack","batch","expiry","paid","free","units","purchase","selling","gst","status")
        self.inv_tree=ttk.Treeview(tab,columns=cols,show="headings")
        heads=[("category","Category",170),("hsn","HSN",90),("name","Item Name",210),("mfg","MFG",100),("pack","Pack",70),("batch","Batch",100),("expiry","EXP",90),("paid","Paid Packs",80),("free","Free Packs",80),("units","Total Units",90),("purchase","Purchase ₹",90),("selling","Selling ₹",90),("gst","GST",60),("status","Status",90)]
        for c,h,w in heads:self.inv_tree.heading(c,text=h);self.inv_tree.column(c,width=w)
        self.inv_tree.pack(fill="both",expand=True)

    def open_purchase(self):
        win=tk.Toplevel(self);win.title("Add Inventory — Purchase Bill Format");win.geometry("850x720");win.transient(self);win.grab_set()
        frm=ttk.Frame(win,padding=16);frm.pack(fill="both",expand=True)
        ttk.Label(frm,text="Add Inventory — Purchase Bill Format",font=("Segoe UI",18,"bold")).pack(anchor="w")
        ttk.Label(frm,text="Purchase Price + GST = Selling Price (pack price)").pack(anchor="w",pady=(2,12))
        fields={}
        grid=ttk.Frame(frm);grid.pack(fill="x")
        defs=[("supplier","Supplier","SRI NIDHI MEDICAL AGENCY"),("invoice","Invoice No.","Q00257"),("invdate","Invoice Date",""),("type","Purchase Type","Credit"),("hsn","HSN","30049099"),("name","Item Name","PANTOP 40MG TAB"),("mfg","MFG","ARBS"),("pack","Pack","15S"),("batch","Batch Number","SPB260316"),("expiry","Expiry (MM/YY)","07/28"),("qty","Quantity (Packs)","1"),("free","Free Qty (Packs)","0"),("purchase","Purchase Price ₹","0"),("gst","GST %","5"),("selling","Selling Price ₹","0"),("category","Category",CATEGORIES[0]),("rack","Rack / Location","A-01")]
        for i,(key,label,default) in enumerate(defs):
            r=i//2;c=(i%2)*2;ttk.Label(grid,text=label).grid(row=r,column=c,padx=5,pady=5,sticky="w")
            if key=="type":
                var=tk.StringVar(value=default); w=ttk.Combobox(grid,textvariable=var,values=["Credit","Cash"],state="readonly",width=30)
            elif key=="category":
                var=tk.StringVar(value=default); w=ttk.Combobox(grid,textvariable=var,values=CATEGORIES,state="readonly",width=30)
            else:
                var=tk.StringVar(value=default);w=ttk.Entry(grid,textvariable=var,width=33)
            w.grid(row=r,column=c+1,padx=5,pady=5,sticky="ew");fields[key]=var
        for c in range(4):grid.columnconfigure(c,weight=1)
        def calc(*_):
            try: p=float(fields["purchase"].get() or 0);g=float(fields["gst"].get() or 0)
            except ValueError:p=g=0
            fields["selling"].set(f"{p*(1+g/100):.2f}")
        fields["purchase"].trace_add("write",calc);fields["gst"].trace_add("write",calc);calc()
        def save():
            try:
                name=fields["name"].get().strip();batch=fields["batch"].get().strip();pack=fields["pack"].get().strip();expiry=fields["expiry"].get().strip();qty=int(fields["qty"].get() or 0);free=int(fields["free"].get() or 0);purchase=float(fields["purchase"].get() or 0);gst=float(fields["gst"].get() or 0)
            except ValueError:messagebox.showerror("Invalid","Check quantity, price and GST.",parent=win);return
            if not name or not batch or not pack or not expiry or qty<0 or free<0 or purchase<0 or gst<0:messagebox.showerror("Missing/Invalid","Item name, batch, pack, expiry and valid numbers are required.",parent=win);return
            if not parse_expiry(expiry):messagebox.showerror("Expiry","Use MM/YY or YYYY-MM-DD.",parent=win);return
            pu=pack_units(pack);selling=purchase*(1+gst/100);units=round((qty+free)*pu)
            con=connect();con.execute("""INSERT INTO medicines(supplier,invoice_no,invoice_date,purchase_type,hsn,name,mfg,pack,batch,expiry,paid_packs,free_packs,stock_units,purchase_price,gst,selling_price,category,rack) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(fields["supplier"].get().strip(),fields["invoice"].get().strip(),fields["invdate"].get().strip(),fields["type"].get(),fields["hsn"].get().strip(),name,fields["mfg"].get().strip(),pack,batch,expiry,qty,free,units,purchase,gst,selling,fields["category"].get(),fields["rack"].get().strip()));con.commit();con.close();win.destroy();self.refresh_all()
        btn=ttk.Frame(frm);btn.pack(fill="x",pady=18);ttk.Button(btn,text="Cancel",command=win.destroy).pack(side="right",padx=5);ttk.Button(btn,text="Save to Inventory",command=save).pack(side="right")

    def billing_tab(self):
        tab=ttk.Frame(self.tabs,padding=10);self.tabs.add(tab,text="Billing")
        ttk.Label(tab,text="Enter individual units. For 15S, Qty 1 = 1 tablet and price = pack selling price ÷ 15.").pack(anchor="w")
        bar=ttk.Frame(tab);bar.pack(fill="x",pady=10)
        self.bill_med=tk.StringVar();self.bill_qty=tk.StringVar(value="1")
        self.bill_combo=ttk.Combobox(bar,textvariable=self.bill_med,state="readonly",width=65);self.bill_combo.pack(side="left")
        ttk.Label(bar,text="Qty Units").pack(side="left",padx=(15,4));ttk.Entry(bar,textvariable=self.bill_qty,width=8).pack(side="left")
        ttk.Button(bar,text="Add",command=self.add_cart).pack(side="left",padx=6)
        cols=("name","batch","qty","rate","total");self.cart_tree=ttk.Treeview(tab,columns=cols,show="headings",height=12)
        for c,h,w in [("name","Medicine",300),("batch","Batch",120),("qty","Qty Units",90),("rate","Rate ₹/Unit",110),("total","Amount ₹",120)]:self.cart_tree.heading(c,text=h);self.cart_tree.column(c,width=w)
        self.cart_tree.pack(fill="both",expand=True)
        bottom=ttk.Frame(tab);bottom.pack(fill="x",pady=10)
        self.bill_total=tk.StringVar(value="0.00");self.paid=tk.StringVar();self.change=tk.StringVar(value="0.00")
        ttk.Label(bottom,text="Total ₹").pack(side="left");ttk.Label(bottom,textvariable=self.bill_total,font=("Segoe UI",15,"bold")).pack(side="left",padx=5)
        ttk.Label(bottom,text="Paid ₹").pack(side="left",padx=(25,4));ttk.Entry(bottom,textvariable=self.paid,width=12).pack(side="left");ttk.Label(bottom,text="Change ₹").pack(side="left",padx=(20,4));ttk.Label(bottom,textvariable=self.change).pack(side="left")
        ttk.Button(bottom,text="Remove Selected",command=self.remove_cart).pack(side="left",padx=20);ttk.Button(bottom,text="Save & Generate Bill",command=self.complete_bill).pack(side="right")

    def sales_tab(self):
        tab=ttk.Frame(self.tabs,padding=10);self.tabs.add(tab,text="Sales History")
        cols=("bill","date","total","paid","change");self.sales_tree=ttk.Treeview(tab,columns=cols,show="headings")
        for c,h,w in [("bill","Bill No",160),("date","Date",180),("total","Total ₹",120),("paid","Paid ₹",120),("change","Change ₹",120)]:self.sales_tree.heading(c,text=h);self.sales_tree.column(c,width=w)
        self.sales_tree.pack(fill="both",expand=True)

    def refresh_all(self):self.load_inventory();self.refresh_dashboard();self.load_billing_meds();self.load_sales()

    def load_inventory(self):
        q=getattr(self,"inv_search",tk.StringVar()).get().lower() if hasattr(self,"inv_search") else ""
        con=connect();rows=con.execute("SELECT * FROM medicines ORDER BY expiry,name").fetchall();con.close()
        for x in self.inv_tree.get_children():self.inv_tree.delete(x)
        for r in rows:
            text=" ".join(str(r[k] or "") for k in ("name","batch","company","hsn","category") if k in r.keys()).lower()
            if q and q not in text:continue
            self.inv_tree.insert("","end",values=(r["category"],r["hsn"],r["name"],r["mfg"],r["pack"],r["batch"],r["expiry"],r["paid_packs"],r["free_packs"],r["stock_units"],f'{r["purchase_price"]:.2f}',f'{r["selling_price"]:.2f}',f'{r["gst"]:.0f}%',expiry_status(r["expiry"])))

    def refresh_dashboard(self):
        con=connect();rows=con.execute("SELECT * FROM medicines").fetchall();con.close();self.card_vars["meds"].set(len(rows));self.card_vars["stock"].set(sum(r["stock_units"] for r in rows));self.card_vars["low"].set(sum(1 for r in rows if r["stock_units"]<=10));exp=[r for r in rows if expiry_status(r["expiry"])=="EXPIRING"];self.card_vars["expiry"].set(len(exp));self.card_vars["expired"].set(sum(1 for r in rows if expiry_status(r["expiry"])=="EXPIRED"))
        for x in self.exp_tree.get_children():self.exp_tree.delete(x)
        for r in sorted(exp,key=lambda x:x["expiry"]):self.exp_tree.insert("","end",values=(r["name"],r["batch"],f'{r["stock_units"]} units',r["expiry"],"EXPIRING"))

    def load_billing_meds(self):
        if not hasattr(self,"bill_combo"):return
        con=connect();rows=con.execute("SELECT * FROM medicines WHERE stock_units>0 ORDER BY name,batch").fetchall();con.close();self.bill_rows=rows
        self.bill_combo["values"]=[f'{r["name"]} | Batch {r["batch"]} | {r["pack"]} | {money(r["selling_price"]/pack_units(r["pack"]))}/unit | {r["stock_units"]} units' for r in rows]
        if rows:self.bill_combo.current(0)

    def add_cart(self):
        if not getattr(self,"bill_rows",[]):return messagebox.showwarning("Stock","No available stock.")
        idx=self.bill_combo.current();
        if idx<0:return
        try:q=int(self.bill_qty.get())
        except ValueError:return messagebox.showerror("Quantity","Enter a whole number of units.")
        if q<1:return messagebox.showerror("Quantity","Quantity must be at least 1.")
        r=self.bill_rows[idx];already=sum(x["qty"] for x in self.cart if x["id"]==r["id"])
        if already+q>r["stock_units"]:return messagebox.showerror("Stock","Not enough units in stock.")
        for x in self.cart:
            if x["id"]==r["id"]:x["qty"]+=q;break
        else:self.cart.append({"id":r["id"],"name":r["name"],"batch":r["batch"],"qty":q,"unit_price":r["selling_price"]/pack_units(r["pack"])})
        self.draw_cart()

    def draw_cart(self):
        for x in self.cart_tree.get_children():self.cart_tree.delete(x)
        total=0
        for i,x in enumerate(self.cart):
            t=x["qty"]*x["unit_price"];total+=t;self.cart_tree.insert("","end",iid=str(i),values=(x["name"],x["batch"],x["qty"],f'{x["unit_price"]:.2f}',f'{t:.2f}'))
        self.bill_total.set(f"{total:.2f}");self.calc_change()

    def calc_change(self):
        try:self.change.set(f'{max(0,float(self.paid.get() or 0)-float(self.bill_total.get() or 0)):.2f}')
        except ValueError:self.change.set("0.00")

    def remove_cart(self):
        sel=self.cart_tree.selection()
        if sel:self.cart.pop(int(sel[0]));self.draw_cart()

    def complete_bill(self):
        if not self.cart:return messagebox.showwarning("Bill","Add medicines first.")
        total=float(self.bill_total.get());
        try:paid=float(self.paid.get())
        except ValueError:return messagebox.showerror("Payment","Enter a valid paid amount.")
        if paid<total:return messagebox.showerror("Payment","Paid amount is less than total.")
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S");change=paid-total
        con=connect();cur=con.cursor();bill_no=f"B{datetime.now().strftime('%Y%m%d%H%M%S%f')}";cur.execute("INSERT INTO bills(bill_no,bill_date,total,paid,change_amt) VALUES(?,?,?,?,?)",(bill_no,now,total,paid,change));bid=cur.lastrowid
        for x in self.cart:
            cur.execute("UPDATE medicines SET stock_units=stock_units-? WHERE id=? AND stock_units>=?",(x["qty"],x["id"],x["qty"]))
            if cur.rowcount!=1:con.rollback();con.close();return messagebox.showerror("Stock","Stock changed. Please retry the bill.")
            cur.execute("INSERT INTO bill_items(bill_id,medicine_id,name,batch,quantity_units,unit_price,total) VALUES(?,?,?,?,?,?,?)",(bid,x["id"],x["name"],x["batch"],x["qty"],x["unit_price"],x["qty"]*x["unit_price"]))
        con.commit();con.close();self.generate_bill(bill_no,now,self.cart,total,paid,change);self.cart=[];self.paid.set("");self.draw_cart();self.refresh_all()

    def generate_bill(self,bill_no,now,items,total,paid,change):
        rows="".join(f'<tr><td>{i}</td><td>{x["name"]}<br><small>Batch: {x["batch"]}</small></td><td>{x["qty"]}</td><td>{money(x["unit_price"])}</td><td>{money(x["qty"]*x["unit_price"])}</td></tr>' for i,x in enumerate(items,1))
        html=f'''<!doctype html><html><head><meta charset="utf-8"><title>{bill_no} - {APP_NAME}</title><style>body{{font-family:Arial;margin:20px}}.bill{{max-width:700px;margin:auto;border:1px solid #aaa;padding:24px}}h1{{text-align:center;font-size:22px}}.meta{{text-align:center;font-size:12px}}table{{width:100%;border-collapse:collapse;margin-top:20px}}th,td{{border-bottom:1px solid #ddd;padding:8px;text-align:left}}.sum{{margin:20px 0 0 auto;width:260px}}.sum p{{display:flex;justify-content:space-between}}button{{padding:8px 14px}}@media print{{button{{display:none}}}}</style></head><body><div class="bill"><h1>{APP_NAME}</h1><div class="meta"><b>{STORE_ADDRESS}</b><br>Mobile: {STORE_PHONE}<br>{("GSTIN: " + STORE_GSTIN) if STORE_GSTIN else ""}<br><br>Bill No: {bill_no} &nbsp; | &nbsp; Date: {now}</div><table><tr><th>#</th><th>Medicine</th><th>Qty</th><th>Rate ₹</th><th>Amount ₹</th></tr>{rows}</table><div class="sum"><p><span>Total</span><b>{money(total)}</b></p><p><span>Paid</span><span>{money(paid)}</span></p><p><span>Change</span><b>{money(change)}</b></p></div><p style="text-align:center;margin-top:30px">Thank you for visiting {APP_NAME}</p><p style="text-align:center"><button onclick="window.print()">🖨 Print Bill</button></p></div></body></html>'''
        fd,path=tempfile.mkstemp(prefix="medical_bill_",suffix=".html");os.close(fd);open(path,"w",encoding="utf-8").write(html);webbrowser.open("file:///"+path.replace(os.sep,"/"))

    def load_sales(self):
        con=connect();rows=con.execute("SELECT * FROM bills ORDER BY id DESC").fetchall();con.close()
        for x in self.sales_tree.get_children():self.sales_tree.delete(x)
        for r in rows:self.sales_tree.insert("","end",values=(r["bill_no"],r["bill_date"],f'{r["total"]:.2f}',f'{r["paid"]:.2f}',f'{r["change_amt"]:.2f}'))


if __name__ == "__main__":
    connect().close()
    App().mainloop()
