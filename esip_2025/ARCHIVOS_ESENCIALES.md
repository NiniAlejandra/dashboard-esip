# 📋 Archivos Esenciales para la App

## ✅ Archivos OBLIGATORIOS (la app NO funciona sin estos):

1. **App.py** - Archivo principal de la aplicación Streamlit
2. **requirements.txt** - Dependencias de Python (streamlit, pandas, plotly, numpy)
3. **Ind_%.csv** o **porcentaje.csv** - Datos de indicadores porcentuales
4. **Ind_n.csv** o **Numericos.csv** - Datos de indicadores numéricos
5. **tipo_indicadores.csv** - Tipos de indicadores (debe tener columnas 'ID' y 'Tipo')

## 🎨 Archivos OPCIONALES (la app funciona sin estos, pero mejoran la presentación):

6. **logo_esip_clear.png** - Logo de la empresa (si no existe, simplemente no se muestra)
7. **Readme.md** - Documentación (si no existe, simplemente no se muestra en el expander)

## 📁 Estructura Recomendada en la Raíz:

```
tu_proyecto/
├── App.py                          ← Archivo principal
├── requirements.txt                ← Dependencias
├── Ind_%.csv                       ← Datos porcentuales
├── Ind_n.csv                       ← Datos numéricos
├── tipo_indicadores.csv            ← Tipos de indicadores
├── logo_esip_clear.png             ← Logo (opcional)
└── Readme.md                       ← Documentación (opcional)
```

## 🔍 Notas Importantes:

- El código busca archivos con nombres alternativos:
  - Para porcentajes: `Ind_%.csv` o `porcentaje.csv`
  - Para numéricos: `Ind_n.csv` o `Numericos.csv`
- Todos los archivos deben estar en la **misma carpeta** que `App.py`
- El código usa `Path(__file__).parent` para encontrar los archivos relativos a donde está `App.py`



