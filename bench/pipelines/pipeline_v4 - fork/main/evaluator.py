#!/usr/bin/env python3
"""
Evaluator - DDX Quality Evaluation Module
=========================================

This module handles the evaluation of differential diagnoses (DDX) quality
against reference diagnoses (GDX) using multiple evaluation methods including
BERT semantic similarity and ICD-10 taxonomic matching.

Features:
- Multi-method evaluation (exact match, semantic similarity, ICD-10 taxonomy)
- BERT semantic similarity with auto-confirmation thresholds
- ICD-10 hierarchical matching (parent/child relationships)
- Comprehensive evaluation trace and reporting
- Progress tracking and detailed logging
"""

import json
import os
import sys
import logging
import time
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics
import yaml

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'utils'))

from utils.llm import get_llm
from utils.bert import calculate_semantic_similarity, warm_up_endpoint
from utils.icd10.taxonomy import ICD10Taxonomy

# Constants
LOG_FILE_NAME = 'evaluation'

@dataclass
class EvaluationTrace:
    """Detailed trace of evaluation process for a single GDX"""
    gdx_evaluated: Dict
    snomed_check: Dict
    icd10_check: Dict
    semantic_check: Dict

@dataclass
class EvaluationResult:
    """Result of a complete case evaluation"""
    case_id: str
    gdx_details: List[Dict]
    ddx_details: List[Dict]
    eval_details: Dict

class DiagnosticEvaluator:
    """Main evaluation engine for diagnostic differential analysis"""
    
    def __init__(self, config: Dict[str, Any], logger):
        self.config = config
        self.evaluator_config = config.get('EVALUATOR', {})
        
        # Configuration parameters
        self.bert_acceptance_threshold = self.evaluator_config.get('BERT_ACCEPTANCE_THRESHOLD', 0.80)
        self.bert_autoconfirm_threshold = self.evaluator_config.get('BERT_AUTOCONFIRM_THRESHOLD', 0.90)
        self.enable_icd10_parent_search = self.evaluator_config.get('ENABLE_ICD10_PARENT_SEARCH', True)
        self.enable_icd10_sibling_search = self.evaluator_config.get('ENABLE_ICD10_SIBLING_SEARCH', True)
        
        # Initialize components
        self.icd10_taxonomy = ICD10Taxonomy()
        self.llm = get_llm("gpt-4o-summary")
        self.bert_warmed_up = False
        self.logger = logger
        
    def evaluate_case(self, case_data: Dict, case_num: int = 0, total_cases: int = 0) -> EvaluationResult:
        """
        Evaluate a single case with complete tracing
        
        Args:
            case_data: Dictionary containing case_id, gdx_details/diagnoses, ddx_details
            case_num: Current case number for progress tracking
            total_cases: Total number of cases for progress tracking
            
        Returns:
            EvaluationResult with detailed trace
        """
        case_id = case_data.get("case_id", case_data.get("id", "unknown"))
        
        # Handle both gdx_details and diagnoses formats
        if "gdx_details" in case_data:
            gdx_details = list(case_data["gdx_details"].items())
        elif "diagnoses" in case_data:
            # Convert diagnoses list to gdx_details format
            gdx_details = []
            for diag in case_data["diagnoses"]:
                gdx_details.append((diag["name"], diag))
        else:
            gdx_details = []
        
        ddx_details = list(case_data.get("ddx_details", {}).items())
        
        # Initialize evaluation details
        eval_details = {
            "best_match_found": False,
            "final_resolution": None,
            "evaluation_trace": []
        }
        
        best_position = None
        best_method = None
        best_value = None
        best_gdx = None
        best_ddx = None
        
        # Track which GDX and method found the match
        winning_gdx_idx = None
        winning_gdx_name = None
        winning_ddx_name = None
        final_method = None
        
        # Evaluate each GDX
        for gdx_idx, (gdx_name, gdx_info) in enumerate(gdx_details, 1):
            trace = self._evaluate_single_gdx_with_trace(case_id, gdx_name, gdx_info, ddx_details, case_num, total_cases, gdx_idx, len(gdx_details))
            eval_details["evaluation_trace"].append(asdict(trace))
            
            # Check if this GDX found a better match
            if trace.snomed_check["status"] == "SUCCESS":
                position = self._extract_position_from_details(trace.snomed_check["details"])
                if best_position is None or position < best_position:
                    best_position = position
                    best_method = "SNOMED_MATCH"
                    best_value = self._extract_value_from_details(trace.snomed_check["details"])
                    best_gdx = {gdx_name: gdx_info}
                    best_ddx = self._get_ddx_at_position(ddx_details, position)
                    winning_gdx_idx = gdx_idx
                    winning_gdx_name = gdx_name
                    winning_ddx_name = list(best_ddx.keys())[0] if best_ddx else "unknown"
                    final_method = "SNOMED"
                    
            elif trace.icd10_check["status"] == "SUCCESS":
                position = self._extract_position_from_details(trace.icd10_check["details"])
                if best_position is None or position < best_position:
                    best_position = position
                    best_method = self._extract_method_from_icd10_details(trace.icd10_check["details"])
                    best_value = self._extract_value_from_details(trace.icd10_check["details"])
                    best_gdx = {gdx_name: gdx_info}
                    best_ddx = self._get_ddx_at_position(ddx_details, position)
                    winning_gdx_idx = gdx_idx
                    winning_gdx_name = gdx_name
                    winning_ddx_name = list(best_ddx.keys())[0] if best_ddx else "unknown"
                    final_method = self._extract_method_from_icd10_details(trace.icd10_check["details"])
                    
            elif trace.semantic_check["status"] == "SUCCESS":
                position = self._extract_position_from_semantic_details(trace.semantic_check)
                if best_position is None or position < best_position:
                    best_position = position
                    best_method = self._extract_method_from_semantic_details(trace.semantic_check)
                    best_value = self._extract_value_from_semantic_details(trace.semantic_check)
                    best_gdx = {gdx_name: gdx_info}
                    best_ddx = self._get_ddx_at_position(ddx_details, position)
                    winning_gdx_idx = gdx_idx
                    winning_gdx_name = gdx_name
                    winning_ddx_name = list(best_ddx.keys())[0] if best_ddx else "unknown"
                    final_method = self._extract_method_from_semantic_details(trace.semantic_check)
        
        # Log case result
        if best_position is not None:
            # Success case
            gdx_short = winning_gdx_name[:30] + "..." if len(winning_gdx_name) > 30 else winning_gdx_name
            ddx_short = winning_ddx_name[:30] + "..." if len(winning_ddx_name) > 30 else winning_ddx_name
            self.logger.info(f"[{case_num}/{total_cases}] {final_method} → GDX[{winning_gdx_idx}]: {gdx_short} | DDX[{best_position}]: {ddx_short} → **P{best_position}**")
            
            eval_details["best_match_found"] = True
            eval_details["final_resolution"] = {
                "position": f"P{best_position}",
                "method": best_method,
                "value": best_value,
                "matched_gdx": best_gdx,
                "matched_ddx": best_ddx
            }
        else:
            # No match case - find what was the last method tried
            last_method_tried = "SEMANTIC"  # Default as it's always the last
            for gdx_idx, (gdx_name, gdx_info) in enumerate(gdx_details, 1):
                trace = eval_details["evaluation_trace"][gdx_idx - 1]
                if trace["snomed_check"]["status"] not in ["SKIPPED", "PENDING"]:
                    last_method_tried = "SNOMED"
                    if trace["icd10_check"]["status"] not in ["SKIPPED", "PENDING"]:
                        last_method_tried = "ICD10"
                        if trace["semantic_check"]["status"] not in ["SKIPPED", "PENDING"]:
                            last_method_tried = "SEMANTIC"
                    break
            
            self.logger.info(f"[{case_num}/{total_cases}] {last_method_tried} → NO_MATCH → **REJECTED**")
        
        return EvaluationResult(
            case_id=case_id,
            gdx_details=gdx_details,
            ddx_details=ddx_details,
            eval_details=eval_details
        )
    
    def _evaluate_single_gdx_with_trace(self, case_id: str, gdx_name: str, gdx_info: Dict, ddx_list: List, case_num: int, total_cases: int, gdx_idx: int, total_gdx: int) -> EvaluationTrace:
        """Evaluate a single GDX without logging"""
        
        # Initialize trace
        trace = EvaluationTrace(
            gdx_evaluated={gdx_name: gdx_info},
            snomed_check={"status": "PENDING", "details": ""},
            icd10_check={"status": "PENDING", "details": ""},
            semantic_check={"status": "PENDING", "details": "", "bert_scores": [], "bert_best": None, "llm_judgment": None}
        )
        
        # Step 1: SNOMED evaluation
        snomed_result = self._evaluate_snomed_match(gdx_name, gdx_info, ddx_list)
        trace.snomed_check = snomed_result
        
        if snomed_result["status"] == "SUCCESS":
            trace.icd10_check = {"status": "SKIPPED", "details": "SNOMED match found first"}
            trace.semantic_check = {"status": "SKIPPED", "details": "SNOMED match found first", "bert_scores": [], "bert_best": None, "llm_judgment": None}
            return trace
        
        # Step 2: ICD-10 evaluation
        icd10_result = self._evaluate_icd10_match(gdx_name, gdx_info, ddx_list)
        trace.icd10_check = icd10_result
        
        if icd10_result["status"] == "SUCCESS":
            trace.semantic_check = {"status": "SKIPPED", "details": "ICD-10 match found first", "bert_scores": [], "bert_best": None, "llm_judgment": None}
            return trace
        
        # Step 3: Semantic evaluation
        semantic_result = self._evaluate_semantic_match(gdx_name, gdx_info, ddx_list)
        trace.semantic_check = semantic_result
        
        return trace
    

    
    def _evaluate_snomed_match(self, gdx_name: str, gdx_info: Dict, ddx_list: List) -> Dict:
        """SNOMED evaluation with detailed trace"""
        gdx_snomed_codes = gdx_info.get("medical_codes", {}).get("snomed", [])
        
        if not gdx_snomed_codes:
            return {"status": "SKIPPED", "details": "GDX has no SNOMED codes"}
        
        for position, (ddx_name, ddx_info) in enumerate(ddx_list, 1):
            ddx_snomed_codes = ddx_info.get("medical_codes", {}).get("snomed", [])
            
            for gdx_code in gdx_snomed_codes:
                if gdx_code in ddx_snomed_codes:
                    return {
                        "status": "SUCCESS",
                        "details": f"SUCCESS: Found match with DDX at P{position} (code: {gdx_code})"
                    }
        
        return {
            "status": "FAILED",
            "details": f"FAILED: No SNOMED code from GDX list {gdx_snomed_codes} found in any DDX"
        }
    
    def _evaluate_icd10_match(self, gdx_name: str, gdx_info: Dict, ddx_list: List) -> Dict:
        """ICD-10 evaluation with minimal logging"""
        gdx_icd10_codes = gdx_info.get("medical_codes", {}).get("icd10", [])
        
        if not gdx_icd10_codes:
            return {"status": "SKIPPED", "details": "GDX has no ICD-10 codes"}
        
        for gdx_code in gdx_icd10_codes:
            # Try exact match first
            for position, (ddx_name, ddx_info) in enumerate(ddx_list, 1):
                ddx_icd10_codes = ddx_info.get("medical_codes", {}).get("icd10", [])
                if gdx_code in ddx_icd10_codes:
                    return {
                        "status": "SUCCESS",
                        "details": f"SUCCESS: Found ICD10_EXACT match with DDX at P{position} (code: {gdx_code})"
                    }
            
            # Try children match
            for position, (ddx_name, ddx_info) in enumerate(ddx_list, 1):
                ddx_icd10_codes = ddx_info.get("medical_codes", {}).get("icd10", [])
                for ddx_code in ddx_icd10_codes:
                    if self._is_child_code(gdx_code, ddx_code):
                        return {
                            "status": "SUCCESS",
                            "details": f"SUCCESS: Found ICD10_CHILD match with DDX at P{position} ({gdx_code} -> {ddx_code})"
                        }
            
            # Try parent match if enabled
            if self.enable_icd10_parent_search:
                for position, (ddx_name, ddx_info) in enumerate(ddx_list, 1):
                    ddx_icd10_codes = ddx_info.get("medical_codes", {}).get("icd10", [])
                    for ddx_code in ddx_icd10_codes:
                        if self._is_parent_code(gdx_code, ddx_code):
                            return {
                                "status": "SUCCESS",
                                "details": f"SUCCESS: Found ICD10_PARENT match with DDX at P{position} ({gdx_code} -> {ddx_code})"
                            }
            
            # Try sibling match if enabled
            if self.enable_icd10_sibling_search:
                for position, (ddx_name, ddx_info) in enumerate(ddx_list, 1):
                    ddx_icd10_codes = ddx_info.get("medical_codes", {}).get("icd10", [])
                    for ddx_code in ddx_icd10_codes:
                        if self._is_sibling_code(gdx_code, ddx_code):
                            return {
                                "status": "SUCCESS",
                                "details": f"SUCCESS: Found ICD10_SIBLING match with DDX at P{position} ({gdx_code} <-> {ddx_code})"
                            }
        
        return {
            "status": "FAILED",
            "details": f"FAILED: No ICD-10 relationship match found for GDX codes {gdx_icd10_codes}"
        }
    
    def _evaluate_semantic_match(self, gdx_name: str, gdx_info: Dict, ddx_list: List) -> Dict:
        """Semantic evaluation with minimal logging"""
        gdx_text = gdx_info.get("normalized_text", gdx_name)
        ddx_texts = [ddx_info.get("normalized_text", ddx_name) for ddx_name, ddx_info in ddx_list]
        
        try:
            # Warm up BERT if needed
            if not self.bert_warmed_up:
                warm_up_endpoint()
                self.bert_warmed_up = True
            
            # Calculate BERT similarities
            similarities = calculate_semantic_similarity(gdx_text, ddx_texts)
            
            # Process BERT scores
            bert_scores = []
            best_bert_score = 0.0
            best_bert_position = None
            
            for i, ddx_text in enumerate(ddx_texts, 1):
                similarity_score = similarities.get(gdx_text, {}).get(ddx_text)
                if similarity_score is not None:
                    bert_scores.append({"position": i, "score": similarity_score})
                    if similarity_score > best_bert_score:
                        best_bert_score = similarity_score
                        best_bert_position = i
            
            bert_best = {"position": best_bert_position, "score": best_bert_score} if best_bert_position else None
            
            # Check for auto-confirmation
            if best_bert_score >= self.bert_autoconfirm_threshold:
                return {
                    "status": "SUCCESS",
                    "details": f"BERT score {best_bert_score:.3f} >= autoconfirm threshold {self.bert_autoconfirm_threshold}. LLM call skipped.",
                    "bert_scores": bert_scores,
                    "bert_best": bert_best,
                    "llm_judgment": None
                }
            
            # Call LLM for judgment
            llm_result = self._get_llm_judgment(gdx_text, ddx_texts)
            
            # Final decision
            if best_bert_score >= self.bert_acceptance_threshold and llm_result["position"] is not None:
                if best_bert_position <= llm_result["position"]:
                    return {
                        "status": "SUCCESS",
                        "details": f"BERT result at P{best_bert_position} (score: {best_bert_score:.3f}) was better than LLM's choice P{llm_result['position']} and score was >= acceptance threshold {self.bert_acceptance_threshold}.",
                        "bert_scores": bert_scores,
                        "bert_best": bert_best,
                        "llm_judgment": llm_result
                    }
                else:
                    return {
                        "status": "SUCCESS",
                        "details": f"LLM choice P{llm_result['position']} was better than BERT's P{best_bert_position} (score: {best_bert_score:.3f}).",
                        "bert_scores": bert_scores,
                        "bert_best": bert_best,
                        "llm_judgment": llm_result
                    }
            elif llm_result["position"] is not None:
                return {
                    "status": "SUCCESS",
                    "details": f"LLM selected P{llm_result['position']}. BERT score {best_bert_score:.3f} below acceptance threshold {self.bert_acceptance_threshold}.",
                    "bert_scores": bert_scores,
                    "bert_best": bert_best,
                    "llm_judgment": llm_result
                }
            else:
                return {
                    "status": "FAILED",
                    "details": f"Both BERT (best: {best_bert_score:.3f}) and LLM found no acceptable matches.",
                    "bert_scores": bert_scores,
                    "bert_best": bert_best,
                    "llm_judgment": llm_result
                }
        
        except Exception as e:
            return {
                "status": "FAILED",
                "details": f"Semantic evaluation error: {str(e)}",
                "bert_scores": [],
                "bert_best": None,
                "llm_judgment": None
            }
    
    def _get_llm_judgment(self, gdx_text: str, ddx_texts: List[str]) -> Dict:
        """Get LLM judgment for semantic matching"""
        try:
            ddx_options = "\n".join([f"{i+1}. {text}" for i, text in enumerate(ddx_texts)])
            
            prompt = f"""You are a medical expert evaluating diagnostic similarity. 

Reference diagnosis: {gdx_text}

Differential diagnosis options:
{ddx_options}

Which of the 5 differential diagnosis options is most clinically similar or interchangeable with the reference diagnosis? Consider:
- Clinical presentation overlap
- Pathophysiology similarity
- Treatment approach similarity
- Differential diagnosis overlap

Respond with ONLY the number (1-5) of the most similar option. If none are clinically similar, respond with "0".

Answer:"""
            
            response = self.llm.generate(prompt, max_tokens=10, temperature=0.1)
            response_text = str(response).strip()
            
            try:
                position = int(response_text)
                if 1 <= position <= 5:
                    return {"position": position}
                else:
                    return {"position": None}
            except ValueError:
                return {"position": None}
        
        except Exception as e:
            return {"position": None}
    
    def _is_child_code(self, parent_code: str, child_code: str) -> bool:
        """Check if child_code is a child of parent_code"""
        try:
            children = self.icd10_taxonomy.children(parent_code)
            return child_code in children
        except:
            return False
    
    def _is_parent_code(self, child_code: str, parent_code: str) -> bool:
        """Check if parent_code is a parent of child_code"""
        try:
            parents = self.icd10_taxonomy.parents(child_code)
            return parent_code in parents
        except:
            return False
    
    def _is_sibling_code(self, code1: str, code2: str) -> bool:
        """Check if code1 and code2 are siblings"""
        try:
            siblings = self.icd10_taxonomy.siblings(code1)
            return code2 in siblings
        except:
            return False
    
    def _extract_position_from_details(self, details: str) -> Optional[int]:
        """Extract position number from details string"""
        import re
        match = re.search(r'P(\d+)', details)
        return int(match.group(1)) if match else None
    
    def _extract_value_from_details(self, details: str) -> str:
        """Extract value from details string"""
        import re
        if "code:" in details:
            match = re.search(r'code:\s*([^)]+)', details)
            return match.group(1) if match else ""
        elif "->" in details:
            match = re.search(r'(\S+\s*->\s*\S+)', details)
            return match.group(1) if match else ""
        elif "<->" in details:
            match = re.search(r'(\S+\s*<->\s*\S+)', details)
            return match.group(1) if match else ""
        return ""
    
    def _extract_method_from_icd10_details(self, details: str) -> str:
        """Extract method from ICD-10 details"""
        if "ICD10_EXACT" in details:
            return "ICD10_EXACT"
        elif "ICD10_CHILD" in details:
            return "ICD10_CHILD"
        elif "ICD10_PARENT" in details:
            return "ICD10_PARENT"
        elif "ICD10_SIBLING" in details:
            return "ICD10_SIBLING"
        return "ICD10_UNKNOWN"
    
    def _extract_position_from_semantic_details(self, semantic_check: Dict) -> Optional[int]:
        """Extract position from semantic check details"""
        if "autoconfirm" in semantic_check["details"]:
            return semantic_check["bert_best"]["position"] if semantic_check["bert_best"] else None
        elif "BERT result" in semantic_check["details"]:
            return semantic_check["bert_best"]["position"] if semantic_check["bert_best"] else None
        elif "LLM choice" in semantic_check["details"] or "LLM selected" in semantic_check["details"]:
            return semantic_check["llm_judgment"]["position"] if semantic_check["llm_judgment"] else None
        return None
    
    def _extract_method_from_semantic_details(self, semantic_check: Dict) -> str:
        """Extract method from semantic check details"""
        if "autoconfirm" in semantic_check["details"]:
            return "BERT_AUTOCONFIRM"
        elif "BERT result" in semantic_check["details"]:
            return "BERT_MATCH"
        elif "LLM choice" in semantic_check["details"] or "LLM selected" in semantic_check["details"]:
            return "LLM_JUDGMENT"
        return "SEMANTIC_UNKNOWN"
    
    def _extract_value_from_semantic_details(self, semantic_check: Dict) -> str:
        """Extract value from semantic check details"""
        if semantic_check["bert_best"] and ("autoconfirm" in semantic_check["details"] or "BERT result" in semantic_check["details"]):
            return str(semantic_check["bert_best"]["score"])
        elif semantic_check["llm_judgment"] and semantic_check["llm_judgment"]["position"]:
            return str(semantic_check["llm_judgment"]["position"])
        return ""
    
    def _get_ddx_at_position(self, ddx_list: List, position: int) -> Dict:
        """Get DDX object at specific position"""
        if 1 <= position <= len(ddx_list):
            ddx_name, ddx_info = ddx_list[position - 1]
            return {ddx_name: ddx_info}
        return {}

def setup_logging(output_dir: str) -> logging.Logger:
    """Setup logging to both console and file"""
    logger = logging.getLogger('pipeline_v4')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - %(message)s', 
                                  datefmt='%Y-%m-%d %H:%M:%S')
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    log_file = os.path.join(output_dir, LOG_FILE_NAME+".log")
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def generate_evaluation_details(results: List[EvaluationResult], output_path: str):
    """Generate detailed evaluation report in JSON format"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, result in enumerate(results):
            if i > 0:
                f.write('\n---\n')
            
            case_data = {
                "case_id": result.case_id,
                "gdx_details": [{"name": name, "details": details} for name, details in result.gdx_details],
                "ddx_details": [{"name": name, "details": details} for name, details in result.ddx_details],
                "eval_details": result.eval_details
            }
            
            json.dump(case_data, f, ensure_ascii=False, indent=2)

def calculate_global_statistics(results: List[EvaluationResult]) -> Dict:
    """Calculate global statistics from all evaluation results"""
    total_cases = len(results)
    matched_cases = sum(1 for r in results if r.eval_details["best_match_found"])
    unmatched_cases = total_cases - matched_cases
    
    # Count positions (dynamic to handle any position that appears)
    position_counts = {}
    method_counts = {
        "snomed_match": 0,
        "icd10_exact": 0,
        "icd10_child": 0,
        "icd10_parent": 0,
        "icd10_sibling": 0,
        "bert_autoconfirm": 0,
        "bert_match": 0,
        "llm_judgment": 0
    }
    
    positions = []
    
    for result in results:
        if result.eval_details["best_match_found"]:
            resolution = result.eval_details["final_resolution"]
            position = resolution["position"]
            position_counts[position] = position_counts.get(position, 0) + 1
            positions.append(int(position[1:]))  # Extract number from "P1", "P2", etc.
            
            # Count by method
            method = resolution["method"].lower()
            if method in method_counts:
                method_counts[method] += 1
    
    # Calculate average position
    avg_position = statistics.mean(positions) if positions else 0
    final_score_percentage = (matched_cases / total_cases * 100) if total_cases > 0 else 0
    
    return {
        "total_cases": total_cases,
        "matched_cases": matched_cases,
        "unmatched_cases": unmatched_cases,
        "top_counts": position_counts,
        "resolution_method_counts": method_counts,
        "average_position": round(avg_position, 3),
        "final_score_percentage": round(final_score_percentage, 2)
    }

def calculate_method_statistics(results: List[EvaluationResult], method_name: str) -> Dict:
    """Calculate statistics for cases resolved by a specific method"""
    method_results = []
    
    for result in results:
        if result.eval_details["best_match_found"]:
            resolution = result.eval_details["final_resolution"]
            if resolution["method"].lower() == method_name.lower():
                method_results.append(result)
    
    if not method_results:
        return {
            "total_cases": 0,
            "matched_cases": 0,
            "unmatched_cases": 0,
            "top_counts": {},
            "average_position": 0,
            "final_score_percentage": 0
        }
    
    total_cases = len(method_results)
    matched_cases = total_cases  # All cases in method_results are matched by definition
    unmatched_cases = 0
    
    position_counts = {"P1": 0, "P2": 0, "P3": 0, "P4": 0, "P5": 0}
    positions = []
    
    for result in method_results:
        resolution = result.eval_details["final_resolution"]
        position = resolution["position"]
        position_counts[position] += 1
        positions.append(int(position[1:]))  # Extract number from "P1", "P2", etc.
    
    # Calculate average position
    avg_position = statistics.mean(positions) if positions else 0
    
    # Calculate final score percentage (100% for method-specific since all are matched)
    final_score_percentage = 100.0
    
    return {
        "total_cases": total_cases,
        "matched_cases": matched_cases,
        "unmatched_cases": unmatched_cases,
        "top_counts": position_counts,
        "average_position": round(avg_position, 3),
        "final_score_percentage": round(final_score_percentage, 2)
    }

def generate_summary_json(results: List[EvaluationResult], output_path: str, config: Dict[str, Any]):
    """Generate comprehensive summary statistics in JSON format"""
    # Calculate global statistics
    global_stats = calculate_global_statistics(results)
    
    # Get all unique methods
    methods = set()
    for result in results:
        if result.eval_details["best_match_found"]:
            resolution = result.eval_details["final_resolution"]
            methods.add(resolution["method"])
    
    # Calculate per-method statistics
    method_stats = {}
    for method in sorted(methods):
        method_stats[method] = calculate_method_statistics(results, method)
    
    # Get evaluator config
    evaluator_config = config.get('EVALUATOR', {})
    
    # Create comprehensive summary
    summary = {
        "configuration": {
            "experiment_name": config.get('EXPERIMENT_NAME', 'unknown'),
            "experiment_description": config.get('EXPERIMENT_DESCRIPTION', 'unknown'),
            "bert_acceptance_threshold": evaluator_config.get('BERT_ACCEPTANCE_THRESHOLD', 0.80),
            "bert_autoconfirm_threshold": evaluator_config.get('BERT_AUTOCONFIRM_THRESHOLD', 0.90),
            "enable_icd10_parent_search": evaluator_config.get('ENABLE_ICD10_PARENT_SEARCH', True),
            "enable_icd10_sibling_search": evaluator_config.get('ENABLE_ICD10_SIBLING_SEARCH', True),
            "dataset_path": config.get('DATASET_PATH', 'unknown'),
            "timestamp": config.get('TIMESTAMP', 'unknown')
        },
        "global": global_stats,
        "by_method": method_stats
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

def evaluate_dataset(input_path: str, output_dir: str, config: Dict[str, Any]) -> None:
    """
    Evaluate a dataset with DDX and GDX
    
    Args:
        input_path: Path to input JSON file with DDX and GDX
        output_dir: Directory to save evaluation results
        config: Configuration dictionary
    """
    # Setup logging
    logger = setup_logging(output_dir)
    
    # Get evaluator config
    evaluator_config = config.get('EVALUATOR', {})
    
    # File paths
    log_file_name = 'evaluation'
    summary_file_name = 'summary'
    details_file_name = 'evaluation_details'
    
    output_details_path = os.path.join(output_dir, details_file_name + ".txt")
    output_summary_path = os.path.join(output_dir, summary_file_name + ".json")

    logger.info("--- Starting Evaluation Pipeline ---")
    logger.info(f"Configuration:")
    logger.info(f"  BERT_ACCEPTANCE_THRESHOLD: {evaluator_config.get('BERT_ACCEPTANCE_THRESHOLD', 0.80)}")
    logger.info(f"  BERT_AUTOCONFIRM_THRESHOLD: {evaluator_config.get('BERT_AUTOCONFIRM_THRESHOLD', 0.90)}")
    logger.info(f"  ENABLE_ICD10_PARENT_SEARCH: {evaluator_config.get('ENABLE_ICD10_PARENT_SEARCH', True)}")
    logger.info(f"  ENABLE_ICD10_SIBLING_SEARCH: {evaluator_config.get('ENABLE_ICD10_SIBLING_SEARCH', True)}")
    logger.info(f"  Output directory: {output_dir}")
    
    # Load input data
    logger.info("Loading input data...")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file '{input_path}' not found")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return
    
    # Handle both list and dict formats
    if isinstance(data, list):
        all_cases = data
    else:
        # Extract cases from all categories
        all_cases = []
        for category, cases in data.items():
            all_cases.extend(cases)
    
    logger.info(f"Found {len(all_cases)} cases to evaluate")
    
    # Initialize evaluator
    logger.info("Initializing evaluator...")
    evaluator = DiagnosticEvaluator(config, logger)
    
    # Process all cases
    logger.info("Processing cases...")
    all_results = []
    
    for i, case_data in enumerate(all_cases, 1):
        result = evaluator.evaluate_case(case_data, i, len(all_cases))
        all_results.append(result)
    
    # Generate outputs
    logger.info("\nGenerating outputs...")
    generate_evaluation_details(all_results, output_details_path)
    generate_summary_json(all_results, output_summary_path, config)
    
    # Final summary stats
    global_stats = calculate_global_statistics(all_results)
    
    logger.info("\n--- FINAL RESULTS ---")
    logger.info(f"Total cases: {global_stats['total_cases']}")
    logger.info(f"Successful matches: {global_stats['matched_cases']}")
    logger.info(f"Success rate: {global_stats['final_score_percentage']:.1f}%")
    if global_stats['top_counts']:
        ddx_positions = " | ".join([f"{pos}: {count}" for pos, count in sorted(global_stats['top_counts'].items())])
        logger.info(f"DDX positions: {ddx_positions}")
    logger.info(f"Average position: {global_stats['average_position']:.3f}")

def main():
    """Main function for standalone execution"""
    # Load configuration with preference for saved copy
    # Import here to avoid circular imports
    from main import load_config_with_fallback
    config = load_config_with_fallback()
    
    # Setup output directory with timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    output_dir = os.path.join(os.path.dirname(__file__), 'output', 'evaluation', timestamp)
    os.makedirs(output_dir, exist_ok=True)
    
    # Assume input file is from medlabeler
    input_path = os.path.join(os.path.dirname(__file__), 'output', 'labeled_output.json')
    
    # Run evaluation
    evaluate_dataset(input_path, output_dir, config)

if __name__ == "__main__":
    main()