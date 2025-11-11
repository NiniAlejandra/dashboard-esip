import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import os

# --- CONFIG ---
st.set_page_config(
    page_title="Gestión de Podas - ESIP - V2",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Logo y título
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    try:
        st.image("logo_esip_clear.png", width=200)
    except Exception:
        st.write("Logo ESIP")
    
st.title("🌳 Gestión de Podas - ESIP - V2")
st.markdown("**Tablero de planeación y control de podas cruzado por ID de luminaria.**")
st.markdown("---")

# --- CARGA DE DATOS ---
@st.cache_data
def load_data():
    """Cargar datos base y enriquecerlos usando ID_Luminaria"""

    cam_layer = pd.DataFrame()

    # 1. Datos base: PQR pendientes
    df = pd.read_csv("data/pqr_pendientes_georreferenciadas.csv", encoding="utf-8")
    df.columns = df.columns.str.strip()

    # Normalizar columnas clave
    if "Latitud" not in df.columns and "Lat" in df.columns:
        df = df.rename(columns={"Lat": "Latitud"})
    if "Longitud" not in df.columns and "Long" in df.columns:
        df = df.rename(columns={"Long": "Longitud"})
    if "inventariado" in df.columns:
        df = df.rename(columns={"inventariado": "Inventariado"})

    # Asegurar columna ID_Luminaria
    if "ID_Luminaria" not in df.columns:
        df["ID_Luminaria"] = None

    # Inicializar columnas usadas en la app
    df["Ejecutada"] = "NO"
    df["Permiso_CAM"] = "NO"
    df["NOMBRE COMÚN"] = None

    # 2. Podas ejecutadas (marca por sticker)
    if os.path.exists("data/podas_ejecutadas.csv"):
        try:
            ejecutadas = pd.read_csv("data/podas_ejecutadas.csv", encoding="utf-8")
            ejecutadas.columns = ejecutadas.columns.str.strip()

            sticker_col = "Sticker" if "Sticker" in ejecutadas.columns else "Stiker"
            obs_col = "Observación" if "Observación" in ejecutadas.columns else ejecutadas.columns[1]

            ejecutadas_filtradas = ejecutadas[
                ejecutadas[obs_col].astype(str).str.contains("YA EJECUTADA", case=False, na=False)
            ]

            df["Sticker_tmp"] = df["Sticker"].astype(str).str.strip()
            ejecutadas_filtradas["Sticker_tmp"] = ejecutadas_filtradas[sticker_col].astype(str).str.strip()

            df.loc[df["Sticker_tmp"].isin(ejecutadas_filtradas["Sticker_tmp"]), "Ejecutada"] = "SI"
            df = df.drop(columns=["Sticker_tmp"], errors="ignore")
        except Exception as exc:
            st.warning(f"Error al cargar podas ejecutadas: {exc}")

    # 3. Inventario CAM (se enlaza por sticker, no dispone de ID_Luminaria)
    if os.path.exists("data/inventario_cam.csv"):
        try:
            cam = pd.read_csv("data/inventario_cam.csv", encoding="utf-8-sig")
            cam.columns = cam.columns.str.strip()

            if 'Latitud' in cam.columns:
                cam = cam.rename(columns={'Latitud': 'Lat'})
            if 'Longitud' in cam.columns:
                cam = cam.rename(columns={'Longitud': 'Long'})

            nombre_col = None
            for col in cam.columns:
                if 'NOMBRE' in col.upper() and 'COM' in col.upper():
                    nombre_col = col
                    break

            cols_needed = ['Sticker']
            if nombre_col:
                cols_needed.append(nombre_col)
            if 'Lat' in cam.columns:
                cols_needed.append('Lat')
            if 'Long' in cam.columns:
                cols_needed.append('Long')
            if 'ID_Luminaria' in cam.columns:
                cols_needed.append('ID_Luminaria')

            cam_clean = cam[cols_needed].copy()
            cam_clean = cam_clean.dropna(subset=['Sticker'])
            cam_clean['Sticker'] = cam_clean['Sticker'].astype(str).str.strip()
            cam_clean['Permiso_CAM'] = 'SI'

            if nombre_col and nombre_col != 'NOMBRE COMÚN':
                cam_clean = cam_clean.rename(columns={nombre_col: 'NOMBRE COMÚN'})

            cam_layer = cam_clean.copy()
            if 'Lat' in cam_layer.columns and 'Long' in cam_layer.columns:
                cam_layer['Lat'] = pd.to_numeric(cam_layer['Lat'], errors='coerce')
                cam_layer['Long'] = pd.to_numeric(cam_layer['Long'], errors='coerce')
                cam_layer = cam_layer.dropna(subset=['Lat', 'Long'])
            else:
                cam_layer = pd.DataFrame()

            df['Sticker_tmp'] = df['Sticker'].astype(str).str.strip()
            cam_clean['Sticker_tmp'] = cam_clean['Sticker'].astype(str).str.strip()

            df = df.merge(
                cam_clean[['Sticker_tmp', 'Permiso_CAM', 'NOMBRE COMÚN']],
                on='Sticker_tmp',
                how='left',
                suffixes=('', '_cam')
            )
            df['Permiso_CAM'] = df['Permiso_CAM'].fillna('NO')
            if 'NOMBRE COMÚN_cam' in df.columns:
                df['NOMBRE COMÚN'] = df['NOMBRE COMÚN'].fillna(df['NOMBRE COMÚN_cam'])
                df = df.drop(columns=['NOMBRE COMÚN_cam'], errors='ignore')
            df = df.drop(columns=['Sticker_tmp'], errors='ignore')
        except Exception as exc:
            st.warning(f"Error al cargar inventario CAM: {exc}")

    # 4. Inventario forestal (enlace principal por ID_Luminaria)
    if os.path.exists("data/Inventario_forestal.csv"):
        try:
            inv = pd.read_csv("data/Inventario_forestal.csv", encoding="utf-8")
            inv.columns = inv.columns.str.strip()

            if "ID_Luminaria" in inv.columns:
                inv_clean = inv.copy()
                inv_clean["ID_Luminaria"] = inv_clean["ID_Luminaria"].astype(str).str.strip()
                inv_clean = inv_clean.drop_duplicates(subset=["ID_Luminaria"], keep="first")

                cols_inv = [
                    "ID_Luminaria",
                    "Nombre_comun",
                    "NOMBRE CIENTIFICO",
                    "HT(m)",
                    "CAP(cm)",
                    "DAP(m)",
                    "DIAMETRO DE COPAS (m)",
                    "TRATAMIENTO, PODA ",
                    "Sticker"
                ]
                cols_inv = [c for c in cols_inv if c in inv_clean.columns]

                df["ID_Luminaria_tmp"] = df["ID_Luminaria"].astype(str).str.strip()
                df = df.merge(
                    inv_clean[cols_inv],
                    left_on="ID_Luminaria_tmp",
                    right_on="ID_Luminaria",
                    how="left",
                    suffixes=("", "_inv")
                )
                df = df.drop(columns=["ID_Luminaria_tmp"], errors="ignore")
        except Exception as exc:
            st.warning(f"Error al cargar inventario forestal: {exc}")

    df['P.Q.R.S'] = df['P.Q.R.S'].astype(str)
    df['Es_Nueva'] = df['P.Q.R.S'].str.contains(r'2025-0[1-9]|2025-1[0-2]', na=False, regex=True)

    df['Latitud'] = pd.to_numeric(df['Latitud'], errors='coerce')
    df['Longitud'] = pd.to_numeric(df['Longitud'], errors='coerce')
    df = df.dropna(subset=['Latitud', 'Longitud']).copy()

    df['Comuna_Num'] = df['Comuna'].str.extract(r'(\d+)').astype(float).fillna(0).astype(int)
    df['Inventariado'] = df['Inventariado'].astype(str).str.strip().str.upper()
    df['Ejecutada'] = df['Ejecutada'].astype(str).str.strip().str.upper()
    df['Permiso_CAM'] = df['Permiso_CAM'].astype(str).str.strip().str.upper()

    if 'NOMBRE COMÚN' not in df.columns:
        df['NOMBRE COMÚN'] = None

    if not cam_layer.empty:
        if 'ID_Luminaria' in cam_layer.columns:
            cam_layer['ID_Luminaria'] = cam_layer['ID_Luminaria'].astype(str).str.strip()
        cam_layer = cam_layer.merge(
            df[['Sticker', 'Comuna']].drop_duplicates(subset=['Sticker']),
            on='Sticker',
            how='left'
        )
        cam_layer = cam_layer.rename(columns={'Lat': 'Latitud', 'Long': 'Longitud'})
        cam_layer['NOMBRE COMÚN'] = cam_layer['NOMBRE COMÚN'].astype(str)

    return df, cam_layer

# Cargar datos
with st.spinner("Cargando datos..."):
    df, cam_layer = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 Filtros")

    comunas = sorted(df['Comuna'].unique())
    selected_comunas = st.multiselect("Comuna", options=comunas, default=comunas)

    cam_nombres = sorted(cam_layer['NOMBRE COMÚN'].dropna().astype(str).str.strip().unique()) if not cam_layer.empty else []
    cam_nombres = [n for n in cam_nombres if n and n.lower() != 'nan']
    selected_especies = st.multiselect("Nombre Común (CAM)", options=cam_nombres, default=[])

    show_cam_layer = st.checkbox("Mostrar capa Inventario CAM", value=True)

    st.markdown("---")
    st.subheader("📊 Estadísticas")
    st.metric("Total Solicitudes", len(df))
    st.metric("Inventariadas (SI)", len(df[df['Inventariado'] == 'SI']))
    st.metric("Pendientes (NO)", len(df[df['Inventariado'] == 'NO']))
    st.metric("Registros CAM", len(cam_layer))

# --- APLICAR FILTROS ---
filtered_df = df.copy()

if selected_comunas:
    filtered_df = filtered_df[filtered_df['Comuna'].isin(selected_comunas)]

if selected_especies:
    especies_norm = [str(e).strip().lower() for e in selected_especies]
    filtered_df = filtered_df[
        filtered_df['NOMBRE COMÚN'].fillna('').astype(str).str.strip().str.lower().isin(especies_norm)
    ]

cam_layer_filtered = cam_layer.copy()
if not cam_layer_filtered.empty:
    if selected_comunas and 'Comuna' in cam_layer_filtered.columns:
        cam_layer_filtered = cam_layer_filtered[cam_layer_filtered['Comuna'].isin(selected_comunas)]
    if selected_especies:
        especies_norm = [str(e).strip().lower() for e in selected_especies]
        cam_layer_filtered = cam_layer_filtered[
            cam_layer_filtered['NOMBRE COMÚN'].fillna('').astype(str).str.strip().str.lower().isin(especies_norm)
        ]

# --- CONTENIDO PRINCIPAL ---
if filtered_df.empty:
    st.warning("⚠️ No hay datos que coincidan con los filtros seleccionados.")
else:
    center = [filtered_df['Latitud'].mean(), filtered_df['Longitud'].mean()]
    m = folium.Map(location=center, zoom_start=12, tiles="CartoDB positron")

    capa_base = folium.FeatureGroup(name="Solicitudes PQR", show=True)
    capa_cam = folium.FeatureGroup(name="Inventario CAM", show=show_cam_layer)

    for _, row in filtered_df.iterrows():
        inventariado_val = str(row.get('Inventariado', 'NO')).upper().strip()
        color = '#2ca02c' if inventariado_val == 'SI' else '#d62728'

        popup_html = f"""
        <div style=\"font-family: Arial; font-size: 12px; width: 240px;\">
            <b>ID Luminaria:</b> {row.get('ID_Luminaria', 'N/D')}<br>
            <b>Sticker:</b> {row.get('Sticker', 'N/D')}<br>
            <b>PQR:</b> {str(row.get('P.Q.R.S', ''))[:80]}...<br>
            <b>Comuna:</b> {row.get('Comuna', 'N/D')}<br>
            <b>Inventariado:</b> {inventariado_val}<br>
        </div>
        """

        folium.CircleMarker(
            location=[row['Latitud'], row['Longitud']],
            radius=4,
            color='black',
            weight=1,
            fill=True,
            fillColor=color,
            fillOpacity=0.85,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{row.get('ID_Luminaria', '')}"
        ).add_to(capa_base)

    if show_cam_layer and not cam_layer_filtered.empty:
        for _, row in cam_layer_filtered.iterrows():
            popup_html = f"""
            <div style=\"font-family: Arial; font-size: 12px; width: 240px;\">
                <b>ID Luminaria:</b> {row.get('ID_Luminaria', 'N/D')}<br>
                <b>Sticker:</b> {row.get('Sticker', 'N/D')}<br>
                <b>Nombre común:</b> {row.get('NOMBRE COMÚN', row.get('Nombre_comun', 'N/D'))}<br>
            </div>
            """
            folium.CircleMarker(
                location=[row['Latitud'], row['Longitud']],
                radius=5,
                color='#072ac8',
                weight=1,
                fill=True,
                fillColor='#072ac8',
                fillOpacity=0.9,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"CAM: {row.get('ID_Luminaria', '')}"
            ).add_to(capa_cam)

    capa_base.add_to(m)
    if show_cam_layer and not cam_layer_filtered.empty:
        capa_cam.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    st.subheader("🗺️ Mapa Interactivo")
    st_folium(m, width=None, height=600, returned_objects=[])

    st.markdown("### Leyenda")
    st.markdown("""
    - 🟢 **Verde**: Inventariado = SI
    - 🔴 **Rojo**: Inventariado = NO
    - 🔵 **Azul (#072ac8)**: Inventario CAM
    """)

    st.subheader("📊 Inventario por Comuna")
    resumen = filtered_df.groupby('Comuna').agg({
        'Sticker': 'count',
        'Inventariado': lambda x: (x == 'SI').sum()
    }).reset_index()
    resumen.columns = ['Comuna', 'Total', 'Inventariado_SI']
    resumen['Inventariado_NO'] = resumen['Total'] - resumen['Inventariado_SI']

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Inventariado SI',
        x=resumen['Comuna'],
        y=resumen['Inventariado_SI'],
        marker_color='#2ca02c'
    ))
    fig.add_trace(go.Bar(
        name='Inventariado NO',
        x=resumen['Comuna'],
        y=resumen['Inventariado_NO'],
        marker_color='#d62728'
    ))
    fig.update_layout(
        barmode='stack',
        xaxis_title='Comuna',
        yaxis_title='Cantidad',
        height=400,
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Detalle de Solicitudes")
    columnas_tabla = [
        'ID_Luminaria', 'Sticker', 'Comuna', 'P.Q.R.S', 'Inventariado',
        'NOMBRE COMÚN', 'Nombre_comun'
    ]
    columnas_tabla = [c for c in columnas_tabla if c in filtered_df.columns]
    if columnas_tabla:
        if 'Comuna_Num' in filtered_df.columns:
            df_sorted = filtered_df.sort_values(['Comuna_Num', 'Latitud'], ascending=[True, False])
        else:
            df_sorted = filtered_df.sort_values(['Comuna', 'Latitud'], ascending=[True, False])
        st.dataframe(df_sorted[columnas_tabla], use_container_width=True, height=400)

st.markdown("---")
st.markdown("**Gestión de Podas - ESIP SAS ESP 2025 (V2)**")
