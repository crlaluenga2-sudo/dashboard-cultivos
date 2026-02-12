import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- CONFIGURACIÓN DE LA PÁGINA (MOBILE FRIENDLY) ---
st.set_page_config(
    page_title="Dashboard Cultivos",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="collapsed" # La barra lateral empieza cerrada en móvil
)

# --- CSS PARA MÓVIL (QUITA MÁRGENES EXCESIVOS) ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        /* Ajuste para títulos más pequeños en móvil */
        h1 { font-size: 1.8rem !important; }
        h3 { font-size: 1.2rem !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🚜 Gestión de Cultivos")
st.markdown("---")

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

# --- 2. FILTROS ---
st.sidebar.header("🔍 Filtros")

opciones_ano = sorted(df['AÑO'].unique())
default_ano = ['2026'] if '2026' in opciones_ano else opciones_ano

filtro_ano = st.sidebar.multiselect("Año:", options=opciones_ano, default=default_ano)
filtro_red = st.sidebar.multiselect("Red de Riego:", options=sorted(df['RED DE RIEGO'].unique()), default=sorted(df['RED DE RIEGO'].unique()))
filtro_cultivo = st.sidebar.multiselect("Cultivo:", options=sorted(df['CULTIVO'].unique()), default=sorted(df['CULTIVO'].unique()))
filtro_doble = st.sidebar.multiselect("Doble Cosecha:", options=sorted(df['DOBLE COSECHA'].unique()), default=sorted(df['DOBLE COSECHA'].unique()))

df_filtered = df.query("`AÑO` == @filtro_ano & `RED DE RIEGO` == @filtro_red & `CULTIVO` == @filtro_cultivo & `DOBLE COSECHA` == @filtro_doble")

# --- 3. KPIs (Mejorados para móvil) ---
total_has = df_filtered['HAS'].sum()

# Usamos columnas, pero en móvil se apilarán bien
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Total Hectáreas", f"{total_has:,.2f}")
with c2:
    st.metric("Parcelas", df_filtered.shape[0])
with c3:
    st.metric("Cultivos", df_filtered['CULTIVO'].nunique())

st.markdown("---")

config_estatica = {'staticPlot': True}

# --- 4. GRÁFICOS (ADAPTADOS: LEYENDA ARRIBA) ---

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
    fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    
    # AJUSTE CLAVE PARA MÓVIL: Leyenda horizontal arriba para no quitar espacio lateral
    fig_bar.update_layout(
        uniformtext_minsize=8, 
        uniformtext_mode='hide', 
        margin=dict(t=30, l=10, r=10, b=10), # Márgenes mínimos
        xaxis_title=None,
        yaxis_title=None,
        legend=dict(
            orientation="h", # Horizontal
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=350 # Altura fija para que no sea enorme en móvil
    )
    st.plotly_chart(fig_bar, use_container_width=True, config=config_estatica)
else:
    st.warning("Sin datos.")

st.markdown("---")

# GRÁFICO 2: RED DE RIEGO (TARTA)
st.subheader("💧 Red de Riego")
if not df_filtered.empty:
    fig_pie = px.pie(
        df_filtered, 
        values="HAS", 
        names="RED DE RIEGO", 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    # Etiquetas dentro para ahorrar espacio
    fig_pie.update_traces(textinfo='percent+label', textposition='inside')
    fig_pie.update_layout(
        showlegend=False, 
        margin=dict(t=20, b=20, l=10, r=10),
        height=300
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
    fig_doble.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_doble.update_layout(
        margin=dict(t=30, l=10, r=10, b=10), 
        showlegend=False,
        xaxis_title=None,
        yaxis_title=None,
        height=300
    )
    st.plotly_chart(fig_doble, use_container_width=True, config=config_estatica)

# --- 6. TABLA DINÁMICA ---
st.markdown("---")
st.subheader("📊 Resumen")

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
            return 'background-color: #FFF59D; color: black; font-weight: bold; border: 2px solid #FBC02D'
        return ''

    def resaltar_fila_totales(row):
        if row.name == ('TOTALES', ''):
            return ['background-color: #ECEFF1; font-weight: bold; border-top: 2px solid #546E7A'] * len(row)
        return [''] * len(row)

    # Tabla responsive
    st.dataframe(
        pivot_final.style
        .format("{:,.2f}", na_rep="")
        .map(resaltar_total_cultivo, subset=['Total Cultivo'])
        .apply(resaltar_fila_totales, axis=1)
        .background_gradient(cmap="Blues", subset=pd.IndexSlice[pivot_final.index[:-1], pivot_final.columns[:-2]]),
        use_container_width=True # IMPORTANTE: Se adapta al ancho del móvil
    )
    
else:
    st.warning("No hay datos.")
