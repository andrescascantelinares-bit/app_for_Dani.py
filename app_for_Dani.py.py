import streamlit as st
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

with tab3:
    st.header("Estado de Cuenta")
    conn = sqlite3.connect('logistica_primo.db')
    df_g = pd.read_sql_query("SELECT * FROM gastos ORDER BY id DESC", conn)
    conn.close()

    if not df_g.empty:
        st.subheader("Evidencia de Gastos")
        for _, row in df_g.iterrows():
            with st.expander(f"{row['fecha']} - {row['concepto']} (₡{row['monto']:,.0f})"):
                if row['foto']:
                    st.image(row['foto'], caption=f"Factura de {row['concepto']}")
                else:
                    st.info("No se adjuntó foto para este gasto.")
    else:
        st.info("No hay gastos registrados.")

# (El resto del código de viajes y PDF se mantiene igual)