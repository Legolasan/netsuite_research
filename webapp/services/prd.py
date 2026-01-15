"""
PRD (Product Requirements Document) Service for NetSuite Connector Research

Loads and aggregates data from research JSON files to provide summary,
comparison, and roadmap views for product planning.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class SummaryStats:
    """Implementation overview statistics."""
    total_objects: int = 0
    implemented_objects: int = 0
    coverage_percentage: float = 0.0
    sdk_version: str = ""
    api_protocol: str = ""
    operations_implemented: List[str] = field(default_factory=list)
    operations_total: int = 0
    operations_coverage: float = 0.0
    replication_modes: Dict[str, List[str]] = field(default_factory=dict)
    limitations: List[str] = field(default_factory=list)
    concurrency_limit: int = 0


@dataclass
class ComparisonItem:
    """Single comparison item between current and available."""
    category: str
    current: str
    available: str
    gap: str
    status: str  # 'full', 'partial', 'missing'


@dataclass
class RoadmapItem:
    """Single roadmap enhancement item."""
    id: str
    name: str
    description: str
    priority: str  # 'P1', 'P2', 'P3'
    effort: str  # 'low', 'medium', 'high'
    impact: str  # 'low', 'medium', 'high'
    timeline: str
    category: str


@dataclass 
class ObjectInfo:
    """Information about a NetSuite object."""
    name: str
    category: str
    status: str  # 'implemented', 'available', 'missing'
    replication_mode: str
    incremental_field: Optional[str] = None
    search_class: Optional[str] = None


class PRDService:
    """Service for PRD data aggregation."""
    
    def __init__(self):
        self.research_dir = Path(__file__).parent.parent.parent
        self._cache: Dict[str, Any] = {}
        self._load_all_data()
    
    def _load_json(self, relative_path: str) -> Dict[str, Any]:
        """Load a JSON file from research directory."""
        file_path = self.research_dir / relative_path
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {relative_path}: {e}")
            return {}
    
    def _load_all_data(self):
        """Load all research JSON files."""
        self._cache = {
            'objects': self._load_json('01_objects/objects_catalog.json'),
            'relations': self._load_json('02_relations/object_relations.json'),
            'permissions': self._load_json('03_permissions/permissions_matrix.json'),
            'replication': self._load_json('04_replication/replication_methods.json'),
            'governance': self._load_json('05_api_limits/api_governance.json'),
            'operations': self._load_json('06_operations/operations_catalog.json'),
            'gap_analysis': self._load_json('07_summary/gap_analysis.json'),
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get implementation summary for the Summary view."""
        objects = self._cache.get('objects', {})
        operations = self._cache.get('operations', {})
        replication = self._cache.get('replication', {})
        governance = self._cache.get('governance', {})
        gap_analysis = self._cache.get('gap_analysis', {})
        
        # Object counts
        summary = objects.get('summary', {})
        total_objects = summary.get('total_objects', 0)
        
        # Metadata
        metadata = objects.get('metadata', {})
        sdk_version = metadata.get('sdk_version', 'Unknown')
        protocol = metadata.get('protocol', 'Unknown')
        
        # Operations
        impl_status = operations.get('implementation_status', {})
        implemented_ops = impl_status.get('implemented', [])
        not_implemented_ops = impl_status.get('not_implemented', [])
        total_ops = len(implemented_ops) + len(not_implemented_ops)
        ops_coverage = (len(implemented_ops) / total_ops * 100) if total_ops > 0 else 0
        
        # Replication modes
        cat_replication = replication.get('category_replication', {})
        replication_by_mode = {
            'incremental': [],
            'full_load': []
        }
        for cat, info in cat_replication.items():
            mode = info.get('mode', 'full_load')
            if mode == 'incremental':
                replication_by_mode['incremental'].append(cat)
            else:
                replication_by_mode['full_load'].append(cat)
        
        # Governance limits
        concurrency = governance.get('concurrency_limits', {}).get('by_service_tier', {})
        default_concurrency = concurrency.get('tier_1', {}).get('concurrent_requests', 5)
        
        # Key gaps/limitations
        exec_summary = gap_analysis.get('executive_summary', {})
        key_gaps = exec_summary.get('key_gaps', [])
        
        # Auth method
        auth_method = "OAuth1 TBA (Token-Based Auth)"
        
        return {
            'overview': {
                'total_objects': total_objects,
                'sdk_version': sdk_version,
                'protocol': protocol,
                'auth_method': auth_method,
            },
            'operations': {
                'implemented': implemented_ops,
                'total': total_ops,
                'coverage_percentage': round(ops_coverage, 1),
            },
            'replication': {
                'incremental': replication_by_mode['incremental'],
                'full_load': replication_by_mode['full_load'],
                'deleted_records_supported': True,
            },
            'governance': {
                'default_concurrency': default_concurrency,
                'page_size': 1000,
                'retry_strategy': 'Exponential backoff with jitter',
            },
            'limitations': key_gaps,
            'categories': {
                'transaction': summary.get('categories', {}).get('transaction', 0),
                'item': summary.get('categories', {}).get('item', 0),
                'standard_full_load': summary.get('categories', {}).get('standard_full_load', 0),
                'custom': 'Dynamic',
                'delete': 1,
            }
        }
    
    def get_comparison(self) -> Dict[str, Any]:
        """Get current vs available comparison data."""
        gap_analysis = self._cache.get('gap_analysis', {})
        operations = self._cache.get('operations', {})
        replication = self._cache.get('replication', {})
        
        gap_data = gap_analysis.get('gap_analysis', {})
        
        # Objects comparison
        objects_gap = gap_data.get('objects', {})
        
        # Operations comparison
        ops_gap = gap_data.get('operations', {})
        
        # API protocols comparison
        api_gap = gap_data.get('api_protocols', {})
        
        # SDK version
        sdk_gap = gap_data.get('sdk_version', {})
        
        # Replication comparison
        replication_gap = gap_data.get('replication', {})
        incremental_implemented = replication_gap.get('incremental_implemented', [])
        incremental_not_used = replication_gap.get('incremental_available_not_used', [])
        
        comparisons = [
            {
                'category': 'Objects',
                'current': f"{objects_gap.get('current', 128)} objects implemented",
                'available': f"{objects_gap.get('available', 160)}+ objects available",
                'gap': f"{objects_gap.get('gap', 32)} objects missing ({objects_gap.get('gap_percentage', '20%')})",
                'status': 'partial',
                'icon': 'cube',
            },
            {
                'category': 'API Protocol',
                'current': api_gap.get('current', 'SOAP only'),
                'available': ', '.join(api_gap.get('available', ['SOAP', 'REST', 'SuiteQL'])),
                'gap': ', '.join(api_gap.get('gap', ['REST API', 'SuiteQL'])),
                'status': 'partial',
                'icon': 'code',
            },
            {
                'category': 'SDK Version',
                'current': sdk_gap.get('current', 'v2022_1'),
                'available': sdk_gap.get('latest', 'v2024_1'),
                'gap': f"{sdk_gap.get('versions_behind', 2)} versions behind",
                'status': 'partial',
                'icon': 'chip',
            },
            {
                'category': 'Operations',
                'current': f"{len(ops_gap.get('implemented', []))} operations (Read-only)",
                'available': f"{len(ops_gap.get('implemented', [])) + len(ops_gap.get('not_implemented', []))} operations (Full CRUD)",
                'gap': f"{len(ops_gap.get('not_implemented', []))} operations not implemented ({ops_gap.get('coverage', '18%')} coverage)",
                'status': 'partial',
                'icon': 'cog',
            },
            {
                'category': 'Authentication',
                'current': 'OAuth1 TBA',
                'available': 'OAuth1, OAuth2 (REST)',
                'gap': 'OAuth2 not implemented',
                'status': 'partial',
                'icon': 'key',
            },
            {
                'category': 'Incremental Sync',
                'current': f"{len(incremental_implemented)} categories",
                'available': f"All entities with lastModifiedDate",
                'gap': f"{len(incremental_not_used)} entities using full load unnecessarily",
                'status': 'partial',
                'icon': 'refresh',
            },
        ]
        
        # Detailed gaps
        detailed_gaps = [
            {
                'title': 'Missing Objects',
                'description': 'REST-only records and newer SOAP records',
                'items': objects_gap.get('missing_categories', []),
            },
            {
                'title': 'Entities Needing Incremental',
                'description': f"High-volume objects syncing as full load ({replication_gap.get('impact', '')})",
                'items': incremental_not_used[:10],  # Show first 10
            },
            {
                'title': 'Missing Operations',
                'description': 'Write and advanced operations',
                'items': ops_gap.get('not_implemented', [])[:10],  # Show first 10
            },
        ]
        
        return {
            'comparisons': comparisons,
            'detailed_gaps': detailed_gaps,
            'summary': {
                'total_gaps': 5,
                'critical_gaps': 2,
                'improvement_potential': 'High',
            }
        }
    
    def get_roadmap(self) -> Dict[str, Any]:
        """Get prioritized roadmap data."""
        gap_analysis = self._cache.get('gap_analysis', {})
        
        priorities = gap_analysis.get('improvement_priorities', {})
        recommended = gap_analysis.get('recommended_roadmap', {})
        benefits = gap_analysis.get('estimated_benefits', {})
        risks = gap_analysis.get('risk_assessment', {})
        
        # P1 Quick Wins
        p1_items = []
        for item in priorities.get('p1_quick_wins', []):
            p1_items.append({
                'id': item.get('id', ''),
                'name': item.get('name', ''),
                'effort': item.get('effort', 'low'),
                'impact': item.get('impact', 'high'),
                'timeline': item.get('timeline', ''),
                'category': 'Quick Win',
            })
        
        # P2 High Value
        p2_items = []
        for item in priorities.get('p2_high_value', []):
            p2_items.append({
                'id': item.get('id', ''),
                'name': item.get('name', ''),
                'effort': item.get('effort', 'medium'),
                'impact': item.get('impact', 'high'),
                'timeline': item.get('timeline', ''),
                'category': 'High Value',
            })
        
        # P3 Advanced
        p3_items = []
        for item in priorities.get('p3_advanced', []):
            p3_items.append({
                'id': item.get('id', ''),
                'name': item.get('name', ''),
                'effort': item.get('effort', 'high'),
                'impact': item.get('impact', 'medium'),
                'timeline': item.get('timeline', ''),
                'category': 'Advanced',
            })
        
        # Phases
        phases = []
        for phase_key in ['phase_1', 'phase_2', 'phase_3']:
            phase = recommended.get(phase_key, {})
            if phase:
                phases.append({
                    'id': phase_key,
                    'name': phase.get('name', ''),
                    'timeline': phase.get('timeline', ''),
                    'items': phase.get('items', []),
                })
        
        return {
            'priorities': {
                'p1': {
                    'label': 'P1 - Quick Wins',
                    'description': 'Low effort, high impact improvements',
                    'items': p1_items,
                },
                'p2': {
                    'label': 'P2 - High Value',
                    'description': 'Medium effort, strategic improvements',
                    'items': p2_items,
                },
                'p3': {
                    'label': 'P3 - Advanced',
                    'description': 'Higher effort, future enhancements',
                    'items': p3_items,
                },
            },
            'phases': phases,
            'benefits': {
                'incremental_sync': benefits.get('incremental_for_entities', {}),
                'write_operations': benefits.get('write_operations', {}),
                'rest_api': benefits.get('rest_api', {}),
            },
            'risks': risks,
        }
    
    def get_objects(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed objects list with status."""
        objects_data = self._cache.get('objects', {})
        replication_data = self._cache.get('replication', {})
        
        categories = objects_data.get('categories', {})
        incremental_eligible = replication_data.get('incremental_eligible_full_load_objects', [])
        
        # Build objects list
        all_objects = []
        
        for cat_name, cat_info in categories.items():
            if category and cat_name.upper() != category.upper():
                continue
            
            cat_objects = cat_info.get('objects', [])
            replication_mode = cat_info.get('replication_mode', 'full_load')
            incremental_field = cat_info.get('incremental_field')
            
            for obj in cat_objects:
                obj_name = obj.get('name', '')
                all_objects.append({
                    'name': obj_name,
                    'category': cat_name,
                    'status': obj.get('status', 'implemented'),
                    'replication_mode': replication_mode,
                    'incremental_field': incremental_field,
                    'class': obj.get('class', ''),
                })
            
            # Handle objects_without_incremental
            for obj in cat_info.get('objects_without_incremental', []):
                obj_name = obj.get('name', '')
                # Check if this object has incremental potential
                has_potential = any(e['name'] == obj_name for e in incremental_eligible)
                all_objects.append({
                    'name': obj_name,
                    'category': cat_name,
                    'status': 'implemented',
                    'replication_mode': 'full_load',
                    'incremental_field': None,
                    'has_incremental_potential': has_potential,
                    'search_class': obj.get('search_class', ''),
                })
            
            # Handle objects_with_incremental_potential
            for obj in cat_info.get('objects_with_incremental_potential', []):
                obj_name = obj.get('name', '')
                all_objects.append({
                    'name': obj_name,
                    'category': cat_name,
                    'status': 'implemented',
                    'replication_mode': 'full_load',  # Currently full load
                    'incremental_field': obj.get('incremental_field'),
                    'has_incremental_potential': True,
                    'search_class': obj.get('search_class', ''),
                    'recommendation': 'Enable incremental sync',
                })
        
        # Group by category
        by_category = {}
        for obj in all_objects:
            cat = obj['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(obj)
        
        # Incremental eligible summary
        incremental_summary = {
            'p1': [e for e in incremental_eligible if e.get('priority') == 'P1'],
            'p2': [e for e in incremental_eligible if e.get('priority') == 'P2'],
            'p3': [e for e in incremental_eligible if e.get('priority') == 'P3'],
        }
        
        return {
            'total': len(all_objects),
            'by_category': by_category,
            'categories': list(by_category.keys()),
            'incremental_eligible': incremental_summary,
        }
    
    def get_all_prd_data(self) -> Dict[str, Any]:
        """Get all PRD data in one call."""
        return {
            'summary': self.get_summary(),
            'comparison': self.get_comparison(),
            'roadmap': self.get_roadmap(),
        }
