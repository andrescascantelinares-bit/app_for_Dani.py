import streamlit as st
import plotly.express as px
from datetime import datetime

# --- CONFIGURACIÓN DE SEGURIDAD AISAAC-SHIELD ---
FECHA_EXPIRACION = "2026-05-01" # Mayo 1ero del 2026
CODIGO_RENOVACION_MAESTRO = "GALLO-2026-TICO"

def verificar_licencia_temporal():
    # 1. Revisar si ya expiró por fecha
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    
    if fecha_actual > FECHA_EXPIRACION:
        st.error("⚠️ SISTEMA BLOQUEADO: La licencia ha expirado.")
        st.info("Contacta a Andrés (Aisaac_surf) para tu código de renovación.")
        
        # Pedir código de renovación
        intento = st.text_input("Ingresa Código de Renovación:", type="password")
        if st.button("Renovar"):
            if intento == CODIGO_RENOVACION_MAESTRO:
                st.success("✅ ¡Licencia renovada! Buen viaje.")
                # Aquí podrías guardar esto en la DB para que no pida más
                return True
            else:
                st.error("Código inválido.")
        return False
    return True

# --- INICIO DE LA APP ---
if verificar_licencia_temporal():
    st.sidebar.success("🛡️ Aisaac-Shield: Activo")
    # ... aquí sigue el resto de tu código de viajes y gastos ...

import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io

# --- CONFIGURACIÓN DE BASE DE DATOS ---
def crear_db():
    conn = sqlite3.connect('logistica_primo.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS viajes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, cliente TEXT, origen TEXT, destino TEXT, monto REAL, notas TEXT)''')
    # Añadimos columna 'foto' para guardar la imagen en formato BLOB
    c.execute('''CREATE TABLE IF NOT EXISTS gastos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, concepto TEXT, monto REAL, foto BLOB)''')
    conn.commit()
    conn.close()

def guardar_gasto(fecha, concepto, monto, foto_bytes):
    conn = sqlite3.connect('logistica_primo.db')
    c = conn.cursor()
    c.execute("INSERT INTO gastos (fecha, concepto, monto, foto) VALUES (?,?,?,?)", (fecha, concepto, monto, foto_bytes))
    conn.commit()
    conn.close()

# --- INTERFAZ ---
crear_db()
st.set_page_config(page_title="Aisaac_surf Logistics", layout="centered")

tab1, tab2, tab3 = st.tabs(["➕ Viajes", "📉 Gastos con Foto", "📊 Resumen"])

with tab2:
    st.header("Registrar Gasto")
    with st.form("form_gasto", clear_on_submit=True):
        f_g = st.date_input("Fecha", datetime.now())
        concep = st.selectbox("Concepto", ["Diesel", "Peaje", "Mantenimiento", "Comida", "Otros"])
        mon_g = st.number_input("Monto (CRC)", min_value=0, step=1000)
        
        st.write("📷 Tomar foto del tiquete/factura:")
        img_file = st.camera_input("Capturar factura")
        
        if st.form_submit_button("Guardar Gasto y Foto"):
            foto_bin = img_file.getvalue() if img_file else None
            guardar_gasto(f_g.strftime("%Y-%m-%d"), concep, mon_g, foto_bin)
            st.success(f"Gasto de {concep} guardado con éxito.")

# --- 1. FUNCIÓN PARA ELIMINAR (Pégala antes del with tab3) ---
def eliminar_gasto_db(id_gasto):
    conn = sqlite3.connect('logistica_primo.db')
    c = conn.cursor()
    c.execute("DELETE FROM gastos WHERE id = ?", (id_gasto,))
    conn.commit()
    conn.close()

# --- 2. REEMPLAZA DESDE LA LÍNEA 80 EN ADELANTE CON ESTO ---
with tab3: 
    st.header("Estado de Cuenta")
    conn = sqlite3.connect('logistica_primo.db')
    df_v = pd.read_sql_query("SELECT * FROM viajes", conn)
    df_g = pd.read_sql_query("SELECT * FROM gastos", conn)
    conn.close()

    if not df_g.empty:
        st.subheader("Análisis de Gastos")
        df_resumen = df_g.groupby("concepto")["monto"].sum().reset_index()
        
        fig = px.pie(df_resumen, 
                 values='monto', 
                 names='concepto', 
                 hole=0.5, 
                 color_discrete_sequence=['#002B7F', '#CE1126', '#F1C40F', '#7F8C8D']) 

        fig.update_layout(showlegend=True, margin=dict(t=30, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider() 
    col1, col2, col3 = st.columns(3)
    
    total_fletes = df_v['monto'].sum() if not df_v.empty else 0
    total_gastos = df_g['monto'].sum() if not df_g.empty else 0
    ganancia_neta = total_fletes - total_gastos

    with col1:
        st.metric("Total Fletes", f"₡{total_fletes:,.0f}")
    with col2:
        st.metric("Total Gastos", f"₡{total_gastos:,.0f}", delta=f"-₡{total_gastos:,.0f}", delta_color="inverse")
    with col3:
        st.metric("Ganancia Neta", f"₡{ganancia_neta:,.0f}", delta=f"₡{ganancia_neta:,.0f}")

    if not df_g.empty:
        st.subheader("Evidencia de Gastos")
        for index, row in df_g.iterrows():
            # Título del expansor
            with st.expander(f"📅 {row['fecha']} — {row['concepto']} (₡{row['monto']:,.0f})"):
                if row['foto']:
                    st.image(row['foto'], caption=f"Factura de {row['concepto']}")
                else:
                    st.info("No hay foto adjunta.")
                
                st.divider()
                # Botón de borrar con confirmación
                borrar_pop = st.popover("🗑️ Borrar este gasto", use_container_width=True)
                borrar_pop.warning("¿Estás seguro de eliminar este registro?")
                if borrar_pop.button("Confirmar Eliminación", key=f"del_{row['id']}", type="primary"):
                    eliminar_gasto_db(row['id'])
                    st.rerun() # Refresca para actualizar gráfico y métricas
    else:
        st.info("No hay gastos registrados todavía.")