"""
FIFCO Route Planner — CEDI Alajuela
Capacitated Vehicle Routing Problem (CVRP)
"""

import streamlit as st
import pandas as pd
import numpy as np
import math
import io
from copy import deepcopy

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="FIFCO Route Planner — CEDI Alajuela",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* Fonts */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Syne:wght@700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Background */
.main .block-container {
    background: #F5F6F8;
    padding-top: 1.5rem;
    max-width: 1400px;
}

/* Header */
.app-header {
    background: linear-gradient(135deg, #1F3A5F 0%, #2C5282 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    color: white;
}
.app-header h1 {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    margin: 0;
    color: white;
}
.app-header p {
    margin: 0.3rem 0 0 0;
    color: #B8C8E0;
    font-size: 0.95rem;
}
.header-badge {
    display: inline-block;
    background: #B89100;
    color: white;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.6rem;
}

/* Section titles */
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #1F3A5F;
    border-left: 4px solid #B89100;
    padding-left: 12px;
    margin: 1.5rem 0 1rem 0;
}

/* Metric cards */
.metric-card {
    background: white;
    border-radius: 12px;
    padding: 1.1rem 1.2rem;
    box-shadow: 0 1px 4px rgba(31,58,95,0.08);
    border-top: 3px solid #1F3A5F;
    height: 100%;
}
.metric-card.gold { border-top-color: #B89100; }
.metric-card.red  { border-top-color: #B00020; }
.metric-card.green{ border-top-color: #2E7D32; }

.metric-card .label {
    font-size: 0.75rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
}
.metric-card .value {
    font-family: 'Syne', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: #1F3A5F;
    line-height: 1.1;
}
.metric-card .sub {
    font-size: 0.78rem;
    color: #888;
    margin-top: 3px;
}

/* Alert boxes */
.alert-ok      { background:#E8F5E9; border-left:4px solid #2E7D32; padding:10px 14px; border-radius:8px; color:#1B5E20; margin:6px 0; }
.alert-warn    { background:#FFF8E1; border-left:4px solid #B89100; padding:10px 14px; border-radius:8px; color:#6D4C00; margin:6px 0; }
.alert-error   { background:#FFEBEE; border-left:4px solid #B00020; padding:10px 14px; border-radius:8px; color:#7F0015; margin:6px 0; }

/* Tables */
.stDataFrame { border-radius: 10px; overflow: hidden; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #1F3A5F;
}
[data-testid="stSidebar"] * {
    color: #E8EEF6 !important;
}
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stCheckbox label {
    color: #B8C8E0 !important;
}

/* Model box */
.model-box {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 4px rgba(31,58,95,0.08);
    font-family: 'DM Mono', monospace;
    border-left: 5px solid #B89100;
    margin: 1rem 0;
}
.model-box h4 { color: #1F3A5F; margin-bottom: 8px; }
.model-box code { background: #F5F6F8; padding: 2px 6px; border-radius: 4px; }

/* Method badge */
.method-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
    margin-left: 10px;
}
.method-ortools { background: #E3F2FD; color: #1565C0; }
.method-heuristic { background: #FFF8E1; color: #6D4C00; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# BASE DATA
# ─────────────────────────────────────────────
def load_base_data():
    """Load all fixed problem data."""
    nodes = {
        0:  "CD Alajuela",
        1:  "Alajuela",
        2:  "San Ramón",
        3:  "Grecia",
        4:  "San Mateo",
        5:  "Atenas",
        6:  "Naranjo",
        7:  "Palmares",
        8:  "Poás",
        9:  "Orotina",
        10: "San Carlos",
        11: "Zarcero",
        12: "Sarchí",
        13: "Upala",
        14: "Los Chiles",
        15: "Guatuso",
        16: "Río Cuarto",
    }

    demand_data = [
        # node, canton, imperial, pilsen, tropical
        (0,  "CD Alajuela", 0,   0,   0),
        (1,  "Alajuela",    121, 60,  60),
        (2,  "San Ramón",   35,  17,  17),
        (3,  "Grecia",      29,  14,  14),
        (4,  "San Mateo",   3,   1,   1),
        (5,  "Atenas",      11,  6,   6),
        (6,  "Naranjo",     17,  9,   9),
        (7,  "Palmares",    15,  7,   7),
        (8,  "Poás",        14,  7,   7),
        (9,  "Orotina",     9,   5,   5),
        (10, "San Carlos",  75,  37,  37),
        (11, "Zarcero",     6,   3,   3),
        (12, "Sarchí",      8,   4,   4),
        (13, "Upala",       22,  11,  11),
        (14, "Los Chiles",  13,  7,   7),
        (15, "Guatuso",     7,   3,   3),
        (16, "Río Cuarto",  5,   3,   3),
    ]

    df_demand = pd.DataFrame(demand_data, columns=["Nodo", "Cantón", "Imperial", "Pilsen", "Tropical"])
    df_demand["Demanda_Total"] = df_demand["Imperial"] + df_demand["Pilsen"] + df_demand["Tropical"]
    df_demand["Trips_Minimos"] = df_demand["Demanda_Total"].apply(lambda x: math.ceil(x / 24) if x > 0 else 0)
    df_demand["Clasificacion"] = df_demand["Demanda_Total"].apply(
        lambda x: "Alta demanda" if x > 24 else ("Baja demanda" if x > 0 else "CEDI")
    )

    distance_matrix = [
        [0,   0,   38,  17,  47,  25,  26,  32,  10,  47,  54,  34,  22,  171, 164, 131, 48],
        [0,   0,   38,  17,  47,  25,  26,  32,  10,  47,  54,  34,  22,  171, 164, 131, 48],
        [38,  38,  0,   22,  22,  21,  13,  7,   34,  27,  35,  18,  17,  140, 141, 100, 52],
        [17,  17,  22,  0,   36,  17,  10,  18,  12,  38,  40,  19,  5,   156, 150, 115, 43],
        [47,  47,  22,  36,  0,   22,  30,  21,  47,  6,   57,  40,  32,  153, 159, 114, 73],
        [25,  25,  21,  17,  22,  0,   17,  14,  26,  22,  51,  30,  16,  161, 160, 120, 59],
        [26,  26,  13,  10,  30,  17,  0,   10,  21,  34,  34,  13,  4,   147, 144, 107, 44],
        [32,  32,  7,   18,  21,  14,  10,  0,   29,  24,  39,  20,  13,  147, 147, 107, 53],
        [10,  10,  34,  12,  47,  26,  21,  29,  0,   48,  45,  26,  17,  162, 154, 122, 39],
        [47,  47,  27,  38,  6,   22,  34,  24,  48,  0,   62,  44,  35,  159, 165, 120, 77],
        [54,  54,  35,  40,  57,  51,  34,  39,  45,  62,  0,   22,  37,  118, 110, 77,  30],
        [34,  34,  18,  19,  40,  30,  13,  20,  26,  44,  22,  0,   15,  137, 132, 97,  34],
        [22,  22,  17,  5,   32,  16,  4,   13,  17,  35,  37,  15,  0,   151, 147, 111, 43],
        [171, 171, 140, 156, 153, 161, 147, 147, 162, 159, 118, 137, 151, 0,   47,  40,  138],
        [164, 164, 141, 150, 159, 160, 144, 147, 154, 165, 110, 132, 147, 47,  0,   53,  122],
        [131, 131, 100, 115, 114, 120, 107, 107, 122, 120, 77,  97,  111, 40,  53,  0,   100],
        [48,  48,  52,  43,  73,  59,  44,  53,  39,  77,  30,  34,  43,  138, 122, 100, 0],
    ]

    return nodes, df_demand, distance_matrix


# ─────────────────────────────────────────────
# VALIDATIONS
# ─────────────────────────────────────────────
def validate_distance_matrix(dm):
    results = []
    n = len(dm)
    # Size
    is_17 = (n == 17)
    row_lens = [len(r) for r in dm]
    is_square = all(l == n for l in row_lens)
    results.append(("Matriz 17×17", "✅ OK" if is_17 and is_square else "❌ Error",
                     f"Dimensión: {n}×{max(row_lens)}", "OK" if is_17 and is_square else "Error"))
    # Diagonal zero
    diag_ok = all(dm[i][i] == 0 for i in range(n))
    results.append(("Diagonal cero", "✅ OK" if diag_ok else "❌ Error",
                     "Todos los nodos tienen distancia 0 a sí mismos" if diag_ok else "Hay valores no cero en diagonal",
                     "OK" if diag_ok else "Error"))
    # Symmetry
    sym_ok = all(dm[i][j] == dm[j][i] for i in range(n) for j in range(n))
    results.append(("Simetría", "✅ OK" if sym_ok else "⚠️ Advertencia",
                     "Matriz simétrica" if sym_ok else "La matriz no es completamente simétrica",
                     "OK" if sym_ok else "Advertencia"))
    return results


def validate_demand(df_demand):
    results = []
    total = df_demand["Demanda_Total"].sum()
    imp   = df_demand["Imperial"].sum()
    pil   = df_demand["Pilsen"].sum()
    trop  = df_demand["Tropical"].sum()
    results.append(("Demanda total = 778", "✅ OK" if total == 778 else "❌ Error",
                     f"Total: {total}", "OK" if total == 778 else "Error"))
    results.append(("Imperial = 390", "✅ OK" if imp == 390 else "❌ Error",
                     f"Imperial: {imp}", "OK" if imp == 390 else "Error"))
    results.append(("Pilsen = 194", "✅ OK" if pil == 194 else "❌ Error",
                     f"Pilsen: {pil}", "OK" if pil == 194 else "Error"))
    results.append(("Tropical = 194", "✅ OK" if trop == 194 else "❌ Error",
                     f"Tropical: {trop}", "OK" if trop == 194 else "Error"))
    return results


# ─────────────────────────────────────────────
# ROUTE & TIME CALCULATIONS
# ─────────────────────────────────────────────
def calculate_route_distance(route, distance_matrix):
    """Sum arc distances for a route list of node indices."""
    total = 0.0
    for i in range(len(route) - 1):
        total += distance_matrix[route[i]][route[i + 1]]
    return total


def calculate_trip_time(distance_km, stops, pallets, speed_kmh, time_per_stop, time_per_pallet):
    """Returns trip duration in minutes."""
    travel_min = (distance_km / speed_kmh) * 60.0 if speed_kmh > 0 else 0
    return travel_min + stops * time_per_stop + pallets * time_per_pallet


# ─────────────────────────────────────────────
# SPLIT DEMAND INTO DELIVERIES
# ─────────────────────────────────────────────
def split_demand_into_deliveries(df_demand, capacity):
    """
    Returns a list of delivery dicts:
    {node, canton, imperial, pilsen, tropical, total}
    Each delivery respects the capacity constraint.
    """
    deliveries = []
    client_rows = df_demand[df_demand["Nodo"] != 0].copy()

    for _, row in client_rows.iterrows():
        node    = int(row["Nodo"])
        canton  = row["Cantón"]
        imp_tot = int(row["Imperial"])
        pil_tot = int(row["Pilsen"])
        trop_tot= int(row["Tropical"])
        total   = imp_tot + pil_tot + trop_tot

        if total == 0:
            continue

        remaining = {"imperial": imp_tot, "pilsen": pil_tot, "tropical": trop_tot}

        while sum(remaining.values()) > 0:
            rem_total = sum(remaining.values())
            chunk = min(rem_total, capacity)

            # Distribute proportionally within capacity
            ratio = chunk / rem_total
            chunk_imp  = min(math.floor(remaining["imperial"]  * ratio), remaining["imperial"])
            chunk_pil  = min(math.floor(remaining["pilsen"]    * ratio), remaining["pilsen"])
            chunk_trop = min(math.floor(remaining["tropical"]  * ratio), remaining["tropical"])

            assigned = chunk_imp + chunk_pil + chunk_trop
            leftover = chunk - assigned

            # Distribute leftover to largest remaining
            products_order = sorted(
                [("imperial", remaining["imperial"] - chunk_imp),
                 ("pilsen",   remaining["pilsen"]   - chunk_pil),
                 ("tropical", remaining["tropical"] - chunk_trop)],
                key=lambda x: -x[1]
            )
            add = {"imperial": chunk_imp, "pilsen": chunk_pil, "tropical": chunk_trop}
            for i in range(int(leftover)):
                p = products_order[i % len(products_order)][0]
                if add[p] < remaining[p]:
                    add[p] += 1

            # Final cap check
            total_chunk = add["imperial"] + add["pilsen"] + add["tropical"]
            if total_chunk > capacity:
                # Trim from tropical first
                excess = total_chunk - capacity
                for p in ["tropical", "pilsen", "imperial"]:
                    trim = min(excess, add[p])
                    add[p] -= trim
                    excess -= trim
                    remaining[p] += trim
                    if excess == 0:
                        break

            if add["imperial"] + add["pilsen"] + add["tropical"] == 0:
                break

            deliveries.append({
                "node": node, "canton": canton,
                "imperial": add["imperial"], "pilsen": add["pilsen"],
                "tropical": add["tropical"],
                "total": add["imperial"] + add["pilsen"] + add["tropical"]
            })

            remaining["imperial"]  -= add["imperial"]
            remaining["pilsen"]    -= add["pilsen"]
            remaining["tropical"]  -= add["tropical"]

    return deliveries


# ─────────────────────────────────────────────
# HEURISTIC TRIP GENERATION
# ─────────────────────────────────────────────
def generate_trips_heuristic(deliveries, distance_matrix, capacity, speed_kmh, time_per_stop, time_per_pallet):
    """
    Nearest-neighbor + bin-packing heuristic.
    Groups deliveries into trips respecting capacity.
    Returns list of trip dicts.
    """
    # Sort deliveries: larger first to fill trips
    sorted_deliveries = sorted(deliveries, key=lambda d: -d["total"])
    used = [False] * len(sorted_deliveries)
    trips = []
    trip_id = 1

    for i, d in enumerate(sorted_deliveries):
        if used[i]:
            continue
        used[i] = True

        trip_nodes   = [d["node"]]
        trip_imp     = d["imperial"]
        trip_pil     = d["pilsen"]
        trip_trop    = d["tropical"]
        trip_total   = d["total"]

        # Try to fill remaining capacity with nearby deliveries
        remaining_cap = capacity - trip_total
        last_node = d["node"]

        while remaining_cap > 0:
            best_j   = None
            best_dist = float("inf")

            for j, d2 in enumerate(sorted_deliveries):
                if used[j]:
                    continue
                if d2["total"] > remaining_cap:
                    continue
                dist = distance_matrix[last_node][d2["node"]]
                if dist < best_dist:
                    best_dist = dist
                    best_j = j

            if best_j is None:
                break

            d2 = sorted_deliveries[best_j]
            used[best_j] = True
            trip_nodes.append(d2["node"])
            trip_imp   += d2["imperial"]
            trip_pil   += d2["pilsen"]
            trip_trop  += d2["tropical"]
            trip_total += d2["total"]
            remaining_cap -= d2["total"]
            last_node = d2["node"]

        # Build route: 0 → nodes → 0
        route = [0] + trip_nodes + [0]
        dist_km = calculate_route_distance(route, distance_matrix)
        stops   = len(trip_nodes)
        time_min = calculate_trip_time(dist_km, stops, trip_total, speed_kmh, time_per_stop, time_per_pallet)

        if trip_total > capacity:
            estado = "❌ Revisar capacidad"
        elif time_min > 480:
            estado = "⚠️ Supera 8 h"
        elif len(trip_nodes) == 1:
            estado = "🔵 Trip dedicado"
        else:
            estado = "✅ OK"

        trips.append({
            "Trip_ID":          f"T{trip_id:03d}",
            "Ruta_nodos":       str(route),
            "Ruta_cantones":    "0→" + "→".join([str(n) for n in trip_nodes]) + "→0",
            "Cantones_visitados": stops,
            "Imperial":         trip_imp,
            "Pilsen":           trip_pil,
            "Tropical":         trip_trop,
            "Carga_total":      trip_total,
            "Distancia_km":     round(dist_km, 1),
            "Paradas":          stops,
            "Tiempo_min":       round(time_min, 1),
            "Tiempo_horas":     round(time_min / 60, 2),
            "Estado":           estado,
            "_route":           route,
        })
        trip_id += 1

    return trips


# ─────────────────────────────────────────────
# OR-TOOLS TRIP GENERATION (stub/wrapper)
# ─────────────────────────────────────────────
def try_generate_trips_ortools(deliveries, distance_matrix, capacity, speed_kmh, time_per_stop, time_per_pallet):
    """
    Attempts to use OR-Tools for routing.
    Returns (trips, success_bool).
    """
    if not ORTOOLS_AVAILABLE:
        return None, False

    try:
        # Build aggregated node list: depot + one node per delivery
        depot = 0
        # Aggregate deliveries: group same-node deliveries won't work well for CVRP
        # Use individual deliveries as customers
        customers = deliveries  # list of dicts with node, total
        n_customers = len(customers)
        n_locations = n_customers + 1  # depot + customers

        # Build distance matrix for OR-Tools (indexed by location)
        # location 0 = depot, location i+1 = customer i
        def loc_dist(i, j):
            if i == 0 and j == 0:
                return 0
            ni = 0 if i == 0 else customers[i - 1]["node"]
            nj = 0 if j == 0 else customers[j - 1]["node"]
            return int(distance_matrix[ni][nj])

        dm_ort = [[loc_dist(i, j) for j in range(n_locations)] for i in range(n_locations)]

        # demands
        demands = [0] + [c["total"] for c in customers]

        n_vehicles = math.ceil(sum(c["total"] for c in customers) / capacity) + 5

        manager = pywrapcp.RoutingIndexManager(n_locations, n_vehicles, 0)
        routing = pywrapcp.RoutingModel(manager)

        def dist_callback(i, j):
            return dm_ort[manager.IndexToNode(i)][manager.IndexToNode(j)]

        transit_cb = routing.RegisterTransitCallback(dist_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)

        def demand_callback(idx):
            node = manager.IndexToNode(idx)
            return demands[node]

        demand_cb = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_cb, 0, [capacity] * n_vehicles, True, "Capacity"
        )

        search_params = pywrapcp.DefaultRoutingSearchParameters()
        search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        search_params.time_limit.seconds = 30

        solution = routing.SolveWithParameters(search_params)

        if not solution:
            return None, False

        trips = []
        trip_id = 1
        for v in range(n_vehicles):
            idx = routing.Start(v)
            route_nodes = []
            while not routing.IsEnd(idx):
                node = manager.IndexToNode(idx)
                if node != 0:
                    route_nodes.append(node)
                idx = solution.Value(routing.NextVar(idx))
            if not route_nodes:
                continue

            # Map location indices back to real node indices
            real_nodes = [customers[n - 1]["node"] for n in route_nodes]
            trip_imp   = sum(customers[n - 1]["imperial"] for n in route_nodes)
            trip_pil   = sum(customers[n - 1]["pilsen"]   for n in route_nodes)
            trip_trop  = sum(customers[n - 1]["tropical"] for n in route_nodes)
            trip_total = trip_imp + trip_pil + trip_trop

            route = [0] + real_nodes + [0]
            dist_km  = calculate_route_distance(route, distance_matrix)
            stops    = len(real_nodes)
            time_min = calculate_trip_time(dist_km, stops, trip_total, speed_kmh, time_per_stop, time_per_pallet)

            estado = "✅ OK"
            if trip_total > capacity:
                estado = "❌ Revisar capacidad"
            elif time_min > 480:
                estado = "⚠️ Supera 8 h"
            elif stops == 1:
                estado = "🔵 Trip dedicado"

            trips.append({
                "Trip_ID":          f"T{trip_id:03d}",
                "Ruta_nodos":       str(route),
                "Ruta_cantones":    "0→" + "→".join([str(n) for n in real_nodes]) + "→0",
                "Cantones_visitados": stops,
                "Imperial":         trip_imp,
                "Pilsen":           trip_pil,
                "Tropical":         trip_trop,
                "Carga_total":      trip_total,
                "Distancia_km":     round(dist_km, 1),
                "Paradas":          stops,
                "Tiempo_min":       round(time_min, 1),
                "Tiempo_horas":     round(time_min / 60, 2),
                "Estado":           estado,
                "_route":           route,
            })
            trip_id += 1

        return trips, True

    except Exception as e:
        return None, False


def generate_trips(deliveries, distance_matrix, capacity, speed_kmh, time_per_stop, time_per_pallet, use_ortools):
    """Main dispatcher."""
    method = "Heurística fallback"
    trips = None

    if use_ortools and ORTOOLS_AVAILABLE:
        trips, ok = try_generate_trips_ortools(
            deliveries, distance_matrix, capacity, speed_kmh, time_per_stop, time_per_pallet
        )
        if ok and trips:
            method = "OR-Tools"
        else:
            trips = None

    if trips is None:
        trips = generate_trips_heuristic(
            deliveries, distance_matrix, capacity, speed_kmh, time_per_stop, time_per_pallet
        )

    return trips, method


# ─────────────────────────────────────────────
# ASSIGN TRIPS TO TRUCKS (BIN PACKING)
# ─────────────────────────────────────────────
def assign_trips_to_trucks(trips, max_jornada, reload_time):
    """
    Bin-packing: assign trips to physical trucks.
    Returns list of truck dicts.
    """
    trucks = []
    # Sort trips by time descending
    sorted_trips = sorted(trips, key=lambda t: -t["Tiempo_min"])

    for trip in sorted_trips:
        t_time = trip["Tiempo_min"]
        placed = False

        for truck in trucks:
            if truck["_dedicated"]:
                continue
            n_existing = len(truck["_trips"])
            reloads = n_existing  # one reload per existing trip boundary
            projected = truck["_time_used"] + t_time + (reload_time if n_existing > 0 else 0)

            if projected <= max_jornada:
                truck["_trips"].append(trip["Trip_ID"])
                truck["_time_used"] += t_time + (reload_time if n_existing > 0 else 0)
                truck["_dist_total"] += trip["Distancia_km"]
                truck["_carga_total"] += trip["Carga_total"]
                placed = True
                break

        if not placed:
            dedicated = t_time > max_jornada
            truck = {
                "_id":          len(trucks) + 1,
                "_trips":       [trip["Trip_ID"]],
                "_time_used":   t_time,
                "_dist_total":  trip["Distancia_km"],
                "_carga_total": trip["Carga_total"],
                "_dedicated":   dedicated,
            }
            trucks.append(truck)

    result = []
    for t in trucks:
        util = (t["_time_used"] / max_jornada) * 100
        t_libre = max(0, max_jornada - t["_time_used"])

        if t["_dedicated"] or t["_time_used"] > max_jornada:
            estado = "⚠️ Dedicado / revisar"
        elif util >= 90:
            estado = "🔴 Alta utilización"
        elif util < 40:
            estado = "🔵 Subutilizado"
        else:
            estado = "✅ OK"

        result.append({
            "Camion_ID":          f"C{t['_id']:03d}",
            "Trips_asignados":    ", ".join(t["_trips"]),
            "Cantidad_trips":     len(t["_trips"]),
            "Tiempo_total_min":   round(t["_time_used"], 1),
            "Tiempo_total_horas": round(t["_time_used"] / 60, 2),
            "Tiempo_libre_min":   round(t_libre, 1),
            "Utilizacion_pct":    round(util, 1),
            "Distancia_total_km": round(t["_dist_total"], 1),
            "Carga_total_pallets":t["_carga_total"],
            "Estado":             estado,
        })

    return result


# ─────────────────────────────────────────────
# SUMMARY & VALIDATIONS
# ─────────────────────────────────────────────
def create_summary(trips, trucks, df_demand, fleet_estimate):
    df_trips = pd.DataFrame(trips)
    df_trucks = pd.DataFrame(trucks)

    # Tiempo total del proceso = tiempo máximo que tarda algún camión (el último en terminar)
    tiempo_total_proceso_min = round(df_trucks["Tiempo_total_min"].max(), 1) if len(trucks) > 0 else 0
    tiempo_total_proceso_h   = round(tiempo_total_proceso_min / 60, 2)

    s = {
        "cantones_atendidos":        16,
        "demanda_total":             778,
        "imperial_total":            390,
        "pilsen_total":              194,
        "tropical_total":            194,
        "trips_generados":           len(trips),
        "distancia_total":           round(df_trips["Distancia_km"].sum(), 1),
        "tiempo_total_min":          round(df_trips["Tiempo_min"].sum(), 1),
        "tiempo_total_proceso_min":  tiempo_total_proceso_min,
        "tiempo_total_proceso_h":    tiempo_total_proceso_h,
        "camiones_requeridos":       len(trucks),
        "flota_estimada":            fleet_estimate,
        "diferencia_flota":          fleet_estimate - len(trucks),
        "util_promedio":             round(df_trucks["Utilizacion_pct"].mean(), 1) if len(trucks) > 0 else 0,
        "trips_supera_8h":           len(df_trips[df_trips["Tiempo_min"] > 480]),
        "trips_cap_error":           len(df_trips[df_trips["Carga_total"] > 24]),
        "carga_prom_trip":           round(df_trips["Carga_total"].mean(), 1),
        "util_prom_trip":            round((df_trips["Carga_total"].mean() / 24) * 100, 1),
        "trips_llenos":              len(df_trips[df_trips["Carga_total"] == 24]),
        "trips_parciales":           len(df_trips[df_trips["Carga_total"] < 24]),
    }
    return s


def create_validations_table(trips, trucks, distance_matrix, df_demand, fleet_estimate, max_jornada, capacity):
    vals = []
    df_trips  = pd.DataFrame(trips)
    df_trucks = pd.DataFrame(trucks)

    # 1. Matrix size
    n = len(distance_matrix)
    vals.append(("Matriz 17×17", "✅ OK" if n == 17 else "❌ Error",
                  f"Filas: {n}", "OK" if n == 17 else "Error"))

    # 2. Diagonal
    diag_ok = all(distance_matrix[i][i] == 0 for i in range(n))
    vals.append(("Diagonal cero", "✅ OK" if diag_ok else "❌ Error",
                  "Todos cero" if diag_ok else "Hay valores no cero", "OK" if diag_ok else "Error"))

    # 3. Demanda total
    tot = df_demand["Demanda_Total"].sum()
    vals.append(("Demanda total = 778", "✅ OK" if tot == 778 else "❌ Error",
                  f"Total: {tot}", "OK" if tot == 778 else "Error"))

    # 4. Imperial
    imp = df_demand["Imperial"].sum()
    vals.append(("Imperial = 390", "✅ OK" if imp == 390 else "❌ Error",
                  f"Imperial: {imp}", "OK" if imp == 390 else "Error"))

    # 5. Pilsen
    pil = df_demand["Pilsen"].sum()
    vals.append(("Pilsen = 194", "✅ OK" if pil == 194 else "❌ Error",
                  f"Pilsen: {pil}", "OK" if pil == 194 else "Error"))

    # 6. Tropical
    trop = df_demand["Tropical"].sum()
    vals.append(("Tropical = 194", "✅ OK" if trop == 194 else "❌ Error",
                  f"Tropical: {trop}", "OK" if trop == 194 else "Error"))

    # 7. Ningún trip supera capacidad
    cap_ok = (df_trips["Carga_total"] <= capacity).all()
    vals.append(("Trips ≤ 24 pallets", "✅ OK" if cap_ok else "❌ Error",
                  f"Máx carga: {df_trips['Carga_total'].max()}", "OK" if cap_ok else "Error"))

    # 8. Demanda entregada total
    total_entregado = df_trips["Carga_total"].sum()
    vals.append(("Demanda entregada = 778", "✅ OK" if total_entregado == 778 else "⚠️ Advertencia",
                  f"Entregado: {total_entregado}", "OK" if total_entregado == 778 else "Advertencia"))

    # 9. Imperial entregado
    imp_e = df_trips["Imperial"].sum()
    vals.append(("Imperial entregado = 390", "✅ OK" if imp_e == 390 else "⚠️ Advertencia",
                  f"Entregado: {imp_e}", "OK" if imp_e == 390 else "Advertencia"))

    # 10. Pilsen entregado
    pil_e = df_trips["Pilsen"].sum()
    vals.append(("Pilsen entregado = 194", "✅ OK" if pil_e == 194 else "⚠️ Advertencia",
                  f"Entregado: {pil_e}", "OK" if pil_e == 194 else "Advertencia"))

    # 11. Tropical entregado
    trop_e = df_trips["Tropical"].sum()
    vals.append(("Tropical entregado = 194", "✅ OK" if trop_e == 194 else "⚠️ Advertencia",
                  f"Entregado: {trop_e}", "OK" if trop_e == 194 else "Advertencia"))

    # 12. Trips inician en 0
    start_ok = all(eval(t["Ruta_nodos"])[0] == 0 for t in trips)
    vals.append(("Trips inician en CEDI (0)", "✅ OK" if start_ok else "❌ Error",
                  "Todos inician en 0" if start_ok else "Algún trip no inicia en 0", "OK" if start_ok else "Error"))

    # 13. Trips terminan en 0
    end_ok = all(eval(t["Ruta_nodos"])[-1] == 0 for t in trips)
    vals.append(("Trips terminan en CEDI (0)", "✅ OK" if end_ok else "❌ Error",
                  "Todos terminan en 0" if end_ok else "Algún trip no termina en 0", "OK" if end_ok else "Error"))

    # 14. Camiones respetan jornada
    jornada_ok = (df_trucks["Tiempo_total_min"] <= max_jornada + 1).all()
    supera = len(df_trucks[df_trucks["Tiempo_total_min"] > max_jornada])
    vals.append(("Camiones ≤ 480 min", "✅ OK" if jornada_ok else "⚠️ Advertencia",
                  f"{supera} camiones superan jornada (dedicados/revisión)",
                  "OK" if jornada_ok else "Advertencia"))

    # 15. Flota vs estimado
    req = len(trucks)
    dif = fleet_estimate - req
    if dif > 0:
        msg = f"Sobran {dif} camiones. Holgura operativa."
        est = "OK"
        sym = "✅ OK"
    elif dif == 0:
        msg = "Flota exacta. Sin holgura."
        est = "Advertencia"
        sym = "⚠️ Advertencia"
    else:
        msg = f"Faltan {abs(dif)} camiones vs estimado de {fleet_estimate}."
        est = "Error"
        sym = "❌ Error"
    vals.append((f"Flota requerida vs estimada ({fleet_estimate})", sym, msg, est))

    return pd.DataFrame(vals, columns=["Validación", "Resultado", "Detalle", "Estado"])


# ─────────────────────────────────────────────
# EXPORT HELPERS
# ─────────────────────────────────────────────
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")


def create_excel_download(df_demand, distance_matrix, trips, trucks, summary, df_validations, nodes):
    buffer = io.BytesIO()
    df_trips  = pd.DataFrame(trips).drop(columns=["_route"], errors="ignore")
    df_trucks = pd.DataFrame(trucks)
    df_dist   = pd.DataFrame(distance_matrix,
                              index=[nodes[i] for i in range(17)],
                              columns=[nodes[i] for i in range(17)])
    df_summary = pd.DataFrame([summary])

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Resumen", index=False)
        df_demand.to_excel(writer, sheet_name="Demanda", index=False)
        df_dist.to_excel(writer, sheet_name="Distancias")
        df_trips.to_excel(writer, sheet_name="Trips", index=False)
        df_trucks.to_excel(writer, sheet_name="Camiones", index=False)
        df_validations.to_excel(writer, sheet_name="Validaciones", index=False)

    buffer.seek(0)
    return buffer.read()


# ─────────────────────────────────────────────
# RENDER FUNCTIONS
# ─────────────────────────────────────────────
def render_header():
    st.markdown("""
    <div class="app-header">
        <h1>🚚 FIFCO Route Planner</h1>
        <p>CEDI Alajuela · Provincia de Alajuela, Costa Rica · CVRP Optimizer</p>
        <span class="header-badge">Capacitated Vehicle Routing Problem</span>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    st.sidebar.markdown("## ⚙️ Parámetros operativos")
    params = {}
    params["capacity"]       = st.sidebar.slider("Capacidad máx. por trip (pallets)", 12, 36, 24, 1)
    params["speed_kmh"]      = st.sidebar.slider("Velocidad promedio (km/h)", 20, 80, 40, 5)
    params["time_per_stop"]  = st.sidebar.slider("Tiempo por parada (min)", 5, 60, 15, 5)
    params["time_per_pallet"]= st.sidebar.slider("Tiempo por pallet (min)", 1, 10, 3, 1)
    params["reload_time"]    = st.sidebar.slider("Tiempo de reload entre trips (min)", 5, 60, 20, 5)
    params["max_jornada"]    = st.sidebar.slider("Jornada máx. por camión (min)", 360, 600, 480, 30)
    params["fleet_estimate"] = st.sidebar.number_input("Flota mínima estimada (camiones)", 10, 100, 33, 1)

    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🔧 Opciones del modelo")
    params["use_ortools"]       = st.sidebar.checkbox("Usar OR-Tools si disponible", value=True)
    params["show_math"]         = st.sidebar.checkbox("Mostrar modelo matemático", value=True)
    params["show_tables"]       = st.sidebar.checkbox("Mostrar tablas detalladas", value=True)
    params["show_downloads"]    = st.sidebar.checkbox("Mostrar exportaciones", value=True)

    st.sidebar.markdown("---")
    if ORTOOLS_AVAILABLE:
        st.sidebar.success("✅ OR-Tools disponible")
    else:
        st.sidebar.warning("⚠️ OR-Tools no instalado — usando heurística")

    return params


def render_executive_summary(s, params):
    st.markdown('<div class="section-title">📊 Resumen Ejecutivo</div>', unsafe_allow_html=True)

    diff = s["diferencia_flota"]
    fleet_color = "green" if diff > 0 else ("gold" if diff == 0 else "red")
    supera_color = "green" if s["trips_supera_8h"] == 0 else "red"
    cap_color    = "green" if s["trips_cap_error"] == 0 else "red"

    cols = st.columns(4)
    metrics = [
        ("Cantones atendidos", s["cantones_atendidos"], "16 cantones", ""),
        ("Demanda total", f"{s['demanda_total']:,}", "pallets/semana", ""),
        ("Imperial", s["imperial_total"], "pallets", "gold"),
        ("Pilsen", s["pilsen_total"], "pallets", "gold"),
    ]
    for col, (label, val, sub, color) in zip(cols, metrics):
        with col:
            c = color or ""
            st.markdown(f"""
            <div class="metric-card {c}">
                <div class="label">{label}</div>
                <div class="value">{val}</div>
                <div class="sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("")
    cols2 = st.columns(4)
    metrics2 = [
        ("Tropical", s["tropical_total"], "pallets", "gold"),
        ("Capacidad por trip", params["capacity"], "pallets máx.", ""),
        ("Trips generados", s["trips_generados"], "viajes totales", ""),
        ("Distancia total", f"{s['distancia_total']:,}", "km/semana", ""),
    ]
    for col, (label, val, sub, color) in zip(cols2, metrics2):
        with col:
            st.markdown(f"""
            <div class="metric-card {color}">
                <div class="label">{label}</div>
                <div class="value">{val}</div>
                <div class="sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("")
    cols3 = st.columns(4)
    diff_txt = f"+{diff} de holgura" if diff > 0 else (f"Sin holgura" if diff == 0 else f"{abs(diff)} insuficientes")
    metrics3 = [
        ("Camiones requeridos", s["camiones_requeridos"], "físicos", fleet_color),
        ("Flota estimada", s["flota_estimada"], diff_txt, fleet_color),
        ("Trips > 8 horas", s["trips_supera_8h"], "requieren revisión", supera_color),
        ("Trips con error cap.", s["trips_cap_error"], "superan 24 pallets", cap_color),
    ]
    for col, (label, val, sub, color) in zip(cols3, metrics3):
        with col:
            st.markdown(f"""
            <div class="metric-card {color}">
                <div class="label">{label}</div>
                <div class="value">{val}</div>
                <div class="sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("")
    # Tiempo total del proceso
    tiempo_color = "green" if s["tiempo_total_proceso_h"] <= 8 else "red"
    cols_t = st.columns(4)
    with cols_t[0]:
        st.markdown(f"""
        <div class="metric-card {tiempo_color}">
            <div class="label">⏱ Tiempo total del proceso</div>
            <div class="value">{s['tiempo_total_proceso_h']:.2f} h</div>
            <div class="sub">{s['tiempo_total_proceso_min']} min · camión más largo</div>
        </div>""", unsafe_allow_html=True)
    with cols_t[1]:
        trucks_over = len([t for t in [] if False])  # placeholder; computed via validation
        jornada_pct = round((s["tiempo_total_proceso_min"] / params["max_jornada"]) * 100, 1)
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Jornada máx. configurada</div>
            <div class="value">{params['max_jornada']} min</div>
            <div class="sub">{jornada_pct}% utilizado por peor camión</div>
        </div>""", unsafe_allow_html=True)
    with cols_t[2]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Tiempo total acumulado (flota)</div>
            <div class="value">{s['tiempo_total_min']:,.0f} min</div>
            <div class="sub">Suma de todos los trips</div>
        </div>""", unsafe_allow_html=True)
    with cols_t[3]:
        st.markdown(f"""
        <div class="metric-card {'red' if s['trips_supera_8h'] > 0 else 'green'}">
            <div class="label">Trips individuales &gt; 8 h</div>
            <div class="value">{s['trips_supera_8h']}</div>
            <div class="sub">{'⚠️ Requieren revisión' if s['trips_supera_8h'] > 0 else '✅ Ninguno'}</div>
        </div>""", unsafe_allow_html=True)

    if s["tiempo_total_proceso_h"] <= 8:
        st.markdown(f'<div class="alert-ok">✅ El proceso completo de distribución se realiza en <b>{s["tiempo_total_proceso_h"]:.2f} horas</b>, dentro de la jornada de 8 h.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alert-warn">⚠️ El camión más tardado requiere <b>{s["tiempo_total_proceso_h"]:.2f} horas</b>. Revisar asignación de trips o aumentar flota.</div>', unsafe_allow_html=True)

    st.markdown("")
    cols4 = st.columns(4)
    metrics4 = [
        ("Util. prom. camiones", f"{s['util_promedio']}%", "de la jornada", ""),
        ("Carga prom. por trip", s["carga_prom_trip"], "pallets", ""),
        ("Util. prom. por trip", f"{s['util_prom_trip']}%", "de 24 pallets", ""),
        ("Trips llenos (24 pal.)", s["trips_llenos"], f"vs {s['trips_parciales']} parciales", ""),
    ]
    for col, (label, val, sub, color) in zip(cols4, metrics4):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">{label}</div>
                <div class="value">{val}</div>
                <div class="sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    # Fleet comparison alert
    st.markdown("")
    if diff > 0:
        st.markdown(f'<div class="alert-ok">✅ La flota estimada de {s["flota_estimada"]} camiones es <b>suficiente</b>. Sobran {diff} camiones de holgura operativa.</div>', unsafe_allow_html=True)
    elif diff == 0:
        st.markdown(f'<div class="alert-warn">⚠️ La flota estimada de {s["flota_estimada"]} camiones es <b>exacta</b>. Sin holgura ante imprevistos.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alert-error">❌ Se requieren {s["camiones_requeridos"]} camiones pero la flota estimada es {s["flota_estimada"]}. Faltan {abs(diff)} camiones.</div>', unsafe_allow_html=True)


def render_demand_section(df_demand, show_tables):
    st.markdown('<div class="section-title">📦 Demanda por Cantón</div>', unsafe_allow_html=True)

    df_show = df_demand[df_demand["Nodo"] != 0].copy()

    if show_tables:
        st.dataframe(df_show[["Nodo","Cantón","Imperial","Pilsen","Tropical","Demanda_Total","Trips_Minimos","Clasificacion"]],
                     use_container_width=True, hide_index=True)

    if PLOTLY_AVAILABLE:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df_show, x="Cantón", y="Demanda_Total",
                         title="Demanda total por cantón",
                         color="Clasificacion",
                         color_discrete_map={"Alta demanda": "#1F3A5F", "Baja demanda": "#B89100"},
                         text="Demanda_Total")
            fig.update_layout(showlegend=True, xaxis_tickangle=-35,
                               plot_bgcolor="white", paper_bgcolor="white",
                               font_family="DM Sans")
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            df_melt = df_show.melt(id_vars="Cantón", value_vars=["Imperial","Pilsen","Tropical"],
                                    var_name="Producto", value_name="Pallets")
            colors = {"Imperial": "#1F3A5F", "Pilsen": "#B89100", "Tropical": "#4A90B8"}
            fig2 = px.bar(df_melt, x="Cantón", y="Pallets", color="Producto",
                          title="Demanda apilada por producto",
                          color_discrete_map=colors, barmode="stack")
            fig2.update_layout(xaxis_tickangle=-35, plot_bgcolor="white",
                                paper_bgcolor="white", font_family="DM Sans")
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            top5 = df_show.nlargest(5, "Demanda_Total")
            fig3 = px.bar(top5, x="Demanda_Total", y="Cantón", orientation="h",
                          title="Top 5 cantones por demanda",
                          color_discrete_sequence=["#1F3A5F"], text="Demanda_Total")
            fig3.update_layout(plot_bgcolor="white", paper_bgcolor="white", font_family="DM Sans")
            fig3.update_traces(textposition="outside")
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            multi = df_show[df_show["Trips_Minimos"] > 1]
            if not multi.empty:
                fig4 = px.bar(multi, x="Cantón", y="Trips_Minimos",
                              title="Cantones que requieren múltiples trips",
                              color_discrete_sequence=["#B89100"], text="Trips_Minimos")
                fig4.update_layout(plot_bgcolor="white", paper_bgcolor="white", font_family="DM Sans")
                fig4.update_traces(textposition="outside")
                st.plotly_chart(fig4, use_container_width=True)


def render_distance_section(distance_matrix, nodes, show_tables):
    st.markdown('<div class="section-title">🗺️ Matriz de Distancias</div>', unsafe_allow_html=True)

    # Validations
    dm_vals = validate_distance_matrix(distance_matrix)
    for v in dm_vals:
        color = "alert-ok" if v[3] == "OK" else ("alert-warn" if v[3] == "Advertencia" else "alert-error")
        st.markdown(f'<div class="{color}">{v[1]} — <b>{v[0]}</b>: {v[2]}</div>', unsafe_allow_html=True)

    if show_tables:
        labels = [nodes[i] for i in range(17)]
        df_dm = pd.DataFrame(distance_matrix, index=labels, columns=labels)
        st.dataframe(df_dm, use_container_width=True)

    # Distance from CEDI
    st.markdown("**Distancias desde el CEDI (nodo 0) a cada cantón:**")
    df_cedi = pd.DataFrame([
        {"Nodo": i, "Cantón": nodes[i], "Distancia desde CEDI (km)": distance_matrix[0][i]}
        for i in range(1, 17)
    ])
    st.dataframe(df_cedi, use_container_width=True, hide_index=True)


def render_model_section():
    st.markdown('<div class="section-title">📐 Modelo CVRP y Restricciones</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="model-box">
    <h4>Descripción del modelo</h4>
    <p>Este modelo busca <b>minimizar la distancia total recorrida por la flota</b>, garantizando que toda la demanda sea entregada y que ningún camión supere <b>24 pallets</b>.</p>

    <h4>Variables de decisión</h4>
    <ul>
        <li><code>y(i,j)</code> — variable entera/binaria: indica si se usa el arco i → j</li>
        <li><code>f(i,j)</code> — flujo: pallets transportados en el arco i → j</li>
        <li><code>d(i,j)</code> — parámetro: distancia por carretera entre nodos i y j (km)</li>
    </ul>

    <h4>Función objetivo</h4>
    <p><b>Min Z = Σ d(i,j) · y(i,j)</b></p>
    <p>Minimizar kilómetros recorridos por toda la flota.</p>

    <h4>Restricciones</h4>
    <ol>
        <li><b>Balance de camiones:</b> para cada nodo, entradas = salidas. Evita rutas abiertas.</li>
        <li><b>Balance de carga:</b> para cada cantón, carga que entra − carga que sale = demanda del cantón.</li>
        <li><b>Carga total del CEDI:</b> carga total que sale del CEDI = 778 pallets.</li>
        <li><b>Capacidad por arco:</b> <code>f(i,j) ≤ 24 · y(i,j)</code></li>
    </ol>

    <p>⚡ La restricción <code>f(i,j) ≤ 24 · y(i,j)</code> <b>asegura que ningún camión transporte más de 24 pallets.</b></p>
    </div>
    """, unsafe_allow_html=True)


def render_trips_section(trips, show_tables, method):
    st.markdown(f'<div class="section-title">🛣️ Generación de Trips <span class="method-badge method-{"ortools" if "OR-Tools" in method else "heuristic"}">{method}</span></div>', unsafe_allow_html=True)

    df_trips = pd.DataFrame(trips).drop(columns=["_route"], errors="ignore")

    total_trips = len(trips)
    dist_total  = df_trips["Distancia_km"].sum()
    carga_prom  = round(df_trips["Carga_total"].mean(), 1)
    util_prom   = round((carga_prom / 24) * 100, 1)
    llenos      = len(df_trips[df_trips["Carga_total"] == 24])
    parciales   = len(df_trips[df_trips["Carga_total"] < 24])
    supera_8h   = len(df_trips[df_trips["Tiempo_min"] > 480])

    cols = st.columns(6)
    vals = [
        ("Total trips", total_trips),
        ("Distancia total km", f"{dist_total:,.1f}"),
        ("Carga promedio", f"{carga_prom} pal"),
        ("Util. promedio", f"{util_prom}%"),
        ("Trips llenos", llenos),
        ("Trips > 8h", supera_8h),
    ]
    for col, (lbl, val) in zip(cols, vals):
        col.metric(lbl, val)

    if supera_8h > 0:
        st.markdown(f'<div class="alert-warn">⚠️ {supera_8h} trip(s) superan 8 horas de jornada y requieren revisión operativa.</div>', unsafe_allow_html=True)

    if show_tables:
        st.dataframe(df_trips, use_container_width=True, hide_index=True)

    if PLOTLY_AVAILABLE:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df_trips, x="Trip_ID", y="Distancia_km",
                         title="Distancia por trip (km)",
                         color_discrete_sequence=["#1F3A5F"], text="Distancia_km")
            fig.update_layout(xaxis_tickangle=-45, plot_bgcolor="white", paper_bgcolor="white",
                               font_family="DM Sans")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = px.bar(df_trips, x="Trip_ID", y="Carga_total",
                          title="Carga por trip (pallets)",
                          color_discrete_sequence=["#B89100"], text="Carga_total")
            fig2.add_hline(y=24, line_dash="dash", line_color="#B00020",
                           annotation_text="Capacidad máx. 24", annotation_position="top right")
            fig2.update_layout(xaxis_tickangle=-45, plot_bgcolor="white", paper_bgcolor="white",
                               font_family="DM Sans")
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            fig3 = px.bar(df_trips, x="Trip_ID", y="Tiempo_min",
                          title="Tiempo por trip (min)",
                          color_discrete_sequence=["#4A90B8"], text="Tiempo_min")
            fig3.add_hline(y=480, line_dash="dash", line_color="#B00020",
                           annotation_text="Jornada máx. 480 min")
            fig3.update_layout(xaxis_tickangle=-45, plot_bgcolor="white", paper_bgcolor="white",
                               font_family="DM Sans")
            st.plotly_chart(fig3, use_container_width=True)


def render_trucks_section(trucks, fleet_estimate, show_tables):
    st.markdown('<div class="section-title">🚛 Asignación de Camiones Físicos</div>', unsafe_allow_html=True)

    df_trucks = pd.DataFrame(trucks)
    n_req = len(trucks)
    diff  = fleet_estimate - n_req

    cols = st.columns(4)
    cols[0].metric("Camiones requeridos", n_req)
    cols[1].metric("Flota estimada", fleet_estimate)
    cols[2].metric("Diferencia", diff, delta=f"{'Holgura' if diff >= 0 else 'Faltan'}")
    cols[3].metric("Util. promedio", f"{round(df_trucks['Utilizacion_pct'].mean(), 1)}%")

    if diff > 0:
        st.markdown(f'<div class="alert-ok">✅ Flota suficiente. Sobran {diff} camiones de holgura.</div>', unsafe_allow_html=True)
    elif diff == 0:
        st.markdown(f'<div class="alert-warn">⚠️ Flota exacta. Sin holgura ante imprevistos.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alert-error">❌ Faltan {abs(diff)} camiones. Flota insuficiente.</div>', unsafe_allow_html=True)

    if show_tables:
        st.dataframe(df_trucks, use_container_width=True, hide_index=True)

    if PLOTLY_AVAILABLE:
        fig = px.bar(df_trucks, x="Camion_ID", y="Utilizacion_pct",
                     title="Utilización por camión físico (%)",
                     color="Utilizacion_pct",
                     color_continuous_scale=[[0, "#4A90B8"], [0.5, "#B89100"], [1, "#B00020"]],
                     text="Utilizacion_pct")
        fig.add_hline(y=100, line_dash="dash", line_color="#B00020",
                      annotation_text="100% jornada")
        fig.update_layout(xaxis_tickangle=-45, plot_bgcolor="white", paper_bgcolor="white",
                          font_family="DM Sans", coloraxis_showscale=False)
        fig.update_traces(textposition="outside", texttemplate="%{text:.1f}%")
        st.plotly_chart(fig, use_container_width=True)


def render_charts_section(trips, df_demand):
    st.markdown('<div class="section-title">📈 Visualizaciones</div>', unsafe_allow_html=True)

    if not PLOTLY_AVAILABLE:
        st.warning("Plotly no disponible. Instala plotly para visualizaciones.")
        return

    # Pie demand by product
    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(
            values=[390, 194, 194],
            names=["Imperial", "Pilsen", "Tropical"],
            title="Participación de productos en demanda total",
            color_discrete_sequence=["#1F3A5F", "#B89100", "#4A90B8"],
            hole=0.45,
        )
        fig.update_layout(font_family="DM Sans", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        df_show = df_demand[df_demand["Nodo"] != 0].sort_values("Demanda_Total", ascending=True)
        fig2 = px.bar(df_show, x="Demanda_Total", y="Cantón", orientation="h",
                      title="Ranking de cantones por demanda",
                      color="Demanda_Total",
                      color_continuous_scale=[[0, "#B8C8E0"], [1, "#1F3A5F"]],
                      text="Demanda_Total")
        fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white", font_family="DM Sans",
                           coloraxis_showscale=False)
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)


def render_validations_section(df_validations):
    st.markdown('<div class="section-title">✅ Validaciones del Modelo</div>', unsafe_allow_html=True)

    def color_row(row):
        if row["Estado"] == "OK":
            return ["background-color: #E8F5E9"] * len(row)
        elif row["Estado"] == "Advertencia":
            return ["background-color: #FFF8E1"] * len(row)
        else:
            return ["background-color: #FFEBEE"] * len(row)

    st.dataframe(df_validations.style.apply(color_row, axis=1),
                 use_container_width=True, hide_index=True)

    ok_count   = len(df_validations[df_validations["Estado"] == "OK"])
    warn_count = len(df_validations[df_validations["Estado"] == "Advertencia"])
    err_count  = len(df_validations[df_validations["Estado"] == "Error"])

    cols = st.columns(3)
    cols[0].metric("✅ OK", ok_count)
    cols[1].metric("⚠️ Advertencias", warn_count)
    cols[2].metric("❌ Errores", err_count)


def render_exports_section(df_demand, distance_matrix, trips, trucks, summary, df_validations, nodes):
    st.markdown('<div class="section-title">💾 Exportaciones</div>', unsafe_allow_html=True)

    df_trips  = pd.DataFrame(trips).drop(columns=["_route"], errors="ignore")
    df_trucks = pd.DataFrame(trucks)
    df_summary = pd.DataFrame([summary])
    labels = [nodes[i] for i in range(17)]
    df_dist = pd.DataFrame(distance_matrix, index=labels, columns=labels)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("📥 demanda.csv", convert_df_to_csv(df_demand),
                           "demanda.csv", "text/csv")
        st.download_button("📥 trips_generados.csv", convert_df_to_csv(df_trips),
                           "trips_generados.csv", "text/csv")
    with col2:
        st.download_button("📥 matriz_distancias.csv", convert_df_to_csv(df_dist.reset_index()),
                           "matriz_distancias.csv", "text/csv")
        st.download_button("📥 camiones_fisicos.csv", convert_df_to_csv(df_trucks),
                           "camiones_fisicos.csv", "text/csv")
    with col3:
        st.download_button("📥 resumen_ejecutivo.csv", convert_df_to_csv(df_summary),
                           "resumen_ejecutivo.csv", "text/csv")

    if OPENPYXL_AVAILABLE:
        st.markdown("---")
        excel_data = create_excel_download(df_demand, distance_matrix, trips, trucks, summary, df_validations, nodes)
        st.download_button("📊 Descargar Excel completo (todas las hojas)",
                           excel_data,
                           "FIFCO_Route_Planner.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Instala openpyxl para exportar Excel: `pip install openpyxl`")


def render_assumptions():
    st.markdown('<div class="section-title">📋 Supuestos y Limitaciones</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="model-box">
    <ul>
        <li>Es una herramienta de <b>planeación aproximada</b>. Los resultados deben validarse con la operación real.</li>
        <li>No considera tráfico real ni condiciones viales variables.</li>
        <li>No considera ventanas horarias de entrega en cada cantón.</li>
        <li>No considera restricciones específicas de cada chofer.</li>
        <li>No considera tiempos de espera en el cliente.</li>
        <li>No considera disponibilidad real diaria de la flota.</li>
        <li>No considera compatibilidad exacta de productos por cliente.</li>
        <li>No considera restricciones de peso o volumen diferenciadas por producto.</li>
        <li>No considera múltiples días de reparto (modelo semanal agregado).</li>
        <li>La matriz de distancias se toma como dato fijo por carretera.</li>
        <li>La distribución por producto dentro de cada trip es proporcional a la demanda del cantón.</li>
    </ul>
    <h4>Posibles mejoras futuras</h4>
    <ul>
        <li>Integrar ventanas horarias (VRPTW).</li>
        <li>Considerar restricciones de peso volumétrico por camión.</li>
        <li>Planificación multi-día y turnos de conductores.</li>
        <li>Integración con datos de tráfico en tiempo real.</li>
        <li>Optimización por costo total (combustible, peajes, horas-chofer).</li>
        <li>Dashboard de seguimiento de rutas en tiempo real.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    render_header()

    # Sidebar
    params = render_sidebar()

    # Load data
    nodes, df_demand, distance_matrix = load_base_data()

    # Generate deliveries
    deliveries = split_demand_into_deliveries(df_demand, params["capacity"])

    # Generate trips
    trips, method = generate_trips(
        deliveries, distance_matrix,
        params["capacity"], params["speed_kmh"],
        params["time_per_stop"], params["time_per_pallet"],
        params["use_ortools"]
    )

    # Assign trucks
    trucks = assign_trips_to_trucks(trips, params["max_jornada"], params["reload_time"])

    # Summary
    summary = create_summary(trips, trucks, df_demand, params["fleet_estimate"])

    # Validations
    df_validations = create_validations_table(
        trips, trucks, distance_matrix, df_demand,
        params["fleet_estimate"], params["max_jornada"], params["capacity"]
    )

    # Navigation tabs
    tabs = st.tabs([
        "📊 Resumen", "📦 Demanda", "🗺️ Distancias", "📐 Modelo",
        "🛣️ Trips", "🚛 Camiones", "📈 Gráficos", "✅ Validaciones",
        "💾 Exportar", "📋 Supuestos"
    ])

    with tabs[0]:
        render_executive_summary(summary, params)

    with tabs[1]:
        render_demand_section(df_demand, params["show_tables"])

    with tabs[2]:
        render_distance_section(distance_matrix, nodes, params["show_tables"])

    with tabs[3]:
        if params["show_math"]:
            render_model_section()
        else:
            st.info("Activa 'Mostrar modelo matemático' en la barra lateral para ver esta sección.")

    with tabs[4]:
        render_trips_section(trips, params["show_tables"], method)

    with tabs[5]:
        render_trucks_section(trucks, params["fleet_estimate"], params["show_tables"])

    with tabs[6]:
        render_charts_section(trips, df_demand)

    with tabs[7]:
        render_validations_section(df_validations)

    with tabs[8]:
        if params["show_downloads"]:
            render_exports_section(df_demand, distance_matrix, trips, trucks, summary, df_validations, nodes)
        else:
            st.info("Activa 'Mostrar exportaciones' en la barra lateral para ver esta sección.")

    with tabs[9]:
        render_assumptions()


if __name__ == "__main__":
    main()
