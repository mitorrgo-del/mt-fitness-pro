
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import os
import requests

# --- MT FITNESS PRO - AGENTE MAESTRO TÁCTICO V2 ---
DB_PATH = "mtfitness.db"
COACH_PASSWORD = "MT_MASTER_PRO_2026"

class CoachMasterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MT FITNESS PRO - CENTRO DE COMANDANCIA")
        self.root.geometry("1300x850")
        self.root.configure(bg="#020617") # Slate 950 (Oscuridad Premium)
        
        # --- ESTILOS MODERNOS (TEMA DARK PRO) ---
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure("TNotebook", background="#020617", borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#1e293b", foreground="#94a3b8", padding=[20, 10], font=("Segoe UI", 10, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", "#2dd4bf")], foreground=[("selected", "#020617")])
        
        self.style.configure("Treeview", background="#0f172a", foreground="white", fieldbackground="#0f172a", rowheight=35, font=("Segoe UI", 10), borderwidth=0)
        self.style.configure("Treeview.Heading", background="#1e293b", foreground="#2dd4bf", font=("Segoe UI", 10, "bold"), padding=10)
        self.style.map("Treeview", background=[('selected', '#2dd4bf')], foreground=[('selected', '#020617')])
        
        self.current_user_id = None
        
        # --- PANTALLA DE LOGIN ---
        self.login_frame = tk.Frame(root, bg="#020617")
        self.login_frame.pack(expand=True, fill="both")
        
        center_f = tk.Frame(self.login_frame, bg="#0f172a", padx=40, pady=40, highlightbackground="#2dd4bf", highlightthickness=1)
        center_f.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(center_f, text="MT FITNESS PRO", font=("Exo 2", 36, "bold"), fg="#2dd4bf", bg="#0f172a").pack()
        tk.Label(center_f, text="ACCESO RESTRINGIDO - AGENTE MAESTRO", font=("Segoe UI", 11), fg="#94a3b8", bg="#0f172a").pack(pady=(0,25))
        
        tk.Label(center_f, text="INTRODUCIR CLAVE DE MANDO", fg="white", bg="#0f172a", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.pw_entry = tk.Entry(center_f, show="*", font=("Arial", 18), bg="#1e293b", fg="white", borderwidth=0, insertbackground="white", width=25)
        self.pw_entry.pack(pady=10, ipady=5)
        self.pw_entry.focus_set()
        self.pw_entry.bind("<Return>", lambda e: self.check_login())
        
        tk.Button(center_f, text="IDENTIFICAR Y ENTRAR", command=self.check_login, bg="#2dd4bf", fg="#020617", font=("Segoe UI", 12, "bold"), 
                  padx=30, pady=12, border=0, cursor="hand2", activebackground="#5eead4").pack(pady=20, fill="x")

    def check_login(self):
        if self.pw_entry.get() == COACH_PASSWORD:
            # First things first: Get the fresh data
            self.download_cloud_data(silent=True)
            self.login_frame.destroy()
            self.setup_main_ui()
        else:
            messagebox.showerror("ACCESO DENEGADO", "Identificación Incorrecta.")

    def get_db(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def download_cloud_data(self, silent=False):
        try:
            url = "https://mt-fitness-pro.onrender.com/api/master/download_db"
            r = requests.post(url, data={'master_token': COACH_PASSWORD}, timeout=30)
            if r.status_code == 200:
                with open(DB_PATH, 'wb') as f:
                    f.write(r.content)
                if not silent:
                    messagebox.showinfo("☁️ DESCARGA ÉXITO", "Base de Datos ACTUALIZADA desde la NUBE.\n\nYa tienes los últimos pesos y medidas de tus atletas.")
                return True
            else:
                if not silent: messagebox.showwarning("☁️ ALERTA", "No se pudo bajar el backup. Trabajando en modo LOCAL.")
        except Exception as e:
            if not silent: messagebox.showerror("☁️ ERROR", f"Fallo al conectar con Cloud: {e}")
        return False

    def setup_main_ui(self):
        self.main_container = tk.Frame(self.root, bg="#020617")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # --- LATERAL: SEARCH & LIST ---
        sidebar = tk.Frame(self.main_container, bg="#0f172a", width=300)
        sidebar.pack(side="left", fill="y", padx=(0, 20))
        
        tk.Label(sidebar, text="BASE DE ATLETAS", font=("Segoe UI", 14, "bold"), fg="#2dd4bf", bg="#0f172a", pady=20).pack()
        
        self.search_u = tk.Entry(sidebar, bg="#1e293b", fg="white", borderwidth=0, font=("Segoe UI", 11), insertbackground="white")
        self.search_u.pack(fill="x", padx=15, pady=(0, 10), ipady=5)
        self.search_u.insert(0, " 🔍 Buscar Atleta...")
        self.search_u.bind("<KeyRelease>", self.filter_users)
        
        self.user_tree = ttk.Treeview(sidebar, columns=("Name"), show="headings", height=20)
        self.user_tree.heading("Name", text="Listado de Clientes")
        self.user_tree.pack(fill="both", expand=True, padx=15, pady=10)
        self.user_tree.bind("<<TreeviewSelect>>", self.on_user_select)

        # --- ÁREA CENTRAL ---
        workspace = tk.Frame(self.main_container, bg="#020617")
        workspace.pack(side="right", fill="both", expand=True)
        
        title_f = tk.Frame(workspace, bg="#020617")
        title_f.pack(fill="x", pady=(0, 15))
        self.client_title = tk.Label(title_f, text="SELECCIONA UN ATLETA PARA TRABAJAR", font=("Segoe UI", 18, "bold"), fg="white", bg="#020617")
        self.client_title.pack(side="left")
        
        self.notebook = ttk.Notebook(workspace)
        self.notebook.pack(fill="both", expand=True)
        
        self.diet_tab = tk.Frame(self.notebook, bg="#0f172a", padx=15, pady=15)
        self.work_tab = tk.Frame(self.notebook, bg="#0f172a", padx=15, pady=15)
        self.system_tab = tk.Frame(self.notebook, bg="#0f172a", padx=15, pady=15)
        
        self.notebook.add(self.diet_tab, text="🍏 NUTRICIÓN INTEL")
        self.notebook.add(self.work_tab, text="⚔️ RUTINA TÁCTICA")
        self.notebook.add(self.system_tab, text="🛰️ CONTROL DE SATÉLITE")
        
        self.setup_diet_ui()
        self.setup_work_ui()
        self.setup_system_ui()
        
        self.load_users()

    def load_users(self, filter_text=""):
        conn = self.get_db()
        q = "SELECT id, name FROM users WHERE role = 'CLIENT'"
        if filter_text and filter_text != " 🔍 Buscar Atleta...":
            q += f" AND name LIKE '%{filter_text}%'"
        users = conn.execute(q).fetchall()
        for i in self.user_tree.get_children(): self.user_tree.delete(i)
        for u in users:
            self.user_tree.insert("", "end", iid=u['id'], values=(u['name'],))
        conn.close()

    def filter_users(self, e):
        self.load_users(self.search_u.get())

    def on_user_select(self, e):
        sel = self.user_tree.selection()
        if not sel: return
        self.current_user_id = sel[0]
        name = self.user_tree.item(self.current_user_id)['values'][0]
        self.client_title.config(text=f"MODO EDICIÓN: {name.upper()}")
        self.refresh_all()

    # --- NUTRICIÓN UI ---
    def setup_diet_ui(self):
        ctrl = tk.Frame(self.diet_tab, bg="#1e293b", pady=10, padx=15)
        ctrl.pack(fill="x", pady=(0, 10))
        
        tk.Button(ctrl, text="+ AÑADIR ALIMENTO AL PLAN", bg="#2dd4bf", fg="#020617", font=("Segoe UI", 10, "bold"), 
                  padx=15, border=0, cursor="hand2", command=self.add_food_window).pack(side="left")
        
        self.diet_tree = ttk.Treeview(self.diet_tab, columns=("Meal", "Food", "Qty", "Kcal", "Macros"), show="headings")
        self.diet_tree.heading("Meal", text="COMIDA")
        self.diet_tree.heading("Food", text="ALIMENTO")
        self.diet_tree.heading("Qty", text="CANTIDAD")
        self.diet_tree.heading("Kcal", text="KCAL")
        self.diet_tree.heading("Macros", text="DISTRIBUCIÓN P/C/F")
        self.diet_tree.pack(fill="both", expand=True)
        
        tk.Button(self.diet_tab, text="X BORRAR SELECCIÓN", bg="#f43f5e", fg="white", font=("Segoe UI", 9, "bold"), 
                  padx=10, border=0, command=self.delete_food).pack(anchor="e", pady=10)

    # --- RUTINA UI ---
    def setup_work_ui(self):
        ctrl = tk.Frame(self.work_tab, bg="#1e293b", pady=10, padx=15)
        ctrl.pack(fill="x", pady=(0, 10))
        
        tk.Button(ctrl, text="+ ASIGNAR EJERCICIO", bg="#2dd4bf", fg="#020617", font=("Segoe UI", 10, "bold"), 
                  padx=15, border=0, cursor="hand2", command=self.add_exercise_window).pack(side="left")
        
        self.work_tree = ttk.Treeview(self.work_tab, columns=("Day", "Ex", "Sets", "Reps", "Type", "Rest"), show="headings")
        self.work_tree.heading("Day", text="DÍA")
        self.work_tree.heading("Ex", text="EJERCICIO")
        self.work_tree.heading("Sets", text="SERIES")
        self.work_tree.heading("Reps", text="REPS")
        self.work_tree.heading("Type", text="TIPO")
        self.work_tree.heading("Rest", text="DESC.")
        self.work_tree.pack(fill="both", expand=True)

        tk.Button(self.work_tab, text="X ELIMINAR SELECCIÓN", bg="#f43f5e", fg="white", font=("Segoe UI", 9, "bold"), 
                  padx=10, border=0, command=self.delete_exercise).pack(anchor="e", pady=10)

    # --- SISTEMA UI ---
    def setup_system_ui(self):
        f = tk.Frame(self.system_tab, bg="#0f172a")
        f.pack(expand=True)
        
        tk.Label(f, text="CONEXIÓN SATELITAL RENDER", font=("Exo 2", 24, "bold"), fg="#2dd4bf", bg="#0f172a").pack(pady=20)
        tk.Label(f, text="Usa este protocolo para subir tu trabajo local a la App en directo.", fg="#94a3b8", bg="#0f172a").pack(pady=(0,30))
        
        self.btn_download = tk.Button(f, text="📥 RECUPERAR DATOS DE LA NUBE (BAJAR)", bg="#0ea5e9", fg="white", 
                                 font=("Segoe UI", 12, "bold"), padx=40, pady=15, border=0, cursor="hand2", command=self.download_cloud_data)
        self.btn_download.pack(pady=10)

        tk.Label(f, text="SIEMPRE 'Baja' los datos antes de empezar y 'Sube' al terminar.", fg="#94a3b8", bg="#0f172a", font=("Arial", 9, "italic")).pack()

        self.btn_sync = tk.Button(f, text="🛰️ SUBIR TRABAJO A LA NUBE (SINCRONIZAR)", bg="#2dd4bf", fg="#020617", 
                                 font=("Segoe UI", 12, "bold"), padx=40, pady=20, border=0, cursor="hand2", command=self.sync_logic)
        self.btn_sync.pack(pady=20)

    def refresh_all(self):
        if not self.current_user_id: return
        conn = self.get_db()
        
        # Dieta
        res = conn.execute("""
            SELECT uf.id, uf.meal_name, f.name, uf.grams, f.kcal, f.protein, f.carbs, f.fat 
            FROM user_foods uf JOIN foods f ON uf.food_id = f.id WHERE uf.user_id = ?
        """, (self.current_user_id,)).fetchall()
        for i in self.diet_tree.get_children(): self.diet_tree.delete(i)
        for r in res:
            kcal_t = int(r['kcal']*r['grams']/100)
            macros = f"P:{int(r['protein']*r['grams']/100)}g | C:{int(r['carbs']*r['grams']/100)}g | F:{int(r['fat']*r['grams']/100)}g"
            self.diet_tree.insert("", "end", iid=r['id'], values=(r['meal_name'], r['name'], f"{r['grams']}g", f"{kcal_t} kcal", macros))

        # Rutina
        res = conn.execute("""
            SELECT ue.id, ue.day_of_week, e.name, ue.sets, ue.reps, ue.set_type, ue.rest 
            FROM user_exercises ue JOIN exercises e ON ue.exercise_id = e.id WHERE ue.user_id = ?
        """, (self.current_user_id,)).fetchall()
        for i in self.work_tree.get_children(): self.work_tree.delete(i)
        for r in res:
            self.work_tree.insert("", "end", iid=r['id'], values=(r['day_of_week'], r['name'], r['sets'], r['reps'], r['set_type'], r['rest']))
        
        conn.close()

    # --- DIÁLOGOS DE ADICIÓN (LÓGICA REAL) ---
    def add_food_window(self):
        if not self.current_user_id: return
        win = tk.Toplevel(self.root)
        win.title("CATÁLOGO DE NUTRICIÓN - ASIGNAR")
        win.geometry("600x650")
        win.configure(bg="#020617")
        win.grab_set()

        f = tk.Frame(win, bg="#020617", padx=20, pady=20)
        f.pack(fill="both", expand=True)

        cat_f = tk.Frame(f, bg="#020617")
        cat_f.pack(fill="x", pady=5)
        
        tk.Label(cat_f, text="GRUPO NUTRICIONAL:", fg="#2dd4bf", bg="#020617", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.cat_v = ttk.Combobox(cat_f, values=["TODOS", "Carnes", "Pescados", "Huevos", "Lácteos", "Cereales/Arroces", "Frutas/Vegetales", "Grasas", "Otros"], state="readonly", width=18)
        self.cat_v.current(0)
        self.cat_v.pack(side="left", padx=10)
        self.cat_v.bind("<<ComboboxSelected>>", lambda e: update_l())

        tk.Label(f, text="BUSCAR POR NOMBRE:", fg="#2dd4bf", bg="#020617", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        s = tk.Entry(f, font=("Segoe UI", 12), bg="#1e293b", fg="white", borderwidth=0, insertbackground="white")
        s.pack(fill="x", pady=5, ipady=5)
        
        lbox = tk.Listbox(f, bg="#0f172a", fg="white", font=("Segoe UI", 11), borderwidth=0)
        lbox.pack(fill="both", expand=True, pady=10)
        
        def update_l(e=None):
            conn = sqlite3.connect("mtfitness.db")
            term = s.get().strip()
            cat = self.cat_v.get()
            
            q = "SELECT id, name, category FROM foods WHERE name LIKE ?"
            params = [f"%{term}%"]
            
            if cat != "TODOS":
                q += " AND category = ?"
                params.append(cat)
                
            res = conn.execute(q + " ORDER BY category, name LIMIT 500", params).fetchall()
            lbox.delete(0, tk.END)
            for r in res: lbox.insert(tk.END, f"[{r[2]}] {r[0]} - {r[1]}")
            conn.close()
        
        s.bind("<KeyRelease>", update_l)
        update_l() # Cargar todo al inicio

        tk.Label(f, text="COMIDA (P.EJ: DESAYUNO)", fg="white", bg="#020617").pack(anchor="w")
        m_e = tk.Entry(f, bg="#1e293b", fg="white", borderwidth=0); m_e.pack(fill="x", pady=5); m_e.insert(0, "Desayuno")
        tk.Label(f, text="GRAMOS O CANTIDAD:", fg="white", bg="#020617").pack(anchor="w")
        g_e = tk.Entry(f, bg="#1e293b", fg="white", borderwidth=0); g_e.pack(fill="x", pady=5); g_e.insert(0, "100")

        def save():
            if not lbox.curselection(): return
            f_id = lbox.get(lbox.curselection()[0]).split(" - ")[0]
            conn = self.get_db()
            conn.execute("INSERT INTO user_foods (user_id, food_id, meal_name, grams) VALUES (?,?,?,?)", 
                         (self.current_user_id, f_id, m_e.get(), g_e.get()))
            conn.commit(); conn.close()
            self.refresh_all(); win.destroy()

        tk.Button(f, text="✅ ASIGNAR A DIETA", bg="#2dd4bf", fg="#020617", font=("Segoe UI", 11, "bold"), border=0, pady=10, command=save).pack(fill="x", pady=20)

    def add_exercise_window(self):
        if not self.current_user_id: return
        win = tk.Toplevel(self.root)
        win.title("CATÁLOGO DE ENTRENAMIENTO - ASIGNAR")
        win.geometry("600x700")
        win.configure(bg="#020617")
        win.grab_set()

        f = tk.Frame(win, bg="#020617", padx=20, pady=20)
        f.pack(fill="both", expand=True)

        tk.Label(f, text="BUSCAR EJERCICIO TÁCTICO:", fg="#2dd4bf", bg="#020617", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        s = tk.Entry(f, font=("Segoe UI", 12), bg="#1e293b", fg="white", borderwidth=0, insertbackground="white")
        s.pack(fill="x", pady=5, ipady=5)
        
        lbox = tk.Listbox(f, bg="#0f172a", fg="white", font=("Segoe UI", 10), borderwidth=0)
        lbox.pack(fill="both", expand=True, pady=10)
        
        def update_l(e=None):
            conn = self.get_db()
            it = conn.execute("SELECT id, name FROM exercises WHERE name LIKE ?", (f"%{s.get().replace(' 🔍 Buscar Ejercicio...', '')}%",)).fetchall()
            lbox.delete(0, tk.END)
            for i in it: lbox.insert(tk.END, f"{i[0]} - {i[1]}")
            conn.close()
        
        s.insert(0, " 🔍 Buscar Ejercicio...")
        s.bind("<FocusIn>", lambda e: s.delete(0, tk.END) if s.get() == " 🔍 Buscar Ejercicio..." else None)
        s.bind("<KeyRelease>", update_l)
        update_l() # Carga inicial inmediata

        # Inputs
        tk.Label(f, text="DÍA (P.EJ: LUNES):", fg="white", bg="#020617").pack(anchor="w")
        d_e = tk.Entry(f, bg="#1e293b", fg="white", borderwidth=0); d_e.pack(fill="x", pady=2); d_e.insert(0, "Lunes")
        tk.Label(f, text="SERIES:", fg="white", bg="#020617").pack(anchor="w")
        s_e = tk.Entry(f, bg="#1e293b", fg="white", borderwidth=0); s_e.pack(fill="x", pady=2); s_e.insert(0, "4")
        tk.Label(f, text="REPS (P.EJ: 12 O 10-12):", fg="white", bg="#020617").pack(anchor="w")
        r_e = tk.Entry(f, bg="#1e293b", fg="white", borderwidth=0); r_e.pack(fill="x", pady=2); r_e.insert(0, "12")
        tk.Label(f, text="DESCANSO (60S, 2MIN...):", fg="white", bg="#020617").pack(anchor="w")
        rs_e = tk.Entry(f, bg="#1e293b", fg="white", borderwidth=0); rs_e.pack(fill="x", pady=2); rs_e.insert(0, "60s")

        def save():
            if not lbox.curselection(): return
            ex_id = lbox.get(lbox.curselection()[0]).split(" - ")[0]
            conn = self.get_db()
            conn.execute("INSERT INTO user_exercises (user_id, exercise_id, day_of_week, sets, reps, rest) VALUES (?,?,?,?,?,?)", 
                         (self.current_user_id, ex_id, d_e.get(), s_e.get(), r_e.get(), rs_e.get()))
            conn.commit(); conn.close()
            self.refresh_all(); win.destroy()

        tk.Button(f, text="✅ ASIGNAR A RUTINA", bg="#2dd4bf", fg="#020617", font=("Segoe UI", 11, "bold"), border=0, pady=10, command=save).pack(fill="x", pady=15)

    def delete_food(self):
        sel = self.diet_tree.selection()
        if not sel: return
        conn = self.get_db()
        conn.execute("DELETE FROM user_foods WHERE id = ?", (sel[0],))
        conn.commit(); conn.close()
        self.refresh_all()

    def delete_exercise(self):
        sel = self.work_tree.selection()
        if not sel: return
        conn = self.get_db()
        conn.execute("DELETE FROM user_exercises WHERE id = ?", (sel[0],))
        conn.commit(); conn.close()
        self.refresh_all()

    def sync_logic(self):
        if not messagebox.askyesno("CONFIRMACIÓN TÁCTICA", "¿Deseas subir los cambios actuales a la nube de Render?"): return
        self.btn_sync.config(text="🛰️ SINCRONIZANDO... ESPERE", state="disabled", bg="#94a3b8")
        self.root.update()
        try:
            url = "https://mt-fitness-pro.onrender.com/api/master/upload_db"
            with open(DB_PATH, 'rb') as f:
                r = requests.post(url, files={'db': f}, data={'master_token': COACH_PASSWORD}, timeout=30)
            if r.status_code == 200:
                messagebox.showinfo("🛰️ SISTEMA", "SINCRONIZACIÓN EXITOSA.\n\nTus atletas ya tienen sus planes actualizados.")
            else:
                messagebox.showerror("🛰️ ERROR", f"Fallo en el enlace satelital: {r.status_code}")
        except Exception as e:
            messagebox.showerror("🛰️ ERROR FATAL", f"Desconexión del servidor: {e}")
        self.btn_sync.config(text="🛰️ INICIAR SINCRONIZACIÓN CLOUD", state="normal", bg="#2dd4bf")

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        messagebox.showerror("AGENTE", "Error: mtfitness.db no detectado. Colócala en esta carpeta.")
    else:
        root = tk.Tk()
        app = CoachMasterApp(root)
        root.mainloop()
