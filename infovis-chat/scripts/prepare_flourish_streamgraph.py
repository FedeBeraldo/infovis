
from pathlib import Path
import pandas as pd

BASE = Path(r"D:\infovis-chat")

INPUT = BASE / "data" / "processed" / "conversations_master.csv"

OUTPUT = (
    BASE / "data" / "processed" / "shareable"
    / "streamgraph_flourish_wide.csv"
)

# ------------------------------------------------------------
# Leer datos
# ------------------------------------------------------------

df = pd.read_csv(INPUT)

df["period"] = df["period"].astype(str)
df["area"] = df["area"].fillna("Sin clasificar")

# ------------------------------------------------------------
# Agregado mensual por área
# ------------------------------------------------------------

agg = (
    df.groupby(["period", "area"])
      .size()
      .reset_index(name="conversations")
)

# ------------------------------------------------------------
# Tabla ancha: una columna por área
# ------------------------------------------------------------

wide = agg.pivot(
    index="period",
    columns="area",
    values="conversations"
).fillna(0)

wide = wide.astype(int)

# ------------------------------------------------------------
# Información adicional para filtros y popups
# ------------------------------------------------------------

meta = (
    agg.groupby("period")["conversations"]
       .sum()
       .reset_index(name="total_month")
)

meta["year"] = meta["period"].str[:4]

# ------------------------------------------------------------
# Combinar
# ------------------------------------------------------------

result = (
    meta.set_index("period")
        .join(wide)
        .reset_index()
)

# Orden cronológico
result = result.sort_values("period")

# ------------------------------------------------------------
# Exportar
# ------------------------------------------------------------

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

result.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

print("Archivo generado:", OUTPUT)
print("Filas:", len(result))
print("Áreas:", len(wide.columns))
print("Columnas:", list(result.columns))
print(result.head())
