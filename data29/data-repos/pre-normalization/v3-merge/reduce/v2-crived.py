#!/usr/bin/env python3
"""
Chapter Balanced Selector - PERFECT VERSION

Algoritmo EXACTO como lo describiste:
1. Por capítulo: procesar datasets del más minoritario al más abundante
2. Cada dataset intenta coger 10, si no puede → transmite deuda al siguiente
3. Descarte: ordenar ICD-10 alfabéticamente (0→Z) y seleccionar equidistantes

Optimización ICD-10:
- Ordenar códigos alfabéticamente: A00.0, A00.1, ..., Z99.9
- Dividir en segmentos equidistantes: Z/target_count
- Seleccionar códigos más cercanos a esos puntos mediales
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime
import statistics

# Añadir utils al path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
utils_path = os.path.join(project_root, 'utils')
sys.path.insert(0, utils_path)

from icd10.taxonomy import ICD10Taxonomy


class PerfectChapterSelector:
    """Selector PERFECTO con algoritmo exacto de deudas y descarte ICD-10."""
    
    def __init__(self, input_file="v1-uniques.json"):
        self.input_file = input_file
        self.taxonomy = ICD10Taxonomy()
        self.cases = []
        self.datasets = set()
        self.cases_by_chapter_dataset = defaultdict(lambda: defaultdict(list))
        
        print("🎯 Perfect Chapter Selector - Algoritmo Exacto")
    
    def load_cases(self):
        """Carga casos."""
        print(f"📂 Cargando {self.input_file}...")
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            self.cases = json.load(f)
        
        print(f"✅ Cargados {len(self.cases)} casos únicos")
    
    def get_icd10_chapter(self, icd10_code):
        """Obtiene capítulo ICD-10."""
        if not icd10_code:
            return None
        
        try:
            hierarchy = self.taxonomy.hierarchy(icd10_code)
            if hierarchy and 'parents' in hierarchy and 'chapter' in hierarchy['parents']:
                return hierarchy['parents']['chapter']['code']
        except:
            pass
        
        # Fallback manual
        first_letter = icd10_code[0].upper()
        three_char = icd10_code[:3].upper()
        
        mapping = {
            'A': 'I', 'B': 'I', 'C': 'II',
            'D': 'II' if three_char <= 'D48' else 'III',
            'E': 'IV', 'F': 'V', 'G': 'VI',
            'H': 'VII' if three_char <= 'H59' else 'VIII',
            'I': 'IX', 'J': 'X', 'K': 'XI', 'L': 'XII',
            'M': 'XIII', 'N': 'XIV', 'O': 'XV', 'P': 'XVI',
            'Q': 'XVII', 'R': 'XVIII', 'S': 'XIX', 'T': 'XIX',
            'V': 'XX', 'W': 'XX', 'X': 'XX', 'Y': 'XX',
            'Z': 'XXI', 'U': 'XXII'
        }
        return mapping.get(first_letter)
    
    def organize_by_chapters(self):
        """Organiza casos por capítulo y dataset."""
        print("🗂️ Organizando por capítulos...")
        
        for case in self.cases:
            dataset = case.get('dataset', 'unknown')
            self.datasets.add(dataset)
            
            # Obtener capítulos de este caso
            case_chapters = set()
            for diagnosis in case.get('diagnoses', []):
                icd10_code = diagnosis.get('icd10', '')
                if icd10_code:
                    chapter = self.get_icd10_chapter(icd10_code)
                    if chapter:
                        case_chapters.add(chapter)
            
            # CRÍTICO: Asignar caso SOLO al primer capítulo alfabéticamente
            # Esto evita duplicados entre capítulos
            if case_chapters:
                primary_chapter = sorted(case_chapters)[0]  # Primer capítulo alfabéticamente
                self.cases_by_chapter_dataset[primary_chapter][dataset].append(case)
                
                # Log para debugging
                if len(case_chapters) > 1:
                    other_chapters = sorted(case_chapters)[1:]
                    print(f"   📝 Caso {case.get('id', 'N/A')}: asignado a {primary_chapter}, ignorando {other_chapters}")
        
        print(f"📊 {len(self.datasets)} datasets: {sorted(self.datasets)}")
        print(f"📋 {len(self.cases_by_chapter_dataset)} capítulos con casos")
    
    def get_case_primary_icd10(self, case):
        """Obtiene el código ICD-10 primario de un caso para ordenamiento."""
        icd10_codes = []
        
        for diagnosis in case.get('diagnoses', []):
            icd10_code = diagnosis.get('icd10', '')
            if icd10_code:
                icd10_codes.append(icd10_code)
        
        # Devolver el primer código (alfabéticamente) como primario
        return min(icd10_codes) if icd10_codes else 'ZZZ999'
    
    def calculate_case_average_severity(self, case):
        """Calcula severidad promedio de un caso."""
        severities = []
        
        for diagnosis in case.get('diagnoses', []):
            severity = diagnosis.get('severity', 'S1')
            if severity.startswith('S'):
                try:
                    severities.append(int(severity[1:]))
                except:
                    severities.append(1)
        
        return statistics.mean(severities) if severities else 1
    
    def select_equidistant_cases(self, available_cases, target_count):
        """
        Selecciona casos usando algoritmo de equidistancia ICD-10.
        
        Algoritmo:
        1. Ordenar casos por ICD-10 alfabéticamente (A00.0 → Z99.9)
        2. Dividir en segmentos: Z/target_count  
        3. Seleccionar casos más cercanos a puntos mediales
        4. Considerar severidad como criterio de desempate
        """
        if not available_cases:
            return []
        
        if len(available_cases) <= target_count:
            return available_cases
        
        print(f"     🎯 Seleccionando {target_count} de {len(available_cases)} usando equidistancia ICD-10")
        
        # 1. Ordenar casos por código ICD-10 primario (alfabéticamente)
        sorted_cases = sorted(available_cases, key=self.get_case_primary_icd10)
        
        # 2. Calcular puntos de segmentación equidistantes
        total_cases = len(sorted_cases)
        segment_size = total_cases / target_count
        
        selected_cases = []
        
        # 3. Para cada segmento, seleccionar el caso más cercano al punto medio
        for i in range(target_count):
            # Punto medio del segmento i
            target_position = (i + 0.5) * segment_size
            target_index = int(round(target_position))
            
            # Asegurar que el índice esté en rango válido
            target_index = max(0, min(target_index, total_cases - 1))
            
            # Seleccionar caso en esa posición
            selected_case = sorted_cases[target_index]
            selected_cases.append(selected_case)
            
            # Log del caso seleccionado
            primary_icd10 = self.get_case_primary_icd10(selected_case)
            avg_severity = self.calculate_case_average_severity(selected_case)
            print(f"       Segmento {i+1}: ICD-10={primary_icd10}, Severidad={avg_severity:.1f}")
        
        return selected_cases
    
    def process_chapter_with_debt_system(self):
        """Procesa cada capítulo con sistema de deudas EXACTO."""
        print("\n💰 Procesando capítulos con sistema de deudas...")
        
        base_target = 10
        selected_cases = []
        
        for chapter in sorted(self.cases_by_chapter_dataset.keys()):
            print(f"\n📋 Capítulo {chapter}:")
            
            # Contar casos disponibles por dataset
            available_counts = {}
            for dataset in self.datasets:
                available_counts[dataset] = len(self.cases_by_chapter_dataset[chapter].get(dataset, []))
            
            # Ordenar datasets por cantidad (MINORITARIO PRIMERO)
            sorted_datasets = sorted(available_counts.items(), key=lambda x: x[1])
            print(f"   Datasets ordenados por cantidad: {dict(sorted_datasets)}")
            
            # Procesar datasets en orden de minoritario a abundante
            accumulated_debt = 0
            chapter_selected_cases = []  # CRÍTICO: Lista local para este capítulo
            
            for dataset, available_count in sorted_datasets:
                print(f"\n   📦 Dataset: {dataset} ({available_count} disponibles)")
                
                # Si ya alcanzamos el máximo por capítulo, salimos temprano
                if len(chapter_selected_cases) >= 50:
                    print(f"       ⛔ Capacidad máxima del capítulo alcanzada (50)")
                    break
                
                # ¿Cuánto necesita tomar este dataset?
                base_need = base_target  # Siempre intenta tomar 10
                total_need = base_need + accumulated_debt  # Base + deuda acumulada
                
                # ¿Cuánto puede tomar realmente?
                # Además, no debemos sobrepasar el límite global de 50 casos por capítulo
                remaining_capacity = 50 - len(chapter_selected_cases)
                actual_take = min(total_need, available_count, remaining_capacity)
                
                print(f"       Base: {base_need}, Deuda recibida: {accumulated_debt}")
                print(f"       Total necesario: {total_need}, Puede tomar: {actual_take}")
                
                # Seleccionar casos usando algoritmo de equidistancia
                if actual_take > 0:
                    available_cases = self.cases_by_chapter_dataset[chapter][dataset]
                    selected = self.select_equidistant_cases(available_cases, actual_take)
                    chapter_selected_cases.extend(selected)  # CRÍTICO: Usar lista local
                    print(f"       ✅ Seleccionados: {len(selected)} casos")
                else:
                    print(f"       ❌ No puede tomar casos")
                
                # ¿Qué deuda transmite al siguiente?
                if actual_take < total_need:
                    # No pudo cumplir completamente → transmite deuda restante
                    new_debt = total_need - actual_take
                    accumulated_debt = new_debt
                    print(f"       💸 Transmite deuda: {new_debt}")
                else:
                    # Pudo cumplir completamente → no hay deuda
                    accumulated_debt = 0
                    print(f"       💚 Deuda saldada")
            
            chapter_total = sum(len(self.cases_by_chapter_dataset[chapter].get(dataset, [])) 
                              for dataset in available_counts.keys())
            
            # Verificar que no exceda 50 casos (sistema de seguridad)
            if len(chapter_selected_cases) > 50:
                print(f"   ⚠️  ERROR: Capítulo {chapter} excede 50 casos: {len(chapter_selected_cases)}")
                # Recortar a 50 como medida de emergencia
                chapter_selected_cases = chapter_selected_cases[:50]
                print(f"   🔧 Recortado a 50 casos")

            # Añadir casos (ya recortados si era necesario) a la lista global
            selected_cases.extend(chapter_selected_cases)
            
            print(f"   📊 Capítulo {chapter}: {len(chapter_selected_cases)} casos seleccionados de {chapter_total} disponibles")
        
        return selected_cases
    
    def remove_duplicates(self, cases):
        """Elimina casos duplicados manteniendo orden."""
        seen_ids = set()
        unique_cases = []
        
        for case in cases:
            case_id = case.get('id')
            if case_id not in seen_ids:
                seen_ids.add(case_id)
                unique_cases.append(case)
        
        print(f"🔄 Eliminación de duplicados: {len(cases)} → {len(unique_cases)}")
        return unique_cases
    
    def save_results(self, selected_cases, output_file="v2-crived-final.json"):
        """Guarda resultados."""
        print(f"\n💾 Guardando {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(selected_cases, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Guardados {len(selected_cases)} casos")
    
    def generate_final_summary(self, selected_cases):
        """Genera resumen final detallado."""
        print(f"\n📊 RESUMEN FINAL DETALLADO:")
        print("=" * 60)
        
        # Crear set de IDs de casos seleccionados para búsqueda eficiente
        selected_ids = {case.get('id') for case in selected_cases}
        
        # Estadísticas por capítulo y dataset
        chapter_stats = defaultdict(lambda: defaultdict(int))
        
        # Contar correctamente usando IDs
        for chapter in self.cases_by_chapter_dataset.keys():
            for dataset in self.datasets:
                chapter_cases = self.cases_by_chapter_dataset[chapter].get(dataset, [])
                # Contar cuántos casos de este dataset/capítulo están en seleccionados
                selected_count = sum(1 for case in chapter_cases 
                                if case.get('id') in selected_ids)
                if selected_count > 0:
                    chapter_stats[chapter][dataset] = selected_count
        
        # Mostrar estadísticas por capítulo
        total_final = 0
        for chapter in sorted(chapter_stats.keys()):
            chapter_total = sum(chapter_stats[chapter].values())
            total_final += chapter_total
            
            print(f"\n📋 Capítulo {chapter}: {chapter_total} casos")
            for dataset in sorted(self.datasets):
                count = chapter_stats[chapter].get(dataset, 0)
                if count > 0:
                    print(f"   {dataset}: {count}")
        
        print(f"\n🎯 TOTAL FINAL: {total_final} casos")
        print(f"📉 Reducción: {len(self.cases)} → {total_final} ({((len(self.cases) - total_final) / len(self.cases) * 100):.1f}% menos)")
        
        # Estadísticas de datasets
        dataset_totals = defaultdict(int)
        for chapter_data in chapter_stats.values():
            for dataset, count in chapter_data.items():
                dataset_totals[dataset] += count
        
        print(f"\n📊 Total por dataset:")
        for dataset in sorted(dataset_totals.keys()):
            print(f"   {dataset}: {dataset_totals[dataset]} casos")
        
    def run(self):
        """Ejecuta el proceso completo."""
        print("🚀 PERFECT CHAPTER BALANCED SELECTOR")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. Cargar y organizar
            self.load_cases()
            self.organize_by_chapters()
            
            # 2. Procesar con sistema de deudas exacto
            selected_cases = self.process_chapter_with_debt_system()
            
            # 3. Eliminar duplicados
            unique_cases = self.remove_duplicates(selected_cases)
            
            # 4. Guardar resultados
            self.save_results(unique_cases)
            
            # 5. Resumen final
            self.generate_final_summary(unique_cases)
            
            print(f"\n🎉 ¡Proceso completado perfectamente!")
            print(f"📄 Archivo generado: v2-crived-final.json")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return 1


def main():
    selector = PerfectChapterSelector()
    return selector.run()


if __name__ == "__main__":
    exit(main())