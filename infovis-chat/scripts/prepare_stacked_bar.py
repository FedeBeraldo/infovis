
from pathlib import Path
import pandas as pd

# Rutas del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "processed" / "conversations_master.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "area_subcategoria_counts.csv"

# Leer dataset maestro
df = pd.read_csv(INPUT_FILE, encoding="cp1252")

# Limpiar espacios y cadenas vacías
for col in ["area", "subcategoria"]:
    df[col] = df[col].astype("string").str.strip()
    df[col] = df[col].replace("", pd.NA)

# Verificar que exista una fila por conversación
if df["conversation_key"].duplicated().any():
    raise ValueError(
        "El dataset maestro contiene conversation_key duplicados."
    )

# Validar columnas necesarias
required_columns = ["conversation_key", "area", "subcategoria"]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Faltan columnas en el dataset: {missing_columns}"
    )

# Eliminar registros sin clasificación temática
df = df.dropna(subset=["area", "subcategoria"])

# Contar conversaciones por área y subcategoría
df_grouped = (
    df.groupby(["area", "subcategoria"], as_index=False)
      ["conversation_key"]
      .nunique()
      .rename(columns={"conversation_key": "conversaciones"})
)

# Ordenar las áreas por volumen total de conversaciones
area_order = (
    df_grouped.groupby("area")["conversaciones"]
    .sum()
    .sort_values(ascending=False)
)

df_grouped["total_area"] = df_grouped["area"].map(area_order)

# Ordenar por área y frecuencia de subcategoría
df_grouped = (
    df_grouped
    .sort_values(
        ["total_area", "area", "conversaciones"],
        ascending=[False, True, False]
    )
    .drop(columns="total_area")
    .reset_index(drop=True)
)

# Exportar CSV
df_grouped.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

# Resumen
print(f"Archivo generado: {OUTPUT_FILE}")
print(f"Áreas: {df_grouped['area'].nunique()}")
print(f"Subcategorías: {df_grouped['subcategoria'].nunique()}")
print(f"Combinaciones área-subcategoría: {len(df_grouped)}")
print(f"Conversaciones representadas: {df_grouped['conversaciones'].sum()}")




# Seleccionar las 8 áreas principales
top_areas = [
    "Tecnología y Electrónica",
    "Data Science y Programación",
    "Salud y Medicina",
    "Física Médica y Radioterapia",
    "Cocina y Alimentación",
    "Hogar y Mantenimiento",
    "Ciencia y Cultura",
    "Finanzas e Inversiones"
]

df_top = df_grouped[
    df_grouped["area"].isin(top_areas)
].copy()

# Construir una fila por área
rows = []

for area in top_areas:

    df_area = (
        df_top[df_top["area"] == area]
        .sort_values("conversaciones", ascending=False)
    )

    # Tres subcategorías más frecuentes
    top3 = df_area.head(3)

    # Cantidad de conversaciones de cada una
    values = top3["conversaciones"].tolist()

    # Completar si hubiera menos de tres subcategorías
    values += [0] * (3 - len(values))

    # Agrupar todas las restantes en Otros
    otros = df_area.iloc[3:]["conversaciones"].sum()

    rows.append({
        "area": area,
        "Top 1": values[0],
        "Top 2": values[1],
        "Top 3": values[2],
        "Otros": int(otros)
    })

# Crear DataFrame final
df_wide = pd.DataFrame(rows)

# Exportar CSV
OUTPUT_WIDE = (
    BASE_DIR / "data" / "processed" /
    "area_subcategoria_top8.csv"
)

df_wide.to_csv(
    OUTPUT_WIDE,
    index=False,
    encoding="utf-8-sig"
)

print("\nCSV generado:", OUTPUT_WIDE)
print("\nDistribución:")
print(df_wide.to_string(index=False))

print(
    "\nConversaciones representadas:",
    int(df_wide[["Top 1", "Top 2", "Top 3", "Otros"]].sum().sum())
)


# Seleccionar las 8 áreas principales
top_areas = [
    "Tecnología y Electrónica",
    "Data Science y Programación",
    "Salud y Medicina",
    "Física Médica y Radioterapia",
    "Cocina y Alimentación",
    "Hogar y Mantenimiento",
    "Ciencia y Cultura",
    "Finanzas e Inversiones"
]

df_top = df_grouped[
    df_grouped["area"].isin(top_areas)
].copy()

# Construir el archivo de detalle
rows = []

for area in top_areas:

    df_area = (
        df_top[df_top["area"] == area]
        .sort_values("conversaciones", ascending=False)
        .reset_index(drop=True)
    )

    for i, row in df_area.iterrows():

        if i < 3:
            grupo = f"Top {i + 1}"
        else:
            grupo = "Otros"

        rows.append({
            "area": area,
            "grupo": grupo,
            "subcategoria": row["subcategoria"],
            "conversaciones": int(row["conversaciones"])
        })

df_detalle = pd.DataFrame(rows)

# Exportar CSV
OUTPUT_DETALLE = (
    BASE_DIR / "data" / "processed" /
    "area_subcategoria_detalle.csv"
)

df_detalle.to_csv(
    OUTPUT_DETALLE,
    index=False,
    encoding="utf-8-sig"
)

print(f"Archivo generado: {OUTPUT_DETALLE}")
print(df_detalle.head(15))