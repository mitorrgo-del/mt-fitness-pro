import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json

class AnalyticsAgentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MT ANALYTICS MASTER v1.0")
        self.root.geometry("800x600")
        self.root.configure(bg="#020617")
        
        self.setup_ui()
        self.refresh_stats()
        
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#0f172a", height=80)
        header.pack(fill="x")
        tk.Label(header, text="PANEL DE TRÁFICO EN VIVO: MT FITNESS PRO", fg="#2dd4bf", bg="#0f172a", font=("Outfit", 16, "bold")).pack(pady=20)
        
        main_f = tk.Frame(self.root, bg="#020617", padx=30, pady=30)
        main_f.pack(fill="both", expand=True)
        
        # Summary Row
        summary_f = tk.Frame(main_f, bg="#020617")
        summary_f.pack(fill="x", pady=20)
        
        self.total_label = tk.Label(summary_f, text="Visitas Totales: ...", fg="white", bg="#020617", font=("Segoe UI", 14, "bold"))
        self.total_label.pack(side="left")
        
        tk.Button(summary_f, text="RECARGAR DATOS", bg="#2dd4bf", fg="#020617", command=self.refresh_stats).pack(side="right")
        
        # Table / Chart Placeholder
        tk.Label(main_f, text="VISITAS POR PAÍS", fg="#2dd4bf", bg="#020617", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        
        self.tree = ttk.Treeview(main_f, columns=("Pais", "Visitas"), show="headings", height=10)
        self.tree.heading("Pais", text="País / Región")
        self.tree.heading("Visitas", text="Número de Atletas")
        self.tree.pack(fill="both", expand=True, pady=10)
        
        # Styling Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#1e293b", foreground="white", fieldbackground="#1e293b", borderwidth=0)
        style.configure("Treeview.Heading", background="#0f172a", foreground="#2dd4bf", borderwidth=0)

    def refresh_stats(self):
        try:
            # Connect to Render API
            res = requests.get("https://mt-fitness-pro.onrender.com/api/get_stats", timeout=5)
            if res.status_code == 200:
                data = res.json()
                self.total_label.config(text=f"Visitas Totales: {data['total_visits']}")
                
                # Clear tree
                for i in self.tree.get_children():
                    self.tree.delete(i)
                
                # Fill tree
                for c in data['countries']:
                    self.tree.insert("", "end", values=(c['country'], c['count']))
            else:
                messagebox.showerror("Error", "No se pudo conectar con el servidor.")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo de conexión: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AnalyticsAgentApp(root)
    root.mainloop()
