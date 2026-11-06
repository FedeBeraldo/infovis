# Datos crudos (Raw Data)

## Descripción

Esta carpeta contiene los datos estructurales y metadatos derivados de un historial personal de conversaciones con ChatGPT, preparados para su utilización en el proyecto de visualización de información.

Los archivos permiten analizar patrones temporales, características de las conversaciones, actividad de uso y distribución de temas, sin publicar el contenido textual íntegro de los mensajes originales.

## Archivos

### `conversations.csv`

Contiene información agregada a nivel de conversación. Cada fila representa una conversación.

| Columna | Descripción |
|---|---|
| `conversation_key` | Identificador pseudónimo de la conversación. |
| `date` | Fecha de inicio de la conversación. |
| `period` | Período mensual en formato `YYYY-MM`. |
| `message_count` | Cantidad total de mensajes de la conversación. |
| `user_messages` | Cantidad de mensajes del usuario. |
| `assistant_messages` | Cantidad de mensajes del asistente. |

### `messages_metadata.csv`

Contiene metadatos individuales de los mensajes. Cada fila representa un mensaje perteneciente a una conversación.

| Columna | Descripción |
|---|---|
| `conversation_key` | Identificador pseudónimo de la conversación. |
| `message_order` | Posición del mensaje dentro de la conversación. |
| `role` | Emisor del mensaje (`user` o `assistant`). |
| `timestamp_utc` | Fecha y hora del mensaje en UTC. |
| `model` | Modelo utilizado para generar la respuesta, cuando corresponde. |
| `content_type` | Tipo de contenido del mensaje. |
| `text_chars` | Cantidad de caracteres del contenido textual. |
| `has_text` | Indica si el mensaje contiene texto. |

### `conversation_titles.csv`

Contiene los títulos anonimizados de las conversaciones, utilizados como referencia para el análisis temático.

| Columna | Descripción |
|---|---|
| `conversation_key` | Identificador pseudónimo de la conversación. |
| `title` | Título anonimizado de la conversación. |

## Relaciones entre archivos

Los tres archivos comparten `conversation_key`, que permite relacionar:

- `conversations.csv` con `messages_metadata.csv`: una conversación puede contener múltiples mensajes.
- `conversations.csv` con `conversation_titles.csv`: cada conversación tiene un título asociado.

La estructura permite reconstruir características temporales y estructurales de las conversaciones sin acceder al contenido textual completo.

## Consideraciones de privacidad

Los datos fueron preparados para su publicación con fines académicos.

- Los identificadores originales fueron reemplazados por identificadores pseudónimos.
- Los títulos originales fueron anonimizados.
- No se publican los mensajes textuales completos.
- Se excluyen atributos personales que no resultan relevantes para el análisis.
- Los timestamps se conservan en UTC para permitir análisis temporales.

Los identificadores pseudónimos permiten relacionar los archivos entre sí, pero no representan identificadores originales de ChatGPT.

## Uso

Estos archivos constituyen la base de los datos procesados y de las visualizaciones desarrolladas en el proyecto.
