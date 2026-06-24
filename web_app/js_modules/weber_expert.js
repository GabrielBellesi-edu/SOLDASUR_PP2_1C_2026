/* ==========================================================================
   WEBER_EXPERT.JS — Sistema Experto de Construcción / Revestimientos Weber
   100% frontend — NO requiere Uvicorn ni ningún backend corriendo.
   Funciona igual que la calculadora PEISA: solo con `python -m http.server`.

   Requiere: core.js (appendMessage, renderOptions, scrollToBottom, etc.)
   ========================================================================== */

/* ── Árbol de decisión del cuestionario ────────────────────────────────── */
const WEBER_FLOW = {
    inicio_weber: {
        id: 'inicio_weber',
        pregunta: '¿Qué tipo de trabajo vas a realizar en la obra?',
        tipo: 'opciones',
        opciones: [
            { texto: 'Colocación de Revestimientos (Cerámicos / Porcelanatos)', siguiente: 'tipo_revestimiento_pastina' },
            { texto: 'Nivelación y Albañilería (Carpetas, revoques)', siguiente: 'tipo_nivelacion' },
            { texto: 'Impermeabilización de Superficies', siguiente: 'tipo_impermeabilizacion' },
            { texto: 'Pisos Decorativos (Microcementos)', siguiente: 'tipo_microcemento' },
            { texto: 'Revestimientos Plásticos Decorativos (weberplast)', siguiente: 'tipo_weberplast' }
        ]
    },

    // ── Rama 1: Revestimientos ──
    tipo_revestimiento_pastina: {
        id: 'tipo_revestimiento_pastina',
        pregunta: '¿Qué material necesitás calcular para el revestimiento?',
        tipo: 'opciones',
        opciones: [
            { texto: 'Adhesivo (Pegamento)', siguiente: 'soporte_pegamiento' },
            { texto: 'Pastina (Tomado de juntas)', siguiente: 'tipo_pastina' }
        ]
    },

    soporte_pegamiento: {
        id: 'soporte_pegamiento',
        pregunta: '¿Qué tipo de revestimiento y soporte vas a utilizar?',
        tipo: 'opciones',
        variable: 'soporte_obra',
        opciones: [
            { texto: 'Cerámica Estándar (Carpeta/Revoque tradicional)', valor: 'peg_classic', siguiente: 'peg_tamano' },
            { texto: 'Porcellanatos (Baja absorción)', valor: 'peg_flex', siguiente: 'peg_tamano' },
            { texto: 'Colocación sobre cerámicas existentes', valor: 'peg_psp', siguiente: 'peg_tamano' },
            { texto: 'Vidrio / Venecitas (Baños y piscinas)', valor: 'peg_glass', siguiente: 'peg_tamano' }
        ]
    },

    peg_tamano: {
        id: 'peg_tamano',
        pregunta: '¿Algún lado de la baldosa o pieza de revestimiento mide más de 30 cm?',
        tipo: 'opciones',
        variable: 'doble_encolado',
        opciones: [
            { texto: 'Sí (requiere doble encolado)', valor: 'si', siguiente: 'superficie_m2' },
            { texto: 'No (colocación tradicional)', valor: 'no', siguiente: 'superficie_m2' }
        ]
    },

    tipo_pastina: {
        id: 'tipo_pastina',
        pregunta: '¿Qué tipo de terminación/resistencia necesitás para la junta?',
        tipo: 'opciones',
        variable: 'soporte_obra',
        opciones: [
            { texto: 'Classic (Juntas finas hasta 5mm)', valor: 'pastina_classic', siguiente: 'pastina_largo' },
            { texto: 'Prestige (Porcellanatos y juntas de 2 a 15mm)', valor: 'pastina_prestige', siguiente: 'pastina_largo' },
            { texto: 'Lista para Usar (Acrílica de 1 a 4mm)', valor: 'pastina_lista', siguiente: 'pastina_largo' },
            { texto: 'Epoxi Max (Máxima resistencia e impermeabilidad)', valor: 'pastina_epoxi', siguiente: 'pastina_largo' }
        ]
    },

    pastina_largo: {
        id: 'pastina_largo',
        pregunta: 'Ingresá el Largo de la cerámica o baldosa en centímetros (cm):',
        tipo: 'entrada_usuario',
        variable: 'pastina_largo',
        unidad: 'cm',
        placeholder: 'Ej: 36',
        siguiente: 'pastina_ancho'
    },

    pastina_ancho: {
        id: 'pastina_ancho',
        pregunta: 'Ingresá el Ancho de la cerámica o baldosa en centímetros (cm):',
        tipo: 'entrada_usuario',
        variable: 'pastina_ancho',
        unidad: 'cm',
        placeholder: 'Ej: 36',
        siguiente: 'pastina_espesor'
    },

    pastina_espesor: {
        id: 'pastina_espesor',
        pregunta: 'Ingresá el Espesor de la baldosa o pieza en milímetros (mm):',
        tipo: 'entrada_usuario',
        variable: 'pastina_espesor',
        unidad: 'mm',
        placeholder: 'Ej: 8',
        siguiente: 'pastina_junta'
    },

    pastina_junta: {
        id: 'pastina_junta',
        pregunta: 'Ingresá el Ancho de la junta deseado en milímetros (mm):',
        tipo: 'entrada_usuario',
        variable: 'pastina_junta',
        unidad: 'mm',
        placeholder: 'Ej: 3',
        siguiente: 'superficie_m2'
    },

    // ── Rama 2: Nivelación y Albañilería ──
    tipo_nivelacion: {
        id: 'tipo_nivelacion',
        pregunta: '¿Qué tipo de trabajo de albañilería / regularización vas a hacer?',
        tipo: 'opciones',
        variable: 'soporte_obra',
        opciones: [
            { texto: 'Autonivelante rápido (Capa fina interior)', valor: 'autonivelante', siguiente: 'espesor_mm' },
            { texto: 'Carpeta tradicional de nivelación', valor: 'carpeta_tradicional', siguiente: 'espesor_cm' },
            { texto: 'Revoque Fino exterior/interior', valor: 'revoque_fino', siguiente: 'superficie_m2' },
            { texto: 'Revoque Monocapa (Grueso+Fino liso)', valor: 'revoque_monocapa', siguiente: 'espesor_cm' }
        ]
    },

    espesor_mm: {
        id: 'espesor_mm',
        pregunta: 'Ingresá el Espesor promedio de regularización en milímetros (mm):',
        tipo: 'entrada_usuario',
        variable: 'espesor_medida',
        unidad: 'mm',
        placeholder: 'Ej: 3',
        siguiente: 'superficie_m2'
    },

    espesor_cm: {
        id: 'espesor_cm',
        pregunta: 'Ingresá el Espesor promedio deseado en centímetros (cm):',
        tipo: 'entrada_usuario',
        variable: 'espesor_medida',
        unidad: 'cm',
        placeholder: 'Ej: 2',
        siguiente: 'superficie_m2'
    },

    // ── Rama 3: Impermeabilización ──
    tipo_impermeabilizacion: {
        id: 'tipo_impermeabilizacion',
        pregunta: '¿Qué tipo de superficie querés proteger de la humedad?',
        tipo: 'opciones',
        variable: 'soporte_obra',
        opciones: [
            { texto: 'Techados / Terrazas / Azoteas expuestas', valor: 'imp_techos', siguiente: 'superficie_m2' },
            { texto: 'Fachadas / Paredes Exteriores', valor: 'imp_frentes', siguiente: 'superficie_m2' },
            { texto: 'Cimientos / Barrera aisladora horizontal', valor: 'imp_ceresita', siguiente: 'superficie_m2' },
            { texto: 'Piscinas / Cisternas / Aljibes', valor: 'imp_piscinas', siguiente: 'superficie_m2' },
            { texto: 'Baños / Cocinas (Bajo revestimiento)', valor: 'imp_banio', siguiente: 'superficie_m2' }
        ]
    },

    // ── Rama 4: Pisos Decorativos (Microcementos) ──
    tipo_microcemento: {
        id: 'tipo_microcemento',
        pregunta: '¿Qué capa del sistema de microcemento decorativo vas a colocar?',
        tipo: 'opciones',
        variable: 'soporte_obra',
        opciones: [
            { texto: 'Capa Base niveladora (weber microbase)', valor: 'microcemento_base', siguiente: 'superficie_m2' },
            { texto: 'Capa Color terminación (weber microcolor)', valor: 'microcemento_color', siguiente: 'superficie_m2' }
        ]
    },

    // ── Rama 5: Revestimientos Plásticos texturados ──
    tipo_weberplast: {
        id: 'tipo_weberplast',
        pregunta: '¿Qué tipo de acabado texturado decorativo (weberplast) vas a aplicar?',
        tipo: 'opciones',
        variable: 'soporte_obra',
        opciones: [
            { texto: 'Textura Fina (Llaneado / Rodillado fino)', valor: 'weberplast_fino', siguiente: 'superficie_m2' },
            { texto: 'Textura Media (Rulato / Travertino medio)', valor: 'weberplast_medio', siguiente: 'superficie_m2' },
            { texto: 'Textura Gruesa (Acabado rústico grueso)', valor: 'weberplast_grueso', siguiente: 'superficie_m2' }
        ]
    },

    superficie_m2: {
        id: 'superficie_m2',
        pregunta: 'Ingresá los metros cuadrados (m²) totales de la superficie a trabajar:',
        tipo: 'entrada_usuario',
        variable: 'metros_cuadrados',
        unidad: 'm²',
        placeholder: 'Ej: 25.5',
        siguiente: 'calcular_weber'
    }
};

/* ── Tabla de rendimientos extendida por tipo de soporte / obra ───────── */
const WEBER_RENDIMIENTOS = {
    // Adhesivos
    peg_classic: { producto: 'weber gris cerámicos', rendimiento_kg_m2: 5.0, descripcion: 'Adhesivo cementicio para cerámicas en interiores y exteriores de absorción media/alta.', tipo: 'adhesivo' },
    peg_flex: { producto: 'weber flex porcellanato', rendimiento_kg_m2: 5.0, descripcion: 'Adhesivo cementicio impermeable especial para porcellanatos y piezas de baja absorción.', tipo: 'adhesivo' },
    peg_psp: { producto: 'weber piso sobre piso 12hs', rendimiento_kg_m2: 6.0, descripcion: 'Adhesivo de alta adherencia para colocar piso nuevo sobre cerámicas preexistentes sin picar.', tipo: 'adhesivo' },
    peg_glass: { producto: 'weber glass', rendimiento_kg_m2: 4.5, descripcion: 'Adhesivo especial para colocación de venecitas y placas de vidrio en piscinas y zonas húmedas.', tipo: 'adhesivo' },

    // Pastinas (la densidad se usa para la fórmula de Opción B)
    pastina_classic: { producto: 'weber pastina classic', densidad: 1.6, descripcion: 'Pastina cementicia impermeable para juntas finas de hasta 5 mm.', tipo: 'pastina' },
    pastina_prestige: { producto: 'weber pastina prestige', densidad: 1.65, descripcion: 'Pastina cementicia de alta performance y flexibilidad para juntas de 2 a 15 mm.', tipo: 'pastina' },
    pastina_lista: { producto: 'weber pastina lista', densidad: 1.5, descripcion: 'Pastina acrílica monocomponente lista para usar, ideal para juntas de 1 a 4 mm.', tipo: 'pastina' },
    pastina_epoxi: { producto: 'weber pastina epoxi max', densidad: 1.8, descripcion: 'Pastina epoxi bicomponente de máxima resistencia química, impermeable y antimanchas.', tipo: 'pastina' },

    // Nivelación
    autonivelante: { producto: 'weber autonivela', rendimiento_mm_m2: 1.6, descripcion: 'Mortero autonivelante para regularizar pisos interiores con secado ultra rápido.', tipo: 'nivelacion_mm' },
    carpeta_tradicional: { producto: 'weber carpeta', rendimiento_cm_m2: 20.0, descripcion: 'Mortero premezclado listo para hacer carpetas de cemento y regularizar bases.', tipo: 'nivelacion_cm' },
    revoque_fino: { producto: 'weber fino', rendimiento_kg_m2: 3.0, descripcion: 'Revoque fino a la cal para interiores o exteriores con excelente terminación.', tipo: 'fijo' },
    revoque_monocapa: { producto: 'weber monocapa prisma', rendimiento_cm_m2: 15.0, descripcion: 'Revoque monocapa exterior que realiza grueso, fino e impermeabilización en un solo paso.', tipo: 'nivelacion_cm' },

    // Impermeabilización
    imp_techos: { producto: 'weberdry techos con poliuretano', rendimiento_kg_m2: 1.5, descripcion: 'Membrana líquida impermeable de alta elasticidad para terrazas y techos.', tipo: 'fijo' },
    imp_frentes: { producto: 'weberdry frentes y muros', rendimiento_kg_m2: 0.8, descripcion: 'Membrana impermeable de alta elasticidad para fachadas y paredes exteriores.', tipo: 'fijo' },
    imp_ceresita: { producto: 'webertec ceresita', rendimiento_kg_m2: 1.5, descripcion: 'Aditivo hidrófugo en pasta para aislar cimientos, sótanos y revoques gruesos.', tipo: 'fijo' },
    imp_piscinas: { producto: 'weber piscinas', rendimiento_kg_m2: 2.5, descripcion: 'Mortero impermeable flexible bicomponente para piscinas, cisternas y aljibes.', tipo: 'fijo' },
    imp_banio: { producto: 'weber impermeable cerámicos con ceresita', rendimiento_kg_m2: 1.5, descripcion: 'Adhesivo cementicio impermeable para colocación en baños y cocinas.', tipo: 'fijo' },

    // Pisos Decorativos (Microcementos)
    microcemento_base: { producto: 'weber microbase', rendimiento_kg_m2: 2.0, producto_aux: 'weber emulsión', factor_aux: 1 / 3, descripcion: 'Base cementicia niveladora para sistema micropiso decorativo.', tipo: 'bicomponente' },
    microcemento_color: { producto: 'weber microcolor', rendimiento_kg_m2: 1.0, producto_aux: 'weber emulsión', factor_aux: 1 / 2, descripcion: 'Terminación cementicia de color para micropiso decorativo de capa fina.', tipo: 'bicomponente' },

    // Revestimientos Plásticos (weberplast)
    weberplast_fino: { producto: 'weberplast llaneado', rendimiento_kg_m2: 1.6, descripcion: 'Revestimiento plástico texturado decorativo, acabado fino.', tipo: 'texturado' },
    weberplast_medio: { producto: 'weberplast rulato travertino medio', rendimiento_kg_m2: 2.2, descripcion: 'Revestimiento plástico texturado decorativo, acabado medio (Rulato).', tipo: 'texturado' },
    weberplast_grueso: { producto: 'weberplast rulato travertino grueso', rendimiento_kg_m2: 3.2, descripcion: 'Revestimiento plástico texturado decorativo, acabado rústico grueso.', tipo: 'texturado' }
};

const WEBER_DESPERDICIO = 0.10; // 10% de desperdicio técnico técnico

/* ── Estado interno de la sesión Weber ────────────────────────────────── */
let weberContext = {};
let weberCurrentNodeId = 'inicio_weber';

/* ── Función de cálculo (Opción B e integrada) ───────────────────────── */
function calcularMaterialesWeber(soporte, m2, context) {
    const config = WEBER_RENDIMIENTOS[soporte];
    if (!config) return null;

    let kgNecesarios = 0;
    let kgConDesperdicio = 0;
    let unidadesNecesarias = 0;
    let pesoEnvase = 25;
    let unidadComercial = 'bolsas';
    let detalleExtra = '';

    const desperdicioFactor = 1 + WEBER_DESPERDICIO;

    if (config.tipo === 'adhesivo') {
        let rendimiento = config.rendimiento_kg_m2;
        if (context.doble_encolado === 'si') {
            rendimiento *= 1.5;
            detalleExtra = '<span class="text-xs text-gray-300"><em>Incluye un incremento del 50% por técnica de doble encolado (piezas > 30 cm).</em></span><br>';
        }
        kgNecesarios = m2 * rendimiento;
        kgConDesperdicio = kgNecesarios * desperdicioFactor;
        pesoEnvase = 25;
        unidadesNecesarias = Math.ceil(kgConDesperdicio / pesoEnvase);
        unidadComercial = 'bolsas';
    }

    else if (config.tipo === 'pastina') {
        const largo = parseFloat(context.pastina_largo);
        const ancho = parseFloat(context.pastina_ancho);
        const espesor = parseFloat(context.pastina_espesor);
        const junta = parseFloat(context.pastina_junta);

        const largo_mm = largo * 10;
        const ancho_mm = ancho * 10;
        const rendimiento_kg_m2 = ((largo_mm + ancho_mm) * espesor * junta * config.densidad) / (largo_mm * ancho_mm);

        kgNecesarios = m2 * rendimiento_kg_m2;
        kgConDesperdicio = kgNecesarios * desperdicioFactor;

        if (soporte === 'pastina_lista') {
            pesoEnvase = 1;
            unidadComercial = 'baldes';
        } else if (soporte === 'pastina_epoxi') {
            pesoEnvase = 3;
            unidadComercial = 'kits';
        } else {
            pesoEnvase = 5;
            unidadComercial = 'bolsas';
        }
        unidadesNecesarias = Math.ceil(kgConDesperdicio / pesoEnvase);
        detalleExtra = `• <em>Juntas de ${junta} mm en piezas de ${largo}x${ancho} cm (espesor ${espesor} mm).</em><br>` +
            `• Rendimiento calculado: ${rendimiento_kg_m2.toFixed(3)} kg/m².<br>`;
    }

    else if (config.tipo === 'nivelacion_mm') {
        const espesor = parseFloat(context.espesor_medida);
        kgNecesarios = m2 * config.rendimiento_mm_m2 * espesor;
        kgConDesperdicio = kgNecesarios * desperdicioFactor;
        pesoEnvase = 25;
        unidadesNecesarias = Math.ceil(kgConDesperdicio / pesoEnvase);
        unidadComercial = 'bolsas';
        detalleExtra = `• <em>Espesor promedio de nivelación: ${espesor} mm.</em><br>`;
    }

    else if (config.tipo === 'nivelacion_cm') {
        const espesor = parseFloat(context.espesor_medida);
        kgNecesarios = m2 * config.rendimiento_cm_m2 * espesor;
        kgConDesperdicio = kgNecesarios * desperdicioFactor;
        pesoEnvase = 25;
        unidadesNecesarias = Math.ceil(kgConDesperdicio / pesoEnvase);
        unidadComercial = 'bolsas';
        detalleExtra = `• <em>Espesor promedio de capa: ${espesor} cm.</em><br>`;
    }

    else if (config.tipo === 'fijo') {
        kgNecesarios = m2 * config.rendimiento_kg_m2;
        kgConDesperdicio = kgNecesarios * desperdicioFactor;

        if (soporte.startsWith('imp_techos') || soporte.startsWith('imp_frentes')) {
            pesoEnvase = 20;
            unidadComercial = 'baldes';
        } else {
            pesoEnvase = 25;
            unidadComercial = 'bolsas';
        }
        unidadesNecesarias = Math.ceil(kgConDesperdicio / pesoEnvase);
    }

    else if (config.tipo === 'texturado') {
        kgNecesarios = m2 * config.rendimiento_kg_m2;
        kgConDesperdicio = kgNecesarios * desperdicioFactor;
        pesoEnvase = 30;
        unidadesNecesarias = Math.ceil(kgConDesperdicio / pesoEnvase);
        unidadComercial = 'baldes';
    }

    else if (config.tipo === 'bicomponente') {
        kgNecesarios = m2 * config.rendimiento_kg_m2;
        kgConDesperdicio = kgNecesarios * desperdicioFactor;
        pesoEnvase = 25;
        unidadesNecesarias = Math.ceil(kgConDesperdicio / pesoEnvase);
        unidadComercial = 'bolsas';

        const litrosEmulsion = kgConDesperdicio * config.factor_aux;
        const envasesEmulsion = Math.ceil(litrosEmulsion / 10);

        detalleExtra = `• **${config.producto_aux}** necesario: ${litrosEmulsion.toFixed(1)} L (${envasesEmulsion} baldes de 10 L).<br>`;
    }

    return {
        producto: config.producto,
        descripcion: config.descripcion,
        unidades: unidadesNecesarias,
        unidadComercial: unidadComercial,
        pesoEnvase: pesoEnvase,
        kg_totales: kgConDesperdicio.toFixed(1),
        detalleExtra: detalleExtra
    };
}

/* ── Punto de entrada del módulo ──────────────────────────────────────── */
function iniciarExpertoWeber() {
    weberContext = {};
    weberCurrentNodeId = 'inicio_weber';

    const nodoInicio = WEBER_FLOW['inicio_weber'];
    const textoCompleto = `Perfecto! Te voy a guiar para calcular los materiales necesarios para tu obra.<br><br>${nodoInicio.pregunta}`;

    appendMessage('system', textoCompleto);
    renderWeberNode(nodoInicio, true);
}

/* ── Renderizador de nodos ────────────────────────────────────────────── */
function renderWeberNode(nodo, skipQuestionPrint = false) {
    if (!nodo) {
        appendMessage('system', '⚠️ Error interno en el flujo Weber. Por favor, reiniciá el asesor.');
        return;
    }

    if (!skipQuestionPrint) {
        appendMessage('system', nodo.pregunta);
    }

    const inputArea = document.getElementById('input-area');
    if (!inputArea) return;
    inputArea.innerHTML = '';

    // ── Caso A: Nodo de opciones (botones) ──
    if (nodo.tipo === 'opciones') {
        const container = document.createElement('div');
        container.className = 'flex flex-col gap-2 w-full p-1';

        nodo.opciones.forEach((opcion) => {
            const btn = document.createElement('button');
            btn.className = 'w-full text-left bg-blue-100 border border-blue-200 hover:bg-blue-200 text-blue-800 p-2.5 rounded-lg transition-all text-sm font-medium shadow-sm';
            btn.textContent = opcion.texto;
            btn.onclick = () => {
                appendMessage('user', opcion.texto);

                if (nodo.variable && opcion.valor !== undefined) {
                    weberContext[nodo.variable] = opcion.valor;
                }

                weberCurrentNodeId = opcion.siguiente;
                _avanzarNodoWeber();
            };
            container.appendChild(btn);
        });

        inputArea.appendChild(container);
    }

    // ── Caso B: Nodo de entrada de texto/número ──
    else if (nodo.tipo === 'entrada_usuario') {
        const form = document.createElement('form');
        form.className = 'flex gap-2 w-full p-1';

        form.onsubmit = (e) => {
            e.preventDefault();
            const inputEl = document.getElementById('weber-txt-input');
            const valor = parseFloat(inputEl.value);

            if (isNaN(valor) || valor <= 0) {
                alert('Por favor, ingresá un número válido mayor a 0.');
                return;
            }

            weberContext[nodo.variable] = valor;
            const unidad = nodo.unidad || '';
            appendMessage('user', `${valor} ${unidad}`);

            weberCurrentNodeId = nodo.siguiente;
            _avanzarNodoWeber();
        };

        const placeholder = nodo.placeholder || 'Ej: 10';
        form.innerHTML = `
            <input type="number" id="weber-txt-input" required step="0.01" min="0.01"
                   class="border border-gray-300 rounded-lg px-3 py-2 flex-1 text-sm text-gray-800 focus:outline-none focus:border-blue-500"
                   placeholder="${placeholder}">
            <button type="submit"
                    class="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg transition-all text-sm shadow">
                Enviar
            </button>
        `;
        inputArea.appendChild(form);
        document.getElementById('weber-txt-input').focus();
    }

    // ── Caso C: Nodo de resultado final ──
    else if (nodo.tipo === 'respuesta') {
        inputArea.innerHTML = `
            <button onclick="iniciarExpertoWeber()"
                    class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-all text-sm shadow">
                Calcular otra superficie
            </button>`;
    }
}

/* ── Función interna: avanzar al siguiente nodo ─────────────────────── */
function _avanzarNodoWeber() {
    if (weberCurrentNodeId === 'calcular_weber') {
        _ejecutarCalculoWeber();
        return;
    }

    const siguienteNodo = WEBER_FLOW[weberCurrentNodeId];
    if (siguienteNodo) {
        renderWeberNode(siguienteNodo);
    } else {
        _ejecutarCalculoWeber();
    }
}

/* ── Ejecutar el cálculo y mostrar el resultado ───────────────────────── */
function _ejecutarCalculoWeber() {
    const soporte = weberContext['soporte_obra'];
    const m2 = weberContext['metros_cuadrados'];

    if (!soporte || !m2) {
        appendMessage('system', '⚠️ Faltan datos para calcular. Por favor, reiniciá el asesor.');
        return;
    }

    const resultado = calcularMaterialesWeber(soporte, m2, weberContext);
    if (!resultado) {
        appendMessage('system', '⚠️ Ocurrió un error al calcular los materiales.');
        return;
    }

    const textoResultado = `
        <strong> Resultado del Asesoramiento Weber</strong><br><br>
        Para cubrir <strong>${m2} m²</strong>, te recomendamos:<br>
        <strong>${resultado.producto}</strong><br>
        <span class="text-xs text-white">${resultado.descripcion}</span><br><br>
        • <strong>Cantidad necesaria:</strong> ${resultado.unidades} ${resultado.unidadComercial} de ${resultado.pesoEnvase} kg/L.<br>
        • <strong>Material total estimado</strong> (+10% desperdicio): ${resultado.kg_totales} kg/L.<br><br>
        ${resultado.detalleExtra}
    `;

    appendMessage('system', textoResultado);

    // Guardar contexto activo para preguntas de seguimiento en el chat libre
    lastActiveBrand = 'WEBER';
    lastActiveProduct = resultado.producto;

    // Buscar y mostrar la tarjeta de producto real en el catálogo
    const targetModel = resultado.producto.toLowerCase();
    const recommendedProduct = productCatalog.find(p => p.model.toLowerCase() === targetModel);
    if (recommendedProduct) {
        setTimeout(() => {
            renderProducts([recommendedProduct]);
        }, 300);
    }

    // Mostrar botón de reinicio
    const inputArea = document.getElementById('input-area');
    if (inputArea) {
        inputArea.innerHTML = `
            <button onclick="iniciarExpertoWeber()"
                    class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-all text-sm shadow">
                 Calcular otra superficie
            </button>`;
    }
}
