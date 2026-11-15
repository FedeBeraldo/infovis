
from pathlib import Path
import pandas as pd

# --------------------------------------------------
# 1. RUTAS
# --------------------------------------------------

# El script está en: scripts/scripts/
BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"

OUTPUT = (
    BASE_DIR
    / "data"
    / "processed"
    / "heatmap_dia_hora_datawrapper.csv"
)

# --------------------------------------------------
# 2. IDENTIFICAR EL ARCHIVO RAW
# --------------------------------------------------

def read_csv_safe(path, nrows=None):
    """Intenta leer el CSV con UTF-8 y luego CP1252."""
    for encoding in ["utf-8-sig", "cp1252"]:
        try:
            return pd.read_csv(
                path,
                encoding=encoding,
                nrows=nrows
            )
        except UnicodeDecodeError:
            continue

    raise ValueError(f"No se pudo leer el archivo: {path}")


candidates = []

for file in RAW_DIR.glob("*.csv"):
    try:
        headers = read_csv_safe(file, nrows=0).columns.tolist()

        if {"timestamp_utc", "role"}.issubset(headers):
            candidates.append(file)

    except Exception:
        continue

if len(candidates) == 0:
    raise FileNotFoundError(
        "No se encontró un CSV con timestamp_utc y role en data/raw."
    )

if len(candidates) > 1:
    print("Se encontraron varios archivos posibles:")
    for file in candidates:
        print(file)
    raise ValueError(
        "Dejá solamente el archivo correcto o seleccioná INPUT manualmente."
    )

INPUT = candidates[0]

print(f"Archivo de entrada: {INPUT}")

# --------------------------------------------------
# 3. LEER Y FILTRAR MENSAJES DEL USUARIO
# --------------------------------------------------

df = read_csv_safe(INPUT)

df["timestamp_utc"] = pd.to_datetime(
    df["timestamp_utc"],
    utc=True,
    errors="coerce"
)

# Descartar timestamps inválidos
df = df.dropna(subset=["timestamp_utc"]).copy()

# Contar solamente mensajes enviados por el usuario
df["role"] = df["role"].astype(str).str.strip().str.lower()

df = df[df["role"] == "user"].copy()

if df.empty:
    raise ValueError(
        "No se encontraron mensajes con role = 'user'."
    )

# --------------------------------------------------
# 4. CONVERTIR A HORA DE BUENOS AIRES
# --------------------------------------------------

df["timestamp_ba"] = (
    df["timestamp_utc"]
    .dt.tz_convert("America/Argentina/Buenos_Aires")
)

df["hora"] = df["timestamp_ba"].dt.hour
df["dia_num"] = df["timestamp_ba"].dt.weekday

# --------------------------------------------------
# 5. AGREGAR POR DÍA Y HORA
# --------------------------------------------------

dias = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo"
]

# Matriz completa: 7 días x 24 horas
heatmap = (
    df.groupby(["dia_num", "hora"])
      .size()
      .unstack(fill_value=0)
)

heatmap = heatmap.reindex(
    index=range(7),
    columns=range(24),
    fill_value=0
)

heatmap.index = dias

# Etiquetas de columnas: 00 a 23
heatmap.columns = [
    f"{hora:02d}" for hora in range(24)
]

# Primera columna: día de la semana
heatmap.index.name = "Día"

# --------------------------------------------------
# 6. EXPORTAR PARA DATAWRAPPER
# --------------------------------------------------

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

heatmap.to_csv(
    OUTPUT,
    encoding="utf-8-sig"
)

# --------------------------------------------------
# 7. RESUMEN
# --------------------------------------------------

print("\nArchivo generado correctamente:")
print(OUTPUT)

print("\nDimensiones:", heatmap.shape)
print("Total de mensajes:", int(heatmap.to_numpy().sum()))

print("\nVista previa:")
print(heatmap)

print("\nTotal por día:")
print(heatmap.sum(axis=1))

print("\nTotal por hora:")
print(heatmap.sum(axis=0))
