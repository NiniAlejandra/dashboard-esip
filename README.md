# 📊 Dashboard Indicadores ESIP SAS ESP

Dashboard interactivo para visualización de indicadores internos de ESIP SAS ESP.

## 🚀 Demo en Vivo
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://dashboard-esip.streamlit.app/)

## 📋 Características Principales

- ✅ **Datos Unificados**: Numéricos y porcentuales en un solo dataset
- ✅ **Filtros Inteligentes**: En cascada por área e indicador
- ✅ **Filtros Especializados**: Para "Atención al Usuario"
- ✅ **Gráficos Especializados**: Optimizados por tipo de indicador
- ✅ **Orden Cronológico**: Enero a Septiembre garantizado
- ✅ **Valores Limpios**: Sin ceros decimales innecesarios
- ✅ **Tabla Completa**: Con fila de totales resaltada
- ✅ **Logo Corporativo**: ESIP en esquina superior derecha

## 🛠️ Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/dashboard-esip.git
cd dashboard-esip

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar dashboard
streamlit run dashboard_indicadores_final.py
```

## 📊 Archivos de Datos

- `Numericos.csv`: Indicadores numéricos
- `porcentaje.csv`: Indicadores porcentuales  
- `logo_esip_clear.png`: Logo de la empresa

## 🔍 Uso del Dashboard

### Filtros Principales
- **Área**: Selecciona área específica o "Todas"
- **Indicador**: Multiselect filtrado por área seleccionada

### Filtros Adicionales (Solo "Atención al Usuario")
- **Subcategoría**: Comunas, Canal de Recepción, Subtema, Remitido a, Otros
- **Comunas**: Filtro específico si se selecciona "Comunas"

### Pestañas Especializadas
- **📈 Tendencias Numéricas**: Gráficos de línea para indicadores numéricos
- **📊 Indicadores Porcentuales**: Barras o líneas según cantidad
- **📋 Tabla de Datos**: Vista tabular con totales resaltados

## 🎯 Características Técnicas

- **Escalas Adaptativas**: Logarítmica para números grandes
- **Tooltips Informativos**: Valores exactos al pasar el mouse
- **Títulos Dinámicos**: Adaptados a filtros seleccionados
- **Abreviaciones**: Nombres largos manejados elegantemente
- **Resumen Ejecutivo**: Métricas que se actualizan dinámicamente

## 📈 Interpretación de Resultados

### Indicadores Numéricos
- Escala logarítmica automática para rangos >100x
- Líneas múltiples con colores distintivos
- Tooltips con valores exactos

### Indicadores Porcentuales
- Escala fija 0-120% para consistencia visual
- Barras agrupadas (≤3 indicadores) o líneas (>3)
- Valores mostrados encima de barras

## 🚀 Deploy

Este dashboard está optimizado para deploy en:
- **Streamlit Cloud** (recomendado)
- **Heroku**
- **Render**
- **Railway**

## 👥 Desarrollado por

**Alejandra Valderrama**  
Jefe de Investigaciones y Desarrollo Social  
ESIP SAS ESP

## 📄 Licencia

Proyecto interno de ESIP SAS ESP - Todos los derechos reservados.

---

**¡Dashboard profesional para análisis de indicadores empresariales!** 🚀