/* ==========================================================================
   CORE.JS — Módulo central compartido
   Contiene: estado global, helpers de UI, navegación, catálogo, sucursales.
   Usado por: peisa_expert.js, weber_expert.js, chatbot.js, soldasur.js
   ========================================================================== */

/* ── Estado Global ─────────────────────────────────────────────────────── */
let conversationId   = 'user_' + Math.random().toString(36).substr(2, 9);
let lastUserResponse = null;
let isLoading        = false;
let currentMode      = 'hybrid';
let inMainMenu       = true;
let chatIsOpen       = false;
let isMaximized      = false;
let conversationStep = 0; // Estado compartido del cuestionario/routing

/* ── Catálogo de productos (cargado al inicio) ─────────────────────────── */
let productCatalog       = [];   // catálogo completo (usado en la navegación por categorías)
let peisaProductsFromJSON = [];  // alias que usa chatbot.js
let peisaCatalog = [];
let weberCatalog = [];
let browsingBrand = null; // 'PEISA' o 'WEBER'

/* ── Toggle del chat flotante ──────────────────────────────────────────── */
function toggleMaximize() {
    const chatWidget    = document.getElementById('chat-widget');
    const maximizeIcon  = document.getElementById('maximize-icon');
    const minimizeIcon  = document.getElementById('minimize-icon');
    const maximizeButton = document.getElementById('maximize-button');

    isMaximized = !isMaximized;

    if (isMaximized) {
        chatWidget.classList.add('maximized');
        maximizeIcon.classList.add('hidden');
        minimizeIcon.classList.remove('hidden');
        maximizeButton.title = 'Restaurar';
    } else {
        chatWidget.classList.remove('maximized');
        maximizeIcon.classList.remove('hidden');
        minimizeIcon.classList.add('hidden');
        maximizeButton.title = 'Maximizar';
    }
}

function toggleChat() {
    const chatWidget    = document.getElementById('chat-widget');
    const chatButton    = document.getElementById('chat-toggle-btn');
    const soldyMessage  = document.getElementById('soldy-message');
    const soldyChatImage = document.getElementById('soldy-chat-image');

    chatIsOpen = !chatIsOpen;

    if (chatIsOpen) {
        chatWidget.classList.add('active');
        chatButton.style.display = 'none';
        if (soldyChatImage) soldyChatImage.style.display = 'block';
        if (soldyMessage)   soldyMessage.classList.add('hidden');
        if (document.getElementById('chat-container').children.length === 0) {
            startConversation();
        }
    } else {
        chatWidget.classList.remove('active');
        chatButton.style.display = 'block';
        if (soldyChatImage) soldyChatImage.style.display = 'none';
        if (soldyMessage)   soldyMessage.classList.remove('hidden');
    }
}

/* ── Navegación ────────────────────────────────────────────────────────── */
function showBackButton() {
    document.getElementById('back-button').classList.remove('hidden');
    inMainMenu = false;
}

function hideBackButton() {
    document.getElementById('back-button').classList.add('hidden');
    inMainMenu = true;
}

function goBack() {
    resetExpertSystem();
    browsingBrand = null;
    document.getElementById('chat-container').innerHTML = '';
    startConversation();
    hideBackButton();
}

function switchMode(mode) {
    currentMode = mode;
    browsingBrand = null;
    conversationId = 'user_' + Math.random().toString(36).substr(2, 9);
    document.getElementById('chat-container').innerHTML = '';
    lastUserResponse = null;
    resetExpertSystem();
    if (typeof resetChatHistory === 'function') resetChatHistory();
    startConversation();
    hideBackButton();
}

/* ── Helpers de mensajería ─────────────────────────────────────────────── */
function appendMessage(sender, text) {
    const chatContainer = document.getElementById('chat-container');
    const div = document.createElement('div');
    div.className = `chat-message rounded-lg p-3 ${sender === 'system' ? 'system-message' : 'user-message'} fade-in`;
    div.innerHTML = text;
    chatContainer.appendChild(div);
    scrollToBottom();
}

function scrollToBottom() {
    const container = document.getElementById('chat-container');
    container.scrollTop = container.scrollHeight;
}

function formatResponseText(text) {
    return text ? text.replace(/\n/g, '<br>').replace(/<br>- /g, '<br>• ') : '';
}

/* ── Renderizado de opciones ───────────────────────────────────────────── */
function renderOptions(options, isResponse = false) {
    const inputArea = document.getElementById('input-area');
    inputArea.innerHTML = '';
    const container = document.createElement('div');
    container.className = 'space-y-2';

    options.forEach(option => {
        const btn = document.createElement('button');
        btn.className = `option-btn w-full ${isResponse
            ? 'bg-green-100 hover:bg-green-200 text-green-800'
            : 'bg-blue-100 hover:bg-blue-200 text-blue-800'} py-2 px-4 rounded-lg`;
        btn.innerHTML = option;
        btn.onclick = () => handleOptionClick(option);
        container.appendChild(btn);
    });

    inputArea.appendChild(container);
}

/* ── Inputs numéricos (usados por ambos sistemas expertos) ─────────────── */
function createNumberInput(config) {
    const inputArea = document.getElementById('input-area');
    inputArea.innerHTML = '';
    const form = document.createElement('form');
    const tipo = typeof userInputs !== 'undefined' ? userInputs.tipo : null;

    form.onsubmit = (e) => {
        e.preventDefault();
        const value = document.getElementById('input-value').value;
        if (value && parseFloat(value) > 0) {
            if (config.onSubmit) {
                config.onSubmit(value);
            } else if (tipo === 'Piso radiante') {
                userInputs.superficie = value;
                appendMessage('user', value + ' m²');
                setTimeout(() => askQuestion(), 500);
            } else if (tipo === 'Calderas') {
                userInputs.carga_termica_total = value;
                appendMessage('user', value + ' kcal/h');
                setTimeout(() => askQuestion(), 500);
            }
        }
    };

    form.innerHTML = `
        <div class="flex flex-col space-y-2">
            <input type="number" id="input-value" required step="0.1"
                class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
                placeholder="${config.input_label || 'Ej: 50'}">
            <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm font-semibold">
                Enviar
            </button>
        </div>
    `;
    inputArea.appendChild(form);
    document.getElementById('input-value').focus();
}

function createDimensionsInput() {
    const inputArea = document.getElementById('input-area');
    inputArea.innerHTML = '';
    const form = document.createElement('form');

    form.onsubmit = (e) => {
        e.preventDefault();
        const largo = parseFloat(document.getElementById('input-largo').value);
        const ancho = parseFloat(document.getElementById('input-ancho').value);
        const alto  = parseFloat(document.getElementById('input-alto').value);
        if (largo > 0 && ancho > 0 && alto > 0) {
            userInputs.largo = largo;
            userInputs.ancho = ancho;
            userInputs.alto  = alto;
            appendMessage('user', `${largo}m x ${ancho}m x ${alto}m`);
            setTimeout(() => askQuestion(), 500);
        }
    };

    form.innerHTML = `
        <div class="flex flex-col space-y-2">
            <div class="grid grid-cols-3 gap-2">
                <input type="number" id="input-largo" required step="0.1" min="0.1"
                    class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" placeholder="Largo (m)">
                <input type="number" id="input-ancho" required step="0.1" min="0.1"
                    class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" placeholder="Ancho (m)">
                <input type="number" id="input-alto" required step="0.1" min="0.1"
                    class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" placeholder="Alto (m)">
            </div>
            <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition text-sm font-semibold">
                Enviar
            </button>
        </div>
    `;
    inputArea.appendChild(form);
    document.getElementById('input-largo').focus();
}

function createRestartButton() {
    const inputArea = document.getElementById('input-area');
    const btn = document.createElement('button');
    btn.className = 'w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition text-sm font-semibold';
    btn.textContent = 'Iniciar nuevo cálculo';
    btn.onclick = () => { if (!isLoading) switchMode(currentMode); };
    inputArea.appendChild(btn);
}

/* ── Renderizado de tarjetas de productos ─────────────────────────────── */
function renderProducts(products) {
    if (!products || products.length === 0) return;
    const chatContainer = document.getElementById('chat-container');

    products.forEach(product => {
        const card = document.createElement('div');
        card.className = 'product-card fade-in';
        card.style.cssText = `
            background: white; border: 1px solid #e5e7eb; border-radius: 8px;
            padding: 12px; margin: 8px 0; cursor: pointer; transition: all 0.2s;
        `;
        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="flex:1;">
                    <div style="font-weight:600; color:#1e40af; margin-bottom:6px;">${product.model}</div>
                    <div style="display:flex; gap:8px;">
                        <span style="font-size:11px; background:#dbeafe; color:#1e40af; padding:2px 8px; border-radius:4px;">
                            ${product.family || product.category || 'Producto'}
                        </span>
                    </div>
                </div>
                <div style="display:flex; align-items:center; gap:8px; margin-left:12px;">
                    <button class="consult-btn"
                        style="background:#2563eb;color:white;border:none;padding:6px 10px;border-radius:6px;font-size:13px;cursor:pointer;"
                        onclick="(function(e){e.stopPropagation(); consultFromProduct('${product.model.replace(/'/g, "\\'")}');})(event)">
                        Consultar
                    </button>
                    <a href="${product.url}" target="_blank"
                        style="color:#2563eb; text-decoration:none; font-size:14px; padding-left:6px;">Ver</a>
                </div>
            </div>
        `;
        card.onmouseenter = () => { card.style.boxShadow = '0 4px 6px -1px rgba(0,0,0,0.1)'; card.style.borderColor = '#2563eb'; };
        card.onmouseleave = () => { card.style.boxShadow = 'none'; card.style.borderColor = '#e5e7eb'; };
        card.onclick = () => { window.open(product.url, '_blank'); };
        chatContainer.appendChild(card);
    });

    scrollToBottom();
}

function updateModeIndicator(mode, label) {
    const indicator = document.getElementById('mode-indicator');
    if (!indicator) return;
    indicator.textContent = label;
    indicator.className = 'mode-indicator';
    if (mode === 'expert')       indicator.classList.add('mode-expert');
    else if (mode === 'rag')     indicator.classList.add('mode-rag');
    else                         indicator.classList.add('mode-hybrid');
}

/* ── Carga del catálogo ────────────────────────────────────────────────── */

async function loadProductCatalog() {
    try {
        const responsePeisa = await fetch('data/products_catalog.json');
        if (responsePeisa.ok) {
            peisaCatalog = await responsePeisa.json();
            peisaCatalog.forEach(p => { p.brand = 'PEISA'; });
            peisaProductsFromJSON = peisaCatalog;   // alias para chatbot.js
        }

        const responseWeber = await fetch('data/weber_catalog.json');
        if (responseWeber.ok) {
            weberCatalog = await responseWeber.json();
            weberCatalog.forEach(p => { 
                p.brand = 'WEBER'; 
                p.family = 'Weber'; 
            });
        }

        productCatalog = [...peisaCatalog, ...weberCatalog];
        console.log(`✅ Catálogos cargados: ${peisaCatalog.length} PEISA, ${weberCatalog.length} WEBER`);
    } catch (error) {
        console.error('❌ Error cargando catálogos:', error);
        productCatalog = [];
        peisaProductsFromJSON = [];
    }
}

loadProductCatalog();

/* ── Catálogo navegable por categorías ────────────────────────────────── */
function showBrandMenu() {
    appendMessage('system', '<strong>Seleccioná una marca de productos:</strong>');
    const options = [
        '<img src="images/peisa-logo.png" class="h-8 mx-auto py-1" alt="PEISA">',
        '<img src="images/weber-logo.png" class="h-8 mx-auto py-1" alt="WEBER">'
    ];
    renderOptions(options, false);
}

function showCategoryMenu() {
    if (!browsingBrand) {
        showBrandMenu();
        return;
    }

    appendMessage('system', `<strong>${browsingBrand}</strong> — Seleccioná una categoría de productos:`);
    
    let categories = [];
    if (browsingBrand === 'PEISA') {
        categories = [...new Set(peisaCatalog.map(p => p.family))].filter(Boolean);
    } else if (browsingBrand === 'WEBER') {
        categories = [...new Set(weberCatalog.map(p => p.category))].filter(Boolean);
    }

    if (categories.length === 0) {
        appendMessage('system', 'No se pudieron cargar las categorías. Por favor, intentá más tarde.');
        return;
    }
    
    categories.push('Ver todas las marcas');
    renderOptions(categories, false);
}

function showProductsByCategory(category) {
    appendMessage('user', `Ver productos de: ${category}`);
    
    let products = [];
    if (browsingBrand === 'PEISA') {
        products = peisaCatalog.filter(p => p.family === category);
    } else if (browsingBrand === 'WEBER') {
        products = weberCatalog.filter(p => p.category === category);
    }

    if (products.length === 0) {
        appendMessage('system', `No se encontraron productos en la categoría ${category}.`);
        renderOptions(['Ver otras categorías'], false);
        return;
    }
    appendMessage('system', `<strong>${category}</strong> — ${products.length} producto${products.length > 1 ? 's' : ''} disponible${products.length > 1 ? 's' : ''}:`);
    const chatContainer  = document.getElementById('chat-container');
    const productsGrid   = document.createElement('div');
    productsGrid.className = 'products-grid fade-in';
    productsGrid.style.cssText = 'display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:12px; margin:12px 0;';

    products.forEach(product => {
        const card = document.createElement('div');
        card.style.cssText = 'background:white; border:1px solid #e5e7eb; border-radius:8px; padding:12px; transition:all 0.2s;';
        card.onmouseover = () => card.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
        card.onmouseout  = () => card.style.boxShadow = 'none';
        const hasUrl = product.url && product.url !== '#';
        const brandLabel = product.brand || 'PEISA';
        card.innerHTML = `
            <div style="font-weight:600; color:#1f2937; margin-bottom:6px; font-size:14px;">${product.model || 'Producto'}</div>
            <div style="color:#6b7280; font-size:12px; margin-bottom:8px; line-height:1.4;">
                ${product.description ? product.description.substring(0, 100) + (product.description.length > 100 ? '...' : '') : 'Sin descripción'}
            </div>
            ${product.type ? `<div style="font-size:11px; color:#9ca3af; margin-bottom:8px;">Tipo: ${product.type}</div>` : ''}
            <div style="display:flex; gap:6px; flex-wrap:wrap;">
                ${hasUrl ? `<a href="${product.url}" target="_blank"
                    style="display:inline-block; background:#3b82f6; color:white; padding:6px 12px; border-radius:6px; text-decoration:none; font-size:12px;">
                    Ver en ${brandLabel}
                </a>` : ''}
                <button onclick="consultFromProduct('${product.model.replace(/'/g, "\\'")}')"
                    style="background:#10b981; color:white; padding:6px 12px; border:none; border-radius:6px; cursor:pointer; font-size:12px;">
                    Consultar
                </button>
            </div>
        `;
        productsGrid.appendChild(card);
    });

    chatContainer.appendChild(productsGrid);
    scrollToBottom();
    renderOptions(['Ver otras categorías', 'Volver al inicio'], false);
}

function showAllProducts() {
    appendMessage('user', 'Ver todos los productos');
    if (productCatalog.length === 0) {
        appendMessage('system', 'No se pudieron cargar los productos. Por favor, intentá más tarde.');
        return;
    }
    
    let productsToDisplay = [];
    if (browsingBrand === 'PEISA') {
        productsToDisplay = peisaCatalog;
    } else if (browsingBrand === 'WEBER') {
        productsToDisplay = weberCatalog;
    } else {
        productsToDisplay = productCatalog;
    }

    appendMessage('system', `<strong>Catálogo completo (${browsingBrand || 'Todas las marcas'})</strong> — ${productsToDisplay.length} productos disponibles:`);
    const byCategory = {};
    productsToDisplay.forEach(p => {
        const cat = browsingBrand === 'WEBER' ? (p.category || 'Otros') : (p.family || 'Otros');
        if (!byCategory[cat]) byCategory[cat] = [];
        byCategory[cat].push(p);
    });
    const chatContainer = document.getElementById('chat-container');
    Object.keys(byCategory).sort().forEach(category => {
        const products = byCategory[category];
        appendMessage('system', `<strong>${category}</strong> (${products.length}):`);
        const grid = document.createElement('div');
        grid.style.cssText = 'display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:12px; margin:12px 0;';
        products.slice(0, 6).forEach(product => {
            const card = document.createElement('div');
            card.style.cssText = 'background:white; border:1px solid #e5e7eb; border-radius:8px; padding:12px;';
            const hasUrl = product.url && product.url !== '#';
            const brandLabel = product.brand || 'PEISA';
            card.innerHTML = `
                <div style="font-weight:600; color:#1f2937; margin-bottom:6px; font-size:14px;">${product.model || 'Producto'}</div>
                <div style="color:#6b7280; font-size:12px; margin-bottom:8px;">
                    ${product.description ? product.description.substring(0, 80) + '...' : ''}
                </div>
                <div style="display:flex; gap:6px;">
                    ${hasUrl ? `<a href="${product.url}" target="_blank" style="display:inline-block; background:#3b82f6; color:white; padding:6px 12px; border-radius:6px; text-decoration:none; font-size:12px;">Ver en ${brandLabel}</a>` : ''}
                    <button onclick="consultFromProduct('${product.model.replace(/'/g, "\\'")}')"
                        style="background:#10b981; color:white; padding:6px 12px; border:none; border-radius:6px; cursor:pointer; font-size:12px;">
                        Consultar
                    </button>
                </div>
            `;
            grid.appendChild(card);
        });
        chatContainer.appendChild(grid);
    });
    scrollToBottom();
    renderOptions(['Ver por categoría', 'Volver al inicio'], false);
}

/* ── Consulta de sucursal ─────────────────────────────────────────────── */
const SUCURSALES = {
    rio_grande: {
        name:    'Sucursal Río Grande — Soldasur',
        address: 'Islas Malvinas 1950, V9421 Río Grande, Tierra del Fuego',
        phone:   '+54 2964 40-1201',
        email:   'ventasrg@soldasur.com.ar',
        mapsUrl: 'https://www.google.com/maps/search/?api=1&query=Islas+Malvinas+1950,+V9421+Río+Grande,+Tierra+del+Fuego'
    },
    ushuaia: {
        name:    'Sucursal Ushuaia — Soldasur',
        address: 'Héroes de Malvinas 4180, V9410 Ushuaia, Tierra del Fuego',
        phone:   '+54 2901 43-6392',
        email:   'ventasush@soldasur.com.ar',
        mapsUrl: 'https://www.google.com/maps/search/?api=1&query=Héroes+de+Malvinas+4180,+V9410+Ushuaia,+Tierra+del+Fuego'
    }
};

function consultSucursal(city = null, showOnPage = true) {
    const sel = document.getElementById('city-select');
    const res = document.getElementById('sucursal-result');

    if (showOnPage && !city) {
        if (!chatIsOpen) toggleChat();
        const optionsHtml = `
            <div style="display:flex;gap:8px;margin-top:8px;">
                <button style="background:#2563eb;color:white;border:none;padding:4px 12px;border-radius:6px;cursor:pointer;"
                    onclick="consultSucursalFromChat('rio_grande')">Río Grande</button>
                <button style="background:#16a34a;color:white;border:none;padding:4px 12px;border-radius:6px;cursor:pointer;"
                    onclick="consultSucursalFromChat('ushuaia')">Ushuaia</button>
            </div>`;
        appendMessage('system', `¿Estás en Río Grande o Ushuaia?${optionsHtml}`);
        scrollToBottom();
        return;
    }

    const selectedCity = city || (sel ? sel.value : null);
    const c = SUCURSALES[selectedCity];
    if (!c) { if (res) res.innerHTML = ''; return; }

    if (showOnPage && res) {
        res.innerHTML = `
            <div class="p-3 bg-blue-50 rounded">
                <div class="font-semibold">${c.name}</div>
                <div class="text-sm text-gray-700">${c.address}</div>
                <div class="text-sm">Tel: <a href="tel:${c.phone.replace(/\s+/g,'')}" class="text-blue-600">${c.phone}</a></div>
                <div class="text-sm">Email: <a href="mailto:${c.email}" class="text-blue-600">${c.email}</a></div>
            </div>`;
    }

    const chatHtml = `
        <div class="sucursal-card">
            <strong>${c.name}</strong><br>
            ${c.address}<br>
            Tel: <a href="tel:${c.phone.replace(/\s+/g,'')}" class="text-blue-600">${c.phone}</a><br>
            Email: <a href="mailto:${c.email}" class="text-blue-600">${c.email}</a>
            <div style="margin-top:8px;display:flex;gap:8px;">
                <a href="tel:${c.phone.replace(/\s+/g,'')}" class="inline-block bg-blue-600 text-white px-3 py-1 rounded text-sm">Llamar</a>
                <a href="mailto:${c.email}" class="inline-block bg-gray-200 text-gray-800 px-3 py-1 rounded text-sm">Email</a>
                <a href="${c.mapsUrl}" target="_blank" class="inline-block bg-green-600 text-white px-3 py-1 rounded text-sm">Ver sucursal</a>
            </div>
        </div>`;
    appendMessage('system', chatHtml);
    scrollToBottom();
}

function consultSucursalFromChat(city) {
    appendMessage('user', `Seleccioné: <strong>${city === 'rio_grande' ? 'Río Grande' : 'Ushuaia'}</strong>`);
    consultSucursal(city, false);
}

function consultFromProduct(productModel) {
    if (!chatIsOpen) toggleChat();
    appendMessage('user', `Estoy interesado en: <strong>${productModel}</strong>`);
    const optionsHtml = `
        <div style="display:flex;gap:8px;margin-top:8px;">
            <button style="background:#2563eb;color:white;border:none;padding:4px 12px;border-radius:6px;cursor:pointer;"
                onclick="consultSucursalFromChat('rio_grande')">Río Grande</button>
            <button style="background:#16a34a;color:white;border:none;padding:4px 12px;border-radius:6px;cursor:pointer;"
                onclick="consultSucursalFromChat('ushuaia')">Ushuaia</button>
        </div>`;
    appendMessage('system', `¿Estás en Río Grande o Ushuaia?${optionsHtml}`);
    scrollToBottom();
}

/* ── Panel de contexto (PEISA expert) ─────────────────────────────────── */
function updateContextPanel() {
    const panel          = document.getElementById('context-panel');
    const itemsContainer = document.getElementById('context-items');
    if (!panel || !itemsContainer) return;
    
    // Ocultado en v4.1.0 para maximizar el espacio útil del chat
    panel.classList.add('hidden');
    return;
    itemsContainer.innerHTML = '';
    for (const [key, value] of Object.entries(contextData)) {
        if (!key.includes('_texto') && typeof value !== 'object') {
            const item = document.createElement('div');
            item.className = 'context-item';
            item.innerHTML = `<span class="font-medium">${key}:</span><span>${value}</span>`;
            itemsContainer.appendChild(item);
        }
    }
}
