import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json

class MarketingAgentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MT MARKETING AI COMMANDER v1.0")
        self.root.geometry("800x700")
        self.root.configure(bg="#020617")
        self.api_url = "https://mt-fitness-pro.onrender.com/api/generate_marketing"
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#0f172a", height=80)
        header.pack(fill="x")
        tk.Label(header, text="MÁQUINA DE CONTENIDO: MIGUEL TORRES PRO", fg="#2dd4bf", bg="#0f172a", font=("Outfit", 18, "bold")).pack(pady=20)
        
        main_f = tk.Frame(self.root, bg="#020617", padx=30, pady=20)
        main_f.pack(fill="both", expand=True)
        
        # Topic Input
        tk.Label(main_f, text="TEMA / IDEA (Ej: Ayuno intermitente, Ganar músculo):", fg="white", bg="#020617", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.topic_entry = tk.Entry(main_f, bg="#1e293b", fg="white", font=("Segoe UI", 11), borderwidth=0, insertbackground="white")
        self.topic_entry.pack(fill="x", pady=10, ipady=8)
        
        # Tools Row
        btn_f = tk.Frame(main_f, bg="#020617")
        btn_f.pack(fill="x", pady=10)
        
        tk.Button(btn_f, text="GENERAR ARTÍCULO PARA BLOG 📝", bg="#2dd4bf", fg="#020617", font=("Segoe UI", 10, "bold"), command=lambda: self.generate('blog')).pack(side="left", expand=True, fill="x", padx=5)
        tk.Button(btn_f, text="GENERAR POST INSTAGRAM 📱", bg="#f43f5e", fg="white", font=("Segoe UI", 10, "bold"), command=lambda: self.generate('instagram')).pack(side="left", expand=True, fill="x", padx=5)
        
        # Result Area
        tk.Label(main_f, text="RESULTADO GENERADO POR LA IA:", fg="#94a3b8", bg="#020617", font=("Segoe UI", 9)).pack(anchor="w", pady=10)
        self.result_text = tk.Text(main_f, bg="#1e293b", fg="white", font=("Segoe UI", 10), padx=15, pady=15, wrap="word", borderwidth=0)
        self.result_text.pack(fill="both", expand=True)
        
        # Actions
        act_f = tk.Frame(main_f, bg="#020617")
        act_f.pack(fill="x", pady=15)
        tk.Button(act_f, text="COPIAR AL PORTAPAPELES 📋", bg="#0f172a", fg="#2dd4bf", command=self.copy_to_clip).pack(side="right")

    def copy_to_clip(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.result_text.get("1.0", tk.END))
        messagebox.showinfo("OK", "¡Copiado con éxito!")

    def generate(self, mode):
        topic = self.topic_entry.get().strip()
        if not topic:
            messagebox.showwarning("Falta Tema", "Por favor escribe un tema pirimero.")
            return
            
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "Generando contenido con IA para Miguel Torres... Espera un momento.")
        self.root.update()
        
        try:
            res = requests.post(self.api_url, json={"topic": topic, "type": mode}, timeout=30)
            if res.status_code == 200:
                data = res.json()
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert(tk.END, data['content'])
            else:
                messagebox.showerror("Error", f"Fallo del servidor: {res.status_code}")
        except Exception as e:
            messagebox.showerror("Conexión", f"No se pudo conectar con la IA: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MarketingAgentApp(root)
    root.mainloop()
