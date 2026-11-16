
(() => {
    "use strict";

    // --------------------------------------------------
    // CONFIGURACIÓN
    // --------------------------------------------------

    const SVG_OBJECT_ID = "grafico-rawgraphs";

    const CSV_URL =
        "visualizations/rawgraphs/area_subcategoria_detalle.csv";

    // Colores de las tres series del SVG exportado.
    // Cada color identifica una posición del ranking.
    const SERIES = {
        "rgb(230, 85, 13)": "Top 1",
        "rgb(253, 174, 107)": "Top 2",
        "rgb(254, 230, 206)": "Top 3"
    };

    // Relaciona las etiquetas abreviadas del SVG
    // con los nombres completos del CSV.
    const CATEGORY_ALIASES = {
        "tecnología y electrónica":
            "Tecnología y Electrónica",

        "ds & programación":
            "Data Science y Programación",

        "salud & medicina":
            "Salud y Medicina",

        "fm & rt":
            "Física Médica y Radioterapia",

        "cocina y alimentación":
            "Cocina y Alimentación",

        "hogar y mantenimiento":
            "Hogar y Mantenimiento",

        "ciencia y cultura":
            "Ciencia y Cultura",

        "finanzas e inversiones":
            "Finanzas e Inversiones"
    };


    // --------------------------------------------------
    // FUNCIONES AUXILIARES
    // --------------------------------------------------

    function normalize(value) {
        return String(value)
            .trim()
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "");
    }


    // Parser CSV que contempla campos entre comillas
    // y comas dentro de los nombres de subcategorías.
    function parseCSV(text) {
        const firstLine = text.split(/\r?\n/)[0];
        const separator = firstLine.includes(";") ? ";" : ",";

        const rows = [];
        let row = [];
        let field = "";
        let quoted = false;

        for (let i = 0; i < text.length; i++) {
            const char = text[i];
            const next = text[i + 1];

            if (char === '"' && quoted && next === '"') {
                field += '"';
                i++;
            } else if (char === '"') {
                quoted = !quoted;
            } else if (char === separator && !quoted) {
                row.push(field);
                field = "";
            } else if (
                (char === "\n" || char === "\r") &&
                !quoted
            ) {
                if (char === "\r" && next === "\n") i++;

                row.push(field);

                if (row.some(value => value.trim() !== "")) {
                    rows.push(row);
                }

                row = [];
                field = "";
            } else {
                field += char;
            }
        }

        row.push(field);

        if (row.some(value => value.trim() !== "")) {
            rows.push(row);
        }

        const headers = rows.shift().map(h => h.trim());

        return rows.map(values => {
            const record = {};

            headers.forEach((header, index) => {
                record[header] = (values[index] ?? "").trim();
            });

            return record;
        });
    }


    function getCenter(element, svg) {
        const bbox = element.getBBox();
        const matrix = element.getCTM();

        const point = svg.createSVGPoint();

        point.x = bbox.x + bbox.width / 2;
        point.y = bbox.y + bbox.height / 2;

        return point.matrixTransform(matrix);
    }


    function getFill(element, svgWindow) {
        return svgWindow
            .getComputedStyle(element)
            .fill
            .replace(/\s+/g, " ")
            .trim();
    }


    function normalizeLabel(text) {
    return text
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/\s+/g, " ")
        .trim()
        .toLowerCase();
}

	function getCategoryFromLabel(label) {
		const normalizedLabel = normalizeLabel(label);

		for (const [alias, area] of Object.entries(CATEGORY_ALIASES)) {
			if (normalizeLabel(alias) === normalizedLabel) {
				return area;
			}
		}

		return null;
	}


    function findNearestCategory(element, categories, svg) {
        const center = getCenter(element, svg);

        return categories.reduce((nearest, category) => {
            const distance = Math.abs(
                center.x - category.x
            );

            if (!nearest || distance < nearest.distance) {
                return {
                    area: category.area,
                    distance
                };
            }

            return nearest;
        }, null).area;
    }


    function getNumber(value) {
        return Number(
            String(value)
                .replace(",", ".")
                .trim()
        );
    }


    function addTooltip(element, lines) {
        const oldTitle = element.querySelector(":scope > title");

        if (oldTitle) oldTitle.remove();

        const title = element.ownerDocument.createElementNS(
            "http://www.w3.org/2000/svg",
            "title"
        );

        title.textContent = lines.join("\n");

        element.appendChild(title);

        element.style.cursor = "pointer";
    }


    // --------------------------------------------------
    // PROCESAMIENTO PRINCIPAL
    // --------------------------------------------------

    async function initializeTooltips() {
        const object = document.getElementById(SVG_OBJECT_ID);

        if (!object) {
            console.error(
                `No se encontró el objeto SVG: ${SVG_OBJECT_ID}`
            );
            return;
        }

        try {
            const response = await fetch(CSV_URL);

            if (!response.ok) {
                throw new Error(
                    `No se pudo cargar el CSV: ${response.status}`
                );
            }

            const csvText = await response.text();
            const data = parseCSV(csvText);

            const svgDocument = object.contentDocument;

            if (!svgDocument) {
                throw new Error(
                    "No se pudo acceder al contenido del SVG."
                );
            }

            const svg = svgDocument.documentElement;
            const svgWindow = svgDocument.defaultView;

            // ------------------------------------------
            // 1. IDENTIFICAR LAS OCHO CATEGORÍAS
            // ------------------------------------------

            const categories = [];

            svg.querySelectorAll("text").forEach(element => {
                const label = element.textContent.trim();
                const area = getCategoryFromLabel(label);

                if (!area) return;

                const center = getCenter(element, svg);

                categories.push({
                    area,
                    x: center.x
                });
            });

            // Orden visual de izquierda a derecha.
            categories.sort((a, b) => a.x - b.x);

            if (categories.length !== 8) {
                throw new Error(
                    `Se encontraron ${categories.length} categorías; se esperaban 8.`
                );
            }

            console.log(
                "Categorías identificadas:",
                categories.map(c => c.area)
            );


            // ------------------------------------------
            // 2. INDEXAR LOS DATOS DEL CSV
            // ------------------------------------------

            const dataByArea = {};

            data.forEach(record => {
                const area = record.area;
                const grupo = normalize(record.grupo);

                if (!dataByArea[area]) {
                    dataByArea[area] = {};
                }

                dataByArea[area][grupo] = record;
            });


            // ------------------------------------------
            // 3. TOOLTIP PARA LOS 24 RECTÁNGULOS
            // ------------------------------------------

            const rectangles = Array.from(
                svg.querySelectorAll("rect")
            );

            const targetRectangles = rectangles.filter(rect => {
                const fill = getFill(rect, svgWindow);
                return Object.keys(SERIES).includes(fill);
            });

            let rectanglesWithTooltip = 0;

            targetRectangles.forEach(rect => {
                const fill = getFill(rect, svgWindow);
                const group = SERIES[fill];

                const area = findNearestCategory(
                    rect,
                    categories,
                    svg
                );

                const record = dataByArea[area]?.[
                    normalize(group)
                ];

                if (!record) {
                    console.warn(
                        `No se encontró ${group} para ${area}`
                    );
                    return;
                }

                const count = getNumber(record.conversaciones);

                addTooltip(rect, [
                    area,
                    record.subcategoria,
                    `${count} conversaciones`
                ]);

                rectanglesWithTooltip++;
            });


            // ------------------------------------------
            // 4. TOOLTIP PARA LAS 8 FLECHAS "OTROS"
            // ------------------------------------------

            const arrows = Array.from(
                svg.querySelectorAll("polygon")
            ).filter(polygon =>
                getFill(polygon, svgWindow) ===
                "rgb(99, 102, 241)"
            );

            const plusLabels = Array.from(
                svg.querySelectorAll("text")
            ).filter(element =>
                /^\+\s*\d+$/.test(
                    element.textContent.trim()
                )
            );

            let arrowsWithTooltip = 0;

            arrows.forEach(arrow => {
                const area = findNearestCategory(
                    arrow,
                    categories,
                    svg
                );

                const arrowCenter = getCenter(arrow, svg);

                // Buscar el valor +N más próximo horizontalmente.
                const label = plusLabels.reduce(
                    (nearest, element) => {
                        const center = getCenter(element, svg);

                        const distance = Math.abs(
                            center.x - arrowCenter.x
                        );

                        if (
                            !nearest ||
                            distance < nearest.distance
                        ) {
                            return {
                                element,
                                distance
                            };
                        }

                        return nearest;
                    },
                    null
                );

                if (!label) return;

                const otherCount = Number(
                    label.element.textContent
                        .replace("+", "")
                        .trim()
                );

                // Para el porcentaje usamos los tres valores
                // Top 1, Top 2 y Top 3 del CSV, más Otros.
                // No sumamos las subcategorías individuales de Otros.

                const topGroups = ["top 1", "top 2", "top 3"];

                const topTotal = topGroups.reduce(
                    (total, group) => {
                        const record = dataByArea[area]?.[group];

                        return total + (
                            record
                                ? getNumber(record.conversaciones)
                                : 0
                        );
                    },
                    0
                );

                const categoryTotal = topTotal + otherCount;

                const percentage = categoryTotal > 0
                    ? (otherCount / categoryTotal) * 100
                    : 0;

                addTooltip(arrow, [
                    area,
                    "Otros",
                    `${otherCount} conversaciones`,
                    `${percentage.toFixed(1).replace(".", ",")} % del total de la categoría`
                ]);

                arrowsWithTooltip++;
            });


            // ------------------------------------------
            // 5. RESULTADO
            // ------------------------------------------

            console.log(
                `Tooltips agregados: ${rectanglesWithTooltip}/24 rectángulos y ${arrowsWithTooltip}/8 flechas.`
            );

        } catch (error) {
            console.error(
                "Error al inicializar los tooltips:",
                error
            );
        }
    }


    // Esperar a que el SVG esté cargado.
    const object = document.getElementById(SVG_OBJECT_ID);

    if (object) {
        object.addEventListener(
            "load",
            initializeTooltips,
            { once: true }
        );

        // Por si el SVG ya estaba cargado.
        if (object.contentDocument?.documentElement) {
            initializeTooltips();
        }
    }

})();
