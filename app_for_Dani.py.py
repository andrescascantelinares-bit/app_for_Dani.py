import streamlit as st
import plotly.express as px
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io

# --- CONFIGURACIÓN DE SEGURIDAD AISAAC-SHIELD ---
FECHA_EXPIRACION = "2026-05-01" 
CODIGO_RENOVACION_MAESTRO = "GALLO-2026-TICO"

def verificar_licencia_temporal():
    # 1. Configuración de vencimiento
    fecha_actual = datetime.now().strftime("2026-1-1")
    
    if fecha_actual > FECHA_EXPIRACION:
        st.error("⚠️ ACCESO RESTRINGIDO: Licencia Vencida")
        
        # Diseño para el cobro por SINPE
        st.markdown(f"""
        ### 🛡️ Renovación de Aisaac-Shield
        Para seguir registrando fletes y gastos, por favor renueva tu suscripción:
        * **Monto:** ₡10,000 (o el monto que acordaron)
        * **SINPE Móvil:** 85643342 (Andrés)
        """)
        
        # Botón de WhatsApp con mensaje automático
        mensaje_wa = "Hola Andrés! Ya te hice el Sinpe para renovar la app de los camiones. ¿Me pasas el código?"
        url_wa = f"https://wa.me/5068XXXXXXX?text={mensaje_wa.replace(' ', '%20')}"
        
        st.link_button("📲 Enviar Comprobante por WhatsApp", url_wa, type="primary")
        
        st.divider()
        
        # Espacio para meter el código que tú le des
        intento = st.text_input("Ingresa el Código de Renovación:", type="password", help="Andrés te dará este código tras el pago.")
        
        if st.button("🔓 Activar Sistema Now"):
            if intento == CODIGO_RENOVACION_MAESTRO:
                    st.success("✅ ¡Licencia validada! Ya puedes entrar.")
            return True
        else:
                # --- ESTO ES LO QUE VA EN EL ELSE ---
            st.error("❌ Código incorrecto o expirado.")
            st.toast("Verifica el pago con Andrés", icon="⚠️")
                
        
        return False # Mantiene la app bloqueada
    
    return True # La app funciona normal si no ha vencido
# --- FUNCIONES DE BASE DE DATOS (IMPORTANTE: Definirlas antes de la interfaz) ---

def crear_db():
    conn = sqlite3.connect('logistica_primo.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS viajes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, cliente TEXT, origen TEXT, destino TEXT, monto REAL, notas TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS gastos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, concepto TEXT, monto REAL, foto BLOB)''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_fecha_gastos ON gastos(fecha)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_fecha_viajes ON viajes(fecha)")
    conn.commit()
    conn.close()

def guardar_gasto(fecha, concepto, monto, foto_bytes):
    conn = sqlite3.connect('logistica_primo.db')
    c = conn.cursor()
    c.execute("INSERT INTO gastos (fecha, concepto, monto, foto) VALUES (?,?,?,?)", 
              (fecha, concepto, monto, foto_bytes))
    conn.commit()
    conn.close()

def eliminar_gasto_db(id_gasto):
    conn = sqlite3.connect('logistica_primo.db')
    c = conn.cursor()
    c.execute("DELETE FROM gastos WHERE id = ?", (id_gasto,))
    conn.commit()
    conn.close()

# --- INICIO DE LA APP ---
if verificar_licencia_temporal():
    crear_db()
    st.set_page_config(page_title="Aisaac_surf Logistics", layout="centered")
    st.sidebar.success("🛡️ Aisaac-Shield: Activo")

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
        st.header("📊 Estado de Cuenta")
        conn = sqlite3.connect('logistica_primo.db')
        df_v = pd.read_sql_query("SELECT * FROM viajes", conn)
        df_g = pd.read_sql_query("SELECT * FROM gastos", conn)
        conn.close()

        if not df_v.empty or not df_g.empty:
            df_v['fecha'] = pd.to_datetime(df_v['fecha'])
            df_g['fecha'] = pd.to_datetime(df_g['fecha'])

            st.subheader("🔍 Filtrar Período")
            col_año, col_mes = st.columns(2)
            with col_año:
                lista_años = sorted(df_g['fecha'].dt.year.unique(), reverse=True) if not df_g.empty else [datetime.now().year]
                año_sel = st.selectbox("Selecciona el Año", lista_años)
            with col_mes:
                meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                mes_sel_nombre = st.selectbox("Selecciona el Mes", meses_nombres, index=datetime.now().month - 1)
                mes_sel = meses_nombres.index(mes_sel_nombre) + 1

            df_v_f = df_v[(df_v['fecha'].dt.year == año_sel) & (df_v['fecha'].dt.month == mes_sel)]
            df_g_f = df_g[(df_g['fecha'].dt.year == año_sel) & (df_g['fecha'].dt.month == mes_sel)]

            if not df_g_f.empty:
                df_resumen = df_g_f.groupby("concepto")["monto"].sum().reset_index()
                fig = px.pie(df_resumen, values='monto', names='concepto', hole=0.5,
                             color_discrete_sequence=['#002B7F', '#CE1126', '#F1C40F', '#7F8C8D'])
                fig.update_layout(margin=dict(t=30, b=10, l=10, r=10))
                st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            c1, c2, c3 = st.columns(3)
            t_fletes = df_v_f['monto'].sum() if not df_v_f.empty else 0
            t_gastos = df_g_f['monto'].sum() if not df_g_f.empty else 0
            g_neta = t_fletes - t_gastos

            c1.metric("Fletes del Mes", f"₡{t_fletes:,.0f}")
            c2.metric("Gastos del Mes", f"₡{t_gastos:,.0f}", delta=f"-₡{t_gastos:,.0f}", delta_color="inverse")
            c3.metric("Ganancia Neta", f"₡{g_neta:,.0f}")

            if not df_g_f.empty:
                st.subheader("Evidencia del Mes")
                for _, row in df_g_f.iterrows():
                    with st.expander(f"📅 {row['fecha'].strftime('%d/%m')} - {row['concepto']} (₡{row['monto']:,.0f})"):
                        if row['foto']: st.image(row['foto'])
                        if st.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                            eliminar_gasto_db(row['id'])
                            st.rerun()
        else:
            st.info("No hay datos registrados aún.")