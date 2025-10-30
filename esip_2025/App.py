import streamlit as st
import pandas as pd
import plotly.express as px
import os
from pathlib import Path

st.set_page_config(page_title="Indicadores ESIP 2025", layout="wide", page_icon="bar_chart")

# Encabezado con título y logo a la derecha
header_left, header_right = st.columns([0.75, 0.25])
with header_left:
    st.title("Indicadores ESIP 2025")
    st.markdown("### Resumen Cualitativo | Enero → Septiembre")
with header_right:
    BASE_DIR = Path(__file__).parent
    logo_path = BASE_DIR / "logo_esip_clear.png"
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
    else:
        st.empty()

# Documentación (si existe Readme.md)
doc_text = None
readme_path = BASE_DIR / "Readme.md"
if readme_path.exists():
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            doc_text = f.read()
    except Exception:
        doc_text = None
if doc_text:
    with st.expander("Cómo leer este tablero (Documentación)"):
        st.markdown(doc_text, unsafe_allow_html=True)

# Localización y carga robusta de archivos desde la carpeta del script
def load_csv(path: str):
    return pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")

def find_first(candidates):
    for name in candidates:
        p = BASE_DIR / name
        if p.exists():
            return str(p)
    return None

f_perc = find_first(["Ind_%.csv", "porcentaje.csv"])
f_num  = find_first(["Ind_n.csv", "Numericos.csv"])
f_tipo = find_first(["tipo_indicadores.csv"])

missing = []
if not f_perc: missing.append("Ind_%.csv o porcentaje.csv")
if not f_num:  missing.append("Ind_n.csv o Numericos.csv")
if not f_tipo: missing.append("tipo_indicadores.csv")
if missing:
    for f in missing:
        st.error(f"Falta el archivo: {f}")
    st.stop()

df_perc = load_csv(f_perc)
df_num  = load_csv(f_num)
tipo_df = load_csv(f_tipo)

# Meses
meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre']

# Validaciones mínimas de columnas
for col in ['ID','Indicador','Área']:
    if col not in df_perc.columns or col not in df_num.columns:
        st.error(f"Falta la columna obligatoria '{col}' en los CSV de indicadores.")
        st.stop()
if 'ID' not in tipo_df.columns or 'Tipo' not in tipo_df.columns:
    st.error("La tabla 'tipo_indicadores.csv' debe tener columnas 'ID' y 'Tipo'.")
    st.stop()
for m in meses:
    if m not in df_perc.columns or m not in df_num.columns:
        st.error(f"Falta la columna de mes '{m}' en uno de los CSV.")
        st.stop()

# Limpieza
def to_float_cols(df, cols, is_percent=False):
    clean = df.copy()
    if is_percent:
        clean[cols] = (clean[cols]
                       .replace({r'%': '', r',': ''}, regex=True)
                       .apply(pd.to_numeric, errors='coerce'))
    else:
        clean[cols] = (clean[cols]
                       .replace({r',': '', r'"': ''}, regex=True)
                       .apply(pd.to_numeric, errors='coerce'))
    return clean

df_perc = to_float_cols(df_perc, meses, is_percent=True)
df_num  = to_float_cols(df_num, meses, is_percent=False)

# Unir 'Tipo' a numéricos
df_num = df_num.merge(tipo_df[['ID','Tipo']], on='ID', how='left')
df_num['Tipo'] = df_num['Tipo'].fillna('NEU').str.upper()

# === Reglas de valoración ===
def valorar_porcentaje(val, indicador):
    if pd.isna(val):
        return "N/A", "gray"
    ind_norm = (indicador or "").strip().casefold()
    # Excepciones: 0% = Alto; >0% = Bajo
    if ind_norm in ['tasa de accidentes laborales', 'prevalencia de enfermedades']:
        return ("Alto","green") if float(val) == 0 else ("Bajo","red")
    v = float(val)
    if v >= 90: return "Alto", "green"
    elif v >= 80: return "Medio", "orange"
    else: return "Bajo", "red"

def valorar_numerico(actual, anterior, tipo):
    tipo = (tipo or "NEU").upper()
    if tipo == "NEU":
        return "N/A", "gray"
    if pd.isna(actual) or pd.isna(anterior) or anterior == 0:
        return "N/A", "gray"
    cambio = (actual - anterior) / anterior * 100.0
    if tipo == "POS":
        if cambio >= 5:      return "Alto", "green"
        elif cambio >= -5:   return "Medio", "orange"
        else:                return "Bajo", "red"
    if tipo == "NEG":
        if cambio <= -10:    return "Alto", "green"
        elif cambio <= 10:   return "Medio", "orange"
        else:                return "Bajo", "red"
    return "N/A", "gray"

# Precalcular valoraciones
for m in meses:
    vals = df_perc.apply(lambda r: valorar_porcentaje(r[m], r['Indicador']), axis=1)
    df_perc[f"{m}_Val"]   = [v[0] for v in vals]
    df_perc[f"{m}_Color"] = [v[1] for v in vals]

for i, m in enumerate(meses):
    if i == 0:
        df_num[f"{m}_Val"] = "N/A"
        df_num[f"{m}_Color"] = "gray"
    else:
        ant = meses[i-1]
        vals = df_num.apply(lambda r: valorar_numerico(r[m], r[ant], r['Tipo']), axis=1)
        df_num[f"{m}_Val"]   = [v[0] for v in vals]
        df_num[f"{m}_Color"] = [v[1] for v in vals]

# Utilidad para badge de color
def color_badge(text, color):
    css = {
        "green":  "#16a34a",
        "orange": "#f59e0b",
        "red":    "#dc2626",
        "gray":   "#6b7280",
    }.get(color, "#6b7280")
    return f"<span style='background:{css}20;color:{css};padding:2px 7px;border-radius:6px;font-weight:600;font-size:0.85rem;'>{text}</span>"

# Áreas
areas = sorted(pd.concat([df_perc['Área'], df_num['Área']]).dropna().unique())

# Filtros opcionales
with st.sidebar:
    st.header("Filtros")
    area_sel = st.multiselect("Áreas", areas, default=areas)
    buscar = st.text_input("Buscar indicador (contiene)", "")

for area in areas:
    if area not in area_sel:
        continue
    st.markdown(f"## **{area}**")
    col1, col2 = st.columns(2)

    # PORCENTAJES
    with col1:
        st.subheader("Indicadores %")
        subset = df_perc[(df_perc['Área'] == area)]
        if buscar:
            subset = subset[subset['Indicador'].str.contains(buscar, case=False, na=False)]
        if subset.empty:
            st.info("Sin indicadores para mostrar.")
        for _, row in subset.iterrows():
            with st.expander(row['Indicador']):
                vals = [row[m] if not pd.isna(row[m]) else None for m in meses]
                fig = px.line(x=meses, y=vals, markers=True, title="Evolución (%)")
                fig.update_layout(margin=dict(l=0,r=0,t=40,b=0), height=260)
                st.plotly_chart(fig, use_container_width=True, key=f"perc:{area}:{row['ID']}:{row.name}")

                cols = st.columns(9)
                for i, m in enumerate(meses):
                    v = row[m]
                    c = row.get(f"{m}_Color","gray")
                    txt = row.get(f"{m}_Val","N/A")
                    val_str = "-" if pd.isna(v) else f"{v:.1f}%"
                    arrow = ""
                    if i > 0:
                        prev = row[meses[i-1]]
                        if not pd.isna(v) and not pd.isna(prev):
                            if v > prev: arrow = "▲"
                            elif v < prev: arrow = "▼"
                            else: arrow = "▶"
                    with cols[i]:
                        st.markdown(f"**{m[:3]}**", help=m)
                        st.markdown(color_badge(txt, c), unsafe_allow_html=True)
                        st.markdown(f"{arrow} `{val_str}`")

    # NUMÉRICOS
    with col2:
        st.subheader("Indicadores numéricos")
        subset = df_num[(df_num['Área'] == area)]
        if buscar:
            subset = subset[subset['Indicador'].str.contains(buscar, case=False, na=False)]
        if subset.empty:
            st.info("Sin indicadores para mostrar.")
        for _, row in subset.iterrows():
            with st.expander(f"{row['Indicador']}  |  Tipo: {row['Tipo']}"):
                vals = [row[m] if not pd.isna(row[m]) else 0 for m in meses]
                fig = px.bar(x=meses, y=vals, title="Evolución (conteos)")
                fig.update_layout(margin=dict(l=0,r=0,t=40,b=0), height=260)
                st.plotly_chart(fig, use_container_width=True, key=f"num:{area}:{row['ID']}:{row.name}")

                cols = st.columns(9)
                for i, m in enumerate(meses):
                    v = row[m]
                    c = row.get(f"{m}_Color","gray")
                    txt = row.get(f"{m}_Val","N/A")
                    val_str = "-" if pd.isna(v) else f"{int(v)}"
                    arrow = ""
                    if i > 0:
                        prev = row[meses[i-1]]
                        if not pd.isna(v) and not pd.isna(prev):
                            if v > prev: arrow = "▲"
                            elif v < prev: arrow = "▼"
                            else: arrow = "▶"
                    with cols[i]:
                        st.markdown(f"**{m[:3]}**", help=m)
                        st.markdown(color_badge(txt, c), unsafe_allow_html=True)
                        st.markdown(f"{arrow} `{val_str}`")

st.success("Dashboard generado con éxito")

# Crédito discreto al final (alineado a la derecha)
st.markdown(
    "<div style='text-align:right; color:#6b7280; font-size:0.85rem; margin-top:24px;'>"
    "Desarrollado por: Alejandra Valderrama. Jefe de Investigaciones y Desarrollo Social ESIP SAS ESP"
    "</div>",
    unsafe_allow_html=True,
)