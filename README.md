# 🚚 FIFCO Route Planner — CEDI Alajuela

Herramienta de optimización logística para la planificación de rutas de distribución desde el CEDI de FIFCO en Alajuela, Costa Rica.

---

## 📋 Contexto del problema

**FIFCO** opera un Centro de Distribución (CEDI) en **Alajuela, Costa Rica**. Desde este CEDI se distribuyen tres productos de cerveza hacia los **16 cantones** de la provincia de Alajuela.

Este proyecto implementa un **CVRP (Capacitated Vehicle Routing Problem)**: un problema de ruteo de vehículos con restricción de capacidad de carga.

---

## 🍺 Productos distribuidos

| Producto | Demanda semanal (pallets) |
|----------|--------------------------|
| Imperial | 390 |
| Pilsen   | 194 |
| Tropical | 194 |
| **Total** | **778** |

---

## 🗺️ Cantones atendidos

16 cantones de la provincia de Alajuela:

Alajuela, San Ramón, Grecia, San Mateo, Atenas, Naranjo, Palmares, Poás, Orotina, San Carlos, Zarcero, Sarchí, Upala, Los Chiles, Guatuso, Río Cuarto.

---

## 🚛 Capacidad máxima por trip

**24 pallets** por viaje/trip (sumando Imperial + Pilsen + Tropical).

> ⚠️ Esta es la capacidad **máxima**, no mínima. Ningún camión puede cargar más de 24 pallets.

---

## ⚙️ Parámetros operativos por defecto

| Parámetro | Valor |
|-----------|-------|
| Capacidad máx. por trip | 24 pallets |
| Velocidad promedio | 40 km/h |
| Tiempo por parada | 15 min |
| Tiempo por pallet | 3 min |
| Tiempo de reload entre trips | 20 min |
| Jornada máx. por camión físico | 480 min (8 h) |
| Flota mínima estimada | 33 camiones |

Todos estos parámetros se pueden ajustar desde la barra lateral de la aplicación.

---

## 📐 ¿Qué es CVRP?

El **Capacitated Vehicle Routing Problem** busca minimizar la distancia total recorrida por una flota de vehículos, respetando la capacidad de carga de cada vehículo y garantizando que toda la demanda sea atendida.

**Función objetivo:**

```
Min Z = Σ d(i,j) · y(i,j)
```

**Restricciones clave:**
1. Balance de camiones en cada nodo (entradas = salidas)
2. Balance de carga en cada cantón (entregado = demandado)
3. Carga total del CEDI = 778 pallets
4. Capacidad por arco: `f(i,j) ≤ 24 · y(i,j)`

---

## 🧩 Estructura del proyecto

```
fifco_route_planner/
├── app.py              # Aplicación principal Streamlit
├── requirements.txt    # Dependencias Python
├── README.md           # Documentación
└── .gitignore          # Archivos excluidos de Git
```

---

## 🖥️ Cómo correr localmente

### 1. Clonar o crear el repositorio

```bash
git clone https://github.com/TU_USUARIO/fifco-route-planner.git
cd fifco-route-planner
```

### 2. Crear y activar entorno virtual

**Linux / macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows (cmd):**
```bash
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`.

> **Nota sobre OR-Tools:** Si la instalación de `ortools` falla (puede ocurrir en algunas configuraciones), la aplicación funcionará correctamente usando la heurística de fallback. Para instalar sin OR-Tools:
> ```bash
> pip install streamlit pandas numpy plotly openpyxl
> ```

---

## 📤 Cómo subir a GitHub

### 1. Inicializar repositorio Git

```bash
git init
git add .
git commit -m "Initial FIFCO route planner app"
```

### 2. Crear repositorio en GitHub

- Ve a [github.com](https://github.com) y crea un nuevo repositorio llamado `fifco-route-planner`.
- No inicialices con README (ya tenemos uno).

### 3. Conectar y subir

```bash
git branch -M main
git remote add origin https://github.com/TU_USUARIO/fifco-route-planner.git
git push -u origin main
```

> Reemplaza `TU_USUARIO` con tu nombre de usuario de GitHub.

---

## ☁️ Cómo desplegar en Streamlit Cloud

### 1. Requisitos previos

- Cuenta en [streamlit.io](https://streamlit.io) (gratuita)
- Repositorio en GitHub con el código subido

### 2. Desplegar

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Haz clic en **"New app"**
3. Conecta tu cuenta de GitHub si aún no lo has hecho
4. Selecciona el repositorio `fifco-route-planner`
5. Selecciona la rama: `main`
6. En **"Main file path"** escribe: `app.py`
7. Haz clic en **"Deploy!"**

Streamlit Cloud instalará automáticamente las dependencias de `requirements.txt`.

### 3. URL de la aplicación

Tu aplicación estará disponible en:
```
https://TU_USUARIO-fifco-route-planner-app-XXXXX.streamlit.app
```

> **Nota:** OR-Tools puede no estar disponible en Streamlit Cloud según la versión del runtime. La aplicación funcionará con la heurística en ese caso.

---

## ⚠️ Limitaciones del modelo

- Herramienta de **planeación aproximada**; los resultados deben validarse con la operación real.
- No considera tráfico real ni condiciones viales variables.
- No considera ventanas horarias de entrega en cada cantón.
- No considera restricciones específicas de conductores.
- No considera tiempos de espera en el cliente.
- No considera disponibilidad real diaria de la flota.
- No considera restricciones de peso/volumen diferenciadas por producto.
- No considera planificación multi-día.
- La matriz de distancias es un dato fijo por carretera.

---

## 🔮 Posibles mejoras futuras

- Integrar ventanas horarias (VRPTW).
- Restricciones de peso volumétrico por tipo de camión.
- Planificación multi-día y gestión de turnos de conductores.
- Integración con datos de tráfico en tiempo real (Google Maps API).
- Optimización por costo total (combustible + peajes + horas-chofer).
- Dashboard de seguimiento de rutas en tiempo real.
- Carga dinámica de demanda desde archivo Excel.

---

## 📄 Licencia

Proyecto de uso interno FIFCO. Todos los derechos reservados.
