import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Dashboard Cultivos",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS PARA MÓVIL Y ESTILOS ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 5rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        h1 { font-size: 1.5rem !important; }
        h3 { font-size: 1.1rem !important; }
        .stExpander { border: 1px solid #ddd; border-radius: 5px; }
        /* Ajuste para que el botón se vea bien */
        div.stButton > button {
            width: 100%;
            border: 1px solid #ccc;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🚜 Gestión de Cultivos")

# --- 1. CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    archivo = 'datos.csv'
    try:
        df = pd.read_csv(archivo)
    except FileNotFoundError:
        st.error(f"⚠️ Falta el archivo '{archivo}' en GitHub.")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

    df.columns = df.columns.str.strip()
    
    # Limpieza de datos
    def clean_currency(x):
        if isinstance(x, str):
            return float(x.replace(',', '.').replace('"', ''))
        return float(x)
    
    if 'HAS' in df.columns:
        df['HAS'] = df['HAS'].apply(clean_currency)
    if 'AÑO' in df.columns:
        df['AÑO'] = df['AÑO'].astype(str)
    
    cols_texto = ['CULTIVO', 'RED DE RIEGO', 'DOBLE COSECHA']
    for col in cols_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()
            df[col] = df[col].replace({'NAN': 'SIN DEFINIR', 'NAM': 'SIN DEFINIR'})

    return df

df = cargar_datos()

if df is None:
    st.stop()

# --- 2. FILTROS (EN DESPLEGABLE PRINCIPAL) ---
with st.expander("🔍 PULSA AQUÍ PARA FILTRAR DATOS", expanded=False):
    st.markdown("Selecciona las opciones para filtrar los gráficos:")
    
    # Preparamos las opciones
    opciones_ano = sorted(df['AÑO'].unique())
    default_ano = ['2026'] if '2026' in opciones_ano else opciones_ano
    opciones_cultivo = sorted(df['CULTIVO'].unique())
    
    # --- GESTIÓN DEL BOTÓN "SELECCIONAR TODOS" ---
    # Inicializamos el estado si no existe (por defecto todos seleccionados)
    if 'cultivos_seleccionados' not in st.session_state:
        st.session_state.cultivos_seleccionados = opciones_cultivo
        
    # Función que se ejecuta al pulsar el botón
    def seleccionar_todos_cultivos():
        st.session_state.cultivos_seleccionados = opciones_cultivo

    # --- DISEÑO DE LOS FILTROS ---
    c_f1, c_f2 = st.columns(2)
    
    with c_f1:
        filtro_ano = st.multiselect("📅 Año:", options=opciones_ano, default=default_ano)
        filtro_red = st.multiselect("💧 Red de Riego:", options=sorted(df['RED DE RIEGO'].unique()), default=sorted(df['RED DE RIEGO'].unique()))
        
    with c_f2:
        # Botón para seleccionar todos (encima del selector de cultivos)
        st.button("✅ Seleccionar todos los cultivos", on_click=seleccionar_todos_cultivos)
        
        # El multiselect está vinculado a la variable de session_state 'cultivos_seleccionados'
        filtro_cultivo = st.multiselect(
            "🌾 Cultivo:", 
            options=opciones_cultivo, 
            key="cultivos_seleccionados" 
        )
        
        filtro_doble = st.multiselect("🔄 Doble Cosecha:", options=sorted(df['DOBLE COSECHA'].unique()), default=sorted(df['DOBLE COSECHA'].unique()))

# APLICAR FILTROS
# Nota: usamos la variable filtro_cultivo que viene del widget (que a su vez lee del session_state)
df_filtered = df.query("`AÑO` == @filtro_ano & `RED DE RIEGO` == @filtro_red & `CULTIVO` == @filtro_cultivo & `DOBLE COSECHA` == @filtro_doble")

st.markdown("---")

# --- 3. KPIs ---
total_has = df_filtered['HAS'].sum()

c1, c2, c3 = st.columns(3)
c1.metric("Has Totales", f"{total_has:,.0f}")
c2.metric("Parcelas", df_filtered.shape[0])
c3.metric("Cultivos", df_filtered['CULTIVO'].nunique())

st.markdown("---")

# CONFIGURACIÓN ESTÁTICA (Sin Zoom)
config_estatica = {'staticPlot': True}

# --- 4. GRÁFICOS ---

# GRÁFICO 1: CULTIVOS
st.subheader("📊 Hectáreas por Cultivo")
if not df_filtered.empty:
    df_agrupado = df_filtered.groupby(['CULTIVO', 'AÑO'])['HAS'].sum().reset_index()
    fig_bar = px.bar(
        df_agrupado, 
        x="CULTIVO", 
        y="HAS", 
        color="AÑO", 
        barmode="group",
        text="HAS",
        color_discrete_map={'2025': '#95a5a6', '2026': '#3498db'}
    )
    
    # Etiquetas grandes y negras
    fig_bar.update_traces(
        texttemplate='%{text:.1f}', 
        textposition='outside',
        textfont=dict(family="Arial Black", size=14, color="black"),
        cliponaxis=False
    )
    
    fig_bar.update_layout(
        uniformtext_minsize=8, 
        uniformtext_mode='hide', 
        margin=dict(t=40, l=0, r=0, b=0),
        xaxis_title=None,
        yaxis_title=None,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=350
    )
    st.plotly_chart(fig_bar, use_container_width=True, config=config_estatica)
else:
    st.info("Selecciona filtros para ver datos.")

st.markdown("---")

# GRÁFICO 2: RED DE RIEGO (TARTA MEJORADA)
st.subheader("💧 Red de Riego")
if not df_filtered.empty:
    fig_pie = px.pie(
        df_filtered, 
        values="HAS", 
        names="RED DE RIEGO", 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig_pie.update_traces(
        textinfo='percent+label', 
        textposition='inside',
        textfont=dict(
            family="Arial", 
            size=16,
            color="black",
            weight="bold"
        )
    )
    
    fig_pie.update_layout(
        showlegend=False, 
        margin=dict(t=20, b=20, l=0, r=0),
        height=350
    )
    st.plotly_chart(fig_pie, use_container_width=True, config=config_estatica)

st.markdown("---")

# GRÁFICO 3: DOBLE COSECHA
st.subheader("🔄 Doble Cosecha")
if not df_filtered.empty:
    df_doble = df_filtered.groupby('DOBLE COSECHA')['HAS'].sum().reset_index()
    fig_doble = px.bar(
        df_doble,
        x='DOBLE COSECHA',
        y='HAS',
        color='DOBLE COSECHA',
        text='HAS',
        color_discrete_sequence=['#e74c3c', '#2ecc71']
    )
    
    fig_doble.update_traces(
        texttemplate='%{text:.1f}', 
        textposition='outside',
        textfont=dict(family="Arial Black", size=14, color="black"),
        cliponaxis=False
    )

    fig_doble.update_layout(
        margin=dict(t=40, l=0, r=0, b=0), 
        showlegend=False,
        xaxis_title=None,
        yaxis_title=None,
        height=250
    )
    st.plotly_chart(fig_doble, use_container_width=True, config=config_estatica)

# --- 6. TABLA DINÁMICA ---
st.markdown("---")
st.subheader("📊 Tabla Resumen")

if not df_filtered.empty:
    pivot = pd.pivot_table(
        df_filtered, 
        values='HAS', 
        index=['CULTIVO', 'RED DE RIEGO'], 
        columns='AÑO', 
        aggfunc='sum', 
        fill_value=0
    )
    
    pivot['Total General'] = pivot.sum(axis=1)
    
    total_por_cultivo = pivot.groupby(level=0)['Total General'].sum()
    pivot['Total Cultivo'] = pivot.index.get_level_values(0).map(total_por_cultivo)
    
    is_not_last = pivot.index.get_level_values(0).duplicated(keep='last')
    pivot.loc[is_not_last, 'Total Cultivo'] = np.nan
    
    totals_row = pivot.sum(axis=0)
    totals_row.name = ('TOTALES', '') 
    
    pivot_final = pd.concat([pivot, totals_row.to_frame().T])
    
    def resaltar_total_cultivo(val):
        if pd.notnull(val) and val != "":
            return 'background-color: #FFF59D; color: black; font-weight: bold; border: 1px solid #FBC02D'
        return ''

    def resaltar_fila_totales(row):
        if row.name == ('TOTALES', ''):
            return ['background-color: #ECEFF1; font-weight: bold; border-top: 2px solid #546E7A'] * len(row)
        return [''] * len(row)

    st.dataframe(
        pivot_final.style
        .format("{:,.2f}", na_rep="")
        .map(resaltar_total_cultivo, subset=['Total Cultivo'])
        .apply(resaltar_fila_totales, axis=1)
        .background_gradient(cmap="Blues", subset=pd.IndexSlice[pivot_final.index[:-1], pivot_final.columns[:-2]]),
        use_container_width=True
    )
    
else:
    st.warning("No hay datos.")
