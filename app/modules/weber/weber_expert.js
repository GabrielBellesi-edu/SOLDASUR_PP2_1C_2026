/* ==========================================================================
   WEBER_EXPERT.JS — Sistema Experto de Construcción / Revestimientos Weber
   100% frontend — NO requiere Uvicorn ni ningún backend corriendo.
   Funciona igual que la calculadora PEISA: solo con `python -m http.server`.

   Requiere: core.js (appendMessage, renderOptions, scrollToBottom, etc.)
   ========================================================================== */

/* ── Árbol de decisión del cuestionario ──────────────────────────────────
   Equivale al archivo weber_advisor_knowledge_base.json + la lógica del
   endpoint /expert/weber/start y /expert/weber/reply del backend.
   ─────────────────────────────────────────────────────────────────────── */
const WEBER_FLOW = {
    inicio_weber: {
        id:       'inicio_weber',
        pregunta: '¿Qué tipo de trabajo vas a realizar en la obra?',
        tipo:     'opciones',
        opciones: [
            { texto: 'Colocación de Revestimientos (Cerámicos / Porcelanatos)', siguiente: 'soporte_revestimiento' },
            { texto: 'Impermeabilización de Superficies',                        siguiente: 'tipo_impermeabilizacion' }
        ]
    },

    soporte_revestimiento: {
        id:       'soporte_revestimiento',
        pregunta: '¿Sobre qué superficie / soporte vas a colocar las piezas?',
        tipo:     'opciones',
        variable: 'soporte_obra',
        opciones: [
            { texto: 'Carpeta de cemento / Revoque tradicional',        valor: 'tradicional',     siguiente: 'superficie_m2' },
            { texto: 'Placas de yeso (Durlock)',                         valor: 'yeso',            siguiente: 'superficie_m2' },
            { texto: 'Piso o revestimiento antiguo (Piso sobre piso)',  valor: 'piso_sobre_piso', siguiente: 'superficie_m2' }
        ]
    },

    tipo_impermeabilizacion: {
        id:       'tipo_impermeabilizacion',
        pregunta: '¿Qué superficie querés impermeabilizar?',
        tipo:     'opciones',
        variable: 'soporte_obra',
        opciones: [
            { texto: 'Losa / Techo expuesto',              valor: 'impermeabilizacion_losa',    siguiente: 'superficie_m2' },
            { texto: 'Baño o cocina (paredes húmedas)',     valor: 'impermeabilizacion_banio',   siguiente: 'superficie_m2' },
            { texto: 'Piscina o aljibe',                    valor: 'impermeabilizacion_piscina', siguiente: 'superficie_m2' }
        ]
    },

    superficie_m2: {
        id:       'superficie_m2',
        pregunta: 'Ingresá los metros cuadrados (m²) totales de la superficie a trabajar:',
        tipo:     'entrada_usuario',
        variable: 'metros_cuadrados',
        siguiente:'calcular_weber'
    }
    // El nodo "calcular_weber" se maneja directamente en código (ver renderWeberNode)
};

/* ── Tabla de rendimientos por tipo de soporte / obra ───────────────────
   Equivale a la función resolver_calculo() de weber_expert_engine.py
   ─────────────────────────────────────────────────────────────────────── */
const WEBER_RENDIMIENTOS = {
    tradicional:                { producto: 'weber gris cerámicos',                  rendimiento_kg_m2: 5.0,  descripcion: 'Adhesivo cementicio para superficies porosas' },
    yeso:                       { producto: 'weber pasta listo',                    rendimiento_kg_m2: 3.5,  descripcion: 'Adhesivo especial para placas de yeso (Durlock)' },
    piso_sobre_piso:            { producto: 'weber piso sobre piso 12hs',           rendimiento_kg_m2: 6.0,  descripcion: 'Adhesivo de alta adherencia para renovación' },
    impermeabilizacion_losa:    { producto: 'webertec membrana',                    rendimiento_kg_m2: 2.0,  descripcion: 'Membrana impermeabilizante para losas y techos expuestos' },
    impermeabilizacion_banio:   { producto: 'weber impermeable cerámicos con ceresita', rendimiento_kg_m2: 1.5,  descripcion: 'Adhesivo impermeable para ambientes húmedos' },
    impermeabilizacion_piscina: { producto: 'weber piscinas',                       rendimiento_kg_m2: 2.5,  descripcion: 'Mortero impermeabilizante para piscinas y aljibes' }
};

const WEBER_PESO_BOLSA_KG = 25;
const WEBER_DESPERDICIO    = 0.10; // 10% de desperdicio técnico

/* ── Estado interno de la sesión Weber ────────────────────────────────── */
let weberContext = {};   // variables acumuladas (soporte_obra, metros_cuadrados, etc.)
let weberCurrentNodeId = 'inicio_weber';

/* ── Función de cálculo (equivale a resolver_calculo en Python) ──────── */
function calcularMaterialesWeber(soporte, m2) {
    const config = WEBER_RENDIMIENTOS[soporte] || { producto: 'weber basic cerámicos', rendimiento_kg_m2: 5.0, descripcion: 'Adhesivo universal' };
    const kgNecesarios      = m2 * config.rendimiento_kg_m2;
    const kgConDesperdicio  = kgNecesarios * (1 + WEBER_DESPERDICIO);
    const bolsasNecesarias  = Math.ceil(kgConDesperdicio / WEBER_PESO_BOLSA_KG);

    return {
        producto:          config.producto,
        descripcion:       config.descripcion,
        rendimiento_kg_m2: config.rendimiento_kg_m2,
        bolsas_necesarias: bolsasNecesarias,
        kg_totales:        kgConDesperdicio.toFixed(1)
    };
}

/* ── Punto de entrada del módulo ──────────────────────────────────────── */
function iniciarExpertoWeber() {
    // Resetear sesión
    weberContext = {};
    weberCurrentNodeId = 'inicio_weber';

    // Mensaje de bienvenida
    appendMessage('system', '<strong>🧱 Asesor Experto Weber:</strong> Te voy a guiar para calcular los materiales necesarios para tu obra.');

    // Renderizar el primer nodo del árbol
    renderWeberNode(WEBER_FLOW['inicio_weber']);
}

/* ── Renderizador de nodos ────────────────────────────────────────────── */
function renderWeberNode(nodo) {
    if (!nodo) {
        appendMessage('system', '⚠️ Error interno en el flujo Weber. Por favor, reiniciá el asesor.');
        return;
    }

    // Mostrar la pregunta del nodo
    appendMessage('system', nodo.pregunta);

    const inputArea = document.getElementById('input-area');
    if (!inputArea) return;
    inputArea.innerHTML = '';

    // ── Caso A: Nodo de opciones (botones) ──
    if (nodo.tipo === 'opciones') {
        const container = document.createElement('div');
        container.className = 'flex flex-col gap-2 w-full p-1';

        nodo.opciones.forEach((opcion, index) => {
            const btn = document.createElement('button');
            btn.className = 'w-full text-left bg-blue-100 border border-blue-200 hover:bg-blue-200 text-blue-800 p-2.5 rounded-lg transition-all text-sm font-medium shadow-sm';
            btn.textContent = opcion.texto;
            btn.onclick = () => {
                appendMessage('user', opcion.texto);

                // Guardar variable en el contexto si el nodo la tiene definida
                if (nodo.variable && opcion.valor !== undefined) {
                    weberContext[nodo.variable] = opcion.valor;
                }

                // Avanzar al siguiente nodo
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
            const valor   = parseFloat(inputEl.value);

            if (!valor || isNaN(valor) || valor <= 0) {
                alert('Por favor, ingresá un número válido mayor a 0.');
                return;
            }

            weberContext[nodo.variable] = valor;
            appendMessage('user', `${valor} m²`);

            // Avanzar al siguiente nodo
            weberCurrentNodeId = nodo.siguiente;
            _avanzarNodoWeber();
        };

        form.innerHTML = `
            <input type="number" id="weber-txt-input" required step="0.1" min="0.1"
                   class="border border-gray-300 rounded-lg px-3 py-2 flex-1 text-sm text-gray-800 focus:outline-none focus:border-blue-500"
                   placeholder="Ej: 25.5">
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
                🔄 Calcular otra superficie
            </button>`;
    }
}

/* ── Función interna: avanzar al siguiente nodo ─────────────────────── */
function _avanzarNodoWeber() {
    // Si el siguiente paso es el cálculo, ejecutarlo directamente
    if (weberCurrentNodeId === 'calcular_weber') {
        _ejecutarCalculoWeber();
        return;
    }

    const siguienteNodo = WEBER_FLOW[weberCurrentNodeId];
    if (siguienteNodo) {
        renderWeberNode(siguienteNodo);
    } else {
        // Si no hay nodo definido en el árbol, intentar el cálculo
        _ejecutarCalculoWeber();
    }
}

/* ── Ejecutar el cálculo y mostrar el resultado ───────────────────────── */
function _ejecutarCalculoWeber() {
    const soporte = weberContext['soporte_obra'];
    const m2      = weberContext['metros_cuadrados'];

    if (!soporte || !m2) {
        appendMessage('system', '⚠️ Faltan datos para calcular. Por favor, reiniciá el asesor.');
        return;
    }

    const resultado = calcularMaterialesWeber(soporte, m2);

    // Mensaje de resultado enriquecido (igual estilo que el sistema PEISA)
    const textoResultado = `
        <strong>📊 Resultado del Asesoramiento Weber</strong><br><br>
        Para cubrir <strong>${m2} m²</strong>, te recomendamos:<br>
        <strong>${resultado.producto}</strong><br><br>
        • <strong>Cantidad necesaria:</strong> ${resultado.bolsas_necesarias} bolsas de ${WEBER_PESO_BOLSA_KG} kg<br>
        • <strong>Rendimiento estimado:</strong> ${resultado.rendimiento_kg_m2} kg/m²<br>
        • <strong>Material total (con +10% de desperdicio):</strong> ${resultado.kg_totales} kg
    `;

    appendMessage('system', textoResultado);

    // Buscar y mostrar la tarjeta de producto real
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
                🔄 Calcular otra superficie
            </button>`;
    }
}
