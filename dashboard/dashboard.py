
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Configuración de página
st.set_page_config(
    page_title="RetailMax Dashboard",
    page_icon="📊",
    layout="wide"
)

# Conexión a base de datos
def get_db():
    conn = sqlite3.connect("../backend/retailmax.db")
    conn.row_factory = sqlite3.Row
    return conn

# Cargar datos
@st.cache_data(ttl=5)
def cargar_inventario():
    conn = get_db()
    df = pd.read_sql_query("""
        SELECT p.sku_id, p.descripcion, p.categoria, p.stock_minimo,
               i.cantidad_actual, i.fecha_actualizacion
        FROM productos p
        LEFT JOIN inventario_perpetuo i ON p.sku_id = i.sku_id AND i.tienda_id = 'TIENDA_001'
        ORDER BY p.categoria, p.descripcion
    """, conn)
    conn.close()
    return df

@st.cache_data(ttl=5)
def cargar_movimientos():
    conn = get_db()
    df = pd.read_sql_query("""
        SELECT m.*, p.descripcion
        FROM movimientos m
        LEFT JOIN productos p ON m.sku_id = p.sku_id
        ORDER BY m.fecha_hora DESC
        LIMIT 50
    """, conn)
    conn.close()
    return df

# Header
st.title("RetailMax - Dashboard Ejecutivo")
st.markdown("---")

# Métricas principales
df_inventario = cargar_inventario()

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_skus = len(df_inventario)
    st.metric("Total SKUs", total_skus)

with col2:
    stock_bajo = len(df_inventario[df_inventario['cantidad_actual'] < df_inventario['stock_minimo']])
    st.metric("Stock Bajo", stock_bajo, delta=f"{stock_bajo} productos")

with col3:
    stock_critico = len(df_inventario[df_inventario['cantidad_actual'] == 0])
    st.metric("Stock Crítico", stock_critico, delta=f"{stock_critico} productos")

with col4:
    df_movimientos = cargar_movimientos()
    conteos_hoy = len(df_movimientos[df_movimientos['fecha_hora'].str.startswith(datetime.now().strftime('%Y-%m-%d'))])
    st.metric("Conteos Hoy", conteos_hoy)

st.markdown("---")

# Tabs
tab1, tab2 = st.tabs(["Inventario", "Historial de Movimientos"])

with tab1:
    st.subheader("Inventario Actual")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        categoria_filtro = st.selectbox(
            "Filtrar por categoría",
            ["Todas"] + sorted(df_inventario['categoria'].unique().tolist())
        )
    
    with col2:
        estado_filtro = st.selectbox(
            "Filtrar por estado",
            ["Todos", "OK", "BAJO", "CRITICO"]
        )
    
    # Aplicar filtros
    df_filtrado = df_inventario.copy()
    
    if categoria_filtro != "Todas":
        df_filtrado = df_filtrado[df_filtrado['categoria'] == categoria_filtro]
    
    # Calcular estado
    df_filtrado['estado'] = df_filtrado.apply(
        lambda row: 'CRITICO' if row['cantidad_actual'] == 0 
                    else 'BAJO' if row['cantidad_actual'] < row['stock_minimo']
                    else 'OK',
        axis=1
    )
    
    if estado_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado['estado'] == estado_filtro]
    
    # Mostrar tabla
    st.dataframe(
        df_filtrado[['sku_id', 'descripcion', 'categoria', 'cantidad_actual', 'stock_minimo', 'estado']],
        use_container_width=True,
        hide_index=True
    )
    
    # Gráfico por categoría
    st.subheader("Stock por Categoría")
    stock_por_categoria = df_inventario.groupby('categoria')['cantidad_actual'].sum().reset_index()
    st.bar_chart(stock_por_categoria.set_index('categoria'))

with tab2:
    st.subheader("Últimos 50 Movimientos")
    
    if len(df_movimientos) > 0:
        st.dataframe(
            df_movimientos[['sku_id', 'descripcion', 'tipo', 'cantidad', 'fecha_hora', 'operador_id']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay movimientos registrados aún")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 12px;'>
        <p>RetailMax MVP - Sprint 1 | Dashboard v1.0.0</p>
        <p>Última actualización: {0}</p>
    </div>
    """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
    unsafe_allow_html=True
)

# Auto-refresh cada 60 segundos
st.markdown(
    """
    <script>
        setTimeout(function(){
            window.location.reload();
        }, 60000);
    </script>
    """,
    unsafe_allow_html=True
)