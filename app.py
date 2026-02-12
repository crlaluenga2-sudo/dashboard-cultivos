import streamlit as st
import pandas as pd
import plotly.express as px

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

# --- 6. TABLA DINÁMICA (NUEVO) ---
st.markdown("---")
st.subheader("📊 Tabla Dinámica de Resumen")

if not df_filtered.empty:
    # Creamos la tabla dinámica (pivot table)
    # Filas: Cultivo
    # Columnas: Año
    # Valores: Suma de Hectáreas
    pivot_table = pd.pivot_table(
        df_filtered, 
        values='HAS', 
        index=['CULTIVO', 'RED DE RIEGO'], # Agrupado por Cultivo y luego Red
        columns=['AÑO'], 
        aggfunc='sum', 
        fill_value=0
    )
    
    # Añadimos totales por fila y columna
    pivot_table['Total General'] = pivot_table.sum(axis=1)
    
    # Formateamos para que se vea bonito (2 decimales)
    st.dataframe(
        pivot_table.style.format("{:.2f}").background_gradient(cmap="Blues", axis=None),
        use_container_width=True
    )
    
    st.info("💡 Esta tabla muestra la suma de hectáreas desglosada por Cultivo y Red de Riego, comparando los años seleccionados.")

else:
    st.warning("No hay datos para generar la tabla dinámica.")
