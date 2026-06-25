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
let lastActiveBrand   = null;   // 'PEISA' o 'WEBER'
let lastActiveProduct = null;  // Nombre del producto recomendado en esta sesión (ej: 'weberplast llaneado')

/* ── Catálogo de productos (cargado al inicio) ─────────────────────────── */
let productCatalog       = [];   // catálogo completo (usado en la navegación por categorías)
let peisaProductsFromJSON = [];  // alias que usa chatbot.js
let peisaCatalog = [];
let weberCatalog = [];
let browsingBrand = null; // 'PEISA' o 'WEBER'

// Registro dinámico v5.0.1
let registeredBrands = {};
let brandCatalogs = {};
let activeExpert = null;

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

function resetExpertSystem() {
    conversationStep = 0;
    activeExpert = null;
    lastActiveBrand = null;
    lastActiveProduct = null;
    
    if (typeof resetPeisaExpert === 'function') resetPeisaExpert();
    if (typeof resetWeberExpert === 'function') resetWeberExpert();
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
            margin: 8px 0; cursor: pointer; transition: all 0.2s;
            display: flex; justify-content: space-between; align-items: stretch;
            overflow: hidden; min-height: 96px;
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

        card.innerHTML = `
            <div style="flex:1; padding:12px; display:flex; flex-direction:column; justify-content:space-between; gap:8px;">
                <div>
                    <div style="font-weight:600; color:#1e40af; margin-bottom:6px; font-size:14px; line-height:1.3;">${product.model}</div>
                    <div style="display:flex; gap:8px;">
                        <span style="font-size:11px; background:#dbeafe; color:#1e40af; padding:2px 8px; border-radius:4px;">
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
        card.onmouseenter = () => { card.style.boxShadow = '0 4px 6px -1px rgba(0,0,0,0.1)'; card.style.borderColor = '#2563eb'; };
        card.onmouseleave = () => { card.style.boxShadow = 'none'; card.style.borderColor = '#e5e7eb'; };
        card.onclick = () => { window.open(product.url, '_blank'); };
        chatContainer.appendChild(card);
    });

    scrollToBottom();
}

/* ── Carga del catálogo ────────────────────────────────────────────────── */

async function loadProductCatalog() {
    try {
        const responseBrands = await fetch('/api/brands');
        if (!responseBrands.ok) throw new Error('Error cargando marcas');
        const brandsData = await responseBrands.json();
        registeredBrands = brandsData.brands || brandsData;

        productCatalog = [];
        peisaCatalog = [];
        weberCatalog = [];
        brandCatalogs = {};

        for (const brandKey in registeredBrands) {
            const b = registeredBrands[brandKey];
            try {
                const responseCatalog = await fetch(`/api/brands/${b.key}/catalog`);
                if (responseCatalog.ok) {
                    const catalog = await responseCatalog.json();
                    catalog.forEach(p => {
                        p.brand = b.key;
                        if (!p.category && p.family) p.category = p.family;
                        if (!p.family && p.category) p.family = p.category;
                    });
                    brandCatalogs[b.key] = catalog;
                    if (b.key === 'PEISA') {
                        peisaCatalog = catalog;
                        peisaProductsFromJSON = catalog;
                    } else if (b.key === 'WEBER') {
                        weberCatalog = catalog;
                    }
                    productCatalog.push(...catalog);
                }
            } catch (err) {
                console.error(`Error cargando catálogo para ${b.key}:`, err);
            }
        }

        console.log(`✅ Catálogos cargados dinámicamente: ${productCatalog.length} productos en total.`);
    } catch (error) {
        console.error('❌ Error cargando catálogos dinámicos:', error);
        productCatalog = [];
        peisaProductsFromJSON = [];
    }
}

loadProductCatalog();

/* ── Catálogo navegable por categorías ────────────────────────────────── */
function showBrandMenu() {
    appendMessage('system', '<strong>Seleccioná una marca de productos:</strong>');
    const options = Object.keys(registeredBrands).map(key => {
        const brand = registeredBrands[key];
        const logoName = brand.key.toLowerCase() + '-logo.png';
        return `<img src="img/${logoName}" class="h-8 mx-auto py-1" alt="${brand.display_name}" onerror="this.outerHTML='${brand.display_name}'">`;
    });
    renderOptions(options, false);
}

function showCategoryMenu() {
    if (!browsingBrand) {
        showBrandMenu();
        return;
    }

    appendMessage('system', `<strong>${browsingBrand}</strong> — Seleccioná una categoría de productos:`);
    
    const catalog = brandCatalogs[browsingBrand] || [];
    const categories = [...new Set(catalog.map(p => p.category || p.family))].filter(Boolean);

    if (categories.length === 0) {
        appendMessage('system', 'No se pudieron cargar las categorías. Por favor, intentá más tarde.');
        return;
    }
    
    categories.push('Ver todas las marcas');
    renderOptions(categories, false);
}

function showProductsByCategory(category) {
    appendMessage('user', `Ver productos de: ${category}`);
    
    const catalog = brandCatalogs[browsingBrand] || [];
    const products = catalog.filter(p => p.category === category || p.family === category);

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
        card.style.cssText = 'background:white; border:1px solid #e5e7eb; border-radius:8px; margin:8px 0; transition:all 0.2s; display:flex; justify-content:space-between; align-items:stretch; overflow:hidden; min-height:96px;';
        card.onmouseover = () => { card.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)'; card.style.borderColor = '#2563eb'; };
        card.onmouseout  = () => { card.style.boxShadow = 'none'; card.style.borderColor = '#e5e7eb'; };
        const hasUrl = product.url && product.url !== '#';
        const brandLabel = product.brand || browsingBrand;

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

        card.innerHTML = `
            <div style="flex:1; padding:12px; display:flex; flex-direction:column; justify-content:space-between; gap:8px;">
                <div>
                    <div style="font-weight:600; color:#1f2937; margin-bottom:6px; font-size:14px; line-height:1.3;">${product.model || 'Producto'}</div>
                    <div style="display:flex; gap:8px; margin-bottom:8px;">
                        <span style="font-size:11px; background:#dbeafe; color:#1e40af; padding:2px 8px; border-radius:4px;">
                            ${product.category || product.family || 'Producto'}
                        </span>
                    </div>
                    ${product.description ? `<div style="color:#6b7280; font-size:12px; margin-bottom:8px; line-height:1.4;">
                        ${product.description.substring(0, 100) + (product.description.length > 100 ? '...' : '')}
                    </div>` : ''}
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
        productsGrid.appendChild(card);
    });

    chatContainer.appendChild(productsGrid);
    scrollToBottom();
    renderOptions(['Ver otras categorías', 'Volver al inicio'], false);
}

function showAllProducts() {
    appendMessage('user', 'Ver todos los productos');
    
    let productsToDisplay = [];
    if (browsingBrand) {
        productsToDisplay = brandCatalogs[browsingBrand] || [];
    } else {
        productsToDisplay = productCatalog;
    }

    if (productsToDisplay.length === 0) {
        appendMessage('system', 'No se pudieron cargar los productos. Por favor, intentá más tarde.');
        return;
    }
    
    appendMessage('system', `<strong>Catálogo completo (${browsingBrand || 'Todas las marcas'})</strong> — ${productsToDisplay.length} productos disponibles:`);
    const byCategory = {};
    productsToDisplay.forEach(p => {
        const cat = p.category || p.family || 'Otros';
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
            card.style.cssText = 'background:white; border:1px solid #e5e7eb; border-radius:8px; margin:8px 0; transition:all 0.2s; display:flex; justify-content:space-between; align-items:stretch; overflow:hidden; min-height:96px;';
            const hasUrl = product.url && product.url !== '#';
            const brandLabel = product.brand || browsingBrand;

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

            card.innerHTML = `
                <div style="flex:1; padding:12px; display:flex; flex-direction:column; justify-content:space-between; gap:8px;">
                    <div>
                        <div style="font-weight:600; color:#1f2937; margin-bottom:6px; font-size:14px; line-height:1.3;">${product.model || 'Producto'}</div>
                        <div style="display:flex; gap:8px; margin-bottom:8px;">
                            <span style="font-size:11px; background:#dbeafe; color:#1e40af; padding:2px 8px; border-radius:4px;">
                                ${product.category || product.family || 'Producto'}
                            </span>
                        </div>
                        ${product.description ? `<div style="color:#6b7280; font-size:12px; margin-bottom:8px;">
                            ${product.description.substring(0, 80) + '...'}
                        </div>` : ''}
                    </div>
                    <div style="display:flex; gap:6px; flex-wrap:wrap;">
                        ${hasUrl ? `<a href="${product.url}" target="_blank" class="card-btn card-btn-primary" onclick="event.stopPropagation();">Ver en ${brandLabel}</a>` : ''}
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
    // Deprecated/Legacy: panel de contexto removido del HTML/CSS
}


/* ── BUSCADOR GENÉRICO DE PRODUCTOS EN CATÁLOGO ────────────────────────── */

function findProductInCatalog(text) {
    if (!text || typeof text !== 'string') return null;
    const cleanText = text.toLowerCase().trim();
    if (cleanText.length < 3) return null;
    
    // 1. Coincidencia exacta
    let match = productCatalog.find(p => p.model.toLowerCase().trim() === cleanText);
    if (match) return match;
    
    // 2. Coincidencia de subcadena (el modelo del catálogo está contenido en el texto buscado)
    match = productCatalog.find(p => {
        const pModel = p.model.toLowerCase().trim();
        return pModel.length >= 3 && cleanText.includes(pModel);
    });
    if (match) return match;
    
    // 3. Coincidencia de subcadena inversa (el texto buscado está contenido en el modelo del catálogo)
    match = productCatalog.find(p => {
        const pModel = p.model.toLowerCase().trim();
        return cleanText.length >= 3 && pModel.includes(cleanText);
    });
    return match;
}


/* ── CLIENTE DE SISTEMA EXPERTO UNIFICADO (v5.0.1) ─────────────────────── */

class GenericExpertClient {
    constructor(brand) {
        this.brand = brand;
        this.conversationId = 'expert_' + Math.random().toString(36).substr(2, 9);
        this.currentNode = null;
    }

    async start() {
        lastActiveBrand = this.brand;
        lastActiveProduct = null; // Reiniciar producto activo al comenzar un cálculo nuevo
        appendMessage('system', `¡Perfecto! Te guiaré paso a paso para hacer el cálculo con <strong>${this.brand}</strong>.`);
        try {
            const res = await fetch(`/api/expert/${this.brand}/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ conversation_id: this.conversationId })
            });
            if (!res.ok) throw new Error('Error iniciando calculadora');
            const data = await res.json();
            this.handleResponse(data);
        } catch (err) {
            console.error(err);
            appendMessage('system', '⚠️ No se pudo iniciar el asistente en este momento.');
        }
    }

    async reply(optionIndex = null, inputValues = {}) {
        try {
            const res = await fetch(`/api/expert/${this.brand}/reply`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    conversation_id: this.conversationId,
                    option_index: optionIndex,
                    input_values: inputValues
                })
            });
            if (!res.ok) throw new Error('Error enviando respuesta');
            const data = await res.json();
            this.handleResponse(data);
        } catch (err) {
            console.error(err);
            appendMessage('system', '⚠️ Ocurrió un error al procesar tu respuesta.');
        }
    }

    handleResponse(data) {
        this.currentNode = data;
        
        if (data.error) {
            appendMessage('system', `⚠️ ${data.error}`);
        }

        if (data.text) {
            appendMessage('system', formatResponseText(data.text));
        }

        const type = data.type || data.tipo;
        const isFinal = data.is_final || 
                        (data.node_id === 'final') || 
                        (data.node_id === 'fin') || 
                        (type === 'respuesta' && (!data.options || data.options.length === 0));

        // Detectar y mostrar productos en cualquier nodo de respuesta
        if (type === 'respuesta' || type === 'response') {
            let recommendedProducts = [];
            if (data.products && data.products.length > 0) {
                recommendedProducts = data.products;
            } else {
                // Escaneo genérico y agnóstico de marca para deducir productos a partir de textos, cálculos o variables
                const searchSources = [];
                if (data.text) searchSources.push(data.text);
                if (data.calculo && data.calculo.producto) searchSources.push(data.calculo.producto);
                if (data.variables) {
                    for (const key in data.variables) {
                        const val = data.variables[key];
                        if (typeof val === 'string') {
                            searchSources.push(val);
                        } else if (val && typeof val === 'object') {
                            if (val.name) searchSources.push(val.name);
                            if (val.model) searchSources.push(val.model);
                        }
                    }
                }

                // Resolver coincidencias contra el catálogo
                searchSources.forEach(sourceText => {
                    const match = findProductInCatalog(sourceText);
                    if (match && !recommendedProducts.some(p => p.model === match.model)) {
                        recommendedProducts.push(match);
                    }
                });
            }

            if (recommendedProducts.length > 0) {
                renderProducts(recommendedProducts);
                lastActiveProduct = recommendedProducts[0].model; // Guardar como producto activo para follow-up
                lastActiveBrand = this.brand; // Asegurar sincronización de marca activa
            }
        }

        if (isFinal) {
            renderOptions(['Nuevo cálculo', 'Volver al inicio'], false);
            conversationStep = 99; // Estado de finalización
            return;
        }

        const inputArea = document.getElementById('input-area');
        inputArea.innerHTML = '';

        if (data.options && data.options.length > 0) {
            const container = document.createElement('div');
            container.className = 'space-y-2 w-full p-1';
            data.options.forEach((opt, idx) => {
                const btn = document.createElement('button');
                btn.className = 'option-btn w-full text-left bg-blue-100 hover:bg-blue-200 text-blue-800 rounded-lg';
                btn.textContent = opt;
                btn.onclick = () => {
                    appendMessage('user', opt);
                    this.reply(idx);
                };
                container.appendChild(btn);
            });
            inputArea.appendChild(container);
        } else if (data.input_type === 'number' || type === 'entrada_usuario') {
            const form = document.createElement('form');
            form.className = 'flex gap-2 w-full p-1';
            
            const varName = data.variable || data.node_id || 'value';
            
            form.onsubmit = (e) => {
                e.preventDefault();
                const valEl = document.getElementById('generic-txt-input');
                const val = parseFloat(valEl.value);
                if (isNaN(val) || val <= 0) {
                    alert('Por favor, ingresá un número válido mayor a 0.');
                    return;
                }
                const unidad = data.unidad || '';
                appendMessage('user', `${val} ${unidad}`);
                
                const replyPayload = { value: val };
                replyPayload[varName] = val;
                this.reply(null, replyPayload);
            };

            const placeholder = data.placeholder || 'Ej: 10';
            form.innerHTML = `
                <input type="number" id="generic-txt-input" required step="0.01" min="0.01"
                       class="border border-gray-300 rounded-lg px-3 py-2 flex-1 text-sm text-gray-800 focus:outline-none focus:border-blue-500"
                       placeholder="${placeholder}">
                <button type="submit"
                        class="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg transition-all text-sm shadow">
                    Enviar
                </button>
            `;
            inputArea.appendChild(form);
            document.getElementById('generic-txt-input').focus();
        } else if (data.input_type === 'multiple') {
            const form = document.createElement('form');
            form.className = 'flex flex-col gap-2 w-full p-1';
            
            let inputsHtml = '<div class="grid grid-cols-3 gap-2">';
            data.inputs.forEach(inp => {
                inputsHtml += `
                    <input type="number" id="inp-${inp.name}" required step="0.1" min="0.1"
                           class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
                           placeholder="${inp.label}">
                `;
            });
            inputsHtml += '</div>';

            form.onsubmit = (e) => {
                e.preventDefault();
                const vals = {};
                let displayStr = '';
                let isValid = true;
                data.inputs.forEach(inp => {
                    const el = document.getElementById(`inp-${inp.name}`);
                    const val = parseFloat(el.value);
                    if (isNaN(val) || val <= 0) {
                        isValid = false;
                    }
                    vals[inp.name] = val;
                    displayStr += `${val}m x `;
                });
                if (!isValid) {
                    alert('Por favor ingrese valores mayores a 0.');
                    return;
                }
                displayStr = displayStr.slice(0, -3);
                appendMessage('user', displayStr);
                this.reply(null, vals);
            };

            form.innerHTML = `
                ${inputsHtml}
                <button type="submit"
                        class="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg transition-all text-sm shadow">
                    Enviar
                </button>
            `;
            inputArea.appendChild(form);
            if (data.inputs.length > 0) {
                document.getElementById(`inp-${data.inputs[0].name}`).focus();
            }
        }
    }
}
