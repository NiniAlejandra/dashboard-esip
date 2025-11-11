# 🌳 Aplicaciones Streamlit - Gestión de Podas ESIP

Este repositorio contiene dos tableros Streamlit para análisis y planeación de podas en Neiva.

## 📦 Aplicaciones disponibles

1. **app.py** – Tablero original
   - Filtros por comuna, inventariado, ejecutada, permiso CAM y especies CAM
   - Mapa interactivo con colores por estado
   - Ruta óptima (inventariado = SI, no ejecutada)
   - Gráfico de barras apiladas y tabla detallada

2. **app_v2.py** – *Gestión de Podas - ESIP - V2*
   - Misma lógica de visualización, cruzando datos principalmente por `ID_Luminaria`
   - Permite filtrar por `ID_Luminaria` y muestra datos provenientes del inventario forestal asociados a ese ID

## 🚀 Requisitos

Instala las dependencias:
```bash
pip install -r requirements.txt
```

## ▶️ Ejecución

### Tablero original
```bash
streamlit run app.py
```

### Tablero V2 (ID_Luminaria)
```bash
streamlit run app_v2.py
```

## 📂 Datos necesarios

Coloca los archivos dentro de `data/`:
- `pqr_pendientes_georreferenciadas.csv`
- `Inventario_forestal.csv`
- `inventario_cam.csv`
- `podas_ejecutadas.csv`

Además, coloca `logo_esip_clear.png` en la raíz del proyecto.

## ✨ Notas

- Ambos tableros utilizan caché de Streamlit (`@st.cache_data`) para acelerar la carga.
- La V2 realiza los cruces principales usando `ID_Luminaria`, por lo que es ideal para análisis ligados a luminarias.
- Los datos se limpian para normalizar campos y evitar inconsistencias de mayúsculas/minúsculas.
