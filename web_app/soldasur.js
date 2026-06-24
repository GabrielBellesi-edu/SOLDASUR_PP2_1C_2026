/* ==========================================================================
   SOLDASUR.JS — Orquestador principal del chat
   Responsabilidades:
     · Iniciar la conversación y mostrar el menú principal
     · Rutear las opciones del usuario al módulo correcto
     · Exponer la función consultSucursal para el HTML estático

   Dependencias (deben cargarse ANTES en index.html):
     1. core.js          — estado global y helpers
     2. peisa_expert.js  — calculadora PEISA (mantenida por compatibilidad)
     3. weber_expert.js  — calculadora Weber (mantenida por compatibilidad)
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
    resetExpertSystem();   // resetea el estado
    appendMessage('system',
        '¡Hola! Soy <strong>Soldy</strong>, tu asistente inteligente de SOLDASUR. ' +
        'Puedo ayudarte a buscar productos por marca, a hacer algún cálculo o a responder a alguna pregunta. ¿Qué necesitás?'
    );
    renderOptions([
        'Calculadoras',
        'Buscar productos'
    ], false);
}

/* ── Submenú Calculadoras ───────────────────────────────────────────────── */
function showCalculatorsMenu() {
    showBackButton();
    appendMessage('system', '<strong>Seleccioná la calculadora de la marca que deseas utilizar:</strong>');
    
    // Generar opciones basadas en registeredBrands con has_calculator === true
    const calculatorOptions = Object.values(registeredBrands)
        .filter(b => b.has_calculator)
        .map(b => b.calculator_display || `Calculadora ${b.display_name}`);
        
    calculatorOptions.push('Volver al inicio');
    renderOptions(calculatorOptions, false);
}

/* ── Routing de opciones del menú principal y navegación ─────────────────── */
function handleOptionClick(option) {
    let cleanOption = typeof option === 'string' ? option.replace(/<[^>]*>/g, '').trim() : option;

    // Si es un botón con logo únicamente (sin texto visible) o HTML complejo
    if (typeof option === 'string' && cleanOption === '') {
        const altMatch = option.match(/alt="([^"]+)"/i);
        if (altMatch && altMatch[1]) {
            cleanOption = altMatch[1].trim();
        } else {
            // Busquemos coincidencia de la clave de la marca en la cadena HTML
            for (const key in registeredBrands) {
                if (option.toLowerCase().includes(key.toLowerCase())) {
                    cleanOption = registeredBrands[key].display_name || key;
                    break;
                }
            }
        }
    }

    appendMessage('user', cleanOption);

    // 1. ¿Es una marca registrada clicada directamente (para ver catálogo)?
    const matchedBrand = Object.values(registeredBrands).find(b => 
        b.display_name.toLowerCase() === cleanOption.toLowerCase() || 
        b.key.toLowerCase() === cleanOption.toLowerCase()
    );
    if (matchedBrand) {
        browsingBrand = matchedBrand.key;
        showCategoryMenu();
        return;
    }

    // 2. ¿Es una opción de navegación general por catálogo?
    if (cleanOption === 'Ver otras marcas' || cleanOption === 'Ver todas las marcas') {
        browsingBrand = null;
        showBrandMenu();
        return;
    }

    // Obtener todas las categorías del catálogo de la marca activa
    let currentBrandCategories = [];
    if (browsingBrand && brandCatalogs[browsingBrand]) {
        currentBrandCategories = [...new Set(brandCatalogs[browsingBrand].map(p => p.category || p.family))].filter(Boolean);
    }

    if (currentBrandCategories.includes(cleanOption)) {
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

    // 3. ¿Es una opción del menú principal?
    if (cleanOption === 'Calculadoras') {
        showCalculatorsMenu();
        return;
    }
    if (cleanOption === 'Buscar productos') {
        showBackButton();
        showCategoryMenu(); // Muestra el menú de marcas si browsingBrand es null
        return;
    }

    // ¿Coincide con alguna calculadora de marca registrada?
    const selectedBrand = Object.values(registeredBrands).find(b =>
        b.has_calculator && (
            b.calculator_display === cleanOption || 
            `Calculadora ${b.display_name}` === cleanOption
        )
    );
    if (selectedBrand) {
        showBackButton();
        activeExpert = new GenericExpertClient(selectedBrand.key);
        activeExpert.start();
        return;
    }

    // 4. Opciones post-cálculo
    if (cleanOption === 'Nuevo cálculo') {
        if (activeExpert && activeExpert.brand) {
            const brand = activeExpert.brand;
            resetExpertSystem();
            showBackButton();
            activeExpert = new GenericExpertClient(brand);
            activeExpert.start();
        } else {
            resetExpertSystem();
            showCalculatorsMenu();
        }
        return;
    }

    if (cleanOption === 'Volver al inicio') {
        goBack();
        return;
    }
}