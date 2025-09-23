"""
Report Generator - Creates comprehensive optimization reports
"""

import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

class ReportGenerator:
    def __init__(self):
        self.console = Console()
    
    def generate_report(self, recommendations: Dict[str, List[Any]], 
                       cluster_data: Dict[str, Any], 
                       cost_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'cluster_name': cluster_data.get('cluster_info', {}).get('name', 'unknown'),
                'report_version': '1.0'
            },
            'executive_summary': self._generate_executive_summary(recommendations, cost_data),
            'cluster_overview': self._generate_cluster_overview(cluster_data),
            'cost_analysis': self._generate_cost_analysis(cost_data),
            'recommendations': self._format_recommendations(recommendations),
            'implementation_roadmap': self._generate_implementation_roadmap(recommendations),
            'risk_assessment': self._generate_risk_assessment(recommendations)
        }
        
        # Save report to file
        self._save_report(report)
        
        # Display report to console
        self._display_report(report)
        
        return report
    
    def _generate_executive_summary(self, recommendations: Dict[str, List[Any]], 
                                  cost_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary"""
        
        total_recommendations = sum(len(recs) for recs in recommendations.values())
        total_potential_savings = sum(
            rec.monthly_savings for recs in recommendations.values() 
            for rec in recs if hasattr(rec, 'monthly_savings')
        )
        
        high_priority_count = sum(
            1 for recs in recommendations.values() 
            for rec in recs if hasattr(rec, 'priority') and rec.priority == 'high'
        )
        
        return {
            'current_monthly_cost': cost_data['total_cost'],
            'total_recommendations': total_recommendations,
            'high_priority_recommendations': high_priority_count,
            'potential_monthly_savings': round(total_potential_savings, 2),
            'potential_annual_savings': round(total_potential_savings * 12, 2),
            'savings_percentage': round((total_potential_savings / cost_data['total_cost']) * 100, 1) if cost_data['total_cost'] > 0 else 0,
            'key_opportunities': [
                'Resource rightsizing',
                'Unused resource cleanup',
                'Storage optimization',
                'Node consolidation'
            ]
        }
    
    def _generate_cluster_overview(self, cluster_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate cluster overview"""
        
        cluster_info = cluster_data.get('cluster_info', {})
        metrics = cluster_data.get('metrics_summary', {})
        
        return {
            'cluster_name': cluster_info.get('name', 'unknown'),
            'kubernetes_version': cluster_info.get('kubernetes_version', 'unknown'),
            'node_count': cluster_info.get('node_count', 0),
            'total_pods': metrics.get('total_pods', 0),
            'average_cpu_utilization': round(metrics.get('average_cpu_utilization', 0), 1),
            'average_memory_utilization': round(metrics.get('average_memory_utilization', 0), 1),
            'unused_resources': {
                'pvcs': metrics.get('unused_pvcs', 0),
                'services': metrics.get('unused_services', 0)
            },
            'optimization_opportunities': metrics.get('optimization_opportunities', 0)
        }
    
    def _generate_cost_analysis(self, cost_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate cost analysis section"""
        
        return {
            'current_monthly_cost': cost_data['total_cost'],
            'cost_breakdown': cost_data.get('service_breakdown', {}),
            'resource_costs': cost_data.get('resource_costs', {}),
            'cost_trends': cost_data.get('cost_trends', {}),
            'top_cost_drivers': self._identify_top_cost_drivers(cost_data)
        }
    
    def _identify_top_cost_drivers(self, cost_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify top cost drivers"""
        
        service_breakdown = cost_data.get('service_breakdown', {})
        cost_drivers = []
        
        for service, details in service_breakdown.items():
            cost_drivers.append({
                'service': service,
                'cost': details.get('cost', 0),
                'percentage': details.get('percentage', 0)
            })
        
        # Sort by cost descending
        cost_drivers.sort(key=lambda x: x['cost'], reverse=True)
        
        return cost_drivers[:5]  # Top 5 cost drivers
    
    def _format_recommendations(self, recommendations: Dict[str, List[Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Format recommendations for the report"""
        
        formatted_recs = {}
        
        for category, recs in recommendations.items():
            formatted_recs[category] = []
            
            for rec in recs:
                if hasattr(rec, 'title'):  # It's a recommendation object
                    formatted_recs[category].append({
                        'title': rec.title,
                        'description': rec.description,
                        'priority': rec.priority,
                        'impact': rec.impact,
                        'effort': rec.effort,
                        'monthly_savings': rec.monthly_savings,
                        'implementation_steps': rec.implementation_steps,
                        'risks': rec.risks,
                        'resources_affected': rec.resources_affected
                    })
        
        return formatted_recs
    
    def _generate_implementation_roadmap(self, recommendations: Dict[str, List[Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate implementation roadmap"""
        
        roadmap = {
            'immediate': [],  # High priority, low effort
            'short_term': [],  # High priority, medium effort
            'long_term': []   # Medium/low priority or high effort
        }
        
        for category, recs in recommendations.items():
            for rec in recs:
                if not hasattr(rec, 'priority'):
                    continue
                
                rec_info = {
                    'title': rec.title,
                    'category': category,
                    'savings': rec.monthly_savings,
                    'effort': rec.effort
                }
                
                if rec.priority == 'high' and rec.effort == 'low':
                    roadmap['immediate'].append(rec_info)
                elif rec.priority == 'high' and rec.effort == 'medium':
                    roadmap['short_term'].append(rec_info)
                else:
                    roadmap['long_term'].append(rec_info)
        
        # Sort by savings within each category
        for phase in roadmap.values():
            phase.sort(key=lambda x: x['savings'], reverse=True)
        
        return roadmap
    
    def _generate_risk_assessment(self, recommendations: Dict[str, List[Any]]) -> Dict[str, Any]:
        """Generate risk assessment"""
        
        risk_levels = {'low': 0, 'medium': 0, 'high': 0}
        total_recs = 0
        
        for recs in recommendations.values():
            for rec in recs:
                if hasattr(rec, 'risks'):
                    total_recs += 1
                    # Simple risk assessment based on effort and impact
                    if rec.effort == 'high' or len(rec.risks) > 2:
                        risk_levels['high'] += 1
                    elif rec.effort == 'medium' or len(rec.risks) > 1:
                        risk_levels['medium'] += 1
                    else:
                        risk_levels['low'] += 1
        
        return {
            'total_recommendations': total_recs,
            'risk_distribution': risk_levels,
            'risk_mitigation_strategies': [
                'Start with low-risk, high-impact recommendations',
                'Implement changes in non-production environments first',
                'Monitor applications closely after changes',
                'Have rollback plans for all modifications',
                'Consider gradual rollout for high-risk changes'
            ]
        }
    
    def _save_report(self, report: Dict[str, Any]):
        """Save report to JSON file"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"gke_optimization_report_{timestamp}.json"
        
        reports_dir = Path('reports')
        reports_dir.mkdir(exist_ok=True)
        
        filepath = reports_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.console.print(f"📄 Report saved to: {filepath}", style="green")
    
    def _display_report(self, report: Dict[str, Any]):
        """Display report summary to console"""
        
        # Executive Summary
        summary = report['executive_summary']
        
        summary_panel = Panel(
            f"""💰 Current Monthly Cost: ${summary['current_monthly_cost']:.2f}
🎯 Total Recommendations: {summary['total_recommendations']}
⚡ High Priority Items: {summary['high_priority_recommendations']}
💡 Potential Monthly Savings: ${summary['potential_monthly_savings']:.2f}
📈 Potential Annual Savings: ${summary['potential_annual_savings']:.2f}
📊 Savings Percentage: {summary['savings_percentage']}%""",
            title="💼 Executive Summary",
            border_style="green"
        )
        
        self.console.print(summary_panel)
        
        # Recommendations by Category
        recs_table = Table(title="📋 Recommendations by Category")
        recs_table.add_column("Category", style="cyan")
        recs_table.add_column("Count", justify="right")
        recs_table.add_column("Potential Savings", justify="right", style="green")
        
        for category, recs in report['recommendations'].items():
            if recs:
                total_savings = sum(rec.get('monthly_savings', 0) for rec in recs)
                recs_table.add_row(
                    category.replace('_', ' ').title(),
                    str(len(recs)),
                    f"${total_savings:.2f}/month"
                )
        
        self.console.print(recs_table)
        
        # Implementation Roadmap
        roadmap = report['implementation_roadmap']
        
        roadmap_panel = Panel(
            f"""🚀 Immediate Actions: {len(roadmap['immediate'])} items
📅 Short-term (1-3 months): {len(roadmap['short_term'])} items  
🎯 Long-term (3+ months): {len(roadmap['long_term'])} items""",
            title="🗺️ Implementation Roadmap",
            border_style="blue"
        )
        
        self.console.print(roadmap_panel)
        
        # Top 3 Immediate Actions
        if roadmap['immediate']:
            immediate_table = Table(title="⚡ Top Immediate Actions")
            immediate_table.add_column("Action", style="cyan")
            immediate_table.add_column("Savings", justify="right", style="green")
            
            for action in roadmap['immediate'][:3]:
                immediate_table.add_row(
                    action['title'],
                    f"${action['savings']:.2f}/month"
                )
            
            self.console.print(immediate_table)
    
    def generate_csv_export(self, recommendations: Dict[str, List[Any]]) -> str:
        """Generate CSV export of recommendations"""
        
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Category', 'Priority', 'Title', 'Description', 'Monthly Savings',
            'Effort', 'Impact', 'Resources Affected'
        ])
        
        # Data rows
        for category, recs in recommendations.items():
            for rec in recs:
                if hasattr(rec, 'title'):
                    writer.writerow([
                        category,
                        rec.priority,
                        rec.title,
                        rec.description,
                        rec.monthly_savings,
                        rec.effort,
                        rec.impact,
                        '; '.join(rec.resources_affected)
                    ])
        
        return output.getvalue()