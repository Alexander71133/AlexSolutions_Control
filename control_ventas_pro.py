import customtkinter as ctk
import pandas as pd
import os
import json
from datetime import datetime
from tkinter import messagebox
from fpdf import FPDF

# Configuración visual
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AppControlViajes(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AlexSolutions - Control de Viajes Pro")
        self.geometry("1150x850")
        
        # Archivos y Carpetas
        self.folder_reportes = "REPORTES_2026"
        self.archivo_historico = "historico_ventas.xlsx"
        self.archivo_pendientes = "datos_ruta_activa.json"
        
        if not os.path.exists(self.folder_reportes): 
            os.makedirs(self.folder_reportes)

        self.dict_productos = self.cargar_productos_con_precios()
        self.lista_nombres = list(self.dict_productos.keys())
        self.carga_actual = {} 
        
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        self.verificar_estado_inicial()

    def cargar_productos_con_precios(self):
        """Carga precios desde productos.txt"""
        productos = {}
        if os.path.exists("productos.txt"):
            with open("productos.txt", "r", encoding="utf-8") as f:
                for linea in f:
                    linea = linea.strip()
                    if "," in linea:
                        partes = linea.rsplit(",", 1)
                        nombre = partes[0].strip().upper()
                        try:
                            precio_str = partes[1].replace(".", "").replace(" ", "").strip()
                            productos[nombre] = float(precio_str)
                        except: productos[nombre] = 0.0
        return productos

    def verificar_estado_inicial(self):
        """Menú inicial: Liquidar, Editar o Nuevo"""
        if os.path.exists(self.archivo_pendientes):
            dialogo = ctk.CTkToplevel(self)
            dialogo.title("Viaje Pendiente Detectado")
            dialogo.geometry("400x250")
            dialogo.grab_set()
            
            ctk.CTkLabel(dialogo, text="¿Qué deseas hacer con la ruta activa?", font=("Roboto", 16)).pack(pady=20)
            
            btn_f = ctk.CTkFrame(dialogo, fg_color="transparent")
            btn_f.pack(pady=10)

            def elegir(op):
                dialogo.destroy()
                if op == "LIQ":
                    self.cargar_datos_pendientes()
                    self.pantalla_liquidacion()
                elif op == "EDT":
                    self.cargar_datos_pendientes()
                    self.pantalla_registro()
                else:
                    if messagebox.askyesno("Confirmar", "¿Borrar viaje actual?"):
                        os.remove(self.archivo_pendientes)
                        self.pantalla_registro()
                    else: self.verificar_estado_inicial()

            ctk.CTkButton(btn_f, text="LIQUIDAR", fg_color="#27ae60", command=lambda: elegir("LIQ")).grid(row=0, column=0, padx=5)
            ctk.CTkButton(btn_f, text="EDITAR", fg_color="#2980b9", command=lambda: elegir("EDT")).grid(row=0, column=1, padx=5)
            ctk.CTkButton(btn_f, text="NUEVO", fg_color="#c0392b", command=lambda: elegir("NEW")).grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")
        else:
            self.pantalla_registro()

    def cargar_datos_pendientes(self):
        with open(self.archivo_pendientes, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.carga_actual = {item['Producto']: item for item in data}

    def limpiar_frame(self):
        for widget in self.main_frame.winfo_children(): widget.destroy()

    # --- PANTALLA REGISTRO ---
    def pantalla_registro(self):
        self.limpiar_frame()
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.pack(fill="x")
        ctk.CTkLabel(header, text="REGISTRO / EDICIÓN DE VIAJE", font=("Roboto", 24, "bold")).pack(side="left", padx=20, pady=10)

        content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content.pack(fill="both", expand=True)

        form = ctk.CTkFrame(content, width=350)
        form.pack(side="left", padx=20, pady=20, fill="y")

        ctk.CTkLabel(form, text="Producto:").pack(pady=(20,0))
        self.var_prod = ctk.StringVar()
        self.var_prod.trace_add("write", self.detectar_cambio_producto)
        self.combo_prod = ctk.CTkComboBox(form, values=self.lista_nombres, width=280, variable=self.var_prod)
        self.combo_prod.pack(pady=10)
        self.combo_prod.bind("<KeyRelease>", self.filtrar_productos)

        ctk.CTkLabel(form, text="Precio:").pack()
        self.ent_pre = ctk.CTkEntry(form, width=280)
        self.ent_pre.pack(pady=10)

        ctk.CTkLabel(form, text="Cantidad:").pack()
        self.ent_can = ctk.CTkEntry(form, width=280)
        self.ent_can.pack(pady=10)
        self.ent_can.bind("<Return>", lambda e: self.agregar_item())

        ctk.CTkButton(form, text="AÑADIR PRODUCTO", fg_color="#2fa572", command=self.agregar_item).pack(pady=20)
        ctk.CTkButton(form, text="GUARDAR Y PDF", fg_color="#e5aa45", text_color="black", command=self.guardar_y_pdf).pack(pady=5)

        self.scroll_view = ctk.CTkScrollableFrame(content, label_text="Resumen de Carga")
        self.scroll_view.pack(side="right", padx=20, pady=20, fill="both", expand=True)
        if self.carga_actual: self.renderizar_lista_salida()

    def agregar_item(self):
        p = self.combo_prod.get().upper().strip()
        try:
            pr = float(self.ent_pre.get())
            c = int(self.ent_can.get())
            if p == "": return
            self.carga_actual[p] = {"Producto": p, "Precio_Unit": pr, "Cant_Inicial": c, "Liquidado": False, "Fecha": datetime.now().strftime("%Y-%m-%d")}
            self.renderizar_lista_salida()
            self.ent_can.delete(0, 'end'); self.combo_prod.set(""); self.combo_prod.focus()
        except: messagebox.showerror("Error", "Datos inválidos")

    def renderizar_lista_salida(self):
        for w in self.scroll_view.winfo_children(): w.destroy()
        for n, d in self.carga_actual.items():
            f = ctk.CTkFrame(self.scroll_view, fg_color="#2b2b2b")
            f.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(f, text=f"{n} | {d['Cant_Inicial']} un.", anchor="w").pack(side="left", padx=10)
            ctk.CTkButton(f, text="X", width=40, fg_color="#c0392b", command=lambda x=n: self.borrar_item(x)).pack(side="right", padx=5)

    def borrar_item(self, n):
        del self.carga_actual[n]
        self.renderizar_lista_salida()

    def guardar_y_pdf(self):
        if not self.carga_actual: return
        with open(self.archivo_pendientes, "w", encoding="utf-8") as f:
            json.dump(list(self.carga_actual.values()), f)
        # Generación de PDF
        pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, 'Inventario de Salida - AlexSolutions', ln=True, align='C')
        pdf.ln(10); pdf.set_font("Arial", 'B', 12)
        pdf.cell(100, 10, "Producto", 1); pdf.cell(40, 10, "Cant.", 1); pdf.cell(40, 10, "Precio", 1, ln=True)
        pdf.set_font("Arial", '', 11)
        for item in self.carga_actual.values():
            pdf.cell(100, 10, item['Producto'][:40], 1); pdf.cell(40, 10, str(item['Cant_Inicial']), 1); pdf.cell(40, 10, f"{item['Precio_Unit']:,.0f}", 1, ln=True)
        n_pdf = os.path.join(self.folder_reportes, f"Salida_{datetime.now().strftime('%H%M%S')}.pdf")
        pdf.output(n_pdf); os.startfile(n_pdf); self.destroy()

    def detectar_cambio_producto(self, *args):
        s = self.combo_prod.get().upper().strip()
        if s in self.dict_productos:
            self.ent_pre.delete(0, 'end'); self.ent_pre.insert(0, f"{self.dict_productos[s]:.0f}")

    def filtrar_productos(self, event):
        b = self.combo_prod.get().upper()
        if event.keysym == "Return": self.ent_can.focus()
        else: self.combo_prod.configure(values=[p for p in self.lista_nombres if b in p])

    # --- PANTALLA LIQUIDACIÓN ---
    def pantalla_liquidacion(self):
        self.limpiar_frame()
        ctk.CTkLabel(self.main_frame, text="CUADRE FINAL DE CAJA", font=("Roboto", 24, "bold")).pack(pady=15)
        container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        container.pack(fill="both", expand=True)

        self.list_f = ctk.CTkScrollableFrame(container, width=450, label_text="Productos en Ruta")
        self.list_f.pack(side="left", padx=20, pady=20, fill="both")
        self.act_lista_liq()

        self.liq_form = ctk.CTkFrame(container)
        self.liq_form.pack(side="right", padx=20, pady=20, fill="both", expand=True)
        ctk.CTkLabel(self.liq_form, text="Seleccione un producto...").pack(pady=100)

    def act_lista_liq(self):
        for w in self.list_f.winfo_children(): w.destroy()
        for n, d in self.carga_actual.items():
            col = "#27ae60" if d.get('Liquidado') else "#2980b9"
            ctk.CTkButton(self.list_f, text=f"{n} {'[OK]' if d.get('Liquidado') else ''}", fg_color=col, anchor="w", 
                          command=lambda x=n: self.form_individual(x)).pack(fill="x", pady=2, padx=5)

    def form_individual(self, n):
        for w in self.liq_form.winfo_children(): w.destroy()
        self.sel = n; d = self.carga_actual[n]
        ctk.CTkLabel(self.liq_form, text=n, font=("Roboto", 18, "bold"), text_color="#e5aa45").pack(pady=20)
        ctk.CTkLabel(self.liq_form, text=f"ENTREGADO: {d['Cant_Inicial']} UNIDADES", font=("Roboto", 16, "bold")).pack(pady=10) #
        self.ev = ctk.CTkEntry(self.liq_form, placeholder_text="Vendidos", width=200); self.ev.pack(pady=5)
        self.ef = ctk.CTkEntry(self.liq_form, placeholder_text="Físico devuelto", width=200); self.ef.pack(pady=5)
        self.ev.bind("<Return>", lambda e: self.ef.focus())
        self.ef.bind("<Return>", lambda e: self.proc_ind())
        ctk.CTkButton(self.liq_form, text="GUARDAR PRODUCTO", fg_color="#27ae60", command=self.proc_ind).pack(pady=20)
        ctk.CTkButton(self.liq_form, text="FINALIZAR DÍA", fg_color="#d35400", command=self.resumen_final).pack(side="bottom", pady=20)
        self.ev.focus()

    def proc_ind(self):
        try:
            v, f = int(self.ev.get()), int(self.ef.get())
            p = self.carga_actual[self.sel]
            p.update({'Vendidos': v, 'Devuelto_Fisico': f, 'Venta_Total': v * p['Precio_Unit'], 
                      'Diferencia': f - (p['Cant_Inicial'] - v), 'Liquidado': True, 'Mes': datetime.now().strftime("%Y-%m")})
            self.act_lista_liq(); [w.destroy() for w in self.liq_form.winfo_children()]
            ctk.CTkLabel(self.liq_form, text="Seleccione el siguiente...").pack(pady=100)
        except: messagebox.showerror("Error", "Use números enteros")

    def resumen_final(self):
        pendientes = [n for n, d in self.carga_actual.items() if not d.get('Liquidado')]
        if pendientes:
            messagebox.showwarning("Faltan Productos", f"Aún quedan {len(pendientes)} ítems sin liquidar.")
            return
        self.limpiar_frame()
        ctk.CTkLabel(self.main_frame, text="RESUMEN DE CUADRE", font=("Roboto", 26, "bold")).pack(pady=20)
        rv = ctk.CTkScrollableFrame(self.main_frame, width=800, height=400); rv.pack(pady=10)
        total = sum(d['Venta_Total'] for d in self.carga_actual.values())
        for n, d in self.carga_actual.items():
            c = "#2ecc71" if d['Diferencia'] == 0 else "#e74c3c"
            ctk.CTkLabel(rv, text=f"{n} | VENDIÓ: {d['Vendidos']} | TOTAL: ${d['Venta_Total']:,.0f}", text_color=c).pack(anchor="w")
        ctk.CTkLabel(self.main_frame, text=f"TOTAL A RECIBIR: ${total:,.0f}", font=("Roboto", 28, "bold"), text_color="#2ecc71").pack(pady=20)
        ctk.CTkButton(self.main_frame, text="CERRAR DÍA Y GUARDAR HISTÓRICO", fg_color="#27ae60", command=self.finalizar).pack(pady=10)

    def finalizar(self):
        """Guardado con dos pestañas y reporte gráfico"""
        try:
            # Convertimos la carga actual a una lista para el DataFrame
            lista_datos = list(self.carga_actual.values())
            df_nuevo = pd.DataFrame(lista_datos)
            
            # Verificamos si hay datos antes de seguir
            if df_nuevo.empty:
                messagebox.showwarning("Atención", "No hay datos para guardar.")
                return

            # Cargar histórico si existe
            if os.path.exists(self.archivo_historico):
                try:
                    # Intentamos leer la pestaña de datos
                    df_hist = pd.read_excel(self.archivo_historico, sheet_name='Datos_Ventas')
                    df_final = pd.concat([df_hist, df_nuevo], ignore_index=True)
                except Exception:
                    # Si la pestaña no existe o el archivo está corrupto, empezamos de nuevo
                    df_final = df_nuevo
            else:
                df_final = df_nuevo

            # Generar el Top 10 para la pestaña de gráficos
            resumen_top = df_final.groupby('Producto').agg({
                'Vendidos': 'sum', 
                'Venta_Total': 'sum'
            }).sort_values(by='Vendidos', ascending=False).head(10)

            # --- OPERACIÓN DE GUARDADO CRÍTICA ---
            with pd.ExcelWriter(self.archivo_historico, engine='openpyxl') as writer:
                df_final.to_excel(writer, sheet_name='Datos_Ventas', index=False)
                resumen_top.to_excel(writer, sheet_name='Resumen_Grafico')
            
            # Si el guardado fue exitoso, borramos el JSON de la ruta activa
            if os.path.exists(self.archivo_pendientes):
                os.remove(self.archivo_pendientes)
            
            messagebox.showinfo("Éxito", "Día guardado correctamente en el histórico.")
            self.destroy() # Esto cierra la ventana del programa

        except PermissionError:
            messagebox.showerror("Archivo Abierto", 
                "No se pudo guardar. Por favor, CIERRA el archivo 'historico_ventas.xlsx' e intenta de nuevo.")
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al guardar: {e}")

if __name__ == "__main__":
    AppControlViajes().mainloop()
