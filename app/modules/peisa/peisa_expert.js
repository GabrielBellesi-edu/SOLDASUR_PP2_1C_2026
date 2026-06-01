/* ==========================================================================
   PEISA_EXPERT.JS — Sistema Experto de Calefacción PEISA
   Contiene: flujo de preguntas, cálculos de carga térmica, recomendación
   de productos. 100% frontend, sin dependencia de backend.
   Requiere: core.js (appendMessage, renderOptions, productCatalog, etc.)
   ========================================================================== */

/* ── Estado del sistema experto PEISA ─────────────────────────────────── */
// conversationStep se encuentra declarado globalmente en core.js
let userInputs       = {};
let contextData      = {};
let lastRecommendedProduct = null;

/* ── Iniciar sistema experto ────────────────────────────────────────────── */
function startExpertSystem() {
    conversationStep = 0;
    userInputs = {};
    contextData = {};
    lastRecommendedProduct = null;
    updateContextPanel();
    appendMessage('system', '¡Perfecto! Te guiaré paso a paso para calcular tu sistema de calefacción.');
    setTimeout(() => askQuestion(), 500);
}

function resetExpertSystem() {
    conversationStep = 0;
    userInputs = {};
    contextData = {};
    lastRecommendedProduct = null;
    updateContextPanel();
}

/* ── Flujo principal de preguntas ──────────────────────────────────────── */
function askQuestion() {
    conversationStep++;
    const tipo = userInputs.tipo;

    // PASO 1: Tipo de calefacción
    if (conversationStep === 1) {
        appendMessage('system', '¿Qué tipo de calefacción deseas calcular?');
        renderOptions(['Piso radiante', 'Radiadores', 'Calderas'], false);
    }

    // ── FLUJO PISO RADIANTE ──
    else if (tipo === 'Piso radiante') {
        if (conversationStep === 2) {
            appendMessage('system', '¿Cuál es la superficie a calefaccionar?');
            createNumberInput({ input_label: 'Superficie en m²' });
        } else if (conversationStep === 3) {
            contextData.superficie = userInputs.superficie + ' m²';
            updateContextPanel();
            appendMessage('system', `Perfecto, ${userInputs.superficie}m². ¿En qué zona geográfica se encuentra?`);
            renderOptions(['Norte', 'Centro', 'Sur'], false);
        } else if (conversationStep === 4) {
            contextData.zona = userInputs.zona;
            updateContextPanel();
            appendMessage('system', '¿Cuál es el nivel de aislación térmica de la vivienda?');
            renderOptions(['Buena', 'Regular', 'Mala'], false);
        } else if (conversationStep === 5) {
            calculateHeatingLoad();
        }
    }

    // ── FLUJO RADIADORES ──
    else if (tipo === 'Radiadores') {
        if (conversationStep === 2) {
            appendMessage('system', '¿Cuál es el principal objetivo para los radiadores?');
            renderOptions(['Calefacción principal de ambiente', 'Calefacción complementaria', 'Secado de toallas (baño)'], false);
        } else if (conversationStep === 3) {
            contextData.objetivo = userInputs.objetivo;
            updateContextPanel();
            if (userInputs.objetivo === 'Secado de toallas (baño)') {
                showTowelRackRecommendation();
                return;
            }
            appendMessage('system', 'Indique las dimensiones del ambiente:');
            createDimensionsInput();
        } else if (conversationStep === 4) {
            contextData.dimensiones = `${userInputs.largo}m x ${userInputs.ancho}m x ${userInputs.alto}m`;
            updateContextPanel();
            appendMessage('system', 'Nivel de aislación térmica del ambiente:');
            renderOptions(['Alta (doble vidrio, aislación en paredes)', 'Media (vidrio simple, algunas paredes aisladas)', 'Baja (sin aislación significativa)'], false);
        } else if (conversationStep === 5) {
            contextData.aislacion = userInputs.aislacion;
            updateContextPanel();
            appendMessage('system', 'Tipo de instalación preferida:');
            renderOptions(['Empotrada', 'Superficie', 'No tengo preferencia'], false);
        } else if (conversationStep === 6) {
            contextData.instalacion = userInputs.instalacion;
            updateContextPanel();
            appendMessage('system', 'Estilo de diseño preferido:');
            renderOptions(['Moderno/minimalista', 'Clásico/tradicional', 'No tengo preferencia'], false);
        } else if (conversationStep === 7) {
            contextData.estilo = userInputs.estilo;
            updateContextPanel();
            appendMessage('system', 'Color preferido para los radiadores:');
            renderOptions(['Blanco', 'Negro', 'Cromo', 'No tengo preferencia'], false);
        } else if (conversationStep === 8) {
            calculateRadiatorLoad();
        }
    }

    // ── FLUJO CALDERAS ──
    else if (tipo === 'Calderas') {
        if (conversationStep === 2) {
            appendMessage('system', '¿Cuál es la carga térmica total de todos los ambientes a calefaccionar?');
            createNumberInput({ input_label: 'Carga térmica en kcal/h' });
        } else if (conversationStep === 3) {
            contextData['Carga térmica total'] = userInputs.carga_termica_total + ' kcal/h';
            updateContextPanel();
            appendMessage('system', '¿Necesita agua caliente sanitaria (ACS)?');
            renderOptions(['Sí, necesito ACS', 'No, solo calefacción'], false);
        } else if (conversationStep === 4) {
            calculateBoilerLoad();
        }
    }
}

/* ── Manejar respuestas del usuario en el flujo experto ───────────────── */
function handleExpertSystemResponse(option) {
    const tipo = userInputs.tipo;

    if (conversationStep === 1) {
        userInputs.tipo = option;
        contextData.tipo = option;
    } else if (tipo === 'Piso radiante') {
        if (conversationStep === 3) userInputs.zona     = option;
        else if (conversationStep === 4) userInputs.aislacion = option;
    } else if (tipo === 'Radiadores') {
        if (conversationStep === 2)      userInputs.objetivo   = option;
        else if (conversationStep === 4) userInputs.aislacion  = option;
        else if (conversationStep === 5) userInputs.instalacion = option;
        else if (conversationStep === 6) userInputs.estilo     = option;
        else if (conversationStep === 7) userInputs.color      = option;
    } else if (tipo === 'Calderas') {
        if (conversationStep === 3) userInputs.agua_caliente = option;
    }

    setTimeout(() => askQuestion(), 500);
}

/* ── Cálculo de carga para piso radiante ──────────────────────────────── */
function calculateHeatingLoad() {
    const superficie = parseFloat(userInputs.superficie);
    const zona       = userInputs.zona;
    const aislacion  = userInputs.aislacion;

    let factor = zona === 'Norte' ? 80 : zona === 'Centro' ? 100 : 125;
    if (aislacion === 'Mala')  factor *= 1.2;
    if (aislacion === 'Buena') factor *= 0.9;

    const cargaTermica      = Math.round(superficie * factor);
    const cargaTermicaKcal  = Math.round(cargaTermica * 0.859845);
    contextData['Carga térmica'] = cargaTermica + ' W';
    updateContextPanel();

    appendMessage('system',
        `¡Perfecto! Analizando tu ambiente de <strong>${superficie}m²</strong> en zona <strong>${zona}</strong> con aislación <strong>${aislacion.toLowerCase()}</strong>, necesitás una potencia de <strong>${cargaTermica}W</strong> (aprox. <strong>${cargaTermicaKcal} kcal/h</strong>).<br><br>Basado en estos datos, te recomiendo el mejor equipo:`);

    setTimeout(() => {
        showRecommendedProducts('piso');
        renderOptions(['Nuevo cálculo', 'Hacer una pregunta'], false);
    }, 500);
}

/* ── Cálculo de carga para radiadores ─────────────────────────────────── */
function calculateRadiatorLoad() {
    const { largo, ancho, alto, aislacion, objetivo, instalacion, estilo, color } = userInputs;
    const volumen      = largo * ancho * alto;
    let factor = 40;
    if (aislacion.includes('Baja')) factor = 50;
    if (aislacion.includes('Alta')) factor = 30;
    const cargaTermica = Math.round(volumen * factor);
    contextData['Carga térmica'] = cargaTermica + ' kcal/h';
    updateContextPanel();

    const descAislacion = aislacion.toLowerCase().includes('alta') ? 'buena aislación térmica'
                        : aislacion.toLowerCase().includes('baja') ? 'aislación térmica básica'
                        : 'aislación térmica media';

    appendMessage('system',
        `¡Excelente! He analizado tu ambiente de <strong>${largo}m x ${ancho}m x ${alto}m</strong> (<strong>${volumen.toFixed(1)}m³</strong>) con <strong>${descAislacion}</strong>.<br><br>Necesitás una potencia de <strong>${cargaTermica} kcal/h</strong>. Basado en tus preferencias de instalación <strong>${instalacion.toLowerCase()}</strong>, estilo <strong>${estilo.toLowerCase()}</strong> y color <strong>${color.toLowerCase()}</strong>, te recomiendo:`);

    setTimeout(() => {
        showRecommendedProductsForRadiators(cargaTermica, objetivo, instalacion, estilo, color);
        renderOptions(['Nuevo cálculo', 'Hacer una pregunta'], false);
    }, 500);
}

/* ── Cálculo de carga para calderas ───────────────────────────────────── */
function calculateBoilerLoad() {
    const cargaTermicaTotal = parseFloat(userInputs.carga_termica_total);
    const necesitaACS       = userInputs.agua_caliente;
    const potenciaRequerida = Math.round(cargaTermicaTotal * 1.2);
    const tipoCaldera = necesitaACS === 'Sí, necesito ACS' ? 'Caldera doble servicio' : 'Caldera mural';
    contextData['Potencia requerida'] = potenciaRequerida + ' kcal/h';
    contextData['Tipo caldera']       = tipoCaldera;
    updateContextPanel();

    const mensajeACS = necesitaACS === 'Sí, necesito ACS'
        ? 'Como necesitás agua caliente sanitaria, buscaremos una caldera de doble servicio.'
        : 'Como solo necesitás calefacción, podemos optimizar la elección.';

    appendMessage('system',
        `¡Muy bien! Necesitás una potencia base de <strong>${cargaTermicaTotal} kcal/h</strong>. Aplicando un factor de seguridad del 20%, necesitarás una caldera de <strong>${potenciaRequerida} kcal/h</strong>.<br><br>${mensajeACS}<br><br>Te recomiendo:`);

    setTimeout(() => {
        showRecommendedProductsForBoilers(potenciaRequerida, necesitaACS);
        renderOptions(['Nuevo cálculo', 'Hacer una pregunta'], false);
    }, 500);
}

/* ── Lógica de selección de productos ─────────────────────────────────── */
function showRecommendedProducts(tipo) {
    const catalog = peisaProductsFromJSON || [];
    if (!catalog.length) return;

    const cargaTermica = parseFloat(contextData['Carga térmica']) || 0;
    const superficie   = parseFloat(userInputs.superficie) || 0;
    let recommendedProduct = null;

    if (tipo === 'piso') {
        const calderas = catalog.filter(p => p.family === 'Calderas' && p.description?.toLowerCase().includes('doble servicio'));
        if (superficie < 100)       recommendedProduct = calderas.find(p => p.model.includes('Diva Tecno') || p.model.includes('Diva DS')) || calderas[0];
        else if (superficie < 200)  recommendedProduct = calderas.find(p => p.model.includes('Prima Tec')) || calderas[0];
        else                        recommendedProduct = calderas.find(p => p.model.includes('Summa Condens') || p.model.includes('Prima Tec Smart')) || calderas[0];
        if (!recommendedProduct && calderas.length) recommendedProduct = calderas[0];
    }

    if (!recommendedProduct) {
        recommendedProduct = catalog.find(p => p.model.includes('Prima Tec Smart') || p.model.includes('Diva'));
    }

    if (recommendedProduct) {
        lastRecommendedProduct = recommendedProduct;
        renderProducts([recommendedProduct]);
    }
}

function showRecommendedProductsForRadiators(cargaTermica, objetivo, instalacion, estilo, color) {
    const catalog = peisaProductsFromJSON || [];
    let radiadores = catalog.filter(p => p.family === 'Radiadores' && p.category === 'Radiadores' && !p.model.toLowerCase().includes('toallero'));

    let filtered = [...radiadores];
    if (color && !color.includes('preferencia')) {
        const cl = color.toLowerCase();
        filtered = filtered.filter(p => {
            const desc  = (p.description || '').toLowerCase();
            const model = p.model.toLowerCase();
            return desc.includes(cl) || model.includes(cl) || (cl === 'blanco' && !desc.includes('negro'));
        });
    }
    if (estilo && !estilo.includes('preferencia')) {
        const es = estilo.toLowerCase();
        filtered = filtered.filter(p => {
            const desc  = (p.description || '').toLowerCase();
            const model = p.model.toLowerCase();
            if (es.includes('moderno'))  return model.includes('broen') || desc.includes('moderno') || desc.includes('minimalista');
            if (es.includes('clasico')) return model.includes('tropical') || desc.includes('clásico') || desc.includes('tradicional');
            return true;
        });
    }
    if (filtered.length === 0) filtered = radiadores;

    let recommendedProduct = null;
    if (cargaTermica < 1500) {
        const electricos = filtered.filter(p => p.model.toLowerCase().includes('eléctrico') || p.model.toLowerCase().includes('electrico'));
        recommendedProduct = electricos.find(p => p.model.includes('Broen E')) || electricos[0];
    } else if (cargaTermica < 3000) {
        recommendedProduct = filtered.find(p => p.model.includes('Broen') && !p.model.includes('Plus')) || filtered.find(p => p.model.includes('Tropical')) || filtered[0];
    } else {
        recommendedProduct = filtered.find(p => p.model.includes('Broen Plus')) || filtered.find(p => p.model.includes('Gamma')) || filtered[0];
    }
    if (!recommendedProduct && filtered.length) recommendedProduct = filtered[0];

    if (recommendedProduct) {
        lastRecommendedProduct = recommendedProduct;
        renderProducts([recommendedProduct]);
    }
}

function showRecommendedProductsForBoilers(potenciaRequerida, necesitaACS) {
    const catalog = peisaProductsFromJSON || [];
    let calderas = catalog.filter(p => p.family === 'Calderas');
    let recommendedProduct = null;

    if (necesitaACS === 'Sí, necesito ACS') {
        const ds = calderas.filter(p => p.description?.toLowerCase().includes('doble servicio'));
        if (potenciaRequerida < 25000)      recommendedProduct = ds.find(p => p.model.includes('Diva DS')) || ds[0];
        else if (potenciaRequerida < 35000) recommendedProduct = ds.find(p => p.model.includes('Prima Tec') || p.model.includes('Diva Tecno')) || ds[0];
        else                                recommendedProduct = ds.find(p => p.model.includes('Prima Tec Smart') || p.model.includes('Summa Condens')) || ds[0];
    } else {
        const sc = calderas.filter(p => p.model.includes('Diva C') || p.category?.toLowerCase().includes('central') || !p.description?.toLowerCase().includes('doble servicio'));
        if (potenciaRequerida < 30000)       recommendedProduct = sc.find(p => p.model.includes('Diva C')) || sc[0];
        else if (potenciaRequerida < 100000) recommendedProduct = sc.find(p => p.model.includes('XP') || p.model.includes('CM')) || sc[0];
        else                                 recommendedProduct = sc.find(p => p.model.includes('Magna') || p.model.includes('Modal') || p.model.includes('Optima')) || sc[0];
    }
    if (!recommendedProduct && calderas.length) recommendedProduct = calderas[0];

    if (recommendedProduct) {
        lastRecommendedProduct = recommendedProduct;
        renderProducts([recommendedProduct]);
    }
}

function showTowelRackRecommendation() {
    const catalog   = peisaProductsFromJSON || [];
    const toalleros = catalog.filter(p => p.category === 'Toalleros' || p.model.toLowerCase().includes('toallero') || p.model.toLowerCase().includes('scala') || p.model.toLowerCase().includes('domino'));
    appendMessage('system', 'Para secado de toallas te recomendamos:');
    if (toalleros.length) {
        const rec = toalleros.find(p => p.model.includes('Domino S')) || toalleros[0];
        lastRecommendedProduct = rec;
        renderProducts([rec]);
    }
    setTimeout(() => renderOptions(['Nuevo cálculo', 'Hacer una pregunta'], false), 500);
}
