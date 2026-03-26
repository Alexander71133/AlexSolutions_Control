import customtkinter as ctk
import pandas as pd
import os
import json
from datetime import datetime
from tkinter import messagebox
from fpdf import FPDF

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AppAlexSolutionsUltra(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AlexSolutions - Control de viaje")
        self.geometry("1150x850")
        
        self.folder_reportes = "REPORTES_2026"
        self.archivo_historico = "historico_ventas.xlsx"
        if not os.path.exists(self.folder_reportes): os.makedirs(self.folder_reportes)

        self.archivo_pendientes = "datos_ruta_activa.json"
        self.dict_productos = self.cargar_productos_con_precios()
        self.lista_nombres = list(self.dict_productos.keys())
        self.carga_actual = {} 
        
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        self.verificar_ruta_activa()

    def cargar_productos_con_precios(self):
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

    def verificar_ruta_activa(self):
        if os.path.exists(self.archivo_pendientes):
            if messagebox.askyesno("Ruta Detectada", "¿Deseas liquidar la carga pendiente?"):
                with open(self.archivo_pendientes, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.carga_actual = {item['Producto']: item for item in data}
                self.pantalla_liquidacion_aleatoria()
                return
        self.pantalla_seleccion()

    def limpiar_frame(self):
        for widget in self.main_frame.winfo_children(): widget.destroy()

    # --- PANTALLA DE SELECCIÓN (REGISTRO DE SALIDA) ---
    def detectar_cambio_producto(self, *args):
        seleccion = self.combo_prod.get().upper().strip()
        if seleccion in self.dict_productos:
            precio = self.dict_productos[seleccion]
            self.ent_pre.delete(0, 'end')
            self.ent_pre.insert(0, f"{precio:.0f}")

    def filtrar_productos(self, event):
        busqueda = self.combo_prod.get().upper()
        if event.keysym == "Return":
            self.ent_can.focus()
            return
        filtrados = [p for p in self.lista_nombres if busqueda in p]
        self.combo_prod.configure(values=filtrados)

    def pantalla_seleccion(self):
        self.limpiar_frame()
        self.carga_actual = {}
        
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.pack(fill="x")
        
        ctk.CTkLabel(header, text="REGISTRO DE SALIDA", font=("Roboto", 24, "bold")).pack(side="left", padx=20, pady=10)
        ctk.CTkButton(header, text="VER HISTÓRICO MENSUAL", fg_color="#34495e", command=self.mostrar_estadisticas_mes).pack(side="right", padx=20)

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
        ctk.CTkButton(form, text="GENERAR PDF DE VIAJE", fg_color="#e5aa45", text_color="black", command=self.guardar_y_pdf).pack(pady=5)

        self.view_container = ctk.CTkFrame(content)
        self.view_container.pack(side="right", padx=20, pady=20, fill="both", expand=True)
        self.scroll_view = ctk.CTkScrollableFrame(self.view_container, label_text="Resumen de Carga Actual")
        self.scroll_view.pack(fill="both", expand=True)

    def agregar_item(self):
        p = self.combo_prod.get().upper().strip()
        try:
            pr = float(self.ent_pre.get())
            c = int(self.ent_can.get())
            if p == "": return
            self.carga_actual[p] = {
                "Producto": p, 
                "Precio_Unit": pr, 
                "Cant_Inicial": c, 
                "Liquidado": False, 
                "Fecha": datetime.now().strftime("%Y-%m-%d")
            }
            self.renderizar_lista_salida()
            self.ent_can.delete(0, 'end')
            self.combo_prod.set("")
            self.combo_prod.focus()
        except: messagebox.showerror("Error", "Datos inválidos")

    def renderizar_lista_salida(self):
        for w in self.scroll_view.winfo_children(): w.destroy()
        for nombre, datos in self.carga_actual.items():
            f = ctk.CTkFrame(self.scroll_view, fg_color="#2b2b2b")
            f.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(f, text=f"{nombre} | {datos['Cant_Inicial']} un.", anchor="w").pack(side="left", padx=10, pady=5)
            ctk.CTkButton(f, text="X", width=40, fg_color="#c0392b", command=lambda n=nombre: self.borrar_item_salida(n)).pack(side="right", padx=5)

    def borrar_item_salida(self, nombre):
        if nombre in self.carga_actual:
            del self.carga_actual[nombre]
            self.renderizar_lista_salida()

    def guardar_y_pdf(self):
        if not self.carga_actual: return
        with open(self.archivo_pendientes, "w", encoding="utf-8") as f:
            json.dump(list(self.carga_actual.values()), f)
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, 'Inventario de viaje "Alexsolution"', ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(100, 10, "Producto", 1); pdf.cell(40, 10, "Cant.", 1); pdf.cell(40, 10, "Precio", 1, ln=True)
        pdf.set_font("Arial", '', 11)
        for item in self.carga_actual.values():
            pdf.cell(100, 10, item['Producto'][:40], 1)
            pdf.cell(40, 10, f"{item['Cant_Inicial']}", 1)
            pdf.cell(40, 10, f"${item['Precio_Unit']:,.0f}", 1, ln=True)
        
        nombre_pdf = os.path.join(self.folder_reportes, f"Salida_{datetime.now().strftime('%H%M%S')}.pdf")
        pdf.output(nombre_pdf)
        os.startfile(nombre_pdf)
        self.destroy()

    # --- PANTALLA DE CUADRE FINAL (LIQUIDACIÓN) ---
    def pantalla_liquidacion_aleatoria(self):
        self.limpiar_frame()
        ctk.CTkLabel(self.main_frame, text="CUADRE FINAL DE CAJA", font=("Roboto", 24, "bold")).pack(pady=15)
        container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        container.pack(fill="both", expand=True)

        self.list_frame = ctk.CTkScrollableFrame(container, width=450, label_text="Productos en Ruta")
        self.list_frame.pack(side="left", padx=20, pady=20, fill="both")
        self.actualizar_lista_pendientes()

        self.liq_form = ctk.CTkFrame(container)
        self.liq_form.pack(side="right", padx=20, pady=20, fill="both", expand=True)
        self.prod_seleccionado = None
        ctk.CTkLabel(self.liq_form, text="Seleccione un producto a la izquierda", font=("Roboto", 16)).pack(pady=100)

    def actualizar_lista_pendientes(self):
        for widget in self.list_frame.winfo_children(): widget.destroy()
        for nombre, datos in self.carga_actual.items():
            color = "#27ae60" if datos.get('Liquidado') else "#2980b9"
            btn = ctk.CTkButton(self.list_frame, text=f"{nombre} {'[OK]' if datos.get('Liquidado') else ''}", 
                                fg_color=color, anchor="w", command=lambda n=nombre: self.cargar_formulario_liq(n))
            btn.pack(fill="x", pady=2, padx=5)

    def cargar_formulario_liq(self, nombre):
        for widget in self.liq_form.winfo_children(): widget.destroy()
        self.prod_seleccionado = nombre
        p = self.carga_actual[nombre]
        
        # Nombre del Producto
        ctk.CTkLabel(self.liq_form, text=nombre, font=("Roboto", 18, "bold"), text_color="#e5aa45").pack(pady=(20, 5))
        
        # REINTEGRO DEL DATO: CARGA INICIAL
        ctk.CTkLabel(self.liq_form, text=f"ENTREGADO: {p['Cant_Inicial']} UNIDADES", 
                    font=("Roboto", 16, "bold"), text_color="white").pack(pady=10)

        # Campos de entrada
        self.ev = ctk.CTkEntry(self.liq_form, placeholder_text="Vendidos", width=250, height=35)
        self.ev.pack(pady=5)
        self.ef = ctk.CTkEntry(self.liq_form, placeholder_text="Físico devuelto", width=250, height=35)
        self.ef.pack(pady=5)
        
        self.ev.bind("<Return>", lambda e: self.ef.focus())
        self.ef.bind("<Return>", lambda e: self.procesar_individual())
        
        ctk.CTkButton(self.liq_form, text="GUARDAR PRODUCTO", fg_color="#2980b9", command=self.procesar_individual).pack(pady=20)
        ctk.CTkButton(self.liq_form, text="FINALIZAR DÍA", fg_color="#d35400", command=self.mostrar_resumen_final).pack(side="bottom", pady=20)
        self.ev.focus()

    def procesar_individual(self):
        try:
            v, f = int(self.ev.get()), int(self.ef.get())
            p = self.carga_actual[self.prod_seleccionado]
            p.update({
                'Vendidos': v, 
                'Devuelto_Fisico': f, 
                'Venta_Total': v * p['Precio_Unit'], 
                'Diferencia': f - (p['Cant_Inicial'] - v), 
                'Liquidado': True, 
                'Mes': datetime.now().strftime("%Y-%m")
            })
            self.actualizar_lista_pendientes()
            for widget in self.liq_form.winfo_children(): widget.destroy()
            ctk.CTkLabel(self.liq_form, text="Seleccione el siguiente producto...", font=("Roboto", 14)).pack(pady=100)
        except: messagebox.showerror("Error", "Ingrese solo números enteros")

    def mostrar_resumen_final(self):
        # 1. Validación de seguridad: Verificar si faltan productos por liquidar
        pendientes = [n for n, d in self.carga_actual.items() if not d.get('Liquidado')]
        
        if pendientes:
            cantidad_faltante = len(pendientes)
            lista_faltante = ", ".join(pendientes[:3]) # Mostrar los primeros 3 nombres
            if cantidad_faltante > 3:
                lista_faltante += "..."
                
            messagebox.showwarning(
                "Productos Pendientes", 
                f"No puedes finalizar. Faltan {cantidad_faltante} productos por liquidar:\n\n{lista_faltante}"
            )
            return # Detiene la ejecución y no permite ver el resumen

        # 2. Si todo está liquidado, procede a mostrar el resumen (igual que antes)
        self.limpiar_frame()
        ctk.CTkLabel(self.main_frame, text="RESUMEN DE CUADRE", font=("Roboto", 26, "bold")).pack(pady=20)
        
        res_view = ctk.CTkScrollableFrame(self.main_frame, width=850, height=450)
        res_view.pack(pady=10)
        
        total_dia = sum(d['Venta_Total'] for d in self.carga_actual.values())
        
        for n, d in self.carga_actual.items():
            color = "#2ecc71" if d['Diferencia'] == 0 else "#e74c3c"
            txt = f"{n} | VENDIÓ: {d['Vendidos']} | FÍSICO: {d['Devuelto_Fisico']} | TOTAL: ${d['Venta_Total']:,.0f}"
            ctk.CTkLabel(res_view, text=txt, text_color=color, font=("Roboto", 13)).pack(pady=2, anchor="w")

        ctk.CTkLabel(self.main_frame, text=f"TOTAL A RECIBIR: ${total_dia:,.0f}", 
                    font=("Roboto", 30, "bold"), text_color="#2ecc71").pack(pady=20)
        
        ctk.CTkButton(self.main_frame, text="CERRAR Y GUARDAR HISTÓRICO", fg_color="#27ae60", 
                      height=40, font=("Roboto", 14, "bold"), command=self.finalizar_liquidacion).pack(pady=10)

    def finalizar_liquidacion(self):
        df_nuevo = pd.DataFrame(list(self.carga_actual.values()))
        nombre_xls = os.path.join(self.folder_reportes, f"Liquidacion_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx")
        df_nuevo.to_excel(nombre_xls, index=False)
        
        if os.path.exists(self.archivo_historico):
            df_hist = pd.read_excel(self.archivo_historico)
            df_final = pd.concat([df_hist, df_nuevo], ignore_index=True)
        else:
            df_final = df_nuevo
        df_final.to_excel(self.archivo_historico, index=False)
        
        if os.path.exists(self.archivo_pendientes): os.remove(self.archivo_pendientes)
        messagebox.showinfo("Éxito", "Día cerrado y guardado en histórico.")
        self.destroy()

    def mostrar_estadisticas_mes(self):
        if not os.path.exists(self.archivo_historico):
            messagebox.showwarning("Sin datos", "Aún no hay ventas en el histórico.")
            return
        df = pd.read_excel(self.archivo_historico)
        mes_actual = datetime.now().strftime("%Y-%m")
        df_mes = df[df['Mes'] == mes_actual]
        if df_mes.empty:
            messagebox.showinfo("Mes vacío", "No hay ventas este mes.")
            return
        resumen = df_mes.groupby('Producto').agg({'Vendidos': 'sum', 'Venta_Total': 'sum'}).reset_index()
        total_dinero = resumen['Venta_Total'].sum()
        win = ctk.CTkToplevel(self)
        win.title(f"Histórico {mes_actual}")
        win.geometry("750x650")
        ctk.CTkLabel(win, text=f"CONSOLIDADO MENSUAL: {mes_actual}", font=("Roboto", 20, "bold")).pack(pady=15)
        scroll = ctk.CTkScrollableFrame(win, width=700, height=450)
        scroll.pack(pady=10, padx=10)
        for i, row in resumen.iterrows():
            f = ctk.CTkFrame(scroll, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=f"{row['Producto']}", width=350, anchor="w").pack(side="left")
            ctk.CTkLabel(f, text=f"Total Cant: {row['Vendidos']}", width=120).pack(side="left")
            ctk.CTkLabel(f, text=f"${row['Venta_Total']:,.0f}", width=150, anchor="e", text_color="#2ecc71").pack(side="right")
        ctk.CTkLabel(win, text=f"VALOR TOTAL MES: ${total_dinero:,.0f}", font=("Roboto", 24, "bold"), text_color="#e5aa45").pack(pady=20)
        ctk.CTkButton(win, text="ABRIR EXCEL MAESTRO", command=lambda: os.startfile(self.archivo_historico)).pack(pady=5)

if __name__ == "__main__":
    AppAlexSolutionsUltra().mainloop()