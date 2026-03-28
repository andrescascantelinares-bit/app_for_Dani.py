import streamlit as st
import plotly.express as px
import sqlite3
import pandas as pd
from datetime import datetime
import io

# --- 1. CONFIGURACIÓN DE APOYO TÉCNICO (Aisaac-Shield) ---
FECHA_SOPORTE = "2026-05-01" 

def mostrar_estado_soporte():
    fecha_actual = datetime.now().strftime("2026-5-1")
    with st.sidebar:
        st.markdown("### 🛡️ Aisaac-Shield")
        if fecha_actual > FECHA_SOPORTE:
            st.info("Soporte técnico: Finalizado")
            url_wa = "https://wa.me/5068XXX?text=Hola%20Andres!%20Necesito%20actualizar%20la%20app"
            st.link_button("📲 Contactar a Andrés", url_wa)
        else:
            st.success("Soporte técnico: Activo")
            st.caption(f"Vence el: {FECHA_SOPORTE}")

# --- 2. FUNCIONES DE BASE DE DATOS ---
def crear_db():
    conn = sqlite3.connect('logistica_primo.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS viajes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, cliente TEXT, origen TEXT, destino TEXT, monto REAL, notas TEXT)''')
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

def eliminar_gasto_db(id_gasto):
    conn = sqlite3.connect('logistica_primo.db')
    c = conn.cursor()
    c.execute("DELETE FROM gastos WHERE id = ?", (id_gasto,))
    conn.commit()
    conn.close()

# --- 3. CONFIGURACIÓN DE PÁGINA E INTERFAZ ---
st.set_page_config(page_title="Logística Primo", layout="centered")
crear_db()
mostrar_estado_soporte()

tab1, tab2, tab3 = st.tabs(["➕ Viajes", "📉 Gastos con Foto", "📊 Resumen"])

with tab1:
    st.header("Registrar Viaje")
    with st.form("form_viaje", clear_on_submit=True):
        f = st.date_input("Fecha", datetime.now())
        cli = st.text_input("Cliente")
        ori = st.text_input("Origen")
        des = st.text_input("Destino")
        mon = st.number_input("Monto Flete (CRC)", min_value=0, step=1000)
        not_v = st.text_area("Notas")
        if st.form_submit_button("Guardar Viaje"):
            conn = sqlite3.connect('logistica_primo.db')
            c = conn.cursor()
            c.execute("INSERT INTO viajes (fecha, cliente, origen, destino, monto, notas) VALUES (?,?,?,?,?,?)",
                      (f.strftime("%Y-%m-%d"), cli, ori, des, mon, not_v))
            conn.commit()
            conn.close()
            st.success("Viaje guardado.")

with tab2:
    st.header("Registrar Gasto")
    with st.form("form_gasto", clear_on_submit=True):
        f_g = st.date_input("Fecha Gasto", datetime.now())
        concep = st.selectbox("Concepto", ["Diesel", "Peaje", "Mantenimiento", "Comida", "Otros"])
        mon_g = st.number_input("Monto (CRC)", min_value=0, step=1000)
        img_file = st.camera_input("Capturar factura")
        if st.form_submit_button("Guardar Gasto"):
            foto_bin = img_file.getvalue() if img_file else None
            guardar_gasto(f_g.strftime("%Y-%m-%d"), concep, mon_g, foto_bin)
            st.success("Gasto guardado.")

with tab3:
    st.header("📊 Resumen y Excel")
    conn = sqlite3.connect('logistica_primo.db')
    df_v = pd.read_sql_query("SELECT * FROM viajes", conn)
    df_g = pd.read_sql_query("SELECT * FROM gastos", conn)
    conn.close()

    if not df_v.empty or not df_g.empty:
        df_v['fecha'] = pd.to_datetime(df_v['fecha'])
        df_g['fecha'] = pd.to_datetime(df_g['fecha'])
        
        # Filtros de mes y año
        años = sorted(df_g['fecha'].dt.year.unique(), reverse=True) if not df_g.empty else [datetime.now().year]
        col1, col2 = st.columns(2)
        a_sel = col1.selectbox("Año", años)
        m_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        m_sel_nom = col2.selectbox("Mes", m_nombres, index=datetime.now().month - 1)
        m_sel = m_nombres.index(m_sel_nom) + 1

        df_v_f = df_v[(df_v['fecha'].dt.year == a_sel) & (df_v['fecha'].dt.month == m_sel)]
        df_g_f = df_g[(df_g['fecha'].dt.year == a_sel) & (df_g['fecha'].dt.month == m_sel)]

        # Métricas
        t_v = df_v_f['monto'].sum()
        t_g = df_g_f['monto'].sum()
        st.metric("Ganancia Neta", f"₡{t_v - t_g:,.0f}", delta=f"Fletes: ₡{t_v:,.0f}")

        # --- BOTÓN DE EXCEL ---
        st.divider()
        if not df_g_f.empty:
            csv = df_g_f.drop(columns=['foto']).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Gastos para Excel", csv, f"gastos_{m_sel_nom}.csv", "text/csv")
            
            # Gráfico
            fig = px.pie(df_g_f, values='monto', names='concepto', hole=0.4, title="Distribución de Gastos")
            st.plotly_chart(fig)

        # Lista de gastos para borrar
        for _, row in df_g_f.iterrows():
            with st.expander(f"{row['concepto']} - ₡{row['monto']:,.0f}"):
                if row['foto']: st.image(row['foto'])
                if st.button("Eliminar", key=f"del_{row['id']}"):
                    eliminar_gasto_db(row['id'])
                    st.rerun()
    else:
        st.info("Sin datos registrados.")