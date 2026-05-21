/* ========== ESTADO GLOBAL ========== */
let conversationId = 'user_' + Math.random().toString(36).substr(2, 9);
let lastUserResponse = null;
let isLoading = false;
let currentMode = 'hybrid';
let inMainMenu = true;

/* ========== TOGGLE DEL CHAT FLOTANTE ========== */
let chatIsOpen = false;
let isMaximized = false;

function toggleMaximize() {
    const chatWidget = document.getElementById('chat-widget');
    const maximizeIcon = document.getElementById('maximize-icon');
    const minimizeIcon = document.getElementById('minimize-icon');
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
    const chatWidget = document.getElementById('chat-widget');
    const chatButton = document.getElementById('chat-toggle-btn');
    const soldyMessage = document.getElementById('soldy-message');
    const soldyChatImage = document.getElementById('soldy-chat-image');
    
    chatIsOpen = !chatIsOpen;
    
    if (chatIsOpen) {
        chatWidget.classList.add('active');
        chatButton.style.display = 'none';
        if (soldyChatImage) {
            soldyChatImage.style.display = 'block';
        }
        if (soldyMessage) {
            soldyMessage.classList.add('hidden');
        }
        if (document.getElementById('chat-container').children.length === 0) {
            startConversation();
        }
    } else {
        chatWidget.classList.remove('active');
        chatButton.style.display = 'block';
        if (soldyChatImage) {
            soldyChatImage.style.display = 'none';
        }
        if (soldyMessage) {
            soldyMessage.classList.remove('hidden');
        }
    }
}

/* ========== INICIALIZACIÓN ========== */
document.addEventListener('DOMContentLoaded', () => {
    // Ocultar mensaje de bienvenida después de 8 segundos
    setTimeout(() => {
        const soldyMessage = document.getElementById('soldy-message');
        if (soldyMessage && !chatIsOpen) {
            soldyMessage.style.animation = 'fadeOut 0.5s ease-out forwards';
            setTimeout(() => {
                soldyMessage.style.display = 'none';
            }, 500);
        }
    }, 8000);
    
    // Login (mantenido por compatibilidad)
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const username = document.getElementById('login-username').value.trim();
            const password = document.getElementById('login-password').value.trim();
            const errorLabel = document.getElementById('login-error');

            if (username === 'admin' && password === 'admin') {
                document.getElementById('login-overlay').classList.add('hidden');
                startConversation();
            } else {
                errorLabel.textContent = 'Usuario o contraseña incorrectos';
            }
        });
    }
});

/* ========== NAVEGACIÓN ========== */
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
    // NO resetear el historial del chatbot para mantener contexto
    document.getElementById('chat-container').innerHTML = '';
    startConversation();
    hideBackButton();
}

function switchMode(mode) {
    currentMode = mode;
    conversationId = 'user_' + Math.random().toString(36).substr(2, 9);
    document.getElementById('chat-container').innerHTML = '';
    lastUserResponse = null;
    resetExpertSystem();
    // Resetear historial del chatbot solo si se cambia explícitamente de modo
    if (typeof resetChatHistory === 'function') {
        resetChatHistory();
    }
    startConversation();
    hideBackButton();
}

/* ========== INICIO DE CONVERSACIÓN ========== */
function startConversation() {
    resetExpertSystem();
    appendMessage('system', '¡Hola! Soy <strong>Soldy</strong> tu asistente inteligente de SOLDASUR. Puedo ayudarte de diferentes formas. ¿Qué necesitas?');
    renderOptions(['Guíame en un cálculo', 'Tengo una pregunta', 'Buscar productos'], false);
}

/* ========== MANEJO DE OPCIONES ========== */
function handleOptionClick(option) {
    appendMessage('user', option);
    
    // Navegación de catálogo (solo si no estamos en el sistema experto)
    if (conversationStep === 0) {
        const productCategories = [...new Set(productCatalog.map(p => p.family))].filter(Boolean);
        
        if (productCategories.includes(option)) {
            showProductsByCategory(option);
            return;
        }
        
        if (option === 'Ver todos') {
            showAllProducts();
            return;
        } else if (option === 'Ver otras categorías' || option === 'Ver por categoría') {
            showCategoryMenu();
            return;
        } else if (option === 'Volver al inicio') {
            goBack();
            return;
        }
    }
    
    // Opciones iniciales del menú principal
    if (conversationStep === 0) {
        if (option.includes('Guíame') || option.includes('cálculo')) {
            showBackButton();
            startExpertSystem();
        } else if (option.includes('pregunta')) {
            showBackButton();
            startChatbot();
        } else if (option.includes('Buscar') || option.includes('productos')) {
            showBackButton();
            showCategoryMenu();
        }
        return;
    }
    
    // Opciones post-cálculo (manejar antes para no ser interceptadas por el flujo experto)
    if (option === 'Nuevo cálculo') {
        // Reiniciar estado y volver a iniciar el sistema experto de inmediato
        resetExpertSystem();
        showBackButton();
        startExpertSystem();
        return;
    } else if (option === 'Hacer una pregunta' || option.includes('pregunta')) {
        startChatbot();
        return;
    }

    // Respuestas del sistema experto
    if (conversationStep >= 1 && conversationStep <= 8) {
        handleExpertSystemResponse(option);
        return;
    }
}

/* ========== RENDERIZADO DE UI ========== */
function renderOptions(options, isResponse = false) {
    const inputArea = document.getElementById('input-area');
    inputArea.innerHTML = '';
    const container = document.createElement('div');
    container.className = 'space-y-2';
    
    options.forEach((option, idx) => {
        const btn = document.createElement('button');
        btn.className = `option-btn w-full ${isResponse ? 'bg-green-100 hover:bg-green-200 text-green-800' : 'bg-blue-100 hover:bg-blue-200 text-blue-800'} py-2 px-4 rounded`;
        btn.textContent = option;
        btn.onclick = () => handleOptionClick(option);
        container.appendChild(btn);
    });
    
    inputArea.appendChild(container);
}

function renderSuggestion(suggestion) {
    const box = document.createElement('div');
    box.className = 'suggestion-box fade-in';
    box.innerHTML = `
        <div class="font-medium mb-2">${suggestion.message || suggestion}</div>
        ${suggestion.options ? `
            <div class="flex gap-2 mt-2">
                ${suggestion.options.map((opt, idx) => `
                    <button onclick="handleSuggestionOption(${idx})" 
                        class="text-xs px-3 py-1 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded transition">
                        ${opt}
                    </button>
                `).join('')}
            </div>
        ` : ''}
    `;
    document.getElementById('chat-container').appendChild(box);
}

function createMultipleInputs(inputs) {
    const inputArea = document.getElementById('input-area');
    const form = document.createElement('form');
    form.onsubmit = (e) => {
        e.preventDefault();
        if (isLoading) return;
        const values = {};
        inputs.forEach(inp => {
            values[inp.name] = document.getElementById(`input-${inp.name}`).value;
        });
        lastUserResponse = `Valores ingresados: ${Object.entries(values).map(([k,v]) => `${k}=${v}`).join(', ')}`;
    };
    
    const fieldsHTML = inputs.map(inp => `
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">${inp.label}</label>
            <input type="${inp.type || 'text'}" inputmode="decimal" id="input-${inp.name}" required 
                class="w-full border border-gray-300 rounded px-3 py-2" placeholder="Ej: 4.5">
        </div>
    `).join('');
    
    form.innerHTML = `
        <div class="space-y-4">
            ${fieldsHTML}
            <button type="submit" class="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition">
                Calcular
            </button>
        </div>
    `;
    inputArea.appendChild(form);
}

function createRestartButton() {
    const inputArea = document.getElementById('input-area');
    const btn = document.createElement('button');
    btn.className = 'w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition';
    btn.textContent = 'Iniciar nuevo cálculo';
    btn.onclick = () => {
        if (isLoading) return;
        switchMode(currentMode);
    };
    inputArea.appendChild(btn);
}

/* ========== HELPERS ========== */
function appendMessage(sender, text) {
    const chatContainer = document.getElementById('chat-container');
    const div = document.createElement('div');
    div.className = `chat-message rounded-lg p-3 ${sender === 'system' ? 'system-message' : 'user-message'} fade-in`;
    div.innerHTML = text;
    chatContainer.appendChild(div);
    scrollToBottom();
}

function formatResponseText(text) {
    return text ? text.replace(/\n/g, '<br>').replace(/<br>- /g, '<br>• ') : '';
}

function scrollToBottom() {
    const container = document.getElementById('chat-container');
    container.scrollTop = container.scrollHeight;
}

function updateModeIndicator(mode, label) {
    const indicator = document.getElementById('mode-indicator');
    if (indicator) {
        indicator.textContent = label;
        indicator.className = 'mode-indicator';
        
        if (mode === 'expert') {
            indicator.classList.add('mode-expert');
        } else if (mode === 'rag') {
            indicator.classList.add('mode-rag');
        } else {
            indicator.classList.add('mode-hybrid');
        }
    }
}

/* ========== CONSULTA SUCURSAL (RIO GRANDE / USHUAIA) ========== */
function consultSucursal(city = null, showOnPage = true) {
    const sel = document.getElementById('city-select');
    const res = document.getElementById('sucursal-result');
    
    // Si showOnPage es true y no se pasó ciudad, abrir chat y preguntar
    if (showOnPage && !city) {
        // Abrir chat si está cerrado
        if (!chatIsOpen) toggleChat();
        // Preguntar en el chat por la ciudad
        if (typeof appendMessage === 'function') {
            const optionsHtml = `
                <div class="sucursal-options" style="display:flex;gap:8px;margin-top:8px;">
                    <button class="inline-block bg-blue-600 text-white px-3 py-1 rounded text-sm" onclick="consultSucursalFromChat('rio_grande')">Río Grande</button>
                    <button class="inline-block bg-green-600 text-white px-3 py-1 rounded text-sm" onclick="consultSucursalFromChat('ushuaia')">Ushuaia</button>
                </div>
            `;
            appendMessage('system', `¿Estás en Río Grande o Ushuaia?${optionsHtml}`);
            scrollToBottom();
        }
        return;
    }
    
    // determine city: priority param -> selector -> default
    const selectedCity = city || (sel ? sel.value : null);
    // info map
    const info = {
        rio_grande: {
            name: 'Sucursal Río Grande - Soldasur',
            address: 'Islas Malvinas 1950, V9421 Río Grande, Tierra del Fuego',
            phone: '+54 2964 40-1201',
            email: 'ventasrg@soldasur.com.ar',
            mapsUrl: 'https://www.google.com/maps/search/?api=1&query=Islas+Malvinas+1950,+V9421+Río+Grande,+Tierra+del+Fuego'
        },
        ushuaia: {
            name: 'Sucursal Ushuaia - Soldasur',
            address: 'Héroes de Malvinas 4180, V9410 Ushuaia, Tierra del Fuego',
            phone: '+54 2901 43-6392',
            email: 'ventasush@soldasur.com.ar',
            mapsUrl: 'https://www.google.com/maps/search/?api=1&query=Héroes+de+Malvinas+4180,+V9410+Ushuaia,+Tierra+del+Fuego'
        }
    };

    const c = info[selectedCity];
    if (!c) {
        if (res) res.innerHTML = '';
        return;
    }

    // Mostrar en el widget (solo si showOnPage)
    if (showOnPage && res) {
        res.innerHTML = `
            <div class="p-3 bg-blue-50 rounded">
                <div class="font-semibold">${c.name}</div>
                <div class="text-sm text-gray-700">${c.address}</div>
                <div class="text-sm">Tel: <a href="tel:${c.phone.replace(/\s+/g,'')}" class="text-blue-600">${c.phone}</a></div>
                <div class="text-sm">Email: <a href="mailto:${c.email}" class="text-blue-600">${c.email}</a></div>
            </div>
        `;
    }

    // Añadir también un mensaje al chat para que quede en el historial
    if (typeof appendMessage === 'function') {
        // Si no se pasó ciudad y la llamada viene desde el chat (showOnPage=false),
        // presentar opciones interactivas para elegir sucursal dentro del chat.
        if (!selectedCity && !showOnPage) {
            const optionsHtml = `
                <div class="sucursal-options" style="display:flex;gap:8px;margin-top:8px;">
                    <button class="inline-block bg-blue-600 text-white px-3 py-1 rounded text-sm" onclick="consultSucursalFromChat('rio_grande')">Río Grande</button>
                    <button class="inline-block bg-green-600 text-white px-3 py-1 rounded text-sm" onclick="consultSucursalFromChat('ushuaia')">Ushuaia</button>
                </div>
            `;
            appendMessage('system', `¿Estás en Río Grande o Ushuaia?${optionsHtml}`);
        } else {
            // Añadir mensaje al chat con botones junto a la tarjeta de contacto
            const chatHtml = `
                <div class="sucursal-card">
                    <strong>${c.name}</strong><br>
                    ${c.address}<br>
                    Tel: <a href="tel:${c.phone.replace(/\s+/g,'')}" class="text-blue-600">${c.phone}</a><br>
                    Email: <a href="mailto:${c.email}" class="text-blue-600">${c.email}</a>
                    <div style="margin-top:8px; display:flex; gap:8px;">
                        <a href="tel:${c.phone.replace(/\s+/g,'')}" class="inline-block bg-blue-600 text-white px-3 py-1 rounded text-sm">Llamar</a>
                        <a href="mailto:${c.email}" class="inline-block bg-gray-200 text-gray-800 px-3 py-1 rounded text-sm">Email</a>
                        <a href="${c.mapsUrl}" target="_blank" class="inline-block bg-green-600 text-white px-3 py-1 rounded text-sm">Ver sucursal</a>
                    </div>
                </div>
            `;
            appendMessage('system', chatHtml);
        }
    }
    // Asegurar scroll al final
    scrollToBottom();
}

// Desplazar a la tarjeta de sucursal en la página y aplicar un breve highlight
function scrollToSucursal(city) {
    const el = document.getElementById('sucursal-result');
    if (!el) return;
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    // efecto highlight
    el.style.transition = 'box-shadow 0.3s ease, transform 0.15s ease';
    el.style.boxShadow = '0 6px 18px rgba(59,130,246,0.25)';
    el.style.transform = 'translateY(-2px)';
    setTimeout(() => {
        el.style.boxShadow = '';
        el.style.transform = '';
    }, 1200);
}

/* ========== CONSULTAR DESDE PRODUCTO ========== */
function consultFromProduct(productModel) {
    // Abrir chat si está cerrado
    if (!chatIsOpen) toggleChat();
    // Añadir mensaje de usuario indicando interés en el producto
    appendMessage('user', `Estoy interesado en: <strong>${productModel}</strong>`);
    
    // Preguntar SIEMPRE por la ciudad (no asumir valor del selector)
    if (typeof appendMessage === 'function') {
        const optionsHtml = `
            <div class="sucursal-options" style="display:flex;gap:8px;margin-top:8px;">
                <button class="inline-block bg-blue-600 text-white px-3 py-1 rounded text-sm" onclick="consultSucursalFromChat('rio_grande')">Río Grande</button>
                <button class="inline-block bg-green-600 text-white px-3 py-1 rounded text-sm" onclick="consultSucursalFromChat('ushuaia')">Ushuaia</button>
            </div>
        `;
        appendMessage('system', `¿Estás en Río Grande o Ushuaia?${optionsHtml}`);
        scrollToBottom();
    }
}

// Función llamada desde los botones de opciones dentro del chat
function consultSucursalFromChat(city) {
    // Añadir un mensaje de confirmación de selección en el chat
    appendMessage('user', `Seleccioné: <strong>${city === 'rio_grande' ? 'Río Grande' : 'Ushuaia'}</strong>`);
    // Mostrar la tarjeta correspondiente en el chat (sin actualizar la página)
    consultSucursal(city, false);
}

/* ========== BÚSQUEDA DE PRODUCTOS POR CATEGORÍA ========== */
let productCatalog = [];

// Cargar catálogo de productos
async function loadProductCatalog() {
    try {
        const response = await fetch('../data/products_catalog.json');
        if (!response.ok) throw new Error('Error cargando catálogo');
        productCatalog = await response.json();
        console.log(`✅ Catálogo cargado: ${productCatalog.length} productos`);
    } catch (error) {
        console.error('❌ Error cargando catálogo:', error);
        productCatalog = [];
    }
}

// Cargar catálogo al iniciar
loadProductCatalog();

// Mostrar menú de categorías
function showCategoryMenu() {
    appendMessage('system', '<strong>Seleccioná una categoría de productos:</strong>');
    
    // Obtener categorías únicas del catálogo
    const categories = [...new Set(productCatalog.map(p => p.family))].filter(Boolean);
    
    if (categories.length === 0) {
        appendMessage('system', 'No se pudieron cargar las categorías. Por favor, intentá más tarde.');
        return;
    }
    
    renderOptions(categories, false);
}

// Mostrar productos por categoría
function showProductsByCategory(category) {
    appendMessage('user', `Ver productos de: ${category}`);
    
    // Filtrar productos por categoría
    const products = productCatalog.filter(p => p.family === category);
    
    if (products.length === 0) {
        appendMessage('system', `No se encontraron productos en la categoría ${category}.`);
        renderOptions(['Ver otras categorías'], false);
        return;
    }
    
    appendMessage('system', `<strong>${category}</strong> - ${products.length} producto${products.length > 1 ? 's' : ''} disponible${products.length > 1 ? 's' : ''}:`);
    
    // Mostrar productos como tarjetas con enlaces
    const chatContainer = document.getElementById('chat-container');
    const productsContainer = document.createElement('div');
    productsContainer.className = 'products-grid fade-in';
    productsContainer.style.cssText = 'display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin: 12px 0;';
    
    products.forEach(product => {
        const productCard = document.createElement('div');
        productCard.className = 'product-card';
        productCard.style.cssText = 'background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; transition: all 0.2s;';
        productCard.onmouseover = () => productCard.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
        productCard.onmouseout = () => productCard.style.boxShadow = 'none';
        
        const productUrl = product.url || '#';
        const hasUrl = productUrl !== '#' && productUrl !== '';
        
        productCard.innerHTML = `
            <div style="font-weight: 600; color: #1f2937; margin-bottom: 6px; font-size: 14px;">
                ${product.model || 'Producto'}
            </div>
            <div style="color: #6b7280; font-size: 12px; margin-bottom: 8px; line-height: 1.4;">
                ${product.description ? product.description.substring(0, 100) + (product.description.length > 100 ? '...' : '') : 'Sin descripción'}
            </div>
            ${product.type ? `<div style="font-size: 11px; color: #9ca3af; margin-bottom: 8px;">Tipo: ${product.type}</div>` : ''}
            <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                ${hasUrl ? `
                    <a href="${productUrl}" target="_blank" 
                       style="display: inline-block; background: #3b82f6; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-size: 12px; transition: background 0.2s;"
                       onmouseover="this.style.background='#2563eb'" 
                       onmouseout="this.style.background='#3b82f6'">
                        Ver en PEISA
                    </a>
                ` : ''}
                <button onclick="consultFromProduct('${product.model}')" 
                        style="background: #10b981; color: white; padding: 6px 12px; border: none; border-radius: 6px; cursor: pointer; font-size: 12px; transition: background 0.2s;"
                        onmouseover="this.style.background='#059669'" 
                        onmouseout="this.style.background='#10b981'">
                    Consultar
                </button>
            </div>
        `;
        
        productsContainer.appendChild(productCard);
    });
    
    chatContainer.appendChild(productsContainer);
    scrollToBottom();
    
    // Opciones de navegación
    renderOptions(['Ver otras categorías', 'Volver al inicio'], false);
}

// Mostrar todos los productos
function showAllProducts() {
    appendMessage('user', 'Ver todos los productos');
    
    if (productCatalog.length === 0) {
        appendMessage('system', 'No se pudieron cargar los productos. Por favor, intentá más tarde.');
        return;
    }
    
    appendMessage('system', `<strong>Catálogo completo</strong> - ${productCatalog.length} productos disponibles:`);
    
    // Agrupar por categoría
    const byCategory = {};
    productCatalog.forEach(p => {
        const cat = p.family || 'Otros';
        if (!byCategory[cat]) byCategory[cat] = [];
        byCategory[cat].push(p);
    });
    
    // Mostrar por categorías
    Object.keys(byCategory).sort().forEach(category => {
        const products = byCategory[category];
        appendMessage('system', `<strong>${category}</strong> (${products.length}):`);
        
        const chatContainer = document.getElementById('chat-container');
        const productsContainer = document.createElement('div');
        productsContainer.className = 'products-grid fade-in';
        productsContainer.style.cssText = 'display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin: 12px 0;';
        
        products.slice(0, 6).forEach(product => {
            const productCard = document.createElement('div');
            productCard.className = 'product-card';
            productCard.style.cssText = 'background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px;';
            
            const productUrl = product.url || '#';
            const hasUrl = productUrl !== '#' && productUrl !== '';
            
            productCard.innerHTML = `
                <div style="font-weight: 600; color: #1f2937; margin-bottom: 6px; font-size: 14px;">
                    ${product.model || 'Producto'}
                </div>
                <div style="color: #6b7280; font-size: 12px; margin-bottom: 8px;">
                    ${product.description ? product.description.substring(0, 80) + '...' : ''}
                </div>
                <div style="display: flex; gap: 6px;">
                    ${hasUrl ? `<a href="${productUrl}" target="_blank" style="display: inline-block; background: #3b82f6; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-size: 12px;">Ver</a>` : ''}
                    <button onclick="consultFromProduct('${product.model}')" style="background: #10b981; color: white; padding: 6px 12px; border: none; border-radius: 6px; cursor: pointer; font-size: 12px;">Consultar</button>
                </div>
            `;
            
            productsContainer.appendChild(productCard);
        });
        
        chatContainer.appendChild(productsContainer);
    });
    
    scrollToBottom();
    renderOptions(['Ver por categoría', 'Volver al inicio'], false);
}
