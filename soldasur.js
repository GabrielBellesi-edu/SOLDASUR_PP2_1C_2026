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
    appendMessage('user', option);

    // ── Navegación por catálogo (cuando ya salimos del menú principal) ──
    if (conversationStep === 0) {
        const productCategories = [...new Set(productCatalog.map(p => p.family))].filter(Boolean);

        if (productCategories.includes(option)) {
            showProductsByCategory(option);
            return;
        }
        if (option === 'Ver todos') {
            showAllProducts();
            return;
        }
        if (option === 'Ver otras categorías' || option === 'Ver por categoría') {
            showCategoryMenu();
            return;
        }
        if (option === 'Volver al inicio') {
            goBack();
            return;
        }
    }

    // ── Opciones del menú principal ──
    if (conversationStep === 0) {
        if (option.includes('PEISA') || option.includes('Guíame') || option.includes('cálculo')) {
            showBackButton();
            startExpertSystem();          // módulo peisa_expert.js
        } else if (option.includes('Weber') || option.includes('Construcción')) {
            showBackButton();
            iniciarExpertoWeber();        // módulo weber_expert.js
        } else if (option.includes('pregunta')) {
            showBackButton();
            startChatbot();               // módulo chatbot.js
        } else if (option.includes('Buscar') || option.includes('productos')) {
            showBackButton();
            showCategoryMenu();           // core.js
        }
        return;
    }

    // ── Opciones post-cálculo ──
    if (option === 'Nuevo cálculo') {
        resetExpertSystem();
        showBackButton();
        startExpertSystem();
        return;
    }
    if (option === 'Hacer una pregunta' || option.includes('pregunta')) {
        startChatbot();
        return;
    }

    // ── Respuestas del sistema experto PEISA ──
    if (conversationStep >= 1 && conversationStep <= 8) {
        handleExpertSystemResponse(option);   // peisa_expert.js
    }
}