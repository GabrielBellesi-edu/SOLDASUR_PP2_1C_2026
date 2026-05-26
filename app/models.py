# Base de datos de modelos de radiadores
RADIATOR_MODELS = {
    "TROPICAL 350": {
        "type": "principal",
        "installation": ["superficie"],
        "style": "clasico",
        "colors": ["blanco"],
        "coeficiente": 0.75,
        "potencia": 185,
        "description": "Radiador de aluminio inyectado, ideal para calefacción principal"
    },
    "TROPICAL 500": {
        "type": "principal",
        "installation": ["superficie"],
        "style": "clasico",
        "colors": ["blanco"],
        "coeficiente": 1.0,
        "potencia": 185,
        "description": "Radiador de aluminio inyectado, alto rendimiento"
    },
    "TROPICAL 600": {
        "type": "principal",
        "installation": ["superficie"],
        "style": "clasico",
        "colors": ["blanco"],
        "coeficiente": 1.16,
        "potencia": 185,
        "description": "Radiador de aluminio inyectado, máxima potencia"
    },
    "BROEN 350": {
        "type": ["principal", "complementaria"],
        "installation": ["superficie"],
        "style": "moderno",
        "colors": ["blanco", "negro"],
        "coeficiente": 0.75,
        "potencia": 185,
        "description": "Diseño discreto y moderno, disponible en dos colores"
    },
    "BROEN 500": {
        "type": ["principal", "complementaria"],
        "installation": ["superficie"],
        "style": "moderno",
        "colors": ["blanco", "negro"],
        "coeficiente": 1.0,
        "potencia": 185,
        "description": "Versión intermedia de la línea Broen"
    },
    "BROEN 600": {
        "type": ["principal", "complementaria"],
        "installation": ["superficie"],
        "style": "moderno",
        "colors": ["blanco", "negro"],
        "coeficiente": 1.16,
        "potencia": 185,
        "description": "Máxima potencia en la línea Broen clásica"
    },
    "BROEN PLUS 700": {
        "type": ["principal", "complementaria"],
        "installation": ["empotrada", "superficie"],
        "style": "moderno",
        "colors": ["blanco"],
        "coeficiente": 1.27,
        "potencia": 185,
        "description": "Emisores mixtos con gran versatilidad de instalación"
    },
    "BROEN PLUS 800": {
        "type": ["principal", "complementaria"],
        "installation": ["empotrada", "superficie"],
        "style": "moderno",
        "colors": ["blanco"],
        "coeficiente": 1.4,
        "potencia": 185,
        "description": "Alto rendimiento con diseño de líneas modernas"
    },
    "BROEN PLUS 1000": {
        "type": ["principal", "complementaria"],
        "installation": ["empotrada", "superficie"],
        "style": "moderno",
        "colors": ["blanco"],
        "coeficiente": 1.65,
        "potencia": 185,
        "description": "Máxima potencia en la línea Broen Plus"
    },
    "GAMMA 500": {
        "type": "complementaria",
        "installation": ["superficie"],
        "style": "moderno",
        "colors": ["blanco"],
        "coeficiente": 0.93,
        "potencia": 185,
        "description": "Radiador de aluminio con alma de acero, resistente a la corrosión"
    },
    "TOALLERO SCALA": {
        "type": "toallero",
        "installation": ["superficie"],
        "style": "moderno",
        "colors": ["blanco", "cromo"],
        "potencia": 632,
        "coeficiente": 1.0,  # Los toalleros no usan coeficiente, pero se mantiene para compatibilidad
        "description": "Especial para baños, mantiene toallas secas y calientes"
    }
}