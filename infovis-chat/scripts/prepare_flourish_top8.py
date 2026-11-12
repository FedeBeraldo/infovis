
from pathlib import Path
import pandas as pd

# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE = Path(r"D:\infovis-chat")

INPUT = BASE / "data" / "processed" / "conversations_master.csv"

OUTPUT = (
    BASE / "data" / "processed" / "shareable"
    / "streamgraph_flourish_top8.csv"
)

TOP_N = 8

# ============================================================
# LECTURA
# ============================================================

df = pd.read_csv(INPUT)

df["period"] = df["period"].astype(str)
df["area"] = df["area"].fillna("Sin clasificar")

# ============================================================
# AGREGACIÓN MENSUAL
# ============================================================

agg = (
    df.groupby(["period", "area"])
      .size()
      .reset_index(name="conversations")
)

# ============================================================
# TOP 8 HISTÓRICO
# ============================================================

ranking = (
    agg.groupby("area")["conversations"]
       .sum()
       .sort_values(ascending=False)
)

top_areas = ranking.head(TOP_N).index.tolist()

print("\nTop 8 áreas:")
print(ranking.head(TOP_N))

# ============================================================
# AGRUPAR RESTO COMO OTROS
# ============================================================

agg["area_stream"] = agg["area"].where(
    agg["area"].isin(top_areas),
    "Otros"
)

stream = (
    agg.groupby(["period", "area_stream"])["conversations"]
       .sum()
       .reset_index()
)

# ============================================================
# FORMATO ANCHO
# ============================================================

wide = stream.pivot(
    index="period",
    columns="area_stream",
    values="conversations"
).fillna(0)

wide = wide.astype(int)

# Asegurar que Otros exista
if "Otros" not in wide.columns:
    wide["Otros"] = 0

# ============================================================
# INFORMACIÓN AUXILIAR
# ============================================================

meta = (
    agg.groupby("period")["conversations"]
       .sum()
       .reset_index(name="total_month")
)

meta["year"] = meta["period"].str[:4]

result = (
    meta.set_index("period")
        .join(wide)
        .reset_index()
)

# ============================================================
# ORDEN DE COLUMNAS
# ============================================================

ordered = top_areas + ["Otros"]

result = result[
    ["period", "total_month", "year"] + ordered
]

result = result.sort_values("period")

# ============================================================
# EXPORTACIÓN
# ============================================================

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

result.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

print("\nArchivo generado:", OUTPUT)
print("Filas:", len(result))
print("Columnas:", list(result.columns))
print("\nPrimeras filas:")
print(result.head(10).to_string(index=False))
