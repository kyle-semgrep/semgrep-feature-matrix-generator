#!/usr/bin/env python3
"""
Competitive Analysis Engine

This module provides the core competitive analysis functionality for the 
Feature Matrix Generator, enabling side-by-side comparisons between Semgrep
and competitors with detailed capability analysis.
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ComparisonResult(Enum):
    SEMGREP_ADVANTAGE = "semgrep_advantage"
    COMPETITOR_ADVANTAGE = "competitor_advantage" 
    EQUIVALENT = "equivalent"
    SEMGREP_DISADVANTAGE = "semgrep_disadvantage"

@dataclass
class CapabilityComparison:
    capability: str
    semgrep_status: bool
    competitor_status: bool
    result: ComparisonResult
    notes: str
    importance: str  # "critical", "important", "nice_to_have"

@dataclass
class LanguageComparison:
    language: str
    semgrep_support: str  # "Yes", "No", "Beta"
    competitor_support: str
    semgrep_features: List[str]
    competitor_features: List[str]
    result: ComparisonResult

@dataclass
class CompetitorAnalysis:
    competitor_name: str
    overall_assessment: ComparisonResult
    capability_comparisons: List[CapabilityComparison]
    language_comparisons: List[LanguageComparison]
    scm_comparison: Dict[str, Any]
    strengths_vs_semgrep: List[str]
    weaknesses_vs_semgrep: List[str]
    key_differentiators: List[str]
    sales_talking_points: List[str]

class CompetitiveAnalysisEngine:
    def __init__(self):
        self.semgrep_capabilities = self._load_semgrep_capabilities()
        self.competitors = self._load_all_competitors()
        
    def _load_semgrep_capabilities(self) -> Dict[str, Any]:
        """Load current Semgrep capabilities from languages.json and known features."""
        semgrep_data = {}
        
        # Load languages data
        try:
            with open('languages.json', 'r') as f:
                languages_data = json.load(f)
                semgrep_data['languages'] = languages_data
        except Exception as e:
            print(f"Warning: Could not load languages.json: {e}")
            semgrep_data['languages'] = {}
        
        # Define Semgrep's current capabilities
        semgrep_data['capabilities'] = {
            "sast": {
                "supported": True,
                "cross_file_dataflow_analysis": True,
                "maturity": "Mature",
                "key_features": [
                    "Pattern-based static analysis",
                    "Custom rule creation", 
                    "Cross-file analysis",
                    "High precision/low false positives",
                    "Multiple language support"
                ]
            },
            "sca": {
                "supported": True,
                "reachability_analysis": False,  # Key differentiator opportunity
                "maturity": "Growing",
                "key_features": [
                    "License compliance",
                    "Vulnerability detection",
                    "Supply chain scanning",
                    "SBOM generation"
                ]
            },
            "secrets": {
                "supported": True,
                "validation": True,
                "maturity": "Mature",
                "key_features": [
                    "Pattern-based detection",
                    "Custom patterns",
                    "Git history scanning",
                    "Real-time scanning"
                ]
            }
        }
        
        # SCM support
        semgrep_data['scm_support'] = {
            "github": {
                "supported": True,
                "plans": ["GitHub.com", "GitHub Enterprise"],
                "integration_quality": "Native"
            },
            "gitlab": {
                "supported": True, 
                "plans": ["GitLab.com", "GitLab Self-Managed"],
                "integration_quality": "Native"
            },
            "bitbucket": {
                "supported": True,
                "plans": ["Bitbucket Cloud", "Bitbucket Data Center"],
                "integration_quality": "Native"
            },
            "azure_devops": {
                "supported": True,
                "plans": ["Azure DevOps Services"],
                "integration_quality": "Native"
            }
        }
        
        return semgrep_data
    
    def _load_all_competitors(self) -> Dict[str, Dict[str, Any]]:
        """Load all competitor data files."""
        competitors = {}
        competitor_files = [
            "competitors/checkmarx.json",
            "competitors/veracode.json",
            "competitors/snyk.json", 
            "competitors/github-advanced-security.json",
            "competitors/sonarqube.json",
            "competitors/endor-labs.json"
        ]
        
        for filename in competitor_files:
            if os.path.exists(filename):
                try:
                    with open(filename, 'r') as f:
                        data = json.load(f)
                        competitors[data['competitor_name']] = data
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        return competitors
    
    def compare_capabilities(self, competitor_name: str) -> List[CapabilityComparison]:
        """Compare core security capabilities between Semgrep and competitor."""
        if competitor_name not in self.competitors:
            return []
            
        competitor = self.competitors[competitor_name]
        comparisons = []
        
        # SAST Cross-file Dataflow Analysis
        semgrep_sast_crossfile = self.semgrep_capabilities['capabilities']['sast']['cross_file_dataflow_analysis']
        competitor_sast_crossfile = competitor.get('products', {}).get('sast', {}).get('cross_file_dataflow_analysis', {}).get('supported', False)
        
        if semgrep_sast_crossfile and competitor_sast_crossfile:
            result = ComparisonResult.EQUIVALENT
            notes = "Both support cross-file dataflow analysis"
        elif semgrep_sast_crossfile and not competitor_sast_crossfile:
            result = ComparisonResult.SEMGREP_ADVANTAGE
            notes = "Semgrep provides cross-file analysis, competitor does not"
        elif not semgrep_sast_crossfile and competitor_sast_crossfile:
            result = ComparisonResult.COMPETITOR_ADVANTAGE
            notes = f"{competitor_name} provides cross-file analysis, Semgrep does not"
        else:
            result = ComparisonResult.EQUIVALENT
            notes = "Neither provides cross-file dataflow analysis"
            
        comparisons.append(CapabilityComparison(
            capability="SAST Cross-file Dataflow Analysis",
            semgrep_status=semgrep_sast_crossfile,
            competitor_status=competitor_sast_crossfile,
            result=result,
            notes=notes,
            importance="critical"
        ))
        
        # SCA Reachability Analysis
        semgrep_sca_reach = self.semgrep_capabilities['capabilities']['sca']['reachability_analysis']
        competitor_sca_reach = competitor.get('products', {}).get('sca', {}).get('reachability_analysis', {}).get('supported', False)
        
        if semgrep_sca_reach and competitor_sca_reach:
            result = ComparisonResult.EQUIVALENT
            notes = "Both provide reachability analysis"
        elif semgrep_sca_reach and not competitor_sca_reach:
            result = ComparisonResult.SEMGREP_ADVANTAGE
            notes = "Semgrep provides reachability analysis, competitor does not"
        elif not semgrep_sca_reach and competitor_sca_reach:
            result = ComparisonResult.COMPETITOR_ADVANTAGE  
            notes = f"{competitor_name} provides reachability analysis, Semgrep does not"
        else:
            result = ComparisonResult.EQUIVALENT
            notes = "Neither provides reachability analysis"
            
        comparisons.append(CapabilityComparison(
            capability="SCA Reachability Analysis",
            semgrep_status=semgrep_sca_reach,
            competitor_status=competitor_sca_reach,
            result=result,
            notes=notes,
            importance="critical"
        ))
        
        # Secrets Validation
        semgrep_secrets_validation = self.semgrep_capabilities['capabilities']['secrets']['validation']
        competitor_secrets_validation = competitor.get('products', {}).get('secrets', {}).get('validation', {}).get('supported', False)
        
        if semgrep_secrets_validation and competitor_secrets_validation:
            result = ComparisonResult.EQUIVALENT
            notes = "Both provide secret validation"
        elif semgrep_secrets_validation and not competitor_secrets_validation:
            result = ComparisonResult.SEMGREP_ADVANTAGE
            notes = "Semgrep validates secrets, competitor only detects"
        elif not semgrep_secrets_validation and competitor_secrets_validation:
            result = ComparisonResult.COMPETITOR_ADVANTAGE
            notes = f"{competitor_name} validates secrets, Semgrep only detects"
        else:
            result = ComparisonResult.EQUIVALENT
            notes = "Both only detect secrets without validation"
            
        comparisons.append(CapabilityComparison(
            capability="Secrets Validation",
            semgrep_status=semgrep_secrets_validation,
            competitor_status=competitor_secrets_validation,
            result=result,
            notes=notes,
            importance="important"
        ))
        
        return comparisons
    
    def compare_language_support(self, competitor_name: str, selected_languages: List[str] = None) -> List[LanguageComparison]:
        """Compare language support between Semgrep and competitor."""
        if competitor_name not in self.competitors:
            return []
            
        competitor = self.competitors[competitor_name]
        comparisons = []
        
        # Get competitor's supported languages for SAST
        competitor_sast_langs = competitor.get('products', {}).get('sast', {}).get('languages_supported', [])
        
        # Get languages to compare
        all_languages = set()
        if selected_languages:
            all_languages.update(selected_languages)
        
        # Add languages from Semgrep's database
        for lang_data in self.semgrep_capabilities.get('languages', {}).values():
            all_languages.add(lang_data.get('language', ''))
            
        # Add languages from competitor
        all_languages.update(competitor_sast_langs)
        
        # Remove empty strings
        all_languages.discard('')
        
        for language in sorted(all_languages):
            # Check Semgrep support
            semgrep_support = "No"
            semgrep_features = []
            
            # Look for language in Semgrep data
            for lang_data in self.semgrep_capabilities.get('languages', {}).values():
                if lang_data.get('language', '').lower() == language.lower():
                    semgrep_support = "Yes"
                    semgrep_features = [
                        "Pattern-based analysis",
                        "Custom rules",
                        "High precision"
                    ]
                    break
            
            # Check competitor support
            competitor_support = "Yes" if language in competitor_sast_langs else "No"
            competitor_features = []
            if competitor_support == "Yes":
                competitor_features = competitor.get('products', {}).get('sast', {}).get('key_features', [])
            
            # Determine result
            if semgrep_support == "Yes" and competitor_support == "Yes":
                result = ComparisonResult.EQUIVALENT
            elif semgrep_support == "Yes" and competitor_support == "No":
                result = ComparisonResult.SEMGREP_ADVANTAGE
            elif semgrep_support == "No" and competitor_support == "Yes":
                result = ComparisonResult.COMPETITOR_ADVANTAGE
            else:
                result = ComparisonResult.EQUIVALENT
                
            comparisons.append(LanguageComparison(
                language=language,
                semgrep_support=semgrep_support,
                competitor_support=competitor_support,
                semgrep_features=semgrep_features,
                competitor_features=competitor_features,
                result=result
            ))
        
        return comparisons
    
    def generate_sales_talking_points(self, competitor_name: str) -> List[str]:
        """Generate sales talking points based on competitive analysis."""
        if competitor_name not in self.competitors:
            return []
            
        talking_points = []
        competitor = self.competitors[competitor_name]
        
        # Analyze capabilities
        capabilities = self.compare_capabilities(competitor_name)
        
        for cap in capabilities:
            if cap.result == ComparisonResult.SEMGREP_ADVANTAGE:
                talking_points.append(f"✅ **{cap.capability}**: {cap.notes}")
            elif cap.result == ComparisonResult.COMPETITOR_ADVANTAGE:
                talking_points.append(f"⚠️ **{cap.capability}**: {cap.notes} - Consider roadmap positioning")
        
        # Generic Semgrep advantages
        semgrep_strengths = [
            "🎯 **Developer-first approach**: Rules as code, easy customization",
            "⚡ **High performance**: Fast analysis with low false positives", 
            "🔧 **Flexible deployment**: Cloud, on-premises, or hybrid",
            "📝 **Custom rules**: Write security rules in simple YAML",
            "🌐 **Multi-language**: Comprehensive language support",
            "💰 **Cost effective**: Competitive pricing model"
        ]
        
        # Add competitor-specific talking points
        competitor_weaknesses = competitor.get('weaknesses', [])
        for weakness in competitor_weaknesses:
            talking_points.append(f"💡 **Vs {competitor_name}**: Semgrep addresses - {weakness}")
        
        talking_points.extend(semgrep_strengths)
        
        return talking_points
    
    def analyze_competitor(self, competitor_name: str, selected_languages: List[str] = None) -> CompetitorAnalysis:
        """Perform comprehensive competitive analysis."""
        if competitor_name not in self.competitors:
            raise ValueError(f"Competitor {competitor_name} not found")
            
        competitor = self.competitors[competitor_name]
        
        # Get capability and language comparisons
        capability_comparisons = self.compare_capabilities(competitor_name)
        language_comparisons = self.compare_language_support(competitor_name, selected_languages)
        
        # Determine overall assessment
        advantages = sum(1 for c in capability_comparisons if c.result == ComparisonResult.SEMGREP_ADVANTAGE)
        disadvantages = sum(1 for c in capability_comparisons if c.result == ComparisonResult.COMPETITOR_ADVANTAGE)
        
        if advantages > disadvantages:
            overall = ComparisonResult.SEMGREP_ADVANTAGE
        elif disadvantages > advantages:
            overall = ComparisonResult.SEMGREP_DISADVANTAGE
        else:
            overall = ComparisonResult.EQUIVALENT
        
        # Extract competitive insights
        strengths_vs_semgrep = competitor.get('strengths', [])
        weaknesses_vs_semgrep = competitor.get('weaknesses', [])
        
        # Key differentiators
        differentiators = []
        for cap in capability_comparisons:
            if cap.result == ComparisonResult.SEMGREP_ADVANTAGE and cap.importance == "critical":
                differentiators.append(f"Semgrep: {cap.capability}")
            elif cap.result == ComparisonResult.COMPETITOR_ADVANTAGE and cap.importance == "critical":
                differentiators.append(f"{competitor_name}: {cap.capability}")
        
        # Generate sales talking points
        sales_points = self.generate_sales_talking_points(competitor_name)
        
        # SCM comparison
        scm_comparison = self._compare_scm_support(competitor_name)
        
        return CompetitorAnalysis(
            competitor_name=competitor_name,
            overall_assessment=overall,
            capability_comparisons=capability_comparisons,
            language_comparisons=language_comparisons,
            scm_comparison=scm_comparison,
            strengths_vs_semgrep=strengths_vs_semgrep,
            weaknesses_vs_semgrep=weaknesses_vs_semgrep,
            key_differentiators=differentiators,
            sales_talking_points=sales_points
        )
    
    def _compare_scm_support(self, competitor_name: str) -> Dict[str, Any]:
        """Compare SCM support between Semgrep and competitor."""
        if competitor_name not in self.competitors:
            return {}
            
        competitor = self.competitors[competitor_name]
        comparison = {}
        
        scm_platforms = ['github', 'gitlab', 'bitbucket', 'azure_devops']
        
        for scm in scm_platforms:
            semgrep_scm = self.semgrep_capabilities['scm_support'].get(scm, {})
            competitor_scm = competitor.get('scm_support', {}).get(scm, {})
            
            comparison[scm] = {
                'semgrep_supported': semgrep_scm.get('supported', False),
                'competitor_supported': competitor_scm.get('supported', False),
                'semgrep_plans': semgrep_scm.get('plans', []),
                'competitor_plans': competitor_scm.get('plans', []),
                'semgrep_features': semgrep_scm.get('features', []),
                'competitor_features': competitor_scm.get('features', [])
            }
        
        return comparison
    
    def get_available_competitors(self) -> List[str]:
        """Get list of available competitors."""
        return list(self.competitors.keys())
    
    def get_competitor_summary(self, competitor_name: str) -> Dict[str, Any]:
        """Get basic summary of competitor."""
        if competitor_name not in self.competitors:
            return {}
            
        competitor = self.competitors[competitor_name]
        return {
            'name': competitor_name,
            'website': competitor.get('website', ''),
            'description': competitor.get('business_overview', {}).get('description', ''),
            'market_position': competitor.get('business_overview', {}).get('market_position', ''),
            'last_updated': competitor.get('last_updated', ''),
            'data_sources': competitor.get('data_sources', [])
        } 