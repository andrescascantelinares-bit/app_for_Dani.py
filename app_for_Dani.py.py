import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import base64

# --- INICIALIZAR SUPABASE ---
# Usamos st.secrets para mayor seguridad al subirlo a la nube
@st.cache_resource
def init_conexion():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_conexion()

# --- 1. CONFIGURACIÓN DE APOYO TÉCNICO (Aisaac-Shield) ---
FECHA_SOPORTE = "2026-05-01" 

def mostrar_estado_soporte():
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    with st.sidebar:
        st.markdown("### 🛡️ Aisaac-Shield")
        if fecha_actual > FECHA_SOPORTE:
            st.info("Soporte técnico: Finalizado")
            url_wa = "https://wa.me/5068XXX?text=Hola%20Andres!%20Necesito%20actualizar%20la%20app"
            st.link_button("📲 Contactar a Andrés", url_wa)
        else:
            st.success("Soporte técnico: Activo")
            st.caption(f"Vence el: {FECHA_SOPORTE}")

# --- 2. FUNCIONES DE BASE DE DATOS (NUBE) ---
def guardar_gasto(fecha, concepto, monto, foto_bytes):
    # Convertimos la imagen a texto (base64) para guardarla en la tabla de Supabase
    foto_b64 = base64.b64encode(foto_bytes).decode('utf-8') if foto_bytes else None
    
    datos = {
        "fecha": fecha,
        "concepto": concepto,
        "monto": monto,
        "foto": foto_b64
    }
    supabase.table("gastos").insert(datos).execute()

def eliminar_gasto_db(id_gasto):
    supabase.table("gastos").delete().eq("id", id_gasto).execute()

# --- 3. CONFIGURACIÓN DE PÁGINA E INTERFAZ ---
st.set_page_config(page_title="Logística Primo", layout="centered")
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
            # VALIDACIÓN DE DATOS PARA EL VIAJE
            if not cli.strip() or mon == 0:
                st.error("⚠️ ¡Epa! Te faltó poner el nombre del cliente o el monto está en cero. Revisá los datos.")
            else:
                datos_viaje = {
                    "fecha": f.strftime("%Y-%m-%d"),
                    "cliente": cli,
                    "origen": ori,
                    "destino": des,
                    "monto": mon,
                    "notas": not_v
                }
                supabase.table("viajes").insert(datos_viaje).execute()
                st.success("✅ Viaje guardado en la nube con éxito.")

with tab2:
    st.header("Registrar Gasto")
    with st.form("form_gasto", clear_on_submit=True):
        f_g = st.date_input("Fecha Gasto", datetime.now())
        concep = st.selectbox("Concepto", ["Diesel", "Peaje", "Mantenimiento", "Comida", "Otros"])
        mon_g = st.number_input("Monto (CRC)", min_value=0, step=1000)
        img_file = st.camera_input("Capturar factura")
        
        if st.form_submit_button("Guardar Gasto"):
            # VALIDACIÓN DE DATOS PARA EL GASTO
            if mon_g == 0:
                st.error("⚠️ El monto del gasto no puede estar en cero.")
            else:
                foto_bin = img_file.getvalue() if img_file else None
                guardar_gasto(f_g.strftime("%Y-%m-%d"), concep, mon_g, foto_bin)
                st.success("✅ Gasto guardado en la nube con éxito.")

with tab3:
    st.header("📊 Resumen y Excel")
    
    # Extraer datos de Supabase
    res_viajes = supabase.table("viajes").select("*").execute()
    res_gastos = supabase.table("gastos").select("*").execute()
    
    # Prevenir errores si la base de datos está vacía
    cols_v = ['id', 'fecha', 'cliente', 'origen', 'destino', 'monto', 'notas']
    cols_g = ['id', 'fecha', 'concepto', 'monto', 'foto']
    
    df_v = pd.DataFrame(res_viajes.data) if res_viajes.data else pd.DataFrame(columns=cols_v)
    df_g = pd.DataFrame(res_gastos.data) if res_gastos.data else pd.DataFrame(columns=cols_g)

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
            # Eliminamos la columna de la foto para que el Excel no quede gigante
            csv = df_g_f.drop(columns=['foto']).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Gastos para Excel", csv, f"gastos_{m_sel_nom}.csv", "text/csv")
            
            # Gráfico
            fig = px.pie(df_g_f, values='monto', names='concepto', hole=0.4, title="Distribución de Gastos")
            st.plotly_chart(fig)

        # Lista de gastos para borrar y ver fotos
        for _, row in df_g_f.iterrows():
            with st.expander(f"{row['concepto']} - ₡{row['monto']:,.0f}"):
                if row['foto']: 
                    # Decodificamos el texto de vuelta a imagen para mostrarla
                    st.image(base64.b64decode(row['foto']))
                if st.button("Eliminar", key=f"del_{row['id']}"):
                    eliminar_gasto_db(row['id'])
                    st.rerun()
    else:
        st.info("Sin datos registrados aún.")
