/* Configuración Ollama */
const OLLAMA_URL = 'http://localhost:11434/api/chat';
const OLLAMA_MODEL = 'llama3.2:3b';
const conversationHistory = [];
const MAX_HISTORY_LENGTH = 10; // Mantener últimos 10 mensajes para no saturar el contexto
let conversationContext = ''; // Resumen del contexto de la conversación
let waitingForCity = false; // Estado para saber si estamos esperando que el usuario elija ciudad
let selectedProductForConsult = null; // Producto elegido para consulta comercial
// NOTA v4: peisaProductsFromJSON y loadProductCatalog viven en core.js

/* Iniciar modo chatbot */
function startChatbot() {
    if (conversationHistory.length > 0) {
        appendMessage('system', '¡Continuemos! ¿Qué más necesitas saber?');
    } else {
        appendMessage('system', '¿Qué necesitas saber?');
    }
    showChatInput();
}

/* Resetear historial de conversación */
function resetChatHistory() {
    conversationHistory.length = 0;
    conversationContext = '';
    waitingForCity = false;
}

/* Mostrar información de contacto según la ciudad */
function showContactInfo(city) {
    let contactHTML = '';

    if (city === 'riogrande') {
        contactHTML = `
            <div class="bg-blue-50 border-l-4 border-blue-600 p-4 rounded">
                <div class="font-bold text-blue-900 mb-2">RÍO GRANDE</div>
                <div class="space-y-2 text-sm">
                    <div>
                        <strong>Sucursal 1:</strong><br>
                        Islas Malvinas 1950<br>
                        Tel. 02964 422350<br>
                        Email: ventasrg@soldasur.com.ar
                    </div>
                    <div class="pt-2 border-t border-blue-200">
                        <strong>Sucursal 2:</strong><br>
                        Av. San Martín 366<br>
                        Tel. 02964 422131
                    </div>
                </div>
            </div>
        `;
    } else if (city === 'ushuaia') {
        contactHTML = `
            <div class="bg-green-50 border-l-4 border-green-600 p-4 rounded">
                <div class="font-bold text-green-900 mb-2">USHUAIA</div>
                <div class="space-y-2 text-sm">
                    <div>
                        <strong>Sucursal 1:</strong><br>
                        Héroes de Malvinas 4180<br>
                        Tel. 02901 436392<br>
                        Email: ventasush@soldasur.com.ar
                    </div>
                    <div class="pt-2 border-t border-green-200">
                        <strong>Sucursal 2:</strong><br>
                        Gobernador Paz 665<br>
                        Tel. 02901 430886
                    </div>
                </div>
            </div>
        `;
    }

    // Mensaje contextual si viene de "Consultar producto"
    if (selectedProductForConsult) {
        appendMessage('system', `Consulta por ${selectedProductForConsult.model}: ¿Querés que te contacten? Acá están nuestros datos según tu ciudad:`);
    } else {
        appendMessage('system', '¡Perfecto! Acá están nuestros datos de contacto:');
    }

    const chatContainer = document.getElementById('chat-container');
    const contactDiv = document.createElement('div');
    contactDiv.className = 'fade-in mt-2';
    contactDiv.innerHTML = contactHTML;
    chatContainer.appendChild(contactDiv);
    scrollToBottom();
    // Resetear producto seleccionado después de mostrar contactos
    selectedProductForConsult = null;
}

/* Mostrar input de chat */
function showChatInput() {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.value = '';
        chatInput.focus();
    }

    const showResetButton = conversationHistory.length > 2; // Mostrar después de 2 mensajes
    const extraActions = document.getElementById('chat-extra-actions');
    if (extraActions) {
        extraActions.innerHTML = showResetButton ? `
            <button onclick="handleResetConversation()" class="w-full text-xs text-gray-500 hover:text-gray-700 py-1 mt-1">
                 Nueva conversación
            </button>
        ` : '';
    }
}

/* Manejar reset de conversación */
function handleResetConversation() {
    if (confirm('¿Deseas iniciar una nueva conversación? Se perderá el contexto actual.')) {
        resetChatHistory();
        document.getElementById('chat-container').innerHTML = '';
        startChatbot();
    }
}

/* Manejar input de chat */
async function handleChatInput() {
    const input = document.getElementById('chat-input');
    const question = input.value.trim();

    if (question) {
        appendMessage('user', question);
        input.value = '';

        // Interceptar consultas de refrigeración (fuera del catálogo)
        if (isCoolingQuestion(question)) {
            appendMessage('system', 'Disculpá, no vendemos equipos de refrigeración o aire acondicionado. Nos especializamos en calefacción y agua caliente. ¿Te puedo ayudar con algo de eso?');
            showChatInput();
            return;
        }

        // NO interceptar consultas de precio - dejar que Ollama las maneje con contexto
        // El system prompt ya tiene instrucciones para manejar precios

        // Detectar si el usuario está respondiendo con una ciudad
        if (waitingForCity && (question.toLowerCase().includes('río grande') || question.toLowerCase().includes('rio grande') || question.toLowerCase().includes('rg'))) {
            showContactInfo('riogrande');
            waitingForCity = false;
            showChatInput();
            return;
        } else if (waitingForCity && (question.toLowerCase().includes('ushuaia') || question.toLowerCase().includes('ush'))) {
            showContactInfo('ushuaia');
            waitingForCity = false;
            showChatInput();
            return;
        }

        showLoadingIndicator();

        try {
            const response = await callOllama(question);
            hideLoadingIndicator();

            // Limpiar y mostrar mensaje humanizado
            const cleanMessage = cleanHtmlFromMessage(response.message);
            appendMessage('system', cleanMessage);

            // Detectar si la respuesta pregunta por la ciudad y mostrar botones
            if (response.message.toLowerCase().includes('río grande o ushuaia') ||
                response.message.toLowerCase().includes('rio grande o ushuaia')) {
                waitingForCity = true;

                // Mostrar botones de ciudad
                setTimeout(() => {
                    const chatContainer = document.getElementById('chat-container');
                    const buttonsDiv = document.createElement('div');
                    buttonsDiv.className = 'fade-in mt-2 flex gap-2';

                    const btnRG = document.createElement('button');
                    btnRG.className = 'text-sm px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors';
                    btnRG.textContent = 'Río Grande';
                    btnRG.onclick = () => {
                        appendMessage('user', 'Río Grande');
                        showContactInfo('riogrande');
                        waitingForCity = false;
                        showChatInput();
                    };

                    const btnUsh = document.createElement('button');
                    btnUsh.className = 'text-sm px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors';
                    btnUsh.textContent = 'Ushuaia';
                    btnUsh.onclick = () => {
                        appendMessage('user', 'Ushuaia');
                        showContactInfo('ushuaia');
                        waitingForCity = false;
                        showChatInput();
                    };

                    buttonsDiv.appendChild(btnRG);
                    buttonsDiv.appendChild(btnUsh);
                    chatContainer.appendChild(buttonsDiv);
                    scrollToBottom();
                }, 300);
            }

            // Si Ollama recomienda productos, mostrarlos
            if (response.products && response.products.length > 0) {
                setTimeout(() => {
                    renderProducts(response.products);
                }, 300);
            }

            // Volver a mostrar el input
            showChatInput();
        } catch (error) {
            hideLoadingIndicator();
            appendMessage('system', 'Lo siento, hubo un error al procesar tu consulta. Por favor, intenta nuevamente.');
            showChatInput();
        }
    }
}

/* Filtrar productos relevantes según la consulta */
function filterRelevantProducts(userMessage, catalog) {
    const msg = userMessage.toLowerCase();
    let relevantProducts = [];

    // Detectar tipo de necesidad (PEISA)
    const needsHeating = msg.includes('frío') || msg.includes('frio') || msg.includes('calefacción') || msg.includes('calefaccion') || msg.includes('calentar');
    const needsHotWater = msg.includes('agua caliente') || msg.includes('ducha') || msg.includes('baño');
    const needsRadiator = msg.includes('radiador') || msg.includes('ambiente') || msg.includes('habitación') || msg.includes('habitacion');
    const needsBoiler = msg.includes('caldera') || msg.includes('casa') || msg.includes('toda');
    const needsElectric = msg.includes('eléctrico') || msg.includes('electrico') || msg.includes('enchufe');
    const needsTowelRack = msg.includes('toallero') || msg.includes('toalla');

    // Detectar tipo de necesidad (Weber)
    const needsWeber = msg.includes('weber') || msg.includes('construc') || msg.includes('obra') || msg.includes('pegar') || msg.includes('baldosa') || msg.includes('cerámic') || msg.includes('ceram');
    const needsWaterproof = msg.includes('impermeab') || msg.includes('humedad') || msg.includes('techo') || msg.includes('losa') || msg.includes('filtrac') || msg.includes('piscina');
    const needsFloors = msg.includes('piso') || msg.includes('nivelar') || msg.includes('microcemento') || msg.includes('carpeta') || msg.includes('alisado');

    // Filtrar por familia/categoría relevante
    if (needsTowelRack) {
        // Priorizar toalleros
        relevantProducts = catalog.filter(p =>
            p.category === 'Toalleros' ||
            p.type?.toLowerCase().includes('toallero') ||
            p.model.toLowerCase().includes('toallero') ||
            p.model.toLowerCase().includes('domino') ||
            p.model.toLowerCase().includes('scala')
        );
    } else if (needsRadiator || (needsHeating && !needsBoiler)) {
        // Priorizar radiadores
        relevantProducts = catalog.filter(p =>
            p.family === 'Radiadores' ||
            p.model.toLowerCase().includes('radiador')
        );
    } else if (needsBoiler || needsHotWater) {
        // Priorizar calderas
        relevantProducts = catalog.filter(p =>
            p.family === 'Calderas' ||
            p.model.toLowerCase().includes('caldera') ||
            p.model.toLowerCase().includes('prima') ||
            p.model.toLowerCase().includes('diva')
        );
    } else if (needsElectric) {
        // Priorizar productos eléctricos
        relevantProducts = catalog.filter(p =>
            p.model.toLowerCase().includes('eléctrico') ||
            p.model.toLowerCase().includes('electrico') ||
            p.model.toLowerCase().includes('broen e')
        );
    } else if (needsWeber || needsWaterproof || needsFloors) {
        // Priorizar productos Weber
        relevantProducts = catalog.filter(p => p.brand === 'WEBER');
        if (needsWaterproof) {
            relevantProducts = relevantProducts.filter(p => p.category?.toLowerCase().includes('impermeabilizantes') || p.model.toLowerCase().includes('imper') || p.model.toLowerCase().includes('membrana'));
        } else if (needsFloors) {
            relevantProducts = relevantProducts.filter(p => p.category?.toLowerCase().includes('pisos') || p.model.toLowerCase().includes('piso') || p.model.toLowerCase().includes('micro') || p.model.toLowerCase().includes('autonivela'));
        }
    } else {
        // Caso general: productos populares balanceados de ambas marcas
        const popularModels = ['Prima Tec Smart', 'Radiador Eléctrico Broen E', 'weber impermeable cerámicos con ceresita', 'weber gris cerámicos', 'weber flex porcellanato'];
        relevantProducts = catalog.filter(p =>
            popularModels.some(pm => p.model.toLowerCase() === pm.toLowerCase() || p.model.includes(pm))
        );
    }

    // Si no hay productos relevantes, tomar los primeros 5 del catálogo
    if (relevantProducts.length === 0) {
        relevantProducts = catalog.slice(0, 5);
    }

    // Limitar a 5 productos para no saturar el contexto
    return relevantProducts.slice(0, 5);
}

/* Llamar a la API del Backend Integrado (FastAPI) */
async function callOllama(userMessage) {
    const BACKEND_URL = '/api/chat';

    const bodyPayload = {
        message: userMessage,
        conversation_id: conversationId,
        last_active_brand: lastActiveBrand,
        last_active_product: lastActiveProduct
    };

    const response = await fetch(BACKEND_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(bodyPayload)
    });

    if (!response.ok) {
        throw new Error('Error en la API del Backend');
    }

    const data = await response.json();

    // Sincronizar contexto de marca y producto basado en la respuesta del chatbot
    if (data.mode && data.mode !== 'neutral') {
        const resolvedBrand = data.mode.toUpperCase();
        if (lastActiveBrand !== resolvedBrand) {
            lastActiveBrand = resolvedBrand;
            lastActiveProduct = null;
        }
        if (data.products && data.products.length > 0) {
            lastActiveProduct = data.products[0].model;
        }
    }

    // Si el backend nos responde en modo Weber
    if (data.mode === 'weber') {
        let assistantMessage = data.text;

        if (data.calculo) {
            assistantMessage += `<br><br><strong>📊 Cálculo Estimado de Obra:</strong><br>• Superficie: ${data.calculo.superficie_m2} m²<br>• Producto: ${data.calculo.producto}<br>• Cantidad Necesaria: <strong>${data.calculo.bolsas_necesarias} bolsas</strong> (Rendimiento: ${data.calculo.rendimiento_kg_m2} kg/m²)`;
        }

        return {
            message: assistantMessage,
            products: data.products || []
        };
    }

    // Flujo de respaldo para PEISA u otras marcas
    const assistantMessage = fixBranding(briefenResponse(data.text || data.message || ''));

    conversationHistory.push({
        role: 'assistant',
        content: assistantMessage
    });

    updateConversationContext();

    const mentionedProducts = detectMentionedProducts(assistantMessage);

    return {
        message: assistantMessage,
        products: data.products || mentionedProducts
    };
}

/* Asegurar brevedad razonable en el mensaje */
function briefenResponse(text) {
    if (!text) return '';

    // Unificar espacios y líneas
    let t = text.replace(/\s+/g, ' ').trim();

    // Permitir hasta 80 palabras para respuestas completas con productos
    const words = t.split(' ');
    const maxWords = 80;

    if (words.length > maxWords) {
        // Buscar hasta el 4to punto para permitir respuestas completas
        const sentences = t.split(/[.!?]+/).filter(s => s.trim().length > 0);

        if (sentences.length >= 2) {
            // Tomar las primeras 3-4 oraciones
            t = sentences.slice(0, 4).join('. ') + '.';
            // Si aún es muy largo, cortar en maxWords
            if (t.split(' ').length > maxWords) {
                t = t.split(' ').slice(0, maxWords).join(' ');
                if (!/[\.!?]$/.test(t)) t += '.';
            }
        } else {
            // Si no hay puntos, cortar en maxWords
            t = words.slice(0, maxWords).join(' ');
            if (!/[\.!?]$/.test(t)) t += '.';
        }
    } else {
        // Agregar punto final si no lo tiene
        if (!/[\.!?]$/.test(t)) t += '.';
    }

    return t;
}

/* Corregir branding: PEISA es marca; la empresa es Soldasur */
function fixBranding(text) {
    if (!text) return '';
    let t = text;
    // Cambios directos de frases típicas
    t = t.replace(/visita a\s+peisa/gi, 'visita a Soldasur');
    t = t.replace(/en\s+peisa\b/gi, 'en Soldasur');
    t = t.replace(/(sucursales?|local|tienda|showroom|empresa|oficina|contacto)s?\s+de\s+peisa/gi, '$1 de Soldasur');
    t = t.replace(/empresa\s+peisa/gi, 'empresa Soldasur');
    // Evitar tocar menciones válidas de productos/catálogo PEISA
    return t;
}

/* Detectar consultas de precio/costo */
function isPriceQuestion(text) {
    if (!text) return false;
    const t = text.toLowerCase();
    const keywords = [
        'precio', 'precios', 'costo', 'costos', 'presupuesto', 'cuesta', 'vale', 'sale',
        'descuento', 'promoción', 'promocion', 'oferta', 'cuotas', 'financiación', 'financiacion'
    ];
    const currencyRegex = /(ar\$|u\$s|us\$|usd|eur|€|\$)\s*\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d{2})?/i;
    return keywords.some(k => t.includes(k)) || currencyRegex.test(text);
}

/* Detectar consultas de refrigeración (fuera del catálogo) */
function isCoolingQuestion(text) {
    if (!text) return false;
    const t = text.toLowerCase();
    const coolingKeywords = [
        'aire acondicionado', 'aire', 'acondicionado', 'split', 'refrigeración', 'refrigeracion',
        'enfriar', 'refrescar', 'ventilador', 'climatizador', 'fresco', 'frío verano'
    ];
    // Excluir falsos positivos
    if (t.includes('agua caliente') || t.includes('calefacción') || t.includes('calefaccion')) {
        return false;
    }
    return coolingKeywords.some(k => t.includes(k));
}

/* Consultar por un producto sugerido (se llama desde productCatalog.js) */
function consultProduct(product) {
    try {
        selectedProductForConsult = product || null;
        waitingForCity = true;
        appendMessage('system', `¿Querés consultar por ${product?.model || 'este producto'}? Elegí tu ciudad:`);
        // Botones rápidos locales (no usan handleOptionClick)
        const chatContainer = document.getElementById('chat-container');
        const div = document.createElement('div');
        div.className = 'fade-in mt-2 flex gap-2';
        const btnRG = document.createElement('button');
        btnRG.className = 'text-xs px-3 py-1 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded';
        btnRG.textContent = 'Río Grande';
        btnRG.onclick = () => { showContactInfo('riogrande'); waitingForCity = false; showChatInput(); };
        const btnUsh = document.createElement('button');
        btnUsh.className = 'text-xs px-3 py-1 bg-green-100 hover:bg-green-200 text-green-800 rounded';
        btnUsh.textContent = 'Ushuaia';
        btnUsh.onclick = () => { showContactInfo('ushuaia'); waitingForCity = false; showChatInput(); };
        div.appendChild(btnRG); div.appendChild(btnUsh);
        chatContainer.appendChild(div);
        scrollToBottom();
    } catch (e) {
        console.error('Error iniciando consulta de producto', e);
    }
}

/* Actualizar contexto de conversación con más detalle */
function updateConversationContext() {
    const catalogToUse = productCatalog;

    // Extraer información clave de la conversación
    const userNeeds = [];
    const userSituation = [];
    const mentionedProducts = new Set();
    const topics = [];

    conversationHistory.forEach(msg => {
        if (msg.role === 'user') {
            const content = msg.content.toLowerCase();

            // Necesidades del usuario
            if (content.includes('frío') || content.includes('frio')) userNeeds.push('tiene frío');
            if (content.includes('calefacción') || content.includes('calefaccion')) userNeeds.push('necesita calefacción');
            if (content.includes('agua caliente')) userNeeds.push('necesita agua caliente');

            // Situación del usuario
            if (content.includes('casa grande') || content.includes('casa')) userSituation.push('casa grande');
            if (content.includes('familia')) userSituation.push('vive con familia');
            if (content.includes('departamento') || content.includes('depto')) userSituation.push('departamento');
            if (content.includes('chico') || content.includes('pequeño')) userSituation.push('espacio pequeño');
            if (content.includes('oficina')) userSituation.push('oficina');

            // Temas específicos
            if (content.includes('caldera')) topics.push('calderas');
            if (content.includes('radiador')) topics.push('radiadores');
            if (content.includes('eléctrico') || content.includes('electrico')) topics.push('productos eléctricos');
            if (content.includes('m²') || content.includes('metros')) topics.push('dimensiones');
        } else if (msg.role === 'assistant') {
            // Productos ya recomendados
            catalogToUse.forEach(product => {
                if (msg.content.toLowerCase().includes(product.model.toLowerCase())) {
                    mentionedProducts.add(product.model);
                }
            });
        }
    });

    // Construir resumen contextual rico
    let contextSummary = '';

    if (userNeeds.length > 0) {
        contextSummary += `Usuario: ${[...new Set(userNeeds)].join(', ')}. `;
    }

    if (userSituation.length > 0) {
        contextSummary += `Situación: ${[...new Set(userSituation)].join(', ')}. `;
    }

    if (mentionedProducts.size > 0) {
        contextSummary += `Productos ya recomendados: ${[...mentionedProducts].join(', ')}. `;
    }

    if (topics.length > 0) {
        contextSummary += `Temas: ${[...new Set(topics)].join(', ')}.`;
    }

    conversationContext = contextSummary;
    console.log('🧠 Contexto actualizado:', contextSummary);
}

/* Detectar productos mencionados en la respuesta */
function detectMentionedProducts(message) {
    // Usar el catálogo JSON actualizado
    const catalogToUse = productCatalog;

    const mentioned = [];
    const messageLower = message.toLowerCase();

    // Solo detectar si el mensaje contiene "te recomiendo" o "recomiendo"
    // Esto evita mostrar tarjetas en respuestas que no son recomendaciones
    const isRecommendation = messageLower.includes('te recomiendo') ||
        messageLower.includes('recomiendo') ||
        messageLower.includes('te sugiero') ||
        messageLower.includes('sugiero');

    if (!isRecommendation) {
        return []; // No mostrar tarjetas si no es una recomendación
    }

    // Ordenar productos por longitud de nombre (más largos primero)
    // Esto evita que "Broen" se detecte cuando en realidad es "Radiador Eléctrico Broen E"
    const sortedProducts = [...catalogToUse].sort((a, b) => b.model.length - a.model.length);

    for (const product of sortedProducts) {
        const modelLower = product.model.toLowerCase();
        if (messageLower.includes(modelLower)) {
            // Verificar que no sea un subproducto ya detectado
            const isSubstring = mentioned.some(m =>
                m.model.toLowerCase().includes(modelLower) ||
                modelLower.includes(m.model.toLowerCase())
            );

            if (!isSubstring) {
                mentioned.push(product);
            }
        }
    }

    // NO mostrar productos por categoría genérica - solo productos específicos mencionados
    return mentioned.slice(0, 3); // Limitar a 3 productos máximo
}

/* Limpiar HTML crudo del mensaje para humanizarlo */
function cleanHtmlFromMessage(message) {
    if (!message) return '';

    // Eliminar tags HTML crudos que puedan aparecer en el texto
    let cleaned = message;

    // Eliminar atributos HTML visibles (target="_blank", class="...", etc.)
    cleaned = cleaned.replace(/\s*(target|class|title|style)\s*=\s*["'][^"']*["']/gi, '');

    // Eliminar tags <a> pero mantener el texto
    cleaned = cleaned.replace(/<a[^>]*>/gi, '');
    cleaned = cleaned.replace(/<\/a>/gi, '');

    // Eliminar otros tags HTML comunes (excepto <strong> y <b>)
    cleaned = cleaned.replace(/<(?!\/?(?:strong|b)\b)[^>]+>/g, '');

    // Limpiar espacios múltiples
    cleaned = cleaned.replace(/\s+/g, ' ').trim();

    // Resaltar nombres de productos en negrita
    if (productCatalog && productCatalog.length > 0) {
        // Ordenar productos por longitud de nombre (más largos primero para evitar reemplazos parciales)
        const sortedProducts = [...productCatalog].sort((a, b) => b.model.length - a.model.length);
        const replacedProducts = new Set();

        for (const product of sortedProducts) {
            if (!product.model || replacedProducts.has(product.model)) continue;

            // Crear regex que busque el nombre del producto (case insensitive)
            // pero que no esté ya dentro de un tag <strong>
            const regex = new RegExp(`(?<!<strong>)\\b(${escapeRegex(product.model)})\\b(?![^<]*<\\/strong>)`, 'gi');

            // Reemplazar solo si encuentra coincidencias
            const newCleaned = cleaned.replace(regex, '<strong>$1</strong>');
            if (newCleaned !== cleaned) {
                cleaned = newCleaned;
                replacedProducts.add(product.model);
            }
        }
    }

    return cleaned;
}

/* Escapar caracteres especiales de regex */
function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/* Enriquecer mensaje con enlaces a productos mencionados */
function enrichMessageWithLinks(message) {
    if (!productCatalog || productCatalog.length === 0) {
        return message;
    }

    let enrichedMessage = message;
    const replacedProducts = new Set();

    // Ordenar productos por longitud de nombre (más largos primero)
    const sortedProducts = [...productCatalog].sort((a, b) => b.model.length - a.model.length);

    // Buscar productos mencionados y reemplazar con enlaces
    for (const product of sortedProducts) {
        // Escapar caracteres especiales para regex
        const escapedModel = product.model.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`\\b(${escapedModel})\\b`, 'gi');

        if (regex.test(enrichedMessage) && !replacedProducts.has(product.model.toLowerCase())) {
            // Crear enlace limpio sin atributos extra que puedan mostrarse
            enrichedMessage = enrichedMessage.replace(regex,
                `<a href="${product.url}" target="_blank" style="color: #2563eb; text-decoration: underline;">$1</a>`
            );
            replacedProducts.add(product.model.toLowerCase());
        }
    }

    return enrichedMessage;
}

/* Renderizar tarjetas de productos recomendados */
function renderProducts(products) {
    if (!products || products.length === 0) return;

    const chatContainer = document.getElementById('chat-container');

    products.forEach(product => {
        const productCard = document.createElement('div');
        productCard.className = 'product-card fade-in';
        productCard.style.cssText = `
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin: 8px 0;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            justify-content: space-between;
            align-items: stretch;
            overflow: hidden;
            min-height: 96px;
        `;
        const hasUrl = product.url && product.url !== '#';
        const brandLabel = product.brand ? (product.brand === 'WEBER' ? 'Weber' : product.brand) : 'PEISA';
        
        // Determinar miniatura
        const brandUpper = brandLabel.toUpperCase();
        let imgUrl = '/img/peisa-logo.png';
        if (brandUpper === 'WEBER') {
            imgUrl = product.imagen_local ? `/scraping/${product.imagen_local.replace(/\\/g, '/')}` : '/img/weber-logo.png';
        } else if (product.imagen_local) {
            imgUrl = `/scraping/${product.imagen_local.replace(/\\/g, '/')}`;
        } else if (product.imagen_url) {
            imgUrl = product.imagen_url;
        } else {
            imgUrl = `/img/${brandUpper.toLowerCase()}-logo.png`;
        }

        productCard.innerHTML = `
            <div style="flex:1; padding:12px; display:flex; flex-direction:column; justify-content:space-between; gap:8px;">
                <div>
                    <div style="font-weight: 600; color: #1e40af; margin-bottom: 6px; font-size:14px; line-height:1.3;">
                        ${product.model}
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <span style="font-size: 11px; background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 4px;">
                            ${product.category || product.family || 'Producto'}
                        </span>
                    </div>
                </div>
                <div style="display:flex; gap:6px; flex-wrap:wrap;">
                    ${hasUrl ? `<a href="${product.url}" target="_blank"
                        class="card-btn card-btn-primary"
                        onclick="event.stopPropagation();">
                        Ver en ${brandLabel}
                    </a>` : ''}
                    <button class="card-btn card-btn-secondary"
                        onclick="(function(e){e.stopPropagation(); consultFromProduct('${product.model.replace(/'/g, "\\'")}');})(event)">
                        Consultar
                    </button>
                </div>
            </div>
            <div style="width:80px; flex-shrink:0; background:white; border-left:1px solid #f3f4f6; display:flex; align-items:center; justify-content:center; padding:4px;" onclick="event.stopPropagation(); window.open('${product.url}', '_blank');">
                <img src="${imgUrl}" alt="${product.model}" style="height:86px; width:auto; max-width:72px; object-fit:contain;" onerror="this.src='/img/logo.webp'" />
            </div>
        `;

        // Hover effect
        productCard.onmouseenter = () => {
            productCard.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
            productCard.style.borderColor = '#2563eb';
        };
        productCard.onmouseleave = () => {
            productCard.style.boxShadow = 'none';
            productCard.style.borderColor = '#e5e7eb';
        };

        // Click para abrir enlace
        productCard.onclick = () => {
            window.open(product.url, '_blank');
        };

        chatContainer.appendChild(productCard);
    });

    scrollToBottom();
}

/* Indicadores de carga */
function showLoadingIndicator() {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) chatInput.disabled = true;
    const chatSendBtn = document.getElementById('chat-send-btn');
    if (chatSendBtn) chatSendBtn.disabled = true;

    const chatContainer = document.getElementById('chat-container');
    const thinkingDiv = document.createElement('div');
    thinkingDiv.id = 'thinking-indicator';
    thinkingDiv.className = 'chat-message system-message rounded-lg p-3 fade-in';
    thinkingDiv.innerHTML = `
        <div class="flex items-center gap-2">
            <div class="loading-spinner inline-block"></div>
            <span class="thinking-text">Soldy está pensando</span>
        </div>
    `;
    chatContainer.appendChild(thinkingDiv);
    scrollToBottom();

    let dots = 0;
    window.thinkingInterval = setInterval(() => {
        dots = (dots + 1) % 4;
        const thinkingText = document.querySelector('.thinking-text');
        if (thinkingText) {
            thinkingText.textContent = 'Soldy está pensando' + '.'.repeat(dots);
        }
    }, 500);
}

function hideLoadingIndicator() {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) chatInput.disabled = false;
    const chatSendBtn = document.getElementById('chat-send-btn');
    if (chatSendBtn) chatSendBtn.disabled = false;

    if (window.thinkingInterval) {
        clearInterval(window.thinkingInterval);
        window.thinkingInterval = null;
    }

    const thinkingIndicator = document.getElementById('thinking-indicator');
    if (thinkingIndicator) {
        thinkingIndicator.remove();
    }
}
