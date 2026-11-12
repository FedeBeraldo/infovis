
from pathlib import Path
import pandas as pd

# Raíz del proyecto
ROOT = Path(__file__).resolve().parent.parent

RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PRIVATE = PROCESSED / "private"

# Archivos de entrada
titles = pd.read_csv(PROCESSED / "conversation_titles.csv")
classified = pd.read_csv(PROCESSED / "conversations_classified.csv")
conversations = pd.read_csv(RAW / "conversations.csv")
mapping = pd.read_csv(PRIVATE / "conversation_mapping.csv")

# Verificar claves únicas
for name, df, col in [
    ("titles", titles, "conversation_id"),
    ("classified", classified, "conversation_id"),
    ("conversations", conversations, "conversation_key"),
    ("mapping", mapping, "conversation_key"),
]:
    if df[col].duplicated().any():
        raise ValueError(f"Hay claves duplicadas en {name}: {col}")

# Mapping: ID numérico -> clave pública
mapping["conversation_id"] = range(1, len(mapping) + 1)

# Unir títulos y clasificación
master = titles.merge(
    classified.drop(columns=["title"], errors="ignore"),
    on="conversation_id",
    how="outer",
    validate="one_to_one"
)

# Incorporar clave pública
master = master.merge(
    mapping[["conversation_id", "conversation_key"]],
    on="conversation_id",
    how="left",
    validate="one_to_one"
)

# Incorporar métricas temporales
master = master.merge(
    conversations,
    on="conversation_key",
    how="left",
    validate="one_to_one"
)

# Controles de integridad
if master["conversation_key"].isna().any():
    raise ValueError("Hay conversaciones sin conversation_key")

if master["date"].isna().any():
    raise ValueError("Hay conversaciones sin fecha")

if len(master) != len(titles):
    raise ValueError("Cambió el número de conversaciones")

# Orden y columnas finales
master = master[
    [
        "conversation_key",
        "date",
        "period",
        "title",
        "area",
        "subcategoria",
        "confianza",
        "titulo_duplicado",
        "message_count",
        "user_messages",
        "assistant_messages",
    ]
].sort_values("conversation_key")

# Exportar
PROCESSED.mkdir(parents=True, exist_ok=True)

output = PROCESSED / "conversations_master.csv"
master.to_csv(output, index=False, encoding="utf-8")

print(f"Archivo generado: {output}")
print(f"Conversaciones: {len(master)}")
print("\nDistribución por área:")
print(master["area"].value_counts())
