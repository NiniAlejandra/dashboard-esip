# 🌳 App Streamlit - Inventario de Podas - ESIP

Aplicación web interactiva para visualizar y gestionar el inventario de podas de ESIP.

## 📋 Características

- **Visualización de todas las solicitudes** (1.380+ registros)
- **Filtros interactivos**:
  - Por Comuna (selección múltiple)
  - Por Estado de Inventario (SI / NO / Todos)
- **Mapa interactivo** con:
  - Puntos coloreados: 🟢 Verde (Inventariado=SI) y 🔴 Rojo (Inventariado=NO)
  - Control de capas para mostrar/ocultar grupos
  - Ruta óptima calculada cuando se filtran solo registros con Inventariado=SI
- **Gráficos estadísticos**:
  - Gráfico de barras apiladas por comuna (Total, SI, NO)
  - Tabla resumen con estadísticas
- **Unión con Inventario Forestal**:
  - Muestra detalles de especie, altura, CAP, DAP, etc. cuando Inventariado=SI
- **Exportación de datos** filtrados en formato CSV

## 🚀 Instalación

1. Asegúrate de tener Python 3.8 o superior instalado

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## 📂 Archivos Requeridos

La aplicación requiere los siguientes archivos en el directorio raíz:

- `pqr_pendientes_georreferenciadas.csv` - Datos principales de solicitudes
- `Inventario_podas.xlsx` - Inventario forestal (hoja "Hoja1")
- `logo_esip_clear.png` - Logo institucional

## ▶️ Ejecución

Para ejecutar la aplicación:

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 📊 Estructura de Datos

### CSV Principal (`pqr_pendientes_georreferenciadas.csv`)

Columnas esperadas:
- `Sticker` - Identificador del sticker
- `Id` - ID de la solicitud
- `Comuna` - Comuna (COMUNA 01, COMUNA 02, etc.)
- `Tipo` - Tipo de solicitud
- `Estado` - Estado de la solicitud
- `P.Q.R.S` - Información de PQR
- `Latitud` / `Longitud` - Coordenadas geográficas
- `Inventariado` - SI o NO

### Excel Inventario Forestal (`Inventario_podas.xlsx`)

Debe contener una hoja "Hoja1" con columnas como:
- `STICKER` / `ID` - Para unión con datos principales
- `Nombre común` / `Nombre cientifico` - Información de especie
- `Altura m`, `CAP m`, `DAP` - Medidas del árbol
- `Proyección de Copa (m)` - Proyección de copa
- `Bueno`, `Regular`, `Malo` - Estado del árbol

## 🔧 Tecnologías Utilizadas

- **Streamlit** - Framework para aplicaciones web
- **Folium** - Visualización de mapas interactivos
- **Pandas** - Manipulación de datos
- **Plotly** - Gráficos interactivos
- **NumPy / SciPy** - Cálculos numéricos y optimización

## 📝 Notas

- La ruta óptima utiliza un algoritmo de vecino más cercano para calcular el recorrido más eficiente
- Los datos se cargan con caché para mejorar el rendimiento
- La unión con el inventario forestal solo se realiza para registros con Inventariado=SI

## 👥 Autor

ESIP 2025

