/* ============================================
   SISTEMA EXPERTO - CÁLCULO DE CALEFACCIÓN
   ============================================ */

/* Variables del sistema experto */
let conversationStep = 0;
let userInputs = {};
let contextData = {};

/* Iniciar flujo del sistema experto */
function startExpertSystem() {
    conversationStep = 0;
    userInputs = {};
    contextData = {};
    lastRecommendedProduct = null; // Resetear producto recomendado
    updateContextPanel();
    
    appendMessage('system', '¡Perfecto! Te guiaré paso a paso para calcular tu sistema de calefacción.');
    setTimeout(() => askQuestion(), 500);
}

/* Preguntar siguiente paso del flujo */
function askQuestion() {
    conversationStep++;
    const tipo = userInputs.tipo;
    
    // PASO 1: Tipo de calefacción
    if (conversationStep === 1) {
        appendMessage('system', '¿Qué tipo de calefacción deseas calcular?');
        renderOptions(['Piso radiante', 'Radiadores', 'Calderas'], false);
    }
    
    // ========== FLUJO PISO RADIANTE ==========
    else if (tipo === 'Piso radiante') {
        if (conversationStep === 2) {
            appendMessage('system', '¿Cuál es la superficie a calefaccionar?');
            createNumberInput({ input_label: 'Superficie en m²' });
        } else if (conversationStep === 3) {
            const superficie = userInputs.superficie;
            contextData.superficie = superficie + ' m²';
            updateContextPanel();
            appendMessage('system', `Perfecto, ${superficie}m². ¿En qué zona geográfica se encuentra?`);
            renderOptions(['Norte', 'Centro', 'Sur'], false);
        } else if (conversationStep === 4) {
            const zona = userInputs.zona;
            contextData.zona = zona;
            updateContextPanel();
            appendMessage('system', '¿Cuál es el nivel de aislación térmica de la vivienda?');
            renderOptions(['Buena', 'Regular', 'Mala'], false);
        } else if (conversationStep === 5) {
            calculateHeatingLoad();
        }
    }
    
    // ========== FLUJO RADIADORES ==========
    else if (tipo === 'Radiadores') {
        if (conversationStep === 2) {
            appendMessage('system', '¿Cuál es el principal objetivo para los radiadores?');
            renderOptions(['Calefacción principal de ambiente', 'Calefacción complementaria', 'Secado de toallas (baño)'], false);
        } else if (conversationStep === 3) {
            const objetivo = userInputs.objetivo;
            contextData.objetivo = objetivo;
            updateContextPanel();
            
            // Si es toallero, recomendar directamente
            if (objetivo === 'Secado de toallas (baño)') {
                showTowelRackRecommendation();
                return;
            }
            
            appendMessage('system', 'Indique las dimensiones del ambiente:');
            createDimensionsInput();
        } else if (conversationStep === 4) {
            const { largo, ancho, alto } = userInputs;
            contextData.dimensiones = `${largo}m x ${ancho}m x ${alto}m`;
            updateContextPanel();
            appendMessage('system', 'Nivel de aislación térmica del ambiente:');
            renderOptions(['Alta (doble vidrio, aislación en paredes)', 'Media (vidrio simple, algunas paredes aisladas)', 'Baja (sin aislación significativa)'], false);
        } else if (conversationStep === 5) {
            const aislacion = userInputs.aislacion;
            contextData.aislacion = aislacion;
            updateContextPanel();
            appendMessage('system', 'Tipo de instalación preferida:');
            renderOptions(['Empotrada', 'Superficie', 'No tengo preferencia'], false);
        } else if (conversationStep === 6) {
            const instalacion = userInputs.instalacion;
            contextData.instalacion = instalacion;
            updateContextPanel();
            appendMessage('system', 'Estilo de diseño preferido:');
            renderOptions(['Moderno/minimalista', 'Clásico/tradicional', 'No tengo preferencia'], false);
        } else if (conversationStep === 7) {
            const estilo = userInputs.estilo;
            contextData.estilo = estilo;
            updateContextPanel();
            appendMessage('system', 'Color preferido para los radiadores:');
            renderOptions(['Blanco', 'Negro', 'Cromo', 'No tengo preferencia'], false);
        } else if (conversationStep === 8) {
            calculateRadiatorLoad();
        }
    }
    
    // ========== FLUJO CALDERAS ==========
    else if (tipo === 'Calderas') {
        if (conversationStep === 2) {
            appendMessage('system', '¿Cuál es la carga térmica total de todos los ambientes a calefaccionar?');
            createNumberInput({ input_label: 'Carga térmica en kcal/h' });
        } else if (conversationStep === 3) {
            const cargaTermica = userInputs.carga_termica_total;
            contextData['Carga térmica total'] = cargaTermica + ' kcal/h';
            updateContextPanel();
            appendMessage('system', '¿Necesita agua caliente sanitaria (ACS)?');
            renderOptions(['Sí, necesito ACS', 'No, solo calefacción'], false);
        } else if (conversationStep === 4) {
            calculateBoilerLoad();
        }
    }
}

/* Calcular carga térmica */
function calculateHeatingLoad() {
    const superficie = parseFloat(userInputs.superficie);
    const zona = userInputs.zona;
    const aislacion = userInputs.aislacion;
    const tipo = userInputs.tipo;
    
    let factor = zona === 'Norte' ? 80 : zona === 'Centro' ? 100 : 125;
    if (aislacion === 'Mala') factor *= 1.2;
    if (aislacion === 'Buena') factor *= 0.9;
    
    const cargaTermica = Math.round(superficie * factor);
    const cargaTermicaKcal = Math.round(cargaTermica * 0.859845);
    contextData['Carga térmica'] = cargaTermica + ' W';
    updateContextPanel();
    
        appendMessage('system', `¡Perfecto! Analizando tu ambiente de <strong>${superficie}m²</strong> ubicado en la zona <strong>${zona}</strong> con aislación <strong>${aislacion.toLowerCase()}</strong>, veo que necesitas una potencia de calefacción de <strong>${cargaTermica}W</strong> (aproximadamente <strong>${cargaTermicaKcal} kcal/h</strong>).<br><br>Basado en estos datos, te voy a recomendar el mejor equipo para tu hogar:`);
    
    setTimeout(() => {
        showRecommendedProducts(tipo);
        renderOptions(['Nuevo cálculo', 'Hacer una pregunta'], false);
    }, 500);
}

/* Mostrar productos recomendados según el tipo y características */
function showRecommendedProducts(tipo) {
    // Usar el catálogo JSON cargado globalmente
    const catalogToUse = peisaProductsFromJSON || [];
    
    if (catalogToUse.length === 0) {
        console.error('❌ Catálogo de productos no cargado');
        return;
    }
    
    const cargaTermica = parseFloat(contextData['Carga térmica']) || 0;
    const cargaTermicaKcal = cargaTermica * 0.859845; // Convertir W a kcal/h
    const superficie = parseFloat(userInputs.superficie) || 0;
    const zona = userInputs.zona || 'Centro';
    const aislacion = userInputs.aislacion || 'Regular';
    
    console.log('🔍 Buscando producto para:', {
        tipo,
        cargaTermica: cargaTermica + 'W',
        cargaTermicaKcal: cargaTermicaKcal.toFixed(0) + ' kcal/h',
        superficie: superficie + 'm²',
        zona,
        aislacion
    });
    
    let recommendedProduct = null;
    
    // ========== RADIADORES ==========
    if (tipo.toLowerCase().includes('radiador')) {
        let radiadores = catalogToUse.filter(p => 
            p.family === 'Radiadores' && 
            p.category === 'Radiadores' &&
            !p.model.toLowerCase().includes('toallero')
        );
        
        // Para cargas pequeñas (<1500W): Radiadores eléctricos
        if (cargaTermica < 1500) {
            const electricos = radiadores.filter(p => 
                p.model.toLowerCase().includes('eléctrico') || 
                p.model.toLowerCase().includes('electrico')
            );
            
            if (electricos.length > 0) {
                // Priorizar Broen E (más popular y eficiente)
                recommendedProduct = electricos.find(p => p.model.includes('Broen E')) || electricos[0];
            }
        }
        // Para cargas medianas (1500-3000W): Radiadores de aluminio
        else if (cargaTermica < 3000) {
            const aluminio = radiadores.filter(p => 
                p.model.toLowerCase().includes('broen') ||
                p.model.toLowerCase().includes('tropical') ||
                p.description?.toLowerCase().includes('aluminio')
            );
            
            if (aluminio.length > 0) {
                // Priorizar Broen (mejor rendimiento)
                recommendedProduct = aluminio.find(p => p.model === 'Broen') || aluminio[0];
            }
        }
        // Para cargas altas (>3000W): Radiadores Broen Plus o Gamma
        else {
            const potentes = radiadores.filter(p => 
                p.model.toLowerCase().includes('broen plus') ||
                p.model.toLowerCase().includes('gamma')
            );
            
            if (potentes.length > 0) {
                recommendedProduct = potentes[0];
            }
        }
        
        // Fallback: cualquier radiador
        if (!recommendedProduct && radiadores.length > 0) {
            recommendedProduct = radiadores[0];
        }
    }
    
    // ========== CALDERAS ==========
    else if (tipo.toLowerCase().includes('caldera')) {
        let calderas = catalogToUse.filter(p => p.family === 'Calderas');
        
        // Para superficies pequeñas (<80m²): Calderas murales compactas
        if (superficie < 80) {
            const murales = calderas.filter(p => 
                p.category?.toLowerCase().includes('hogareña') ||
                p.type?.toLowerCase().includes('mural')
            );
            
            // Priorizar Diva DS (económica y eficiente para espacios pequeños)
            recommendedProduct = murales.find(p => p.model.includes('Diva DS')) || murales[0];
        }
        // Para superficies medianas (80-150m²): Calderas doble servicio
        else if (superficie < 150) {
            const dobleServicio = calderas.filter(p => 
                p.description?.toLowerCase().includes('doble servicio')
            );
            
            // Priorizar Prima Tec (mejor tecnología)
            recommendedProduct = dobleServicio.find(p => p.model.includes('Prima Tec')) || dobleServicio[0];
        }
        // Para superficies grandes (>150m²): Calderas de alta potencia
        else {
            const potentes = calderas.filter(p => 
                p.category?.toLowerCase().includes('central') ||
                p.model.toLowerCase().includes('magna') ||
                p.model.toLowerCase().includes('optima')
            );
            
            if (potentes.length > 0) {
                recommendedProduct = potentes[0];
            } else {
                // Fallback: Prima Tec Smart (la más potente de las murales)
                recommendedProduct = calderas.find(p => p.model.includes('Prima Tec Smart'));
            }
        }
        
        // Fallback: cualquier caldera
        if (!recommendedProduct && calderas.length > 0) {
            recommendedProduct = calderas[0];
        }
    }
    
    // ========== PISO RADIANTE ==========
    else if (tipo.toLowerCase().includes('piso')) {
        // Para piso radiante, necesitamos calderas doble servicio
        const calderas = catalogToUse.filter(p => 
            p.family === 'Calderas' && 
            p.description?.toLowerCase().includes('doble servicio')
        );
        
        // Según superficie y zona, elegir potencia adecuada
        if (superficie < 100) {
            // Para espacios pequeños: Diva Tecno o Diva DS
            recommendedProduct = calderas.find(p => 
                p.model.includes('Diva Tecno') || p.model.includes('Diva DS')
            ) || calderas[0];
        } else if (superficie < 200) {
            // Para espacios medianos: Prima Tec
            recommendedProduct = calderas.find(p => 
                p.model.includes('Prima Tec')
            ) || calderas[0];
        } else {
            // Para espacios grandes: Summa Condens (alta eficiencia)
            recommendedProduct = calderas.find(p => 
                p.model.includes('Summa Condens')
            ) || calderas.find(p => 
                p.model.includes('Prima Tec Smart')
            ) || calderas[0];
        }
        
        // Fallback: cualquier caldera doble servicio
        if (!recommendedProduct && calderas.length > 0) {
            recommendedProduct = calderas[0];
        }
    }
    
    // Si no se encontró producto específico, usar fallback genérico
    if (!recommendedProduct) {
        console.warn('⚠️ No se encontró producto específico, usando fallback');
        recommendedProduct = catalogToUse.find(p => 
            p.model.includes('Prima Tec Smart') || 
            p.model.includes('Radiador Eléctrico Broen E') ||
            p.model.includes('Diva')
        );
    }
    
    console.log('✅ Producto seleccionado:', recommendedProduct?.model || 'Ninguno');
    
    if (recommendedProduct) {
        // Guardar producto recomendado para contexto del chatbot
        lastRecommendedProduct = recommendedProduct;
        console.log('💾 Producto guardado para contexto:', lastRecommendedProduct.model);
        renderProducts([recommendedProduct]);
    } else {
        console.error('❌ No se encontraron productos para recomendar');
    }
}

/* Calcular carga térmica para radiadores */
function calculateRadiatorLoad() {
    const { largo, ancho, alto } = userInputs;
    const aislacion = userInputs.aislacion;
    const objetivo = userInputs.objetivo;
    const instalacion = userInputs.instalacion;
    const estilo = userInputs.estilo;
    const color = userInputs.color;
    
    // Calcular volumen del ambiente
    const volumen = largo * ancho * alto;
    
    // Factor según aislación (de peisa_advisor_knowledge_base.json)
    let factor = 40; // Media por defecto
    if (aislacion.includes('Baja')) factor = 50;
    if (aislacion.includes('Alta')) factor = 30;
    
    // Carga térmica en kcal/h
    const cargaTermica = Math.round(volumen * factor);
    contextData['Carga térmica'] = cargaTermica + ' kcal/h';
    updateContextPanel();
    
    const descripcionAislacion = aislacion.toLowerCase().includes('alta') ? 'buena aislación térmica' : 
                                aislacion.toLowerCase().includes('baja') ? 'aislación térmica básica' : 
                                'aislación térmica media';
    
        appendMessage('system', `¡Excelente! He analizado tu ambiente de <strong>${largo}m x ${ancho}m x ${alto}m</strong> (<strong>${volumen.toFixed(1)}m³</strong>) que cuenta con <strong>${descripcionAislacion}</strong>.<br><br>
        Para este espacio, necesitas una potencia de calefacción de <strong>${cargaTermica} kcal/h</strong>. ${objetivo.toLowerCase().includes('principal') ? 'Al ser calefacción principal, es importante elegir un radiador eficiente.' : 'Al ser calefacción complementaria, podemos optimizar la elección.'}<br><br>
        Basado en tus preferencias de instalación <strong>${instalacion.toLowerCase()}</strong>, estilo <strong>${estilo.toLowerCase()}</strong> y color <strong>${color.toLowerCase()}</strong>, te recomiendo:`);
    
    setTimeout(() => {
        showRecommendedProductsForRadiators(cargaTermica, objetivo, instalacion, estilo, color);
        renderOptions(['Nuevo cálculo', 'Hacer una pregunta'], false);
    }, 500);
}

/* Calcular carga térmica para calderas */
function calculateBoilerLoad() {
    const cargaTermicaTotal = parseFloat(userInputs.carga_termica_total);
    const necesitaACS = userInputs.agua_caliente;
    
    // Factor de seguridad del 20% (de peisa_advisor_knowledge_base.json)
    const factorSeguridad = 1.2;
    const potenciaRequerida = Math.round(cargaTermicaTotal * factorSeguridad);
    
    // Determinar tipo de caldera
    let tipoCaldera = 'Caldera mural';
    if (necesitaACS === 'Sí, necesito ACS') {
        tipoCaldera = 'Caldera doble servicio';
    }
    
    contextData['Potencia requerida'] = potenciaRequerida + ' kcal/h';
    contextData['Tipo caldera'] = tipoCaldera;
    updateContextPanel();
    
    const mensajeACS = necesitaACS === 'Sí, necesito ACS' ? 
        'Como necesitas agua caliente sanitaria, buscaremos una caldera de doble servicio que cubra ambas necesidades.' :
        'Como solo necesitas calefacción, podemos enfocarnos en una caldera optimizada para este uso.';
    
        appendMessage('system', `¡Muy bien! Analizando tus necesidades, veo que requieres una potencia base de <strong>${cargaTermicaTotal} kcal/h</strong>. Aplicando un factor de seguridad del 20% para garantizar un funcionamiento óptimo, necesitaremos una caldera de <strong>${potenciaRequerida} kcal/h</strong>.<br><br>
    ${mensajeACS}<br><br>
    Basado en estos requerimientos, te recomiendo:`);
    
    setTimeout(() => {
        showRecommendedProductsForBoilers(potenciaRequerida, necesitaACS);
        renderOptions(['Nuevo cálculo', 'Hacer una pregunta'], false);
    }, 500);
}

/* Recomendar productos para radiadores según preferencias */
function showRecommendedProductsForRadiators(cargaTermica, objetivo, instalacion, estilo, color) {
    const catalogToUse = peisaProductsFromJSON || [];
    
    console.log('🔍 Buscando radiador para:', {
        cargaTermica: cargaTermica + ' kcal/h',
        objetivo,
        instalacion,
        estilo,
        color
    });
    
    // Filtrar radiadores del catálogo
    let radiadores = catalogToUse.filter(p => 
        p.family === 'Radiadores' && 
        p.category === 'Radiadores' &&
        !p.model.toLowerCase().includes('toallero')
    );
    
    // Filtrar por preferencias del usuario
    let filtered = radiadores;
    
    // Filtrar por color si no es "cualquiera"
    if (color && !color.includes('preferencia')) {
        const colorLower = color.toLowerCase();
        filtered = filtered.filter(p => {
            const desc = (p.description || '').toLowerCase();
            const model = p.model.toLowerCase();
            return desc.includes(colorLower) || model.includes(colorLower) ||
                   (colorLower === 'blanco' && !desc.includes('negro'));
        });
    }
    
    // Filtrar por estilo si no es "cualquiera"
    if (estilo && !estilo.includes('preferencia')) {
        const estiloLower = estilo.toLowerCase();
        filtered = filtered.filter(p => {
            const desc = (p.description || '').toLowerCase();
            const model = p.model.toLowerCase();
            if (estiloLower.includes('moderno')) {
                return model.includes('broen') || desc.includes('moderno') || desc.includes('minimalista');
            } else if (estiloLower.includes('clasico')) {
                return model.includes('tropical') || desc.includes('clásico') || desc.includes('tradicional');
            }
            return true;
        });
    }
    
    // Si no quedan productos después del filtrado, usar todos los radiadores
    if (filtered.length === 0) {
        filtered = radiadores;
    }
    
    // Seleccionar según carga térmica
    let recommendedProduct = null;
    
    // Para cargas bajas (<1500 kcal/h): Radiadores eléctricos
    if (cargaTermica < 1500) {
        const electricos = filtered.filter(p => 
            p.model.toLowerCase().includes('eléctrico') || 
            p.model.toLowerCase().includes('electrico')
        );
        recommendedProduct = electricos.find(p => p.model.includes('Broen E')) || electricos[0];
    }
    // Para cargas medianas (1500-3000 kcal/h): Broen o Tropical
    else if (cargaTermica < 3000) {
        recommendedProduct = filtered.find(p => 
            p.model.includes('Broen') && !p.model.includes('Plus')
        ) || filtered.find(p => p.model.includes('Tropical')) || filtered[0];
    }
    // Para cargas altas (>3000 kcal/h): Broen Plus o Gamma
    else {
        recommendedProduct = filtered.find(p => 
            p.model.includes('Broen Plus')
        ) || filtered.find(p => p.model.includes('Gamma')) || filtered[0];
    }
    
    // Fallback: primer producto disponible
    if (!recommendedProduct && filtered.length > 0) {
        recommendedProduct = filtered[0];
    }
    
    console.log('✅ Radiador seleccionado:', recommendedProduct?.model || 'Ninguno');
    
    if (recommendedProduct) {
        // Guardar producto recomendado para contexto del chatbot
        lastRecommendedProduct = recommendedProduct;
        console.log('💾 Producto guardado para contexto:', lastRecommendedProduct.model);
        renderProducts([recommendedProduct]);
    } else {
        console.error('❌ No se encontraron radiadores para recomendar');
    }
}

/* Recomendar productos para calderas según potencia y ACS */
function showRecommendedProductsForBoilers(potenciaRequerida, necesitaACS) {
    const catalogToUse = peisaProductsFromJSON || [];
    
    console.log('🔍 Buscando caldera para:', {
        potenciaRequerida: potenciaRequerida + ' kcal/h',
        necesitaACS
    });
    
    // Filtrar calderas del catálogo
    let calderas = catalogToUse.filter(p => p.family === 'Calderas');
    
    let recommendedProduct = null;
    
    // Si necesita ACS, filtrar calderas doble servicio
    if (necesitaACS === 'Sí, necesito ACS') {
        const dobleServicio = calderas.filter(p => 
            p.description?.toLowerCase().includes('doble servicio')
        );
        
        // Según potencia requerida
        if (potenciaRequerida < 25000) {
            // Potencia baja: Diva DS
            recommendedProduct = dobleServicio.find(p => p.model.includes('Diva DS')) || dobleServicio[0];
        } else if (potenciaRequerida < 35000) {
            // Potencia media: Prima Tec o Diva Tecno
            recommendedProduct = dobleServicio.find(p => 
                p.model.includes('Prima Tec') || p.model.includes('Diva Tecno')
            ) || dobleServicio[0];
        } else {
            // Potencia alta: Prima Tec Smart o Summa Condens
            recommendedProduct = dobleServicio.find(p => 
                p.model.includes('Prima Tec Smart') || p.model.includes('Summa Condens')
            ) || dobleServicio[0];
        }
    } else {
        // Solo calefacción: calderas simples o de potencia
        const soloCalefaccion = calderas.filter(p => 
            p.model.includes('Diva C') || 
            p.category?.toLowerCase().includes('central') ||
            !p.description?.toLowerCase().includes('doble servicio')
        );
        
        if (potenciaRequerida < 30000) {
            recommendedProduct = soloCalefaccion.find(p => p.model.includes('Diva C')) || soloCalefaccion[0];
        } else if (potenciaRequerida < 100000) {
            recommendedProduct = soloCalefaccion.find(p => 
                p.model.includes('XP') || p.model.includes('CM')
            ) || soloCalefaccion[0];
        } else {
            // Alta potencia: calderas centrales
            recommendedProduct = soloCalefaccion.find(p => 
                p.model.includes('Magna') || p.model.includes('Modal') || p.model.includes('Optima')
            ) || soloCalefaccion[0];
        }
    }
    
    // Fallback: cualquier caldera
    if (!recommendedProduct && calderas.length > 0) {
        recommendedProduct = calderas[0];
    }
    
    console.log('✅ Caldera seleccionada:', recommendedProduct?.model || 'Ninguna');
    
    if (recommendedProduct) {
        // Guardar producto recomendado para contexto del chatbot
        lastRecommendedProduct = recommendedProduct;
        console.log('💾 Producto guardado para contexto:', lastRecommendedProduct.model);
        renderProducts([recommendedProduct]);
    } else {
        console.error('❌ No se encontraron calderas para recomendar');
    }
}

/* Mostrar recomendación de toallero */
function showTowelRackRecommendation() {
    const catalogToUse = peisaProductsFromJSON || [];
    
    // Filtrar toalleros del catálogo
    const toalleros = catalogToUse.filter(p => 
        p.category === 'Toalleros' || 
        p.model.toLowerCase().includes('toallero') ||
        p.model.toLowerCase().includes('scala') ||
        p.model.toLowerCase().includes('domino')
    );
    
    appendMessage('system', 'Para secado de toallas te recomendamos:');
    
    if (toalleros.length > 0) {
        // Priorizar Domino S (eléctrico, fácil instalación)
        const recommendedTowelRack = toalleros.find(p => p.model.includes('Domino S')) || toalleros[0];
        // Guardar producto recomendado para contexto del chatbot
        lastRecommendedProduct = recommendedTowelRack;
        console.log('💾 Producto guardado para contexto:', lastRecommendedProduct.model);
        renderProducts([recommendedTowelRack]);
    } else {
        console.error(' No se encontraron toalleros en el catálogo');
    }
    
    setTimeout(() => {
        renderOptions(['Nuevo cálculo', 'Hacer una pregunta'], false);
    }, 500);
}

/* Manejar respuestas del sistema experto */
function handleExpertSystemResponse(option) {
    const tipo = userInputs.tipo;
    
    // Paso 1: Tipo de calefacción
    if (conversationStep === 1) {
        userInputs.tipo = option;
        contextData.tipo = option;
    }
    // PISO RADIANTE
    else if (tipo === 'Piso radiante') {
        if (conversationStep === 3) {
            userInputs.zona = option;
        } else if (conversationStep === 4) {
            userInputs.aislacion = option;
        }
    }
    // RADIADORES
    else if (tipo === 'Radiadores') {
        if (conversationStep === 2) {
            userInputs.objetivo = option;
        } else if (conversationStep === 4) {
            userInputs.aislacion = option;
        } else if (conversationStep === 5) {
            userInputs.instalacion = option;
        } else if (conversationStep === 6) {
            userInputs.estilo = option;
        } else if (conversationStep === 7) {
            userInputs.color = option;
        }
    }
    // CALDERAS
    else if (tipo === 'Calderas') {
        if (conversationStep === 3) {
            userInputs.agua_caliente = option;
        }
    }
    
    setTimeout(() => askQuestion(), 500);
}

/* Crear input numérico */
function createNumberInput(response) {
    const inputArea = document.getElementById('input-area');
    inputArea.innerHTML = '';
    const form = document.createElement('form');
    const tipo = userInputs.tipo;
    
    form.onsubmit = (e) => {
        e.preventDefault();
        const value = document.getElementById('input-value').value;
        if (value && parseFloat(value) > 0) {
            // Para piso radiante
            if (tipo === 'Piso radiante') {
                userInputs.superficie = value;
                appendMessage('user', value + ' m²');
            }
            // Para calderas
            else if (tipo === 'Calderas') {
                userInputs.carga_termica_total = value;
                appendMessage('user', value + ' kcal/h');
            }
            setTimeout(() => askQuestion(), 500);
        }
    };
    form.innerHTML = `
        <div class="flex flex-col space-y-2">
            <input type="number" id="input-value" required step="0.1"
                class="border border-gray-300 rounded px-3 py-2" 
                placeholder="${response.input_label || 'Ej: 50'}">
            <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition">
                Enviar
            </button>
        </div>
    `;
    inputArea.appendChild(form);
    document.getElementById('input-value').focus();
}

/* Crear input de dimensiones (para radiadores) */
function createDimensionsInput() {
    const inputArea = document.getElementById('input-area');
    inputArea.innerHTML = '';
    const form = document.createElement('form');
    
    form.onsubmit = (e) => {
        e.preventDefault();
        const largo = parseFloat(document.getElementById('input-largo').value);
        const ancho = parseFloat(document.getElementById('input-ancho').value);
        const alto = parseFloat(document.getElementById('input-alto').value);
        
        if (largo > 0 && ancho > 0 && alto > 0) {
            userInputs.largo = largo;
            userInputs.ancho = ancho;
            userInputs.alto = alto;
            appendMessage('user', `${largo}m x ${ancho}m x ${alto}m`);
            setTimeout(() => askQuestion(), 500);
        }
    };
    
    form.innerHTML = `
        <div class="flex flex-col space-y-2">
            <div class="grid grid-cols-3 gap-2">
                <input type="number" id="input-largo" required step="0.1" min="0.1"
                    class="border border-gray-300 rounded px-3 py-2" 
                    placeholder="Largo (m)">
                <input type="number" id="input-ancho" required step="0.1" min="0.1"
                    class="border border-gray-300 rounded px-3 py-2" 
                    placeholder="Ancho (m)">
                <input type="number" id="input-alto" required step="0.1" min="0.1"
                    class="border border-gray-300 rounded px-3 py-2" 
                    placeholder="Alto (m)">
            </div>
            <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition">
                Enviar
            </button>
        </div>
    `;
    inputArea.appendChild(form);
    document.getElementById('input-largo').focus();
}

/* Resetear sistema experto */
function resetExpertSystem() {
    conversationStep = 0;
    userInputs = {};
    contextData = {};
    lastRecommendedProduct = null; // Resetear producto recomendado
    updateContextPanel();
}

/* Actualizar panel de contexto */
function updateContextPanel() {
    const panel = document.getElementById('context-panel');
    const itemsContainer = document.getElementById('context-items');
    
    if (Object.keys(contextData).length === 0) {
        panel.classList.add('hidden');
        return;
    }

    panel.classList.remove('hidden');
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
