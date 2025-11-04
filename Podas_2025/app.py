"""
App Streamlit - Gestión de Podas
Visualización de PQR pendientes georreferenciadas con mapa interactivo
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
from pathlib import Path
import matplotlib.pyplot as plt

# Colores personalizados
COLOR_VERDE = '#70e000'
COLOR_ROJO = '#d80032'

# Configuración de la página
st.set_page_config(
    page_title="Gestión de Podas - ESIP",
    page_icon="🌳",
    layout="wide"
)

# Ruta de los archivos CSV
DATA_DIR = Path("data")
PQR_FILE = DATA_DIR / "pqr_pendientes_georreferenciadas.csv"
INVENTARIO_FILE = DATA_DIR / "Inventario_forestal.csv"


def clean_coordinate(value):
    """
    Limpia y convierte una coordenada a float.
    Maneja strings con comas como separador decimal y valores no numéricos.
    """
    if pd.isna(value):
        return None
    
    try:
        # Si ya es numérico, convertir directamente
        if isinstance(value, (int, float)):
            return float(value)
        
        # Si es string, limpiar y convertir
        if isinstance(value, str):
            # Eliminar espacios
            value = value.strip()
            # Reemplazar comas por puntos (formato decimal europeo)
            value = value.replace(',', '.')
        
        # Convertir a float
        result = float(value)
        
        # Validar rangos razonables para coordenadas
        # Latitud: -90 a 90, Longitud: -180 a 180
        if abs(result) > 180:
            return None
            
        return result
    except (ValueError, TypeError, AttributeError):
        return None


@st.cache_data
def load_pqr_data():
    """
    Carga el archivo CSV de PQR pendientes georreferenciadas.
    Fuerza Sticker a string y lo rellena con ceros a 6 cifras.
    """
    try:
        df = pd.read_csv(PQR_FILE, dtype={'Sticker': str})
        # Convertir Sticker a string y rellenar con ceros a 6 cifras
        df['Sticker'] = df['Sticker'].astype(str).str.zfill(6)
        
        # Limpiar y convertir coordenadas a float
        if 'Latitud' in df.columns:
            df['Latitud'] = df['Latitud'].apply(clean_coordinate)
        if 'Longitud' in df.columns:
            df['Longitud'] = df['Longitud'].apply(clean_coordinate)
        
        return df
    except FileNotFoundError:
        st.error(f"❌ No se encontró el archivo: {PQR_FILE}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error al cargar PQR: {str(e)}")
        return pd.DataFrame()


@st.cache_data
def load_inventario_data():
    """
    Carga el archivo CSV de Inventario forestal si existe.
    Fuerza Sticker a string y lo rellena con ceros a 6 cifras.
    """
    if not INVENTARIO_FILE.exists():
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(INVENTARIO_FILE, dtype={'Sticker': str})
        # Convertir Sticker a string y rellenar con ceros a 6 cifras
        df['Sticker'] = df['Sticker'].astype(str).str.zfill(6)
        
        # Limpiar y convertir coordenadas a float
        if 'Latitud' in df.columns:
            df['Latitud'] = df['Latitud'].apply(clean_coordinate)
        if 'Longitud' in df.columns:
            df['Longitud'] = df['Longitud'].apply(clean_coordinate)
        
        return df
    except Exception as e:
        st.warning(f"⚠️ Error al cargar Inventario forestal: {str(e)}")
        return pd.DataFrame()


def add_legend(m):
    """
    Agrega una leyenda al mapa indicando los colores de Inventariado.
    
    Args:
        m: Objeto folium.Map al que agregar la leyenda
    """
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 180px; height: 100px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p style="margin: 0; font-weight: bold;">Inventario</p>
    <p style="margin: 5px 0; color: black;">
        <span style="color: {COLOR_VERDE};">●</span> 'Sí'
    </p>
    <p style="margin: 5px 0; color: black;">
        <span style="color: {COLOR_ROJO};">●</span> 'No'
    </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))


def create_map(df_pqr, df_inventario, show_inventario, show_ruta_optima, comunas_seleccionadas=None):
    """
    Crea un mapa Folium con marcadores de PQR e Inventario.
    
    Args:
        df_pqr: DataFrame con datos de PQR filtrados
        df_inventario: DataFrame con datos de Inventario forestal
        show_inventario: Boolean para mostrar capa de Inventario
        show_ruta_optima: Boolean para mostrar ruta óptima
        comunas_seleccionadas: Lista de comunas seleccionadas para filtrar inventario
    """
    if df_pqr.empty:
        # Mapa por defecto si no hay datos
        m = folium.Map(location=[2.94, -75.30], zoom_start=12)
        add_legend(m)
        return m
    
    # Calcular coordenadas promedio para centrar el mapa
    lat_valid = df_pqr['Latitud'].dropna()
    lon_valid = df_pqr['Longitud'].dropna()
    
    if lat_valid.empty or lon_valid.empty:
        # Mapa por defecto si no hay coordenadas válidas
        lat_mean = 2.94
        lon_mean = -75.30
    else:
        lat_mean = lat_valid.mean()
        lon_mean = lon_valid.mean()
    
    # Crear mapa centrado en las coordenadas promedio
    m = folium.Map(
        location=[lat_mean, lon_mean],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Añadir marcadores de PQR
    for idx, row in df_pqr.iterrows():
        lat = row.get('Latitud')
        lon = row.get('Longitud')
        
        # Validar que las coordenadas sean numéricas
        if pd.isna(lat) or pd.isna(lon) or not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            continue
        
        # Color según Inventariado (verde para SI, rojo para NO)
        color = COLOR_VERDE if str(row.get('Inventariado', 'NO')).upper() == 'SI' else COLOR_ROJO
        
        # Tamaño del marcador según Requiere_acción (reducido para mejor visualización)
        size = 8 if str(row.get('Requiere_Acción', 'NO')).upper() == 'SI' else 6
        
        # Información del popup
        popup_text = f"""
        <b>Sticker:</b> {row.get('Sticker', 'N/A')}<br>
        <b>P.Q.R.S:</b> {row.get('P.Q.R.S', 'N/A')}<br>
        <b>Comuna:</b> {row.get('Comuna', 'N/A')}<br>
        <b>Inventariado:</b> {row.get('Inventariado', 'N/A')}<br>
        <b>Requiere Acción:</b> {row.get('Requiere_Acción', 'N/A')}
        """
        
        folium.CircleMarker(
            location=[float(lat), float(lon)],
            radius=size,
            popup=folium.Popup(popup_text, max_width=300),
            color='black',
            weight=1,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            tooltip=f"Sticker: {row.get('Sticker', 'N/A')}"
        ).add_to(m)
    
    # Añadir puntos del Inventario forestal si está activado
    if show_inventario and not df_inventario.empty:
        # Filtrar inventario por comunas seleccionadas
        df_inventario_filtrado = df_inventario.copy()
        
        if comunas_seleccionadas:
            # Si el inventario tiene columna Comuna, filtrar directamente
            if 'Comuna' in df_inventario_filtrado.columns:
                df_inventario_filtrado = df_inventario_filtrado[
                    df_inventario_filtrado['Comuna'].isin(comunas_seleccionadas)
                ]
            else:
                # Si no tiene columna Comuna, hacer join con PQR filtrado por Sticker
                df_pqr_filtrado = df_pqr[df_pqr['Comuna'].isin(comunas_seleccionadas)]
                stickers_comunas = df_pqr_filtrado['Sticker'].unique()
                df_inventario_filtrado = df_inventario_filtrado[
                    df_inventario_filtrado['Sticker'].isin(stickers_comunas)
                ]
        
        for idx, row in df_inventario_filtrado.iterrows():
            lat = row.get('Latitud', None)
            lon = row.get('Longitud', None)
            
            # Validar que las coordenadas sean numéricas
            if (pd.notna(lat) and pd.notna(lon) and 
                isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
                popup_text = f"""
                <b>Sticker:</b> {row.get('Sticker', 'N/A')}<br>
                <b>Nombre común:</b> {row.get('Nombre_comun', 'N/A')}<br>
                <b>Nombre científico:</b> {row.get('NOMBRE CIENTIFICO', 'N/A')}<br>
                <b>Altura (m):</b> {row.get('HT(m)', 'N/A')}<br>
                <b>CAP (cm):</b> {row.get('CAP(cm)', 'N/A')}
                """
                
                folium.CircleMarker(
                    location=[float(lat), float(lon)],
                    radius=6,
                    popup=folium.Popup(popup_text, max_width=300),
                    color='blue',
                    weight=1,
                    fill=True,
                    fillColor='blue',
                    fillOpacity=0.6,
                    tooltip=f"Inventario - Sticker: {row.get('Sticker', 'N/A')}"
                ).add_to(m)
    
    # Añadir ruta óptima si está activada
    if show_ruta_optima and not df_pqr.empty:
        # Ordenar por Comuna y Latitud descendente
        df_ruta = df_pqr.sort_values(['Comuna', 'Latitud'], ascending=[True, False])
        
        # Crear lista de coordenadas para la ruta
        coordinates = []
        for idx, row in df_ruta.iterrows():
            lat = row.get('Latitud')
            lon = row.get('Longitud')
            # Validar que las coordenadas sean numéricas
            if (pd.notna(lat) and pd.notna(lon) and 
                isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
                coordinates.append([float(lat), float(lon)])
        
        # Dibujar línea verde conectando los puntos
        if len(coordinates) > 1:
            folium.PolyLine(
                locations=coordinates,
                color='green',
                weight=3,
                opacity=0.7,
                tooltip='Ruta óptima'
            ).add_to(m)
            
            # Agregar marcador de inicio (primer punto) - icono verde distintivo
            inicio_lat, inicio_lon = coordinates[0]
            folium.Marker(
                location=[inicio_lat, inicio_lon],
                popup=folium.Popup('<b>▶️ INICIO</b><br>Punto de partida de la ruta', max_width=200),
                tooltip='INICIO - Punto de partida',
                icon=folium.Icon(color='green', icon='play', prefix='fa')
            ).add_to(m)
            
            # Agregar marcador de fin (último punto) - icono rojo distintivo
            fin_lat, fin_lon = coordinates[-1]
            folium.Marker(
                location=[fin_lat, fin_lon],
                popup=folium.Popup('<b>⏹️ FIN</b><br>Punto final de la ruta', max_width=200),
                tooltip='FIN - Punto final',
                icon=folium.Icon(color='darkred', icon='stop', prefix='fa')
            ).add_to(m)
    
    # Agregar leyenda al mapa
    add_legend(m)
    
    return m


def main():
    """Función principal de la aplicación"""
    
    # Header con título y logo
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.title("🌳 Gestión de Podas - ESIP")
    with col_header2:
        logo_path = Path("logo_esip_clear.png")
        if logo_path.exists():
            st.image(str(logo_path), width=150)
    
    st.markdown("---")
    
    # Cargar datos
    df_pqr = load_pqr_data()
    df_inventario = load_inventario_data()
    
    if df_pqr.empty:
        st.error("No se pudieron cargar los datos de PQR. Verifica que el archivo exista.")
        return
    
    # Sidebar con filtros
    st.sidebar.header("🔍 Filtros")
    
    # Filtro por Comuna (multiselect)
    comunas_disponibles = sorted(df_pqr['Comuna'].dropna().unique())
    comunas_seleccionadas = st.sidebar.multiselect(
        "Comuna",
        options=comunas_disponibles,
        default=comunas_disponibles
    )
    
    # Filtro por Inventariado
    inventariado_options = ['Todos', 'SI', 'NO']
    inventariado_seleccionado = st.sidebar.selectbox(
        "Inventariado",
        options=inventariado_options,
        index=0
    )
    
    # Filtro por Requiere_acción
    requiere_accion_options = ['Todos', 'SI', 'NO']
    requiere_accion_seleccionado = st.sidebar.selectbox(
        "Requiere Acción",
        options=requiere_accion_options,
        index=0
    )
    
    # Checkbox para mostrar Inventario Forestal
    show_inventario = st.sidebar.checkbox(
        "Mostrar capa Inventario Forestal",
        value=False
    )
    
    # Checkbox para mostrar ruta óptima
    show_ruta_optima = st.sidebar.checkbox(
        "Mostrar ruta óptima",
        value=False
    )
    
    # Aplicar filtros
    df_filtered = df_pqr.copy()
    
    # Filtrar por Comuna
    if comunas_seleccionadas:
        df_filtered = df_filtered[df_filtered['Comuna'].isin(comunas_seleccionadas)]
    
    # Filtrar por Inventariado
    if inventariado_seleccionado != 'Todos':
        df_filtered = df_filtered[
            df_filtered['Inventariado'].astype(str).str.upper() == inventariado_seleccionado
        ]
    
    # Filtrar por Requiere_acción
    if requiere_accion_seleccionado != 'Todos':
        df_filtered = df_filtered[
            df_filtered['Requiere_Acción'].astype(str).str.upper() == requiere_accion_seleccionado
        ]
    
    # Crear mapa
    st.subheader("🗺️ Mapa Interactivo")
    m = create_map(df_filtered, df_inventario, show_inventario, show_ruta_optima, comunas_seleccionadas)
    
    # Mostrar mapa
    map_data = st_folium(m, width=1200, height=500)
    
    # Métricas de conteo por comuna
    st.markdown("---")
    st.subheader("📊 Métricas por Comuna")
    
    # Obtener conteo por comuna
    conteo_por_comuna = df_filtered.groupby('Comuna').size().sort_values(ascending=False)
    
    # Crear columnas para mostrar métricas (máximo 4 columnas)
    num_columnas = min(4, len(conteo_por_comuna))
    if num_columnas > 0 and len(conteo_por_comuna) > 0:
        cols_metricas = st.columns(num_columnas)
        for idx, (comuna, conteo) in enumerate(conteo_por_comuna.items()):
            # Extraer número de comuna si está en formato "COMUNA XX"
            comuna_label = comuna.split()[-1] if ' ' in str(comuna) and comuna.split()[-1].isdigit() else str(comuna)
            with cols_metricas[idx % num_columnas]:
                st.metric(label=f"{comuna}", value=int(conteo))
    
    # Estadísticas y gráficos
    st.markdown("---")
    st.subheader("📊 Estadísticas")
    
    col1, col2 = st.columns(2)
    
    # Gráfico de barras: Conteo de Inventariado
    with col1:
        st.markdown("**Conteo por Inventariado**")
        inventariado_counts = df_filtered['Inventariado'].value_counts()
        
        # Crear gráfico con colores personalizados y estilo moderno
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#0E1117')
        ax.set_facecolor('#0E1117')
        
        colors = []
        labels = []
        values = []
        
        for idx, (label, value) in enumerate(inventariado_counts.items()):
            labels.append(str(label))
            values.append(value)
            if str(label).upper() == 'SI':
                colors.append(COLOR_VERDE)
            elif str(label).upper() == 'NO':
                colors.append(COLOR_ROJO)
            else:
                colors.append('#808080')
        
        bars = ax.bar(labels, values, color=colors, alpha=0.8, edgecolor='white', linewidth=1.5)
        
        # Estilizar ejes
        ax.set_ylabel('Conteo', color='white', fontsize=11)
        ax.set_xlabel('Inventariado', color='white', fontsize=11)
        ax.tick_params(colors='white', labelsize=10)
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('#0E1117')
        ax.spines['right'].set_color('#0E1117')
        ax.spines['left'].set_color('white')
        ax.grid(axis='y', alpha=0.3, color='white', linestyle='--')
        
        plt.tight_layout()
        st.pyplot(fig, facecolor='#0E1117')
        plt.close(fig)
    
    # Gráfico de barras: Conteo de Requiere_acción
    with col2:
        st.markdown("**Conteo por Requiere Acción**")
        requiere_accion_counts = df_filtered['Requiere_Acción'].value_counts()
        
        # Crear gráfico con colores personalizados y estilo moderno
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#0E1117')
        ax.set_facecolor('#0E1117')
        
        colors = []
        labels = []
        values = []
        
        for idx, (label, value) in enumerate(requiere_accion_counts.items()):
            labels.append(str(label))
            values.append(value)
            if str(label).upper() == 'SI':
                colors.append(COLOR_VERDE)
            elif str(label).upper() == 'NO':
                colors.append(COLOR_ROJO)
            else:
                colors.append('#808080')
        
        bars = ax.bar(labels, values, color=colors, alpha=0.8, edgecolor='white', linewidth=1.5)
        
        # Estilizar ejes
        ax.set_ylabel('Conteo', color='white', fontsize=11)
        ax.set_xlabel('Requiere Acción', color='white', fontsize=11)
        ax.tick_params(colors='white', labelsize=10)
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('#0E1117')
        ax.spines['right'].set_color('#0E1117')
        ax.spines['left'].set_color('white')
        ax.grid(axis='y', alpha=0.3, color='white', linestyle='--')
        
        plt.tight_layout()
        st.pyplot(fig, facecolor='#0E1117')
        plt.close(fig)
    
    # Gráfico de conteo por comuna e inventariado
    st.markdown("---")
    st.subheader("📊 Conteo de Inventariado por Comuna")
    
    # Crear tabla cruzada de Comuna vs Inventariado
    if not df_filtered.empty and 'Comuna' in df_filtered.columns and 'Inventariado' in df_filtered.columns:
        conteo_comuna_inventariado = pd.crosstab(df_filtered['Comuna'], df_filtered['Inventariado'])
        
        # Asegurar que existan las columnas SI y NO, rellenar con 0 si no existen
        if 'SI' not in conteo_comuna_inventariado.columns:
            conteo_comuna_inventariado['SI'] = 0
        if 'NO' not in conteo_comuna_inventariado.columns:
            conteo_comuna_inventariado['NO'] = 0
        
        # Ordenar columnas: SI primero (se dibuja abajo) y NO después (arriba)
        column_order = []
        if 'SI' in conteo_comuna_inventariado.columns:
            column_order.append('SI')
        if 'NO' in conteo_comuna_inventariado.columns:
            column_order.append('NO')
        
        # Agregar cualquier otra columna que pueda existir
        for col in conteo_comuna_inventariado.columns:
            if col not in column_order:
                column_order.append(col)
        
        conteo_comuna_inventariado = conteo_comuna_inventariado[column_order]
        
        # Crear gráfico de barras apiladas con colores personalizados y estilo moderno
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('#0E1117')
        ax.set_facecolor('#0E1117')
        
        # Obtener los índices (comunas) ordenadas
        comunas = conteo_comuna_inventariado.index.tolist()
        x_pos = range(len(comunas))
        
        # Dibujar barras apiladas (SI primero abajo, NO arriba)
        bottom = None
        for col in column_order:
            values = conteo_comuna_inventariado[col].values
            if col.upper() == 'SI':
                color = COLOR_VERDE
                label = 'SI'
            elif col.upper() == 'NO':
                color = COLOR_ROJO
                label = 'NO'
            else:
                color = '#808080'
                label = col
            
            ax.bar(x_pos, values, bottom=bottom, color=color, label=label, 
                   alpha=0.8, edgecolor='white', linewidth=1.5)
            if bottom is None:
                bottom = values
            else:
                bottom = bottom + values
        
        # Estilizar ejes
        ax.set_xlabel('Comuna', color='white', fontsize=12)
        ax.set_ylabel('Conteo', color='white', fontsize=12)
        ax.set_title('Conteo de Inventariado por Comuna', color='white', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(comunas, rotation=45, ha='right', color='white', fontsize=10)
        ax.tick_params(colors='white', labelsize=10)
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('#0E1117')
        ax.spines['right'].set_color('#0E1117')
        ax.spines['left'].set_color('white')
        ax.grid(axis='y', alpha=0.3, color='white', linestyle='--')
        
        # Estilizar leyenda
        legend = ax.legend(title='Inventariado', title_fontsize=11, fontsize=10,
                          facecolor='#0E1117', edgecolor='white', labelcolor='white')
        legend.get_title().set_color('white')
        
        plt.tight_layout()
        st.pyplot(fig, facecolor='#0E1117')
        plt.close(fig)
    
    # Tabla final
    st.markdown("---")
    st.subheader("📋 Tabla de Datos")
    
    # Seleccionar columnas para mostrar
    columnas_tabla = [
        'Sticker', 'P.Q.R.S', 'Comuna', 'Inventariado', 
        'Requiere_Acción', 'Latitud', 'Longitud'
    ]
    
    # Verificar que las columnas existan
    columnas_disponibles = [col for col in columnas_tabla if col in df_filtered.columns]
    df_tabla = df_filtered[columnas_disponibles].copy()
    
    st.dataframe(df_tabla, use_container_width=True)
    
    # Botón de descarga CSV de la ruta óptima
    st.markdown("---")
    st.subheader("💾 Exportar Datos")
    
    if show_ruta_optima and not df_filtered.empty:
        # Ordenar por Comuna y Latitud descendente (igual que en la ruta)
        df_ruta_optima = df_filtered.sort_values(['Comuna', 'Latitud'], ascending=[True, False])
        
        # Preparar CSV para descarga
        csv_ruta = df_ruta_optima.to_csv(index=False)
        
        st.download_button(
            label="📥 Descargar CSV de Ruta Óptima",
            data=csv_ruta,
            file_name="ruta_optima.csv",
            mime="text/csv",
            help="Descarga la ruta óptima ordenada por Comuna y Latitud descendente"
        )
    else:
        st.info("💡 Activa 'Mostrar ruta óptima' para habilitar la descarga de la ruta óptima.")
    
    # Créditos al final
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; font-size: 10px; color: gray; margin-top: 20px;">'
        'Desarrollado por: Alejandra Valderrama. Jefe de Investigaciones y Desarrollo Social ESIP SAS ESP'
        '</p>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

