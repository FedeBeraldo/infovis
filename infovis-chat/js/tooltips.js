
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
        "tecnologia y electronica": "Tecnología y Electrónica",
        "ds & programacion": "Data Science y Programación",
        "salud & medicina": "Salud y Medicina",
        "fm & rt": "Física Médica y Radioterapia",
        "cocina y alimentacion": "Cocina y Alimentación",
        "hogar y mantenimiento": "Hogar y Mantenimiento",
        "ciencia y cultura": "Ciencia y Cultura",
        "finanzas e inversiones": "Finanzas e Inversiones"
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

    function createCustomTooltip() {

        const existingTooltip = document.getElementById("custom-svg-tooltip");

        if (existingTooltip) {
            return existingTooltip;
        }

        const tooltip = document.createElement("div");

        tooltip.id = "custom-svg-tooltip";

        tooltip.style.cssText = `
            position: fixed;
            display: none;
            z-index: 99999;
            width: 240px;
            padding: 11px;
            background: #171923;
            color: #FFFFFF;
            border: 1px solid #393B49;
            border-radius: 10px;
            box-shadow: 0 8px 28px rgba(0, 0, 0, 0.30);
            font-family: inherit;
            pointer-events: none;
            font-size: 12px;
        `;

        document.body.appendChild(tooltip);

        return tooltip;
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
        const number = Number(
            String(value)
                .replace(",", ".")
                .trim()
        );

        return Number.isFinite(number) ? number : 0;
    }


    function createCustomTooltip() {
        const tooltip = document.createElement("div");

        tooltip.id = "custom-svg-tooltip";

        tooltip.style.cssText = `
        position: fixed;
        display: none;
        z-index: 99999;
        width: 290px;
        padding: 16px;
        background: #171923;
        color: #FFFFFF;
        border: 1px solid #393B49;
        border-radius: 12px;
        box-shadow: 0 8px 28px rgba(0,0,0,0.30);
        font-family: inherit;
        pointer-events: none;
    `;

        document.body.appendChild(tooltip);

        return tooltip;
    }


    function escapeHTML(value) {
        return String(value).replace(/[&<>"']/g, character => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        })[character]);
    }

    function positionTooltip(tooltip, event) {
        const offset = 14;

        const rect = tooltip.getBoundingClientRect();

        let x = event.clientX + offset;
        let y = event.clientY + offset;

        if (x + rect.width > window.innerWidth - 10) {
            x = event.clientX - rect.width - offset;
        }

        if (y + rect.height > window.innerHeight - 10) {
            y = event.clientY - rect.height - offset;
        }

        tooltip.style.left = `${Math.max(10, x)}px`;
        tooltip.style.top = `${Math.max(10, y)}px`;
    }

    function addTooltip(element, data, tooltip) {
        const colors = {
            "Top 1": "#E6550D",
            "Top 2": "#FDAE6B",
            "Top 3": "#FEE6CE",
            "Otros": "#6366F1"
        };

        const color = colors[data.grupo] || "#A5B4FC";

        element.querySelectorAll(":scope > title").forEach(title => {
            title.remove();
        });

        element.style.cursor = "pointer";

        element.addEventListener("mouseenter", event => {
            const percentage = Number(data.porcentaje) || 0;

            tooltip.innerHTML = `
                <div style="display:flex; justify-content:space-between;
                            align-items:center; gap:8px; margin-bottom:8px;">
                    <span style="color:#A1A1AA; font-size:9px;
                                font-weight:700; letter-spacing:0.8px;">
                        ${escapeHTML(data.area.toUpperCase())}
                    </span>
                    <span style="color:${color}; font-size:10px;
                                font-weight:700;">
                        ${escapeHTML(data.grupo.toUpperCase())}
                    </span>
                </div>

                <div style="font-size:13px; font-weight:600;
                            line-height:1.35; margin-bottom:8px;">
                    ${escapeHTML(data.subcategoria)}
                </div>

                <div style="font-size:23px; font-weight:700;">
                    ${escapeHTML(data.conversaciones)}
                </div>

                <div style="color:#A1A1AA; font-size:10px;
                            margin-top:2px; margin-bottom:10px;">
                    conversaciones
                </div>

                <div style="display:flex; justify-content:space-between;
                            font-size:11px; margin-bottom:5px;">
                    <span style="color:#A1A1AA">Participación</span>
                    <strong>${percentage.toFixed(1).replace(".", ",")}%</strong>
                </div>

                <div style="height:5px; background:#393B49;
                            border-radius:10px; overflow:hidden;">
                    <div style="height:100%; width:${Math.min(100, Math.max(0, percentage))}%;
                                background:${color}; border-radius:10px;"></div>
                </div>
            `;

            tooltip.style.display = "block";
            positionTooltip(tooltip, event);
        });


        element.addEventListener("mousemove", event => {
            positionTooltip(tooltip, event);
        });

        element.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });
    }


    function showCustomTooltip(tooltip, data, event) {
        const colors = {
            "Top 1": "#E6550D",
            "Top 2": "#FDAE6B",
            "Top 3": "#FEE6CE",
            "Otros": "#6366F1"
        };

        const color = colors[data.grupo] || "#A5B4FC";

        tooltip.innerHTML = `
        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap:12px;
            margin-bottom:12px;
        ">
            <span style="
                color:#A1A1AA;
                font-size:10px;
                font-weight:700;
                letter-spacing:1px;
                text-transform:uppercase;
            ">${data.area}</span>

            <span style="
                color:${color};
                font-size:12px;
                font-weight:700;
                white-space:nowrap;
            ">${data.grupo.toUpperCase()}</span>
        </div>

        <div style="
            font-size:15px;
            font-weight:600;
            line-height:1.4;
            margin-bottom:12px;
        ">${data.subcategoria}</div>

        <div style="
            font-size:28px;
            font-weight:700;
            line-height:1;
        ">${data.conversaciones}</div>

        <div style="
            color:#A1A1AA;
            font-size:11px;
            margin-top:4px;
            margin-bottom:14px;
        ">conversaciones</div>

        <div style="
            display:flex;
            justify-content:space-between;
            font-size:12px;
            margin-bottom:7px;
        ">
            <span style="color:#A1A1AA">Participación</span>
            <strong>${data.porcentaje}%</strong>
        </div>

        <div style="
            height:6px;
            background:#393B49;
            border-radius:10px;
            overflow:hidden;
        ">
            <div style="
                height:100%;
                width:${data.porcentaje}%;
                background:${color};
                border-radius:10px;
            "></div>
        </div>
    `;

        tooltip.style.display = "block";

        const offset = 14;
        const rect = tooltip.getBoundingClientRect();

        let x = event.clientX + offset;
        let y = event.clientY + offset;

        if (x + rect.width > window.innerWidth - 10) {
            x = event.clientX - rect.width - offset;
        }

        if (y + rect.height > window.innerHeight - 10) {
            y = event.clientY - rect.height - offset;
        }

        tooltip.style.left = `${Math.max(10, x)}px`;
        tooltip.style.top = `${Math.max(10, y)}px`;
    }


    // --------------------------------------------------
    // PROCESAMIENTO PRINCIPAL
    // --------------------------------------------------

    async function initializeTooltips() {
        console.log("TOOLTIPS: initializeTooltips ejecutada");
        const object = document.getElementById(SVG_OBJECT_ID);

        if (!object) {
            console.error(`No se encontró el objeto SVG: ${SVG_OBJECT_ID}`);
            return;
        }

        // Evitar inicializaciones duplicadas.
        if (object.dataset.tooltipsInitialized === "true") {
            return;
        }

        object.dataset.tooltipsInitialized = "true";

        try {

            const tooltip = createCustomTooltip();

            // ------------------------------------------
            // 1. CARGAR EL CSV Y EL SVG
            // ------------------------------------------

            const response = await fetch(CSV_URL);

            if (!response.ok) {
                throw new Error(`No se pudo cargar el CSV: ${response.status}`);
            }

            const csvText = await response.text();
            const data = parseCSV(csvText);

            const svgDocument = object.contentDocument;

            console.log("SVG document:", svgDocument);

            if (!svgDocument) {
                throw new Error("No se pudo acceder al contenido del SVG.");
            }

            const svg = svgDocument.documentElement;
            const svgWindow = svgDocument.defaultView;

            // Obtener el centro horizontal de cualquier elemento
            // expresado en las coordenadas del SVG.
            function getElementCenterX(element) {

                const bbox = element.getBBox();
                const matrix = element.getCTM();

                if (!matrix) {
                    throw new Error("No se pudo obtener la transformación del SVG.");
                }

                const point = svg.createSVGPoint();

                point.x = bbox.x + bbox.width / 2;
                point.y = bbox.y + bbox.height / 2;

                return point.matrixTransform(matrix).x;
            }

            // ------------------------------------------
            // 2. IDENTIFICAR LAS OCHO CATEGORÍAS
            // ------------------------------------------

            const categories = [];

            svg.querySelectorAll("text").forEach(element => {

                const label = element.textContent.trim();
                const area = getCategoryFromLabel(label);

                if (!area) return;

                categories.push({
                    area,
                    x: getElementCenterX(element)
                });

            });

            // Orden visual de izquierda a derecha.
            categories.sort((a, b) => a.x - b.x);

            if (categories.length !== 8) {
                throw new Error(
                    `Se encontraron ${categories.length} categorías; se esperaban 8.`
                );
            }

            console.log("Categorías:", categories.length, categories);

            console.log(
                "Categorías identificadas:",
                categories.map(category => category.area)
            );

            // ------------------------------------------
            // 3. INDEXAR LOS DATOS DEL CSV
            // ------------------------------------------

            const dataByArea = {};

            data.forEach(record => {

                const area = normalize(record.area);
                const grupo = normalize(record.grupo);

                if (!dataByArea[area]) {
                    dataByArea[area] = {};
                }

                // Solo necesitamos un registro por cada grupo Top.
                // Las filas individuales de Otros se conservan en el CSV,
                // pero no se utilizan para calcular el total de Otros.
                if (grupo !== "otros") {
                    dataByArea[area][grupo] = record;
                }

            });

            // ------------------------------------------
            // 4. IDENTIFICAR LOS VALORES +N DE OTROS
            // ------------------------------------------

            const plusLabels = Array.from(
                svg.querySelectorAll("text")
            )
                .filter(element =>
                    /^\+\s*\d+$/.test(element.textContent.trim())
                )
                .map(element => ({
                    element,
                    x: getElementCenterX(element),
                    count: Number(
                        element.textContent.trim().replace("+", "")
                    )
                }))
                .sort((a, b) => a.x - b.x);

            if (plusLabels.length !== 8) {
                throw new Error(
                    `Se encontraron ${plusLabels.length} etiquetas +N; se esperaban 8.`
                );
            }

            // Asociar cada valor +N con su categoría por orden horizontal.
            const otherByArea = {};

            categories.forEach((category, index) => {

                otherByArea[normalize(category.area)] =
                    plusLabels[index].count;

            });

            // ------------------------------------------
            // 5. CALCULAR EL TOTAL DE CADA CATEGORÍA
            // ------------------------------------------

            const topGroups = ["top 1", "top 2", "top 3"];

            const totalsByArea = {};

            categories.forEach(category => {

                const areaKey = normalize(category.area);
                const areaData = dataByArea[areaKey] || {};

                const topTotal = topGroups.reduce(
                    (total, group) => {

                        const record = areaData[group];

                        return total + (
                            record
                                ? getNumber(record.conversaciones)
                                : 0
                        );

                    },
                    0
                );

                const otherCount = otherByArea[areaKey] || 0;

                totalsByArea[areaKey] = {
                    topTotal,
                    otherCount,
                    categoryTotal: topTotal + otherCount
                };

            });

            // ------------------------------------------
            // 6. TOOLTIP PARA LOS 24 RECTÁNGULOS
            // ------------------------------------------

            const targetRectangles = Array.from(
                svg.querySelectorAll("rect")
            ).filter(rect => {

                const fill = getFill(rect, svgWindow);

                return Object.prototype.hasOwnProperty.call(SERIES, fill);

            });

            let rectanglesWithTooltip = 0;

            targetRectangles.forEach(rect => {

                const fill = getFill(rect, svgWindow);
                const group = SERIES[fill];

                const rectX = getElementCenterX(rect);

                // Buscar la categoría cuyo centro horizontal
                // está más cerca del centro del rectángulo.
                const nearestCategory = categories.reduce(
                    (nearest, category) => {

                        const distance = Math.abs(rectX - category.x);

                        if (!nearest || distance < nearest.distance) {
                            return {
                                category,
                                distance
                            };
                        }

                        return nearest;

                    },
                    null
                );

                const area = nearestCategory.category.area;
                const areaKey = normalize(area);

                const record = dataByArea[areaKey]?.[normalize(group)];

                if (!record) {
                    console.warn(`No se encontró ${group} para ${area}`);
                    return;
                }

                const count = getNumber(record.conversaciones);
                const categoryTotal = totalsByArea[areaKey].categoryTotal;

                const percentage = categoryTotal > 0
                    ? (count / categoryTotal) * 100
                    : 0;

                addTooltip(rect, {
                    area,
                    grupo: group,
                    subcategoria: record.subcategoria,
                    conversaciones: count,
                    porcentaje: percentage
                }, tooltip);

                rectanglesWithTooltip++;

            });

            // ------------------------------------------
            // 7. TOOLTIP PARA LAS 8 FLECHAS "OTROS"
            // ------------------------------------------

            const arrows = Array.from(
                svg.querySelectorAll("polygon")
            )
                .filter(polygon =>
                    getFill(polygon, svgWindow) === "rgb(99, 102, 241)"
                )
                .map(arrow => ({
                    element: arrow,
                    x: getElementCenterX(arrow)
                }))
                .sort((a, b) => a.x - b.x);

            if (arrows.length !== 8) {
                throw new Error(
                    `Se encontraron ${arrows.length} flechas; se esperaban 8.`
                );
            }

            let arrowsWithTooltip = 0;

            arrows.forEach((arrow, index) => {

                // Las flechas y las categorías están ordenadas
                // de izquierda a derecha: se corresponden por índice.
                const area = categories[index].area;
                const areaKey = normalize(area);

                const otherCount = otherByArea[areaKey];
                const categoryTotal = totalsByArea[areaKey].categoryTotal;

                const percentage = categoryTotal > 0
                    ? (otherCount / categoryTotal) * 100
                    : 0;

                addTooltip(arrow.element, {
                    area,
                    grupo: "Otros",
                    subcategoria: "Resto de subcategorías",
                    conversaciones: otherCount,
                    porcentaje: percentage
                }, tooltip);

                arrowsWithTooltip++;

            });

            // ------------------------------------------
            // 8. RESULTADO
            // ------------------------------------------

            console.log(
                `Tooltips agregados: ${rectanglesWithTooltip}/24 rectángulos y ${arrowsWithTooltip}/8 flechas.`
            );

            console.log("Totales por categoría:", totalsByArea);

        } catch (error) {

            // Permitir volver a intentar la inicialización si hubo un error.
            delete object.dataset.tooltipsInitialized;

            console.error(
                "Error al inicializar los tooltips:",
                error
            );

        }

    }

    // --------------------------------------------------
    // INICIALIZAR TOOLTIPS CUANDO SE CARGA EL SVG
    // --------------------------------------------------

    const object = document.getElementById(SVG_OBJECT_ID);

    if (object) {

        object.addEventListener("load", () => {
            initializeTooltips();
        }, { once: true });

        // Si el SVG ya estaba cargado, inicializar inmediatamente.
        if (object.contentDocument?.documentElement) {
            initializeTooltips();
        }

    } else {
        console.error(`No se encontró el objeto SVG: ${SVG_OBJECT_ID}`);
    }

})();
