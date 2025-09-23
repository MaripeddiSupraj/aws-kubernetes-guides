"""
Cost Optimizer - Generates intelligent optimization recommendations
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class OptimizationRecommendation:
    category: str
    priority: str  # high, medium, low
    title: str
    description: str
    impact: str
    effort: str  # low, medium, high
    monthly_savings: float
    implementation_steps: List[str]
    risks: List[str]
    resources_affected: List[str]

class CostOptimizer:
    def __init__(self):
        self.optimization_thresholds = {
            'cpu_underutilization': 20.0,  # Below 20% CPU usage
            'memory_underutilization': 30.0,  # Below 30% memory usage
            'node_underutilization': 40.0,  # Below 40% node usage
            'pvc_unused_days': 7,  # Unused for 7+ days
            'service_unused_days': 3  # Unused for 3+ days
        }
    
    def analyze_and_recommend(self, cluster_data: Dict[str, Any], cost_data: Dict[str, Any]) -> Dict[str, List[OptimizationRecommendation]]:
        """Generate comprehensive optimization recommendations"""
        
        recommendations = {
            'rightsizing': [],
            'resource_cleanup': [],
            'node_optimization': [],
            'storage_optimization': [],
            'cost_optimization': [],
            'performance_optimization': []
        }
        
        # Analyze pod rightsizing opportunities
        recommendations['rightsizing'].extend(
            self._analyze_pod_rightsizing(cluster_data['pods'], cost_data)
        )
        
        # Analyze resource cleanup opportunities
        recommendations['resource_cleanup'].extend(
            self._analyze_resource_cleanup(cluster_data, cost_data)
        )
        
        # Analyze node optimization opportunities
        recommendations['node_optimization'].extend(
            self._analyze_node_optimization(cluster_data['nodes'], cost_data)
        )
        
        # Analyze storage optimization
        recommendations['storage_optimization'].extend(
            self._analyze_storage_optimization(cluster_data['pvcs'], cost_data)
        )
        
        # Analyze cost optimization opportunities
        recommendations['cost_optimization'].extend(
            self._analyze_cost_optimization(cluster_data, cost_data)
        )
        
        # Analyze performance optimization
        recommendations['performance_optimization'].extend(
            self._analyze_performance_optimization(cluster_data, cost_data)
        )
        
        return recommendations
    
    def _analyze_pod_rightsizing(self, pods: List[Any], cost_data: Dict[str, Any]) -> List[OptimizationRecommendation]:
        """Analyze pods for rightsizing opportunities"""
        recommendations = []
        
        for pod in pods:
            # Check for CPU over-provisioning
            if (pod.cpu_utilization < self.optimization_thresholds['cpu_underutilization'] and 
                pod.cpu_request > 0.1):  # Only consider pods with significant CPU requests
                
                # Calculate recommended CPU
                recommended_cpu = max(pod.cpu_usage * 1.2, 0.05)  # 20% buffer, minimum 50m
                cpu_reduction = pod.cpu_request - recommended_cpu
                
                # Estimate monthly savings (rough calculation)
                monthly_savings = cpu_reduction * 30 * 0.05  # $0.05 per vCPU-hour
                
                recommendations.append(OptimizationRecommendation(
                    category='rightsizing',
                    priority='high' if cpu_reduction > 0.5 else 'medium',
                    title=f'Reduce CPU request for {pod.name}',
                    description=f'Pod is using only {pod.cpu_utilization:.1f}% of requested CPU. '
                               f'Reduce from {pod.cpu_request:.2f} to {recommended_cpu:.2f} cores.',
                    impact=f'Reduce CPU allocation by {cpu_reduction:.2f} cores',
                    effort='low',
                    monthly_savings=monthly_savings,
                    implementation_steps=[
                        f'Update deployment/pod spec for {pod.name}',
                        f'Change CPU request from {pod.cpu_request:.2f} to {recommended_cpu:.2f}',
                        'Monitor application performance after change',
                        'Gradually reduce if application remains stable'
                    ],
                    risks=[
                        'Potential CPU throttling during traffic spikes',
                        'Application performance degradation',
                        'Need monitoring during transition'
                    ],
                    resources_affected=[f'{pod.namespace}/{pod.name}']
                ))
            
            # Check for memory over-provisioning
            if (pod.memory_utilization < self.optimization_thresholds['memory_underutilization'] and 
                pod.memory_request > 256 * 1024 * 1024):  # Only consider pods with >256MB requests
                
                recommended_memory = max(pod.memory_usage * 1.3, 128 * 1024 * 1024)  # 30% buffer, minimum 128MB
                memory_reduction = pod.memory_request - recommended_memory
                
                # Estimate monthly savings
                monthly_savings = (memory_reduction / (1024**3)) * 30 * 0.01  # $0.01 per GB-hour
                
                recommendations.append(OptimizationRecommendation(
                    category='rightsizing',
                    priority='high' if memory_reduction > 512 * 1024 * 1024 else 'medium',
                    title=f'Reduce memory request for {pod.name}',
                    description=f'Pod is using only {pod.memory_utilization:.1f}% of requested memory. '
                               f'Reduce from {pod.memory_request/(1024**3):.2f}GB to {recommended_memory/(1024**3):.2f}GB.',
                    impact=f'Reduce memory allocation by {memory_reduction/(1024**3):.2f}GB',
                    effort='low',
                    monthly_savings=monthly_savings,
                    implementation_steps=[
                        f'Update deployment/pod spec for {pod.name}',
                        f'Change memory request from {pod.memory_request/(1024**3):.2f}GB to {recommended_memory/(1024**3):.2f}GB',
                        'Monitor for OOMKilled events',
                        'Adjust if memory pressure occurs'
                    ],
                    risks=[
                        'Potential out-of-memory kills',
                        'Application instability',
                        'Need careful monitoring'
                    ],
                    resources_affected=[f'{pod.namespace}/{pod.name}']
                ))
        
        return recommendations
    
    def _analyze_resource_cleanup(self, cluster_data: Dict[str, Any], cost_data: Dict[str, Any]) -> List[OptimizationRecommendation]:
        """Analyze unused resources for cleanup"""
        recommendations = []
        
        # Unused PVCs
        unused_pvcs = [pvc for pvc in cluster_data['pvcs'] if pvc['is_unused']]
        if unused_pvcs:
            total_storage = sum(self._parse_storage_size(pvc['size']) for pvc in unused_pvcs)
            monthly_savings = total_storage * 0.04  # $0.04 per GB/month for standard disk
            
            recommendations.append(OptimizationRecommendation(
                category='resource_cleanup',
                priority='high',
                title=f'Remove {len(unused_pvcs)} unused PVCs',
                description=f'Found {len(unused_pvcs)} PVCs not attached to any pods, '
                           f'totaling {total_storage:.1f}GB of unused storage.',
                impact=f'Free up {total_storage:.1f}GB of storage',
                effort='low',
                monthly_savings=monthly_savings,
                implementation_steps=[
                    'Verify PVCs are truly unused',
                    'Check for any backup or disaster recovery dependencies',
                    'Delete unused PVCs: kubectl delete pvc <pvc-name>',
                    'Monitor for any application issues'
                ],
                risks=[
                    'Potential data loss if PVC contains important data',
                    'Applications may fail if PVC is actually needed',
                    'Backup data before deletion'
                ],
                resources_affected=[f"{pvc['namespace']}/{pvc['name']}" for pvc in unused_pvcs]
            ))
        
        # Unused LoadBalancer services
        unused_services = [svc for svc in cluster_data['services'] if svc['is_unused']]
        if unused_services:
            monthly_savings = len(unused_services) * 18.25  # $18.25 per LB per month
            
            recommendations.append(OptimizationRecommendation(
                category='resource_cleanup',
                priority='high',
                title=f'Remove {len(unused_services)} unused LoadBalancers',
                description=f'Found {len(unused_services)} LoadBalancer services with no endpoints.',
                impact=f'Remove {len(unused_services)} unused load balancers',
                effort='low',
                monthly_savings=monthly_savings,
                implementation_steps=[
                    'Verify services have no active endpoints',
                    'Check if services are used for external access',
                    'Delete unused services: kubectl delete svc <service-name>',
                    'Update any DNS records pointing to these services'
                ],
                risks=[
                    'Service disruption if LoadBalancer is actually needed',
                    'DNS resolution issues',
                    'External traffic routing problems'
                ],
                resources_affected=[f"{svc['namespace']}/{svc['name']}" for svc in unused_services]
            ))
        
        return recommendations
    
    def _analyze_node_optimization(self, nodes: List[Dict[str, Any]], cost_data: Dict[str, Any]) -> List[OptimizationRecommendation]:
        """Analyze node optimization opportunities"""
        recommendations = []
        
        # Check for underutilized nodes
        underutilized_nodes = [
            node for node in nodes 
            if (node.get('cpu_utilization', 0) < self.optimization_thresholds['node_underutilization'] and
                node.get('memory_utilization', 0) < self.optimization_thresholds['node_underutilization'])
        ]
        
        if underutilized_nodes:
            # Estimate cost per node (rough calculation)
            cost_per_node = cost_data['resource_costs']['compute'] / len(nodes)
            potential_savings = len(underutilized_nodes) * cost_per_node * 0.5  # 50% savings through consolidation
            
            recommendations.append(OptimizationRecommendation(
                category='node_optimization',
                priority='medium',
                title=f'Consolidate {len(underutilized_nodes)} underutilized nodes',
                description=f'Found {len(underutilized_nodes)} nodes with low utilization. '
                           f'Consider consolidating workloads to fewer nodes.',
                impact=f'Reduce node count by up to {len(underutilized_nodes)}',
                effort='medium',
                monthly_savings=potential_savings,
                implementation_steps=[
                    'Analyze pod placement and resource requirements',
                    'Use node affinity to consolidate workloads',
                    'Implement cluster autoscaler for automatic scaling',
                    'Consider using smaller node types with higher density'
                ],
                risks=[
                    'Reduced fault tolerance',
                    'Potential resource contention',
                    'Need careful capacity planning'
                ],
                resources_affected=[node['name'] for node in underutilized_nodes]
            ))
        
        # Recommend preemptible instances
        total_compute_cost = cost_data['resource_costs']['compute']
        preemptible_savings = total_compute_cost * 0.70  # Up to 70% savings
        
        recommendations.append(OptimizationRecommendation(
            category='node_optimization',
            priority='medium',
            title='Use preemptible instances for fault-tolerant workloads',
            description='Migrate suitable workloads to preemptible instances for significant cost savings.',
            impact='Up to 70% reduction in compute costs for eligible workloads',
            effort='high',
            monthly_savings=preemptible_savings * 0.3,  # Assume 30% of workloads are suitable
            implementation_steps=[
                'Identify fault-tolerant workloads (batch jobs, stateless apps)',
                'Create separate node pools with preemptible instances',
                'Use node selectors to schedule appropriate workloads',
                'Implement proper handling for preemption events'
            ],
            risks=[
                'Workload interruptions due to preemption',
                'Not suitable for critical applications',
                'Need robust restart mechanisms'
            ],
            resources_affected=['cluster-wide']
        ))
        
        return recommendations
    
    def _analyze_storage_optimization(self, pvcs: List[Dict[str, Any]], cost_data: Dict[str, Any]) -> List[OptimizationRecommendation]:
        """Analyze storage optimization opportunities"""
        recommendations = []
        
        # Check for oversized PVCs (this would require usage metrics in production)
        ssd_pvcs = [pvc for pvc in pvcs if pvc.get('storage_class') == 'fast' or 'ssd' in pvc.get('storage_class', '').lower()]
        
        if ssd_pvcs:
            total_ssd_storage = sum(self._parse_storage_size(pvc['size']) for pvc in ssd_pvcs)
            # Assume 50% could be moved to standard storage
            potential_standard_storage = total_ssd_storage * 0.5
            monthly_savings = potential_standard_storage * (0.17 - 0.04)  # SSD vs Standard pricing difference
            
            recommendations.append(OptimizationRecommendation(
                category='storage_optimization',
                priority='medium',
                title='Migrate suitable workloads from SSD to Standard storage',
                description=f'Found {total_ssd_storage:.1f}GB of SSD storage. '
                           f'Consider migrating non-performance-critical workloads to standard storage.',
                impact=f'Potential to migrate {potential_standard_storage:.1f}GB to cheaper storage',
                effort='medium',
                monthly_savings=monthly_savings,
                implementation_steps=[
                    'Identify workloads that don\'t require high IOPS',
                    'Create new PVCs with standard storage class',
                    'Migrate data from SSD to standard storage',
                    'Update applications to use new PVCs'
                ],
                risks=[
                    'Performance degradation for I/O intensive applications',
                    'Data migration complexity',
                    'Potential downtime during migration'
                ],
                resources_affected=[f"{pvc['namespace']}/{pvc['name']}" for pvc in ssd_pvcs]
            ))
        
        return recommendations
    
    def _analyze_cost_optimization(self, cluster_data: Dict[str, Any], cost_data: Dict[str, Any]) -> List[OptimizationRecommendation]:
        """Analyze general cost optimization opportunities"""
        recommendations = []
        
        # Recommend committed use discounts
        monthly_cost = cost_data['total_cost']
        if monthly_cost > 500:  # Only recommend for significant spend
            cud_savings = monthly_cost * 0.30  # Up to 30% savings with 1-year commitment
            
            recommendations.append(OptimizationRecommendation(
                category='cost_optimization',
                priority='high',
                title='Consider Committed Use Discounts (CUDs)',
                description=f'With monthly spend of ${monthly_cost:.2f}, '
                           f'committed use discounts could provide significant savings.',
                impact='Up to 30% reduction in compute costs',
                effort='low',
                monthly_savings=cud_savings,
                implementation_steps=[
                    'Analyze historical usage patterns',
                    'Purchase 1-year or 3-year committed use discounts',
                    'Monitor usage to ensure commitment utilization',
                    'Adjust commitments based on growth patterns'
                ],
                risks=[
                    'Commitment to minimum usage levels',
                    'Reduced flexibility for scaling down',
                    'Penalty for under-utilization'
                ],
                resources_affected=['billing-account']
            ))
        
        return recommendations
    
    def _analyze_performance_optimization(self, cluster_data: Dict[str, Any], cost_data: Dict[str, Any]) -> List[OptimizationRecommendation]:
        """Analyze performance optimization opportunities"""
        recommendations = []
        
        # Recommend resource limits
        pods_without_limits = [
            pod for pod in cluster_data['pods'] 
            if pod.cpu_request > 0 and not hasattr(pod, 'cpu_limit')  # Simplified check
        ]
        
        if len(pods_without_limits) > len(cluster_data['pods']) * 0.3:  # More than 30% without limits
            recommendations.append(OptimizationRecommendation(
                category='performance_optimization',
                priority='medium',
                title='Set resource limits for better resource management',
                description=f'Many pods lack resource limits, which can lead to resource contention.',
                impact='Improved cluster stability and resource utilization',
                effort='medium',
                monthly_savings=0,  # Performance benefit, not direct cost savings
                implementation_steps=[
                    'Analyze application resource usage patterns',
                    'Set appropriate CPU and memory limits',
                    'Implement resource quotas at namespace level',
                    'Monitor for resource throttling'
                ],
                risks=[
                    'Application throttling if limits are too low',
                    'Need careful tuning based on workload patterns',
                    'Potential performance impact'
                ],
                resources_affected=['cluster-wide']
            ))
        
        return recommendations
    
    def _parse_storage_size(self, size_str: str) -> float:
        """Parse storage size string to GB"""
        if not size_str:
            return 0.0
        
        size_str = size_str.upper()
        if size_str.endswith('GI'):
            return float(size_str[:-2])
        elif size_str.endswith('G'):
            return float(size_str[:-1])
        elif size_str.endswith('TI'):
            return float(size_str[:-2]) * 1024
        elif size_str.endswith('T'):
            return float(size_str[:-1]) * 1000
        elif size_str.endswith('MI'):
            return float(size_str[:-2]) / 1024
        elif size_str.endswith('M'):
            return float(size_str[:-1]) / 1000
        else:
            return float(size_str) / (1024**3)  # Assume bytes