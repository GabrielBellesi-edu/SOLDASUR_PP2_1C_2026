import json
import math
import os
from pathlib import Path
from typing import Dict, Any, Optional

class WeberExpertEngine:
    def __init__(self, knowledge_base_path: str = "app/weber_advisor_knowledge_base.json"):
        self.knowledge_base = []
        
        # Sistema inteligente para encontrar tu JSON sin importar desde dónde prendas el servidor
        base_dir = Path(__file__).resolve().parent.parent.parent # Sube a la raíz del proyecto
        posibles_rutas = [
            Path(knowledge_base_path),
            base_dir / "app" / "weber_advisor_knowledge_base.json",
            base_dir / "weber_advisor_knowledge_base.json"
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

            # Nodo de emergencia para evitar que FastAPI crashee
            self.knowledge_base = [{
                "id": "inicio_weber", 
                "tipo": "respuesta", 
                "texto": "⚠️ Error interno: El servidor no encuentra el archivo weber_advisor_knowledge_base.json. Por favor, verificá que esté en la carpeta 'app/'."
            }]

    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        for node in self.knowledge_base:
            if node.get("id") == node_id:
                return node
        return None

    def resolver_calculo(self, soporte: str, m2: float) -> Dict[str, Any]:
        """
        Determina el producto correcto basándose en las reglas del soporte
        y calcula las cantidades necesarias de forma exacta.
        """
        if soporte == "tradicional":
            producto_modelo = "weber col mortero"
            rendimiento = 5.0
        elif soporte == "yeso":
            producto_modelo = "weber col pasta"
            rendimiento = 3.5
        elif soporte == "piso_sobre_piso":
            producto_modelo = "weber col piso sobre piso"
            rendimiento = 6.0
        else:
            producto_modelo = "weber basic cerámicos"
            rendimiento = 5.0

        peso_bolsa = 25.0
        kg_necesarios = m2 * rendimiento
        kg_con_desperdicio = kg_necesarios * 1.10
        bolsas_finales = math.ceil(kg_con_desperdicio / peso_bolsa)

        return {
            "producto": producto_modelo,
            "rendimiento_kg_m2": rendimiento,
            "bolsas_necesarias": bolsas_finales,
            "kg_totales": round(kg_con_desperdicio, 1)
        }