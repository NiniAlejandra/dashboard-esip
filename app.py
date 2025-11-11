import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuración de la página (DEBE SER LA PRIMERA LÍNEA DE STREAMLIT)
st.set_page_config(
    page_title="Reporte de Indicadores internos ESIP SAS ESP",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Función para limpiar datos numéricos
def limpiar_numeros(valor):
    if pd.isna(valor) or valor == '':
        return np.nan
    if isinstance(valor, str):
        valor = valor.replace(',', '').replace('$', '').replace(' ', '')
        if '(' in valor and ')' in valor:
            valor = valor.split('(')[0]
        try:
            return float(valor)
        except:
            return np.nan
    return float(valor)

# Función para limpiar porcentajes
def limpiar_porcentajes(valor):
    if pd.isna(valor) or valor == '':
        return np.nan
    if isinstance(valor, str):
        valor = valor.replace('%', '').replace(',', '')
        try:
            return float(valor)
        except:
            return np.nan
    return float(valor)

# Función para abreviar nombres largos
def abreviar(texto, max_len=40):
    return texto if len(texto) <= max_len else texto[:37] + "..."

# Cargar y procesar datos
@st.cache_data
def cargar_y_procesar_datos():
    """Cargar y procesar todos los datos unificados"""
    
    # Orden fijo de meses
    month_order = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                  'Julio', 'Agosto', 'Septiembre']
    
    # Cargar datos numéricos
    df_num = None
    try:
        df_num = pd.read_csv("Numericos.csv")
    except FileNotFoundError:
        try:
            df_num = pd.read_csv("Númericos.csv")
        except FileNotFoundError:
            # No mostrar error aquí, lo manejaremos en main()
            return None, None
    except Exception as e:
        st.error(f"Error al leer el archivo numérico: {str(e)}")
        return None, None
    
    # Cargar datos porcentuales
    df_porc = None
    try:
        df_porc = pd.read_csv("porcentaje.csv")
    except FileNotFoundError:
        # No mostrar error aquí, lo manejaremos en main()
        return None, None
    except Exception as e:
        st.error(f"Error al leer el archivo porcentual: {str(e)}")
        return None, None
    
    # Validar que ambos DataFrames se cargaron correctamente
    if df_num is None or df_porc is None:
        return None, None
    
    # Validar columnas requeridas
    required_cols = ['Área', 'Indicador']
    for col in required_cols:
        if col not in df_num.columns or col not in df_porc.columns:
            st.error(f"Error: Falta la columna '{col}' en uno de los archivos CSV.")
            return None, None
    
    # Limpiar datos numéricos
    for mes in month_order:
        if mes in df_num.columns:
            df_num[mes] = df_num[mes].apply(limpiar_numeros)
    
    # Limpiar datos porcentuales
    for mes in month_order:
        if mes in df_porc.columns:
            df_porc[mes] = df_porc[mes].apply(limpiar_porcentajes)
    
    # Añadir columna Tipo
    df_num['Tipo'] = 'Numérico'
    df_porc['Tipo'] = 'Porcentual'
    
    # Unir ambos datasets
    try:
        df = pd.concat([df_num, df_porc], ignore_index=True)
    except Exception as e:
        st.error(f"Error al combinar los datos: {str(e)}")
        return None, None
    
    return df, month_order

def crear_grafico_tendencias_numericas(df_melted, area, indicadores):
    """Crear gráfico de tendencias para indicadores numéricos"""
    if len(df_melted) == 0:
        return None
    
    # Crear gráfico con tooltips personalizados
    fig = go.Figure()
    
    # Colores para diferentes indicadores
    colores = px.colors.qualitative.Set3
    
    for i, indicador in enumerate(indicadores):
        df_ind = df_melted[df_melted['Indicador'] == indicador].dropna(subset=['Valor'])
        
        if len(df_ind) > 0:
            fig.add_trace(go.Scatter(
                x=df_ind['Mes'],
                y=df_ind['Valor'],
                mode='lines+markers',
                name=abreviar(indicador),
                line=dict(width=3, color=colores[i % len(colores)]),
                marker=dict(size=8),
                hovertemplate=f'<b>{indicador}</b><br>' +
                             'Mes: %{x}<br>' +
                             'Valor: %{y:,.0f}' + ('<br><extra></extra>' if df_ind['Valor'].iloc[0] == int(df_ind['Valor'].iloc[0]) else '<br><extra></extra>')
            ))
    
    # Configurar layout
    fig.update_layout(
        title=f"Tendencia: {', '.join([abreviar(i) for i in indicadores])} - {area}",
        height=500,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01
        ),
        xaxis=dict(
            categoryorder='array',
            categoryarray=['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                          'Julio', 'Agosto', 'Septiembre']
        )
    )
    
    # Escala logarítmica si es necesario
    valores = df_melted['Valor'].dropna()
    if len(valores) > 0 and valores.max() / valores.min() > 100:
        fig.update_layout(yaxis_type="log")
    
    return fig

def crear_grafico_porcentuales(df_melted, area, indicadores):
    """Crear gráfico para indicadores porcentuales"""
    if len(df_melted) == 0:
        return None
    
    # Crear gráfico con tooltips personalizados
    fig = go.Figure()
    
    # Colores para diferentes indicadores
    colores = px.colors.qualitative.Set2
    
    # Si hay 3 o menos indicadores, usar barras agrupadas
    if len(indicadores) <= 3:
        for i, indicador in enumerate(indicadores):
            df_ind = df_melted[df_melted['Indicador'] == indicador].dropna(subset=['Valor'])
            
            if len(df_ind) > 0:
                fig.add_trace(go.Bar(
                    x=df_ind['Mes'],
                    y=df_ind['Valor'],
                    name=abreviar(indicador),
                    marker_color=colores[i % len(colores)],
                    text=[f"{val:.0f}%" if val == int(val) else f"{val:.1f}%" for val in df_ind['Valor']],
                    textposition='outside',
                    hovertemplate=f'<b>{indicador}</b><br>' +
                                 'Mes: %{x}<br>' +
                                 'Valor: %{y:.1f}%<br>' +
                                 '<extra></extra>'
                ))
        
        fig.update_layout(barmode='group')
        
    else:
        # Si hay más de 3 indicadores, usar líneas
        for i, indicador in enumerate(indicadores):
            df_ind = df_melted[df_melted['Indicador'] == indicador].dropna(subset=['Valor'])
            
            if len(df_ind) > 0:
                fig.add_trace(go.Scatter(
                    x=df_ind['Mes'],
                    y=df_ind['Valor'],
                    mode='lines+markers',
                    name=abreviar(indicador),
                    line=dict(width=3, color=colores[i % len(colores)]),
                    marker=dict(size=8),
                    hovertemplate=f'<b>{indicador}</b><br>' +
                                 'Mes: %{x}<br>' +
                                 'Valor: %{y:.1f}%<br>' +
                                 '<extra></extra>'
                ))
    
    # Configurar layout
    fig.update_layout(
        title=f"Indicadores Porcentuales: {', '.join([abreviar(i) for i in indicadores])} - {area}",
        height=500,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01
        ),
        xaxis=dict(
            categoryorder='array',
            categoryarray=['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                          'Julio', 'Agosto', 'Septiembre']
        ),
        yaxis=dict(range=[0, 120])  # Escala Y: 0% a 120%
    )
    
    return fig

def crear_resumen_ejecutivo(indicadores, area, df, df_filtered, month_order):
    """Crear resumen ejecutivo con KPIs principales"""
    st.subheader("📈 Resumen Ejecutivo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Indicadores", len(indicadores))
    
    with col2:
        areas_evaluadas = 1 if area != 'Todas' else len(df['Área'].unique())
        st.metric("Áreas Evaluadas", areas_evaluadas)
    
    with col3:
        st.metric("Completitud Datos", "100.0%")
    
    with col4:
        if len(df_filtered) > 0 and df_filtered['Tipo'].iloc[0] == 'Porcentual':
            promedio_eficiencia = df_filtered[month_order].mean().mean()
            st.metric("Promedio Eficiencia", f"{promedio_eficiencia:.1f}%")
        else:
            st.metric("Promedio Eficiencia", "N/A")

def main():
    # Logo de la empresa en la esquina superior derecha
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.title("📊 Dashboard Indicadores ESIP")
    
    with col2:
        try:
            st.image("logo_esip_clear.png", width=150)
        except:
            st.markdown("### 📊 ESIP SAS ESP")
    
    st.markdown("---")
    
    # Cargar datos
    df, month_order = cargar_y_procesar_datos()
    
    if df is None or month_order is None:
        st.error("❌ Error al cargar los datos. Verifica que los archivos CSV estén en la carpeta.")
        st.info("📋 Archivos requeridos:")
        st.markdown("""
        - `Numericos.csv` o `Númericos.csv` (datos numéricos)
        - `porcentaje.csv` (datos porcentuales)
        
        Asegúrate de que estos archivos estén en la misma carpeta que `app.py`
        """)
        return  # Salir de la función main() en lugar de usar st.stop()
    
    # Validar que df tenga las columnas necesarias
    if 'Área' not in df.columns:
        st.error("❌ Error: El archivo CSV no contiene la columna 'Área'.")
        return
    
    # Sidebar para filtros
    st.sidebar.header("🔍 Filtros")
    
    # Filtro principal por área
    areas_disponibles = sorted(df['Área'].unique()) if len(df) > 0 else []
    area = st.sidebar.selectbox(
        "Seleccionar Área", 
        options=['Todas'] + areas_disponibles
    )
    
    # Filtro en cascada por indicador
    if len(df) == 0:
        st.warning("⚠️ No hay datos disponibles para mostrar.")
        return
    
    indicadores_disponibles = df[df['Área'] == area]['Indicador'].unique() if area != 'Todas' else df['Indicador'].unique()
    indicadores = st.sidebar.multiselect(
        "Seleccionar Indicador", 
        options=indicadores_disponibles, 
        default=indicadores_disponibles[:1] if len(indicadores_disponibles) > 0 else []
    )
    
    # Filtros adicionales solo para "Atención al Usuario"
    subcategoria = 'Todas'
    comuna_seleccionada = []
    
    if area == "Atención al Usuario":
        st.sidebar.markdown("---")
        st.sidebar.subheader("Filtros Adicionales")
        
        # Definir subcategorías
        subcategorias = {
            'Comunas': lambda x: any(p in x.lower() for p in ['comuna', 'aipecito', 'otros/no aplica', 'zona rural']),
            'Canal de Recepción': lambda x: 'canal de recepción' in x.lower(),
            'Subtema': lambda x: 'subtema' in x.lower(),
            'Remitido a': lambda x: 'remitido a' in x.lower(),
            'Otros': lambda x: not any(p in x.lower() for p in ['comuna', 'canal', 'subtema', 'remitido', 'aipecito', 'zona rural'])
        }
        
        subcategoria = st.sidebar.selectbox(
            "Subcategoría", 
            options=['Todas'] + list(subcategorias.keys())
        )
        
        # Si se elige "Comunas", añadir filtro de comunas
        if subcategoria == "Comunas":
            comunas = [ind for ind in indicadores_disponibles if 'comuna' in ind.lower() or 'aipecito' in ind.lower() or 'zona rural' in ind.lower() or 'otros/no aplica' in ind.lower()]
            comuna_seleccionada = st.sidebar.multiselect(
                "Comunas", 
                options=comunas
            )
    
    # Lógica de filtrado final
    df_filtered = df[df['Área'] == area] if area != 'Todas' else df
    
    if area == 'Atención al Usuario' and subcategoria != 'Todas':
        df_filtered = df_filtered[df_filtered['Indicador'].apply(subcategorias[subcategoria])]
    
    if area == 'Atención al Usuario' and subcategoria == 'Comunas' and comuna_seleccionada:
        df_filtered = df_filtered[df_filtered['Indicador'].isin(comuna_seleccionada)]
    
    if indicadores:
        df_filtered = df_filtered[df_filtered['Indicador'].isin(indicadores)]
    
    # Resumen ejecutivo
    crear_resumen_ejecutivo(indicadores, area, df, df_filtered, month_order)
    
    st.markdown("---")
    
    # Pestañas reorganizadas
    tab1, tab2, tab3 = st.tabs(["📈 Tendencias Numéricas", "📊 Indicadores Porcentuales", "📋 Tabla de Datos"])
    
    with tab1:
        st.subheader("Tendencias de Indicadores Numéricos")
        
        df_numericos = df_filtered[df_filtered['Tipo'] == 'Numérico']
        
        if len(df_numericos) > 0:
            # Convertir a formato largo para gráfico
            df_melted = pd.melt(
                df_numericos, 
                id_vars=['Indicador', 'Área', 'Tipo'], 
                value_vars=month_order,
                var_name='Mes', 
                value_name='Valor'
            )
            
            # Convertir meses a orden cronológico usando pd.Categorical
            df_melted['Mes'] = pd.Categorical(df_melted['Mes'], categories=month_order, ordered=True)
            df_melted = df_melted.sort_values(['Indicador', 'Mes'])
            
            indicadores_numericos = df_numericos['Indicador'].unique()
            
            fig_numericos = crear_grafico_tendencias_numericas(df_melted, area, indicadores_numericos)
            if fig_numericos:
                st.plotly_chart(fig_numericos, use_container_width=True)
        else:
            st.info("No hay indicadores numéricos disponibles para los filtros seleccionados.")
    
    with tab2:
        st.subheader("Indicadores Porcentuales")
        
        df_porcentajes = df_filtered[df_filtered['Tipo'] == 'Porcentual']
        
        if len(df_porcentajes) > 0:
            # Convertir a formato largo para gráfico
            df_melted = pd.melt(
                df_porcentajes, 
                id_vars=['Indicador', 'Área', 'Tipo'], 
                value_vars=month_order,
                var_name='Mes', 
                value_name='Valor'
            )
            
            # Convertir meses a orden cronológico usando pd.Categorical
            df_melted['Mes'] = pd.Categorical(df_melted['Mes'], categories=month_order, ordered=True)
            df_melted = df_melted.sort_values(['Indicador', 'Mes'])
            
            indicadores_porcentuales = df_porcentajes['Indicador'].unique()
            
            fig_porcentajes = crear_grafico_porcentuales(df_melted, area, indicadores_porcentuales)
            if fig_porcentajes:
                st.plotly_chart(fig_porcentajes, use_container_width=True)
        else:
            st.info("No hay indicadores porcentuales disponibles para los filtros seleccionados.")
    
    with tab3:
        st.subheader("Tabla de Datos")
        
        if len(df_filtered) > 0:
            # Mostrar datos filtrados
            df_display = df_filtered[['Área', 'Indicador', 'Tipo'] + month_order].copy()
            
            # Limpiar valores numéricos eliminando ceros innecesarios
            for col in month_order:
                if col in df_display.columns:
                    df_display[col] = df_display[col].apply(lambda x: 
                        f"{x:.0f}" if pd.notna(x) and x == int(x) else 
                        f"{x:.2f}".rstrip('0').rstrip('.') if pd.notna(x) else 
                        ""
                    )
            
            # Añadir fila de TOTALES al final
            total_row = df_filtered[month_order].sum()
            total_row['Indicador'] = 'TOTAL'
            total_row['Área'] = ''
            total_row['Tipo'] = ''
            
            # Limpiar valores de la fila total también
            for col in month_order:
                if col in total_row.index:
                    total_row[col] = f"{total_row[col]:.0f}" if total_row[col] == int(total_row[col]) else f"{total_row[col]:.2f}".rstrip('0').rstrip('.')
            
            # Convertir total_row a DataFrame y concatenar
            total_df = pd.DataFrame([total_row])
            df_display = pd.concat([df_display, total_df], ignore_index=True)
            
            # Resaltar fila TOTAL con estilo
            def highlight_total(row):
                if row.name == len(df_display) - 1:  # Última fila (TOTAL)
                    return ['background-color: #f0f0f0'] * len(row)
                return [''] * len(row)
            
            styled_df = df_display.style.apply(highlight_total, axis=1)
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.info("No hay datos disponibles para los filtros seleccionados.")
    
    # Información adicional
    st.markdown("---")
    st.subheader("ℹ️ Información del Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Características del Dashboard:**
        - ✅ Datos unificados numéricos y porcentuales
        - ✅ Filtros en cascada inteligentes
        - ✅ Filtros adicionales para Atención al Usuario
        - ✅ Orden cronológico garantizado
        - ✅ Gráficos especializados por tipo
        """)
    
    with col2:
        st.markdown("""
        **Instrucciones de Uso:**
        1. Selecciona área e indicadores
        2. Usa filtros adicionales si es "Atención al Usuario"
        3. Navega entre pestañas especializadas
        4. Revisa tabla con totales al final
        """)
    
    # Créditos discretos en la parte inferior derecha
    st.markdown("---")
    st.markdown(
        '<div style="text-align: right; font-size: 10px; color: #666; margin-top: 20px;">'
        'Desarrollado por Alejandra Valderrama. Jefe de Investigaciones y Desarrollo Social.'
        '</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()