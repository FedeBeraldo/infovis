
import json
import pandas as pd
import csv
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

# ============================================================
# CONFIGURACIÓN
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "original"
PRIVATE = ROOT / "data" / "processed" / "private"
PUBLIC = ROOT / "data" / "processed" / "shareable"

PRIVATE.mkdir(parents=True, exist_ok=True)
PUBLIC.mkdir(parents=True, exist_ok=True)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

from math import isfinite
from datetime import datetime, timezone

timestamps_invalidos = []
timestamps_corregidos = []
mapeo_privado = []

def fecha_utc(timestamp, archivo="", conversacion="", mensaje=""):
    if timestamp is None:
        return ""

    try:
        valor = float(timestamp)

        if not isfinite(valor):
            raise ValueError("Timestamp no finito")

        # Detectar Unix en milisegundos
        unidad = "segundos"

        if abs(valor) >= 1e12:
            original = valor
            valor = valor / 1000
            unidad = "milisegundos"

        fecha = datetime.fromtimestamp(
            valor, timezone.utc
        ).isoformat(timespec="seconds")

        if unidad == "milisegundos":
            timestamps_corregidos.append({
                "archivo": archivo,
                "conversation_id": conversacion,
                "message_id": mensaje,
                "timestamp_original": original,
                "timestamp_normalizado": valor,
                "fecha_utc": fecha
            })

        return fecha

    except (ValueError, TypeError, OverflowError, OSError) as error:

        timestamps_invalidos.append({
            "archivo": archivo,
            "conversation_id": conversacion,
            "message_id": mensaje,
            "timestamp_original": repr(timestamp),
            "error": str(error)
        })

        return ""


def texto_parts(parts):
    """Convierte parts a texto, sin asumir que siempre es una lista."""
    if isinstance(parts, str):
        return parts
    if isinstance(parts, list):
        return "\n".join(
            str(x) for x in parts if isinstance(x, str)
        )
    return ""


def guardar_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# IMPORTACIÓN
# ============================================================

conversaciones_privadas = []
mensajes_privados = []

conversaciones_publicas = []
mensajes_publicos = []

roles = Counter()
archivos_faltantes = []
errores = []

muestra_raw = []

contador_conversaciones = 0

for numero_archivo in range(19):

    archivo = INPUT / f"conversations-{numero_archivo:03d}.json"

    if not archivo.exists():
        archivos_faltantes.append(archivo.name)
        continue

    print("Procesando:", archivo.name)

    try:
        with archivo.open(encoding="utf-8") as f:
            lote = json.load(f)

    except Exception as error:
        errores.append({
            "archivo": archivo.name,
            "error": str(error)
        })
        continue

    for conv in lote:

        contador_conversaciones += 1

        conv_id = conv.get("conversation_id") or conv.get("id")
        titulo = conv.get("title", "")
        fecha = conv.get("create_time")
        mapping = conv.get("mapping") or {}

        mensajes = []

        # Recorremos los nodos del árbol de conversación.
        for nodo_id, nodo in mapping.items():

            mensaje = nodo.get("message")

            # Los nodos sin mensaje no son mensajes reales.
            if not isinstance(mensaje, dict):
                continue

            autor = mensaje.get("author") or {}
            contenido = mensaje.get("content") or {}

            partes = contenido.get("parts", [])
            texto = texto_parts(partes)

            timestamp = mensaje.get("create_time")

            mensajes.append({
                "message_id": mensaje.get("id", nodo_id),
                "node_id": nodo_id,
                "parent_id": nodo.get("parent"),
                "role": autor.get("role", "unknown"),
                "model": (mensaje.get("metadata") or {}).get(
                    "model_slug", ""
                ),
                "timestamp": timestamp,
                "timestamp_utc": fecha_utc(
                    timestamp,
                    archivo=archivo.name,
                    conversacion=conv_id,
                    mensaje=mensaje.get("id", nodo_id)
                ),
                "content_type": contenido.get("content_type", ""),
                "text": texto,
                "text_chars": len(texto),
            })

        # Orden cronológico para facilitar análisis temporal.
        mensajes.sort(
            key=lambda m: (
                m["timestamp"] is None,
                m["timestamp"] or 0
            )
        )

        user_count = sum(m["role"] == "user" for m in mensajes)
        assistant_count = sum(
            m["role"] == "assistant" for m in mensajes
        )

        # --------------------------------------------------------
        # TABLA PRIVADA: conserva título, UUID y textos.
        # --------------------------------------------------------

        conversaciones_privadas.append({
            "conversation_id": conv_id,
            "title": titulo,
            "create_time": fecha,
            "create_time_utc": fecha_utc(
                fecha,
                archivo=archivo.name,
                conversacion=conv_id,
                mensaje="CREATE_TIME_CONVERSACION"
            ),
            "update_time_utc": fecha_utc(conv.get("update_time")),
            "source_file": archivo.name,
            "message_count": len(mensajes),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "is_archived": conv.get("is_archived"),
            "is_starred": conv.get("is_starred"),
        })

        for orden, m in enumerate(mensajes, start=1):

            roles[m["role"]] += 1

            mensajes_privados.append({
                "conversation_id": conv_id,
                "message_order": orden,
                **m
            })

        # --------------------------------------------------------
        # TABLA COMPARTIBLE: sin textos, títulos ni UUID originales.
        # --------------------------------------------------------
        
        clave = f"C{contador_conversaciones:06d}"

        mapeo_privado.append({
            "conversation_id": conv_id,
            "conversation_key": clave
        })

        conversaciones_publicas.append({
            "conversation_key": clave,
            "date": fecha_utc(fecha)[:10],
            "period": fecha_utc(fecha)[:7],
            "message_count": len(mensajes),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "is_archived": conv.get("is_archived"),
            "is_starred": conv.get("is_starred"),
        })

        for orden, m in enumerate(mensajes, start=1):

            mensajes_publicos.append({
                "conversation_key": clave,
                "message_order": orden,
                "role": m["role"],
                "timestamp_utc": m["timestamp_utc"],
                "model": m["model"],
                "content_type": m["content_type"],
                "text_chars": m["text_chars"],
                "has_text": bool(m["text"].strip()),
            })

        # --------------------------------------------------------
        # MUESTRA RAW REDACTADA (3 conversaciones).
        # --------------------------------------------------------

        if len(muestra_raw) < 3:

            demo = dict(conv)

            demo["conversation_id"] = f"DEMO_{len(muestra_raw)+1}"
            demo["id"] = demo["conversation_id"]
            demo["title"] = "Título anonimizado"

            mapping_demo = {}

            for i, (node_id, nodo) in enumerate(mapping.items(), 1):

                nuevo_nodo = dict(nodo)
                nuevo_nodo["id"] = f"NODE_{i:04d}"
                nuevo_nodo["parent"] = None

                mensaje = nodo.get("message")

                if isinstance(mensaje, dict):

                    nuevo_mensaje = dict(mensaje)
                    nuevo_mensaje["id"] = f"MSG_{i:04d}"

                    contenido_demo = dict(
                        mensaje.get("content") or {}
                    )

                    if "parts" in contenido_demo:
                        contenido_demo["parts"] = [
                            "[CONTENIDO OMITIDO]"
                        ]

                    nuevo_mensaje["content"] = contenido_demo
                    nuevo_nodo["message"] = nuevo_mensaje

                mapping_demo[f"NODE_{i:04d}"] = nuevo_nodo

            demo["mapping"] = mapping_demo
            demo["current_node"] = None

            muestra_raw.append(demo)


# ============================================================
# EXPORTACIÓN
# ============================================================
pd.DataFrame(mapeo_privado).to_csv(
    ROOT / "data" / "processed" / "private" / "conversation_mapping.csv",
    index=False
)

guardar_csv(
    PRIVATE / "conversations_private.csv",
    conversaciones_privadas
)

guardar_csv(
    PRIVATE / "messages_private.csv",
    mensajes_privados
)

guardar_csv(
    PUBLIC / "conversations.csv",
    conversaciones_publicas
)

guardar_csv(
    PUBLIC / "messages_metadata.csv",
    mensajes_publicos
)


with (PRIVATE / "diagnostics.json").open(
    "w", encoding="utf-8"
) as f:

    json.dump({
        "files_expected": 19,
        "files_missing": archivos_faltantes,
        "errors": errores,

        "conversations": len(conversaciones_privadas),
        "messages": len(mensajes_privados),

        "messages_by_role": dict(roles),

        "invalid_timestamps_count": len(timestamps_invalidos),
        "invalid_timestamps": timestamps_invalidos,
        "timestamps_corrected_count": len(timestamps_corregidos),
        "timestamps_corrected": timestamps_corregidos,

        "invalid_timestamps_count": len(timestamps_invalidos),
        "invalid_timestamps": timestamps_invalidos,

    }, f, ensure_ascii=False, indent=2)



# ============================================================
# RESUMEN
# ============================================================

print("\n========== IMPORTACIÓN FINALIZADA ==========")
print("Conversaciones:", len(conversaciones_privadas))
print("Mensajes:", len(mensajes_privados))
print("Archivos faltantes:", archivos_faltantes or "ninguno")
print("Errores:", errores or "ninguno")
print("==========================================")
