import json
import math
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Rendimientos dict
WEBER_RENDIMIENTOS = {
    # Adhesivos
    "peg_classic": { "producto": "weber gris cerámicos", "rendimiento_kg_m2": 5.0, "descripcion": "Adhesivo cementicio para cerámicas en interiores y exteriores de absorción media/alta.", "tipo": "adhesivo" },
    "peg_flex": { "producto": "weber flex porcellanato", "rendimiento_kg_m2": 5.0, "descripcion": "Adhesivo cementicio impermeable especial para porcellanatos y piezas de baja absorción.", "tipo": "adhesivo" },
    "peg_psp": { "producto": "weber piso sobre piso 12hs", "rendimiento_kg_m2": 6.0, "descripcion": "Adhesivo de alta adherencia para colocar piso nuevo sobre cerámicas preexistentes sin picar.", "tipo": "adhesivo" },
    "peg_glass": { "producto": "weber glass", "rendimiento_kg_m2": 4.5, "descripcion": "Adhesivo especial para colocación de venecitas y placas de vidrio en piscinas y zonas húmedas.", "tipo": "adhesivo" },

    # Pastinas
    "pastina_classic": { "producto": "weber pastina classic", "densidad": 1.6, "descripcion": "Pastina cementicia impermeable para juntas finas de hasta 5 mm.", "tipo": "pastina" },
    "pastina_prestige": { "producto": "weber pastina prestige", "densidad": 1.65, "descripcion": "Pastina cementicia de alta performance y flexibilidad para juntas de 2 a 15 mm.", "tipo": "pastina" },
    "pastina_lista": { "producto": "weber pastina lista", "densidad": 1.5, "descripcion": "Pastina acrílica monocomponente lista para usar, ideal para juntas de 1 a 4 mm.", "tipo": "pastina" },
    "pastina_epoxi": { "producto": "weber pastina epoxi max", "densidad": 1.8, "descripcion": "Pastina epoxi bicomponente de máxima resistencia química, impermeable y antimanchas.", "tipo": "pastina" },

    # Nivelación
    "autonivelante": { "producto": "weber autonivela", "rendimiento_mm_m2": 1.6, "descripcion": "Mortero autonivelante para regularizar pisos interiores con secado ultra rápido.", "tipo": "nivelacion_mm" },
    "carpeta_tradicional": { "producto": "weber carpeta", "rendimiento_cm_m2": 20.0, "descripcion": "Mortero premezclado listo para hacer carpetas de cemento y regularizar bases.", "tipo": "nivelacion_cm" },
    "revoque_fino": { "producto": "weber fino", "rendimiento_kg_m2": 3.0, "descripcion": "Revoque fino a la cal para interiores o exteriores con excelente terminación.", "tipo": "fijo" },
    "revoque_monocapa": { "producto": "weber monocapa prisma", "rendimiento_cm_m2": 15.0, "descripcion": "Revoque monocapa exterior que realiza grueso, fino e impermeabilización en un solo paso.", "tipo": "nivelacion_cm" },

    # Impermeabilización
    "imp_techos": { "producto": "weberdry techos con poliuretano", "rendimiento_kg_m2": 1.5, "descripcion": "Membrana líquida impermeable de alta elasticidad para terrazas y techos.", "tipo": "fijo" },
    "imp_frentes": { "producto": "weberdry frentes y muros", "rendimiento_kg_m2": 0.8, "descripcion": "Membrana impermeable de alta elasticidad para fachadas y paredes exteriores.", "tipo": "fijo" },
    "imp_ceresita": { "producto": "webertec ceresita", "rendimiento_kg_m2": 1.5, "descripcion": "Aditivo hidrófugo en pasta para aislar cimientos, sótanos y revoques gruesos.", "tipo": "fijo" },
    "imp_piscinas": { "producto": "weber piscinas", "rendimiento_kg_m2": 2.5, "descripcion": "Mortero impermeable flexible bicomponente para piscinas, cisternas y aljibes.", "tipo": "fijo" },
    "imp_banio": { "producto": "weber impermeable cerámicos con ceresita", "rendimiento_kg_m2": 1.5, "descripcion": "Adhesivo cementicio impermeable para colocación en baños y cocinas.", "tipo": "fijo" },

    # Pisos Decorativos
    "microcemento_base": { "producto": "weber microbase", "rendimiento_kg_m2": 2.0, "producto_aux": "weber emulsión", "factor_aux": 1 / 3, "descripcion": "Base cementicia niveladora para sistema micropiso decorativo.", "tipo": "bicomponente" },
    "microcemento_color": { "producto": "weber microcolor", "rendimiento_kg_m2": 1.0, "producto_aux": "weber emulsión", "factor_aux": 1 / 2, "descripcion": "Terminación cementicia de color para micropiso decorativo de capa fina.", "tipo": "bicomponente" },

    # Revestimientos Plásticos (weberplast)
    "weberplast_fino": { "producto": "weberplast llaneado", "rendimiento_kg_m2": 1.6, "descripcion": "Revestimiento plástico texturado decorativo, acabado fino.", "tipo": "texturado" },
    "weberplast_medio": { "producto": "weberplast rulato travertino medio", "rendimiento_kg_m2": 2.2, "descripcion": "Revestimiento plástico texturado decorativo, acabado medio (Rulato).", "tipo": "texturado" },
    "weberplast_grueso": { "producto": "weberplast rulato travertino grueso", "rendimiento_kg_m2": 3.2, "descripcion": "Revestimiento plástico texturado decorativo, acabado rústico grueso.", "tipo": "texturado" }
}

class WeberExpertEngine:
    def __init__(self, knowledge_base_path: str = "app/advisor_knowledge_base_weber.json"):
        self.knowledge_base = []
        
        # Sistema inteligente para encontrar tu JSON sin importar desde dónde prendas el servidor
        base_dir = Path(__file__).resolve().parent.parent.parent # Sube a la raíz del proyecto
        posibles_rutas = [
            Path(knowledge_base_path),
            base_dir / "app" / "advisor_knowledge_base_weber.json",
            base_dir / "advisor_knowledge_base_weber.json"
        ]
        
        archivo_encontrado = None
        for ruta in posibles_rutas:
            if ruta.exists():
                archivo_encontrado = ruta
                break
                
        if archivo_encontrado:
            print(f"[OK] [Weber Expert] JSON cargado exitosamente desde: {archivo_encontrado}")
            with open(archivo_encontrado, "r", encoding="utf-8") as f:
                self.knowledge_base = json.load(f)
        else:
            print("[ERROR] [Weber Expert] ERROR: No se encontró el archivo JSON.")
            self.knowledge_base = [{
                "id": "inicio_weber", 
                "tipo": "respuesta", 
                "texto": "⚠️ Error interno: El servidor no encuentra el archivo advisor_knowledge_base_weber.json."
            }]

    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        for node in self.knowledge_base:
            if node.get("id") == node_id:
                return node
        return None

    def resolver_calculo(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determina el producto correcto basándose en las reglas del soporte
        y calcula las cantidades necesarias de forma exacta.
        """
        soporte = context.get("soporte_obra")
        m2 = float(context.get("metros_cuadrados", 0))

        config = WEBER_RENDIMIENTOS.get(soporte)
        if not config:
            return {}

        kg_necesarios = 0.0
        kg_con_desperdicio = 0.0
        unidades_necesarias = 0
        peso_envase = 25
        unidad_comercial = "bolsas"
        detalle_extra = ""

        desperdicio_factor = 1.10  # 10% desperdicio técnico

        tipo = config.get("tipo")
        producto = config.get("producto")

        if tipo == "adhesivo":
            rendimiento = config.get("rendimiento_kg_m2", 5.0)
            if context.get("doble_encolado") == "si":
                rendimiento *= 1.5
                detalle_extra = "• Incluye un incremento del 50% por técnica de doble encolado (piezas > 30 cm).\n"
            kg_necesarios = m2 * rendimiento
            kg_con_desperdicio = kg_necesarios * desperdicio_factor
            peso_envase = 25
            unidades_necesarias = math.ceil(kg_con_desperdicio / peso_envase)
            unidad_comercial = "bolsas"

        elif tipo == "pastina":
            largo = float(context.get("pastina_largo", 0))
            ancho = float(context.get("pastina_ancho", 0))
            espesor = float(context.get("pastina_espesor", 0))
            junta = float(context.get("pastina_junta", 0))

            largo_mm = largo * 10
            ancho_mm = ancho * 10
            densidad = config.get("densidad", 1.6)

            if largo_mm > 0 and ancho_mm > 0:
                rendimiento_kg_m2 = ((largo_mm + ancho_mm) * espesor * junta * densidad) / (largo_mm * ancho_mm)
            else:
                rendimiento_kg_m2 = 0.0

            kg_necesarios = m2 * rendimiento_kg_m2
            kg_con_desperdicio = kg_necesarios * desperdicio_factor

            if soporte == "pastina_lista":
                peso_envase = 1
                unidad_comercial = "baldes"
            elif soporte == "pastina_epoxi":
                peso_envase = 3
                unidad_comercial = "kits"
            else:
                peso_envase = 5
                unidad_comercial = "bolsas"
            unidades_necesarias = math.ceil(kg_con_desperdicio / peso_envase)
            detalle_extra = (
                f"• *Juntas de {junta} mm en piezas de {largo}x{ancho} cm (espesor {espesor} mm).*\n"
                f"• Rendimiento calculado: {rendimiento_kg_m2:.3f} kg/m².\n"
            )

        elif tipo == "nivelacion_mm":
            espesor = float(context.get("espesor_medida", 0))
            kg_necesarios = m2 * config.get("rendimiento_mm_m2", 1.6) * espesor
            kg_con_desperdicio = kg_necesarios * desperdicio_factor
            peso_envase = 25
            unidades_necesarias = math.ceil(kg_con_desperdicio / peso_envase)
            unidad_comercial = "bolsas"
            detalle_extra = f"• *Espesor promedio de nivelación: {espesor} mm.*\n"

        elif tipo == "nivelacion_cm":
            espesor = float(context.get("espesor_medida", 0))
            kg_necesarios = m2 * config.get("rendimiento_cm_m2", 20.0) * espesor
            kg_con_desperdicio = kg_necesarios * desperdicio_factor
            peso_envase = 25
            unidades_necesarias = math.ceil(kg_con_desperdicio / peso_envase)
            unidad_comercial = "bolsas"
            detalle_extra = f"• *Espesor promedio de capa: {espesor} cm.*\n"

        elif tipo == "fijo":
            kg_necesarios = m2 * config.get("rendimiento_kg_m2", 1.5)
            kg_con_desperdicio = kg_necesarios * desperdicio_factor

            if soporte.startswith("imp_techos") or soporte.startswith("imp_frentes"):
                peso_envase = 20
                unidad_comercial = "baldes"
            else:
                peso_envase = 25
                unidad_comercial = "bolsas"
            unidades_necesarias = math.ceil(kg_con_desperdicio / peso_envase)

        elif tipo == "texturado":
            kg_necesarios = m2 * config.get("rendimiento_kg_m2", 1.6)
            kg_con_desperdicio = kg_necesarios * desperdicio_factor
            peso_envase = 30
            unidades_necesarias = math.ceil(kg_con_desperdicio / peso_envase)
            unidad_comercial = "baldes"

        elif tipo == "bicomponente":
            kg_necesarios = m2 * config.get("rendimiento_kg_m2", 2.0)
            kg_con_desperdicio = kg_necesarios * desperdicio_factor
            peso_envase = 25
            unidades_necesarias = math.ceil(kg_con_desperdicio / peso_envase)
            unidad_comercial = "bolsas"

            litros_emulsion = kg_con_desperdicio * config.get("factor_aux", 0.33)
            envases_emulsion = math.ceil(litros_emulsion / 10)

            detalle_extra = f"• **{config.get('producto_aux')}** necesario: {litros_emulsion:.1f} L ({envases_emulsion} baldes de 10 L).\n"

        return {
            "producto": producto,
            "descripcion": config.get("descripcion", ""),
            "unidades": unidades_necesarias,
            "unidadComercial": unidad_comercial,
            "pesoEnvase": peso_envase,
            "kg_totales": round(kg_con_desperdicio, 1),
            "detalleExtra": detalle_extra
        }

    async def process(self, conversation_id: str, expert_state: Dict[str, Any],
                      option_index: Optional[int] = None,
                      input_values: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa la interacción del usuario en el flujo experto para Weber de forma genérica.
        """
        current_node_id = expert_state.get('current_node', 'inicio_weber')
        context = expert_state.get('variables', {})
        
        node = self.get_node_by_id(current_node_id)
        if not node:
            return {'error': 'Nodo no encontrado', 'node_id': current_node_id}
            
        # 1. Procesar entrada del usuario si existe
        if option_index is not None or input_values:
            if "opciones" in node and option_index is not None:
                if 0 <= option_index < len(node["opciones"]):
                    selected_option = node["opciones"][option_index]
                    siguiente_nodo_id = selected_option["siguiente"]
                    var_name = node.get("variable", node["id"])
                    context[var_name] = selected_option.get("valor", selected_option["texto"])
                    context[f"{var_name}_texto"] = selected_option["texto"]
                else:
                    return {'error': 'Opción inválida', 'node_id': node['id']}
            elif "siguiente" in node:
                siguiente_nodo_id = node["siguiente"]
                if "variable" in node:
                    var_name = node["variable"]
                    val = 0
                    if input_values:
                        val = input_values.get(var_name, input_values.get("value", 0))
                    try:
                        context[var_name] = float(str(val).replace(",", "."))
                    except ValueError:
                        context[var_name] = 0.0
            else:
                siguiente_nodo_id = current_node_id
                
            expert_state["current_node"] = siguiente_nodo_id
            node = self.get_node_by_id(siguiente_nodo_id)
            
        # 2. Si el nodo actual es de tipo "calculo", resolver cálculo
        if node and node.get("tipo") == "calculo":
            calculo_res = self.resolver_calculo(context)
            context["resultado"] = calculo_res
            siguiente_nodo_id = node["siguiente"]
            expert_state["current_node"] = siguiente_nodo_id
            node = self.get_node_by_id(siguiente_nodo_id)
            
        # 3. Si es el nodo final
        if node and node["id"] == "resultado_final_weber":
            res = context.get("resultado", {})
            texto_salida = (
                f"Resultado del Asesoramiento Weber\n\n"
                f"Para cubrir {context.get('metros_cuadrados')} m² sobre el soporte seleccionado, "
                f"te recomendamos utilizar {res.get('producto', '').upper()}.\n\n"
                f"• Cantidad necesaria: {res.get('unidades')} {res.get('unidadComercial')} de {res.get('pesoEnvase')} kg/L.\n"
                f"• Rendimiento estimado: {res.get('kg_totales')} kg/L (+10% desperdicio técnico).\n"
                f"{res.get('detalleExtra', '')}"
            )
            return {
                "conversation_id": conversation_id,
                "node_id": "final",
                "type": "respuesta",
                "text": texto_salida,
                "is_final": True,
                "variables": context,
                "calculo": res
            }
            
        # 4. Retornar mensaje para el nodo actual
        response = {
            "conversation_id": conversation_id,
            "node_id": node["id"],
            "type": "question" if "opciones" in node or node.get("tipo") == "entrada_usuario" else "response",
            "text": node.get("pregunta", node.get("texto", "")),
            "variables": context
        }
        
        if "opciones" in node:
            response["options"] = [opt["texto"] for opt in node["opciones"]]
        elif node.get("tipo") == "entrada_usuario":
            response["input_type"] = "number"
            response["input_label"] = node.get("pregunta", "Ingrese el valor")
            response["placeholder"] = node.get("placeholder", "Ej: 10")
            
        return response