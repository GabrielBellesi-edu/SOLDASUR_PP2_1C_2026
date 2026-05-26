"""
product_loader.py - Cargador dinámico de productos desde Excel

Este módulo carga la base de conocimiento de productos desde Products_db.xlsx
y la convierte en estructuras utilizables por el sistema experto.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import json


class ProductLoader:
    """Carga y procesa productos desde el archivo Excel"""
    
    def __init__(self, excel_path: str = "data/raw/Products_db.xlsx"):
        """
        Inicializa el cargador de productos.
        
        Args:
            excel_path: Ruta al archivo Excel con los productos
        """
        self.excel_path = Path(excel_path)
        self.products_df = None
        self.radiators = {}
        self.boilers = {}
        self.floor_heating = {}
        
        if self.excel_path.exists():
            self.load_products()
        else:
            print(f"Advertencia: No se encontró {excel_path}")
    
    def load_products(self) -> None:
        """Carga los productos desde el archivo Excel"""
        try:
            self.products_df = pd.read_excel(self.excel_path)
            print(f"Cargados {len(self.products_df)} productos desde {self.excel_path}")
            
            # Procesar productos por categoría
            self._process_radiators()
            self._process_boilers()
            self._process_floor_heating()
            
        except Exception as e:
            print(f"Error cargando productos: {e}")
            # Intentar cargar desde CSV procesado como fallback
            self._load_from_csv_fallback()
    
    def _load_from_csv_fallback(self) -> None:
        """Carga productos desde CSV procesado como fallback"""
        try:
            csv_path = Path("data/processed/products_mock.csv")
            if csv_path.exists():
                self.products_df = pd.read_csv(csv_path)
                print(f"Cargados {len(self.products_df)} productos desde CSV fallback")
                self._process_radiators()
                self._process_boilers()
                self._process_floor_heating()
        except Exception as e:
            print(f"Error en fallback CSV: {e}")
    
    def _process_radiators(self) -> None:
        """Procesa radiadores del catálogo"""
        if self.products_df is None:
            return
        
        radiators_df = self.products_df[self.products_df['type'] == 'Radiador']
        
        for _, row in radiators_df.iterrows():
            model_name = f"{row['family']} {row['model']}"
            
            # Determinar características del radiador
            installation_type = self._determine_installation_type(row)
            style = self._determine_style(row)
            colors = self._determine_colors(row)
            
            self.radiators[model_name] = {
                'name': model_name,
                'family': row['family'],
                'model': row['model'],
                'description': row.get('description', ''),
                'power_w': float(row.get('power_w', 0)),
                'potencia': self._watts_to_kcal(float(row.get('power_w', 0))),
                'coeficiente': self._calculate_coefficient(row),
                'dimensions': row.get('dimentions', ''),
                'installation': installation_type,
                'style': style,
                'colors': colors,
                'type': 'principal',  # Por defecto
                'liters': float(row.get('liters', 0)),
                'max_pressure_bar': float(row.get('max_pressure_bar', 0))
            }
    
    def _process_boilers(self) -> None:
        """Procesa calderas del catálogo"""
        if self.products_df is None:
            return
        
        boilers_df = self.products_df[self.products_df['type'] == 'Caldera']
        
        for _, row in boilers_df.iterrows():
            model_name = f"{row['family']} {row['model']}"
            
            self.boilers[model_name] = {
                'name': model_name,
                'family': row['family'],
                'model': row['model'],
                'description': row.get('description', ''),
                'power_w': float(row.get('power_w', 0)),
                'potencia_kcal': self._watts_to_kcal(float(row.get('power_w', 0))),
                'dimensions': row.get('dimentions', ''),
                'liters': float(row.get('liters', 0)),
                'max_pressure_bar': float(row.get('max_pressure_bar', 0)),
                'type': 'mural' if 'mural' in str(row.get('description', '')).lower() else 'piso'
            }
    
    def _process_floor_heating(self) -> None:
        """Procesa sistemas de piso radiante del catálogo"""
        if self.products_df is None:
            return
        
        floor_df = self.products_df[self.products_df['type'] == 'Piso Radiante']
        
        for _, row in floor_df.iterrows():
            model_name = f"{row['family']} {row['model']}"
            
            self.floor_heating[model_name] = {
                'name': model_name,
                'family': row['family'],
                'model': row['model'],
                'description': row.get('description', ''),
                'dimensions': row.get('dimentions', ''),
                'surface_m2': self._extract_surface(row)
            }
    
    def _determine_installation_type(self, row: pd.Series) -> str:
        """Determina el tipo de instalación del radiador"""
        desc = str(row.get('description', '')).lower()
        model = str(row.get('model', '')).lower()
        
        if 'empotrado' in desc or 'empotrado' in model:
            return 'empotrada'
        elif 'superficie' in desc or 'superficie' in model:
            return 'superficie'
        else:
            # Por defecto, los radiadores son de superficie
            return ['empotrada', 'superficie']
    
    def _determine_style(self, row: pd.Series) -> str:
        """Determina el estilo del radiador"""
        desc = str(row.get('description', '')).lower()
        model = str(row.get('model', '')).lower()
        
        if 'minimalista' in desc or 'moderno' in desc:
            return 'moderno'
        elif 'clásico' in desc or 'tradicional' in desc:
            return 'clasico'
        else:
            return 'moderno'  # Por defecto
    
    def _determine_colors(self, row: pd.Series) -> List[str]:
        """Determina los colores disponibles del radiador"""
        desc = str(row.get('description', '')).lower()
        colors = []
        
        if 'blanco' in desc:
            colors.append('blanco')
        if 'negro' in desc:
            colors.append('negro')
        if 'cromo' in desc:
            colors.append('cromo')
        
        # Si no se especifica, asumir blanco por defecto
        if not colors:
            colors = ['blanco', 'negro', 'cromo']
        
        return colors
    
    def _calculate_coefficient(self, row: pd.Series) -> float:
        """Calcula el coeficiente del radiador basado en su modelo"""
        model = str(row.get('model', '')).upper()
        
        # Extraer número del modelo (ej: "350" de "350 Inyectado")
        import re
        match = re.search(r'(\d+)', model)
        if match:
            size = int(match.group(1))
            # Coeficientes aproximados basados en tamaño
            if size <= 350:
                return 0.75
            elif size <= 500:
                return 1.0
            elif size <= 600:
                return 1.16
            elif size <= 700:
                return 1.27
            elif size <= 800:
                return 1.4
            elif size <= 1000:
                return 1.65
            else:
                return 2.0
        
        return 1.0  # Por defecto
    
    def _watts_to_kcal(self, watts: float) -> float:
        """Convierte Watts a kcal/h"""
        return watts * 0.859845  # 1W = 0.859845 kcal/h
    
    def _extract_surface(self, row: pd.Series) -> float:
        """Extrae la superficie en m² del nombre del producto"""
        model = str(row.get('model', ''))
        import re
        match = re.search(r'(\d+)\s*m²', model)
        if match:
            return float(match.group(1))
        return 0.0
    
    def get_radiators_dict(self) -> Dict[str, Dict[str, Any]]:
        """Retorna diccionario de radiadores para RADIATOR_MODELS"""
        return self.radiators
    
    def get_boilers_list(self) -> List[Dict[str, Any]]:
        """Retorna lista de calderas"""
        return list(self.boilers.values())
    
    def get_floor_heating_list(self) -> List[Dict[str, Any]]:
        """Retorna lista de sistemas de piso radiante"""
        return list(self.floor_heating.values())
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """Retorna todos los productos como lista"""
        all_products = []
        all_products.extend(self.radiators.values())
        all_products.extend(self.boilers.values())
        all_products.extend(self.floor_heating.values())
        return all_products
    
    def filter_radiators_by_criteria(self, radiator_type: str, installation: str, 
                                     style: str, color: str, heat_load: float) -> List[Dict[str, Any]]:
        """
        Filtra radiadores según criterios específicos.
        
        Args:
            radiator_type: Tipo de radiador
            installation: Tipo de instalación
            style: Estilo del radiador
            color: Color preferido
            heat_load: Carga térmica requerida en kcal/h
            
        Returns:
            Lista de radiadores que cumplen los criterios
        """
        recommended = []
        
        for name, model in self.radiators.items():
            # Filtrar por tipo de instalación
            if installation != 'cualquiera':
                if isinstance(model['installation'], str):
                    if model['installation'] != installation:
                        continue
                elif installation not in model['installation']:
                    continue
            
            # Filtrar por estilo
            if style != 'cualquiera' and model['style'] != style:
                continue
            
            # Filtrar por color
            if color != 'cualquiera' and color not in model['colors']:
                continue
            
            recommended.append(model)
        
        # Ordenar por mejor ajuste a la carga térmica
        recommended.sort(key=lambda x: abs(x['potencia'] * x['coeficiente'] - heat_load))
        
        return recommended[:5]  # Top 5 recomendaciones
    
    def find_boiler_by_power(self, power_required_kcal: float, 
                            boiler_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Encuentra la caldera más adecuada según la potencia requerida.
        
        Args:
            power_required_kcal: Potencia requerida en kcal/h
            boiler_type: Tipo de caldera ('mural' o 'piso'), opcional
            
        Returns:
            Caldera recomendada o None
        """
        boilers = list(self.boilers.values())
        
        # Filtrar por tipo si se especifica
        if boiler_type:
            boilers = [b for b in boilers if b['type'] == boiler_type]
        
        if not boilers:
            return None
        
        # Encontrar la caldera con potencia más cercana (pero suficiente)
        suitable = [b for b in boilers if b['potencia_kcal'] >= power_required_kcal]
        
        if suitable:
            return min(suitable, key=lambda x: x['potencia_kcal'])
        else:
            # Si ninguna cumple, retornar la de mayor potencia
            return max(boilers, key=lambda x: x['potencia_kcal'])
    
    def export_to_json(self, output_path: str = "data/processed/products_catalog.json") -> None:
        """Exporta el catálogo procesado a JSON"""
        catalog = {
            'radiators': self.radiators,
            'boilers': self.boilers,
            'floor_heating': self.floor_heating
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        
        print(f"Catálogo exportado a {output_path}")


# Instancia global del cargador
_product_loader = None

def get_product_loader() -> ProductLoader:
    """Obtiene la instancia global del cargador de productos"""
    global _product_loader
    if _product_loader is None:
        _product_loader = ProductLoader()
    return _product_loader


# Funciones de conveniencia para compatibilidad con código existente
def load_radiator_models() -> Dict[str, Dict[str, Any]]:
    """Carga modelos de radiadores desde Excel"""
    loader = get_product_loader()
    return loader.get_radiators_dict()


def load_product_catalog() -> List[Dict[str, Any]]:
    """Carga catálogo completo de productos"""
    loader = get_product_loader()
    return loader.get_all_products()
