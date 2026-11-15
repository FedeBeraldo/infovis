
from pathlib import Path
import pandas as pd

# ==================================================
# 1. RUTAS
# ==================================================

# El script está en: scripts/scripts/
BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"

OUTPUT = (
    BASE_DIR / "data" / "processed" /
    "heatmap_dia_horario_datawrapper.csv"
)

# ==================================================
# 2. FUNCION PARA LEER CSV
# ==================================================

def read_csv_safe(path, nrows=None):

    for encoding in ["utf-8-sig", "cp1252"]:

        try:
            return pd.read_csv(
                path,
                encoding=encoding,
                nrows=nrows
            )

        except UnicodeDecodeError:
            continue

    raise ValueError(
        f"No se pudo leer el archivo: {path}"
    )


# ==================================================
# 3. IDENTIFICAR ARCHIVO DE MENSAJES
# ==================================================

candidates = []

for file in RAW_DIR.glob("*.csv"):

    try:

        headers = read_csv_safe(
            file,
            nrows=0
        ).columns.tolist()

        if {
            "timestamp_utc",
            "role"
        }.issubset(headers):

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
        "Seleccioná manualmente el archivo correcto."
    )


INPUT = candidates[0]

print("Archivo de entrada:", INPUT)


# ==================================================
# 4. LEER Y LIMPIAR DATOS
# ==================================================

df = read_csv_safe(INPUT)

# Normalizar timestamps UTC
df["timestamp_utc"] = pd.to_datetime(
    df["timestamp_utc"],
    utc=True,
    errors="coerce"
)

# Normalizar roles
df["role"] = (
    df["role"]
    .astype(str)
    .str.strip()
    .str.lower()
)

# Eliminar timestamps inválidos
df = df.dropna(
    subset=["timestamp_utc"]
).copy()

# Solo mensajes enviados por el usuario
df = df[
    df["role"] == "user"
].copy()


if df.empty:

    raise ValueError(
        "No se encontraron mensajes del usuario."
    )


# ==================================================
# 5. CONVERTIR A HORA DE BUENOS AIRES
# ==================================================

df["timestamp_ba"] = (
    df["timestamp_utc"]
    .dt.tz_convert(
        "America/Argentina/Buenos_Aires"
    )
)

df["fecha"] = (
    df["timestamp_ba"].dt.date
)

df["dia_num"] = (
    df["timestamp_ba"].dt.weekday
)

df["hora"] = (
    df["timestamp_ba"].dt.hour
)


# ==================================================
# 6. DEFINIR DIAS Y FRANJAS HORARIAS
# ==================================================

dias = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo"
]

rangos = {

    "Madrugada": range(0, 7),

    "Al despertar": range(7, 9),

    "Media mañana": range(9, 12),

    "Mediodía": range(12, 14),

    "Tarde": range(14, 18),

    "Noche": range(18, 22),

    "Después de la cena": range(22, 24)

}

franjas = list(rangos.keys())


# ==================================================
# 7. CONTAR MENSAJES POR DIA Y HORA
# ==================================================

conteos_hora = (

    df.groupby([
        "dia_num",
        "hora"
    ])

    .size()

    .unstack(
        fill_value=0
    )

    .reindex(
        index=range(7),
        columns=range(24),
        fill_value=0
    )
)


# ==================================================
# 8. AGRUPAR MENSAJES POR FRANJA HORARIA
# ==================================================

conteos = pd.DataFrame(
    index=range(7)
)

for franja, horas in rangos.items():

    conteos[franja] = (
        conteos_hora[
            list(horas)
        ].sum(axis=1)
    )


# ==================================================
# 9. CALCULAR OCURRENCIAS DE CADA DIA
# ==================================================

fecha_inicio = df["fecha"].min()
fecha_fin = df["fecha"].max()

# Calendario completo del período
calendario = pd.date_range(
    start=fecha_inicio,
    end=fecha_fin,
    freq="D"
)

# Cantidad de lunes, martes, etc.
dias_observados = (

    pd.Series(
        calendario.dayofweek
    )

    .value_counts()

    .reindex(
        range(7),
        fill_value=0
    )
)



# ==================================================
# 10. CALCULAR INTENSIDAD HORARIA PROMEDIO
# ==================================================

resultado = pd.DataFrame(index=range(7))

# Promedio de mensajes por hora considerando
# las 24 horas de cada ocurrencia del día
resultado["Promedio diario"] = (
    conteos_hora.sum(axis=1)
    / (dias_observados * 24)
)

# Promedio de mensajes por hora dentro de cada franja
for franja, horas in rangos.items():

    resultado[franja] = (
        conteos[franja]
        / (dias_observados * len(horas))
    )

# ==================================================
# 11. FORMATO FINAL
# ==================================================

resultado.index = dias
resultado.index.name = "Día"

resultado = resultado.round(2)


# ==================================================
# 11. EXPORTAR CSV PARA DATAWRAPPER
# ==================================================

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

resultado.to_csv(
    OUTPUT,
    encoding="utf-8-sig"
)


# ==================================================
# 13. VALIDACIONES Y RESUMEN
# ==================================================

print("\n===================================")
print("HEATMAP GENERADO CORRECTAMENTE")
print("===================================")

print("\nArchivo de salida:")
print(OUTPUT)

print("\nPeríodo analizado:")
print(fecha_inicio, "hasta", fecha_fin)

print("\nCantidad total de mensajes:")
print(len(df))

print("\nCantidad de ocurrencias por día:")
print(dias_observados)

print("\nTabla final:")
print(resultado)

print("\nValidación: promedio diario menos suma de franjas")

validacion = (
    resultado["Promedio diario"]
    - resultado[franjas].sum(axis=1)
)

print(validacion.round(2))

print("\nSuma de promedios diarios:")
print(
    resultado["Promedio diario"].sum()
)

print("\nArchivo listo para importar en Datawrapper.")
