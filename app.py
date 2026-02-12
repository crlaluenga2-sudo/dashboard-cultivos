import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Dashboard Cultivos",
    page_icon="🚜",
    layout="wide"
)

st.title("🚜 Dashboard de Gestión de Cultivos")
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

# Filtro Año (2026 por defecto)
opciones_ano = sorted(df['AÑO'].unique())
default_ano = ['2026'] if '2026' in opciones_ano else opciones_ano

filtro_ano = st.sidebar.multiselect("Año:", options=opciones_ano, default=default_ano)
filtro_red = st.sidebar.multiselect("Red de Riego:", options=sorted(df['RED DE RIEGO'].unique()), default=sorted(df['RED DE RIEGO'].unique()))
filtro_cultivo = st.sidebar.multiselect("Cultivo:", options=sorted(df['CULTIVO'].unique()), default=sorted(df['CULTIVO'].unique()))
filtro_doble = st.sidebar.multiselect("Doble Cosecha:", options=sorted(df['DOBLE COSECHA'].unique()), default=sorted(df['DOBLE COSECHA'].unique()))

# APLICAR FILTROS
df_filtered = df.query("`AÑO` == @filtro_ano & `RED DE RIEGO` == @filtro_red & `CULTIVO` == @filtro_cultivo & `DOBLE COSECHA` == @filtro_doble")

# --- 3. KPIs ---
total_has = df_filtered['HAS'].sum()
c1, c2, c3 = st.columns(3)
c1.metric("Total Hectáreas", f"{total_has:,.2f} ha")
c2.metric("Nº de Parcelas", df_filtered.shape[0])
c3.metric("Cultivos", df_filtered['CULTIVO'].nunique())

st.markdown("---")

# CONFIGURACIÓN ESTÁTICA
config_estatica = {'staticPlot': True}

# --- 4. GRÁFICOS (FILA 1) ---
col1, col2 = st.columns(2)

# GRÁFICO 1: CULTIVOS
with col1:
    st.subheader("📊 Hectáreas por Cultivo y Año")
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
        fig_bar.update_layout(
            uniformtext_minsize=8, 
            uniformtext_mode='hide', 
            margin=dict(t=50),
            xaxis_title=None,
            yaxis_title="Hectáreas"
        )
        st.plotly_chart(fig_bar, use_container_width=True, config=config_estatica)
    else:
        st.warning("No hay datos visibles.")

# GRÁFICO 2: RED DE RIEGO (TARTA)
with col2:
    st.subheader("💧 Distribución por Red de Riego")
    if not df_filtered.empty:
        fig_pie = px.pie(
            df_filtered, 
            values="HAS", 
            names="RED DE RIEGO", 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_traces(textinfo='percent+label', textposition='outside')
        fig_pie.update_layout(showlegend=False, margin=dict(t=50, b=50))
        st.plotly_chart(fig_pie, use_container_width=True, config=config_estatica)

# --- 5. GRÁFICOS (FILA 2) ---
st.markdown("---")
st.subheader("🔄 Hectáreas con Doble Cosecha")

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
        margin=dict(t=50), 
        showlegend=False,
        xaxis_title="¿Tiene Doble Cosecha?",
        yaxis_title="Hectáreas"
    )
    st.plotly_chart(fig_doble, use_container_width=True, config=config_estatica)

# --- 6. TABLA DINÁMICA DE RESUMEN ---
st.markdown("---")
st.subheader("📊 Tabla Dinámica de Resumen")

if not df_filtered.empty:
    # 1. Crear Pivot Table
    pivot = pd.pivot_table(
        df_filtered, 
        values='HAS', 
        index=['CULTIVO', 'RED DE RIEGO'], 
        columns='AÑO', 
        aggfunc='sum', 
        fill_value=0
    )
    
    # 2. Total General por fila (suma de años)
    pivot['Total General'] = pivot.sum(axis=1)
    
    # 3. Calcular Total por CULTIVO
    total_por_cultivo = pivot.groupby(level=0)['Total General'].sum()
    pivot['Total Cultivo'] = pivot.index.get_level_values(0).map(total_por_cultivo)
    
    # 4. Limpieza: Dejar solo el valor en la última fila del grupo
    is_not_last = pivot.index.get_level_values(0).duplicated(keep='last')
    pivot.loc[is_not_last, 'Total Cultivo'] = np.nan
    
    # 5. Fila de TOTALES
    totals_row = pivot.sum(axis=0)
    totals_row.name = ('TOTALES', '') 
    
    # Unir
    pivot_final = pd.concat([pivot, totals_row.to_frame().T])
    
    # --- FUNCIONES DE ESTILO ---
    
    # Estilo para la columna 'Total Cultivo': Amarillo, Negrita y Borde
    def resaltar_total_cultivo(val):
        if pd.notnull(val) and val != "":
            return 'background-color: #FFF59D; color: black; font-weight: bold; border: 2px solid #FBC02D'
        return ''

    # Estilo para la fila 'TOTALES': Gris y Negrita
    def resaltar_fila_totales(row):
        if row.name == ('TOTALES', ''):
            return ['background-color: #ECEFF1; font-weight: bold; border-top: 2px solid #546E7A'] * len(row)
        return [''] * len(row)

    # 6. Mostrar con formato
    st.dataframe(
        pivot_final.style
        .format("{:,.2f}", na_rep="")
        .map(resaltar_total_cultivo, subset=['Total Cultivo']) # Aplica estilo a la columna clave
        .apply(resaltar_fila_totales, axis=1) # Aplica estilo a la fila final
        .background_gradient(cmap="Blues", subset=pd.IndexSlice[pivot_final.index[:-1], pivot_final.columns[:-2]]), # Degradado solo en los años
        use_container_width=True
    )
    
else:
    st.warning("No hay datos para generar la tabla.")
