/* ==========================================================================
   SOLDASUR.JS — Orquestador principal del chat
   Responsabilidades:
     · Iniciar la conversación y mostrar el menú principal
     · Rutear las opciones del usuario al módulo correcto
     · Exponer la función consultSucursal para el HTML estático

   Dependencias (deben cargarse ANTES en index.html):
     1. core.js          — estado global y helpers
     2. peisa_expert.js  — calculadora PEISA
     3. weber_expert.js  — calculadora Weber
     4. chatbot.js       — chat libre de texto (llama a Ollama/backend)
   ========================================================================== */

/* ── Inicialización DOM ─────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
    // Ocultar burbuja de bienvenida de Soldy después de 8 segundos
    setTimeout(() => {
        const soldyMessage = document.getElementById('soldy-message');
        if (soldyMessage && !chatIsOpen) {
            soldyMessage.style.animation = 'fadeOut 0.5s ease-out forwards';
            setTimeout(() => { soldyMessage.style.display = 'none'; }, 500);
        }
    }, 8000);

    // Formulario de login (mantenido por compatibilidad)
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
                if (errorLabel) errorLabel.textContent = 'Usuario o contraseña incorrectos';
            }
        });
    }

});

/* ── Inicio de conversación ──────────────────────────────────────────────── */
function startConversation() {
    resetExpertSystem();   // resetea el estado del módulo PEISA
    appendMessage('system',
        '¡Hola! Soy <strong>Soldy</strong>, tu asistente inteligente de SOLDASUR. ' +
        'Puedo ayudarte de diferentes formas. ¿Qué necesitás?'
    );
    renderOptions([
        'Calculadora PEISA (Calefacción)',
        'Calculadora Weber (Construcción)',
        'Tengo una pregunta',
        'Buscar productos'
    ], false);
}

/* ── Routing de opciones del menú principal ──────────────────────────────── */
function handleOptionClick(option) {
    let cleanOption = typeof option === 'string' ? option.replace(/<[^>]*>/g, '').trim() : option;

    // Si es un botón con logo únicamente (sin texto visible)
    if (typeof option === 'string' && cleanOption === '') {
        if (option.toLowerCase().includes('peisa')) cleanOption = 'PEISA';
        else if (option.toLowerCase().includes('weber')) cleanOption = 'WEBER';
    }

    appendMessage('user', cleanOption);

    // ── Navegación por catálogo (cuando ya salimos del menú principal) ──
    if (conversationStep === 0) {
        if (cleanOption === 'PEISA') {
            browsingBrand = 'PEISA';
            showCategoryMenu();
            return;
        }
        if (cleanOption === 'WEBER') {
            browsingBrand = 'WEBER';
            showCategoryMenu();
            return;
        }
        if (cleanOption === 'Ver otras marcas' || cleanOption === 'Ver todas las marcas') {
            browsingBrand = null;
            showBrandMenu();
            return;
        }

        const peisaCategories = [...new Set(peisaCatalog.map(p => p.family))].filter(Boolean);
        const weberCategories = [...new Set(weberCatalog.map(p => p.category))].filter(Boolean);

        if (peisaCategories.includes(cleanOption) || weberCategories.includes(cleanOption)) {
            showProductsByCategory(cleanOption);
            return;
        }
        if (cleanOption === 'Ver todos' || cleanOption === 'Ver todos los productos') {
            showAllProducts();
            return;
        }
        if (cleanOption === 'Ver otras categorías' || cleanOption === 'Ver por categoría') {
            showCategoryMenu();
            return;
        }
        if (cleanOption === 'Volver al inicio') {
            goBack();
            return;
        }
    }

    // ── Opciones del menú principal ──
    if (conversationStep === 0) {
        if (cleanOption.includes('Calculadora PEISA') || cleanOption.includes('Guíame') || cleanOption.includes('cálculo')) {
            showBackButton();
            startExpertSystem();          // módulo peisa_expert.js
        } else if (cleanOption.includes('Calculadora Weber') || cleanOption.includes('Construcción')) {
            showBackButton();
            iniciarExpertoWeber();        // módulo weber_expert.js
        } else if (cleanOption.includes('pregunta') || cleanOption.includes('Tengo una pregunta')) {
            showBackButton();
            startChatbot();               // módulo chatbot.js
        } else if (cleanOption.includes('Buscar') || cleanOption.includes('productos')) {
            showBackButton();
            showCategoryMenu();           // core.js
        }
        return;
    }

    // ── Opciones post-cálculo ──
    if (cleanOption === 'Nuevo cálculo') {
        resetExpertSystem();
        showBackButton();
        startExpertSystem();
        return;
    }
    if (cleanOption === 'Hacer una pregunta' || cleanOption.includes('pregunta')) {
        startChatbot();
        return;
    }

    // ── Respuestas del sistema experto PEISA ──
    if (conversationStep >= 1 && conversationStep <= 8) {
        handleExpertSystemResponse(cleanOption);   // peisa_expert.js
    }
}