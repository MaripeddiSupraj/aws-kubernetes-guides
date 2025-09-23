"""
GKE Cluster Scanner - Analyzes Kubernetes resources for optimization opportunities
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass

from kubernetes import client, config
from google.cloud import container_v1
from google.cloud import monitoring_v3

@dataclass
class ResourceMetrics:
    name: str
    namespace: str
    cpu_request: float
    memory_request: float
    cpu_usage: float
    memory_usage: float
    cpu_utilization: float
    memory_utilization: float

class ClusterScanner:
    def __init__(self, project_id: str, cluster_name: str, zone: str):
        self.project_id = project_id
        self.cluster_name = cluster_name
        self.zone = zone
        
        # Initialize clients
        self._init_kubernetes_client()
        self.container_client = container_v1.ClusterManagerClient()
        self.monitoring_client = monitoring_v3.MetricServiceClient()
    
    def _init_kubernetes_client(self):
        """Initialize Kubernetes client for GKE"""
        try:
            # Try in-cluster config first
            config.load_incluster_config()
        except:
            # Fall back to local kubeconfig
            config.load_kube_config()
        
        self.k8s_core = client.CoreV1Api()
        self.k8s_apps = client.AppsV1Api()
        self.k8s_metrics = client.CustomObjectsApi()
    
    async def scan_cluster(self) -> Dict[str, Any]:
        """Perform comprehensive cluster scan"""
        cluster_data = {
            'timestamp': datetime.now().isoformat(),
            'cluster_info': await self._get_cluster_info(),
            'nodes': await self._analyze_nodes(),
            'pods': await self._analyze_pods(),
            'pvcs': await self._analyze_pvcs(),
            'services': await self._analyze_services(),
            'resource_quotas': await self._get_resource_quotas(),
            'metrics_summary': {}
        }
        
        # Calculate summary metrics
        cluster_data['metrics_summary'] = self._calculate_summary_metrics(cluster_data)
        
        return cluster_data
    
    async def _get_cluster_info(self) -> Dict[str, Any]:
        """Get basic cluster information"""
        cluster_path = f"projects/{self.project_id}/locations/{self.zone}/clusters/{self.cluster_name}"
        cluster = self.container_client.get_cluster(name=cluster_path)
        
        return {
            'name': cluster.name,
            'status': cluster.status.name,
            'node_count': cluster.current_node_count,
            'machine_type': cluster.node_pools[0].config.machine_type if cluster.node_pools else 'unknown',
            'kubernetes_version': cluster.current_master_version,
            'location': cluster.location
        }
    
    async def _analyze_nodes(self) -> List[Dict[str, Any]]:
        """Analyze node utilization and costs"""
        nodes = self.k8s_core.list_node()
        node_data = []
        
        for node in nodes.items:
            # Get node metrics
            node_metrics = await self._get_node_metrics(node.metadata.name)
            
            # Calculate allocatable vs requested resources
            allocatable = node.status.allocatable
            capacity = node.status.capacity
            
            node_info = {
                'name': node.metadata.name,
                'machine_type': node.metadata.labels.get('node.kubernetes.io/instance-type', 'unknown'),
                'zone': node.metadata.labels.get('topology.kubernetes.io/zone', 'unknown'),
                'capacity': {
                    'cpu': self._parse_cpu(capacity.get('cpu', '0')),
                    'memory': self._parse_memory(capacity.get('memory', '0'))
                },
                'allocatable': {
                    'cpu': self._parse_cpu(allocatable.get('cpu', '0')),
                    'memory': self._parse_memory(allocatable.get('memory', '0'))
                },
                'usage': node_metrics,
                'pods_count': len([p for p in self.k8s_core.list_pod_for_all_namespaces().items 
                                 if p.spec.node_name == node.metadata.name]),
                'created': node.metadata.creation_timestamp.isoformat() if node.metadata.creation_timestamp else None
            }
            
            # Calculate utilization percentages
            if node_info['allocatable']['cpu'] > 0:
                node_info['cpu_utilization'] = (node_metrics['cpu'] / node_info['allocatable']['cpu']) * 100
            if node_info['allocatable']['memory'] > 0:
                node_info['memory_utilization'] = (node_metrics['memory'] / node_info['allocatable']['memory']) * 100
            
            node_data.append(node_info)
        
        return node_data
    
    async def _analyze_pods(self) -> List[ResourceMetrics]:
        """Analyze pod resource requests vs actual usage"""
        pods = self.k8s_core.list_pod_for_all_namespaces()
        pod_metrics = []
        
        for pod in pods.items:
            if pod.status.phase != 'Running':
                continue
            
            # Get pod resource requests
            cpu_request = 0
            memory_request = 0
            
            for container in pod.spec.containers:
                if container.resources and container.resources.requests:
                    cpu_request += self._parse_cpu(container.resources.requests.get('cpu', '0'))
                    memory_request += self._parse_memory(container.resources.requests.get('memory', '0'))
            
            # Get actual usage metrics
            usage_metrics = await self._get_pod_metrics(pod.metadata.name, pod.metadata.namespace)
            
            if cpu_request > 0 or memory_request > 0:  # Only include pods with resource requests
                metrics = ResourceMetrics(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    cpu_request=cpu_request,
                    memory_request=memory_request,
                    cpu_usage=usage_metrics['cpu'],
                    memory_usage=usage_metrics['memory'],
                    cpu_utilization=(usage_metrics['cpu'] / cpu_request * 100) if cpu_request > 0 else 0,
                    memory_utilization=(usage_metrics['memory'] / memory_request * 100) if memory_request > 0 else 0
                )
                pod_metrics.append(metrics)
        
        return pod_metrics
    
    async def _analyze_pvcs(self) -> List[Dict[str, Any]]:
        """Analyze Persistent Volume Claims for unused storage"""
        pvcs = self.k8s_core.list_persistent_volume_claim_for_all_namespaces()
        pvc_data = []
        
        for pvc in pvcs.items:
            # Check if PVC is actually used by any pod
            pods_using_pvc = []
            all_pods = self.k8s_core.list_pod_for_all_namespaces()
            
            for pod in all_pods.items:
                if pod.spec.volumes:
                    for volume in pod.spec.volumes:
                        if (volume.persistent_volume_claim and 
                            volume.persistent_volume_claim.claim_name == pvc.metadata.name and
                            pod.metadata.namespace == pvc.metadata.namespace):
                            pods_using_pvc.append(pod.metadata.name)
            
            pvc_info = {
                'name': pvc.metadata.name,
                'namespace': pvc.metadata.namespace,
                'size': pvc.spec.resources.requests.get('storage', '0'),
                'storage_class': pvc.spec.storage_class_name,
                'status': pvc.status.phase,
                'used_by_pods': pods_using_pvc,
                'is_unused': len(pods_using_pvc) == 0,
                'created': pvc.metadata.creation_timestamp.isoformat() if pvc.metadata.creation_timestamp else None
            }
            
            pvc_data.append(pvc_info)
        
        return pvc_data
    
    async def _analyze_services(self) -> List[Dict[str, Any]]:
        """Analyze services for unused load balancers"""
        services = self.k8s_core.list_service_for_all_namespaces()
        service_data = []
        
        for service in services.items:
            if service.spec.type == 'LoadBalancer':
                # Check if service has endpoints
                try:
                    endpoints = self.k8s_core.read_namespaced_endpoints(
                        name=service.metadata.name,
                        namespace=service.metadata.namespace
                    )
                    has_endpoints = bool(endpoints.subsets)
                except:
                    has_endpoints = False
                
                service_info = {
                    'name': service.metadata.name,
                    'namespace': service.metadata.namespace,
                    'type': service.spec.type,
                    'external_ip': service.status.load_balancer.ingress[0].ip if (
                        service.status.load_balancer and service.status.load_balancer.ingress
                    ) else None,
                    'has_endpoints': has_endpoints,
                    'is_unused': not has_endpoints,
                    'created': service.metadata.creation_timestamp.isoformat() if service.metadata.creation_timestamp else None
                }
                
                service_data.append(service_info)
        
        return service_data
    
    async def _get_resource_quotas(self) -> List[Dict[str, Any]]:
        """Get resource quotas for all namespaces"""
        quotas = self.k8s_core.list_resource_quota_for_all_namespaces()
        quota_data = []
        
        for quota in quotas.items:
            quota_info = {
                'name': quota.metadata.name,
                'namespace': quota.metadata.namespace,
                'hard_limits': dict(quota.spec.hard) if quota.spec.hard else {},
                'used': dict(quota.status.used) if quota.status.used else {}
            }
            quota_data.append(quota_info)
        
        return quota_data
    
    async def _get_node_metrics(self, node_name: str) -> Dict[str, float]:
        """Get node resource usage metrics"""
        try:
            # This would typically use metrics-server or monitoring API
            # For now, return mock data - in production, integrate with GCP Monitoring
            return {
                'cpu': 0.5,  # 0.5 cores
                'memory': 2 * 1024 * 1024 * 1024  # 2GB in bytes
            }
        except Exception:
            return {'cpu': 0, 'memory': 0}
    
    async def _get_pod_metrics(self, pod_name: str, namespace: str) -> Dict[str, float]:
        """Get pod resource usage metrics"""
        try:
            # This would typically use metrics-server API
            # For now, return mock data - in production, integrate with GCP Monitoring
            return {
                'cpu': 0.1,  # 0.1 cores
                'memory': 256 * 1024 * 1024  # 256MB in bytes
            }
        except Exception:
            return {'cpu': 0, 'memory': 0}
    
    def _parse_cpu(self, cpu_str: str) -> float:
        """Parse CPU resource string to float (in cores)"""
        if not cpu_str or cpu_str == '0':
            return 0.0
        
        if cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1000
        elif cpu_str.endswith('n'):
            return float(cpu_str[:-1]) / 1000000000
        else:
            return float(cpu_str)
    
    def _parse_memory(self, memory_str: str) -> int:
        """Parse memory resource string to bytes"""
        if not memory_str or memory_str == '0':
            return 0
        
        units = {
            'Ki': 1024,
            'Mi': 1024**2,
            'Gi': 1024**3,
            'Ti': 1024**4,
            'K': 1000,
            'M': 1000**2,
            'G': 1000**3,
            'T': 1000**4
        }
        
        for unit, multiplier in units.items():
            if memory_str.endswith(unit):
                return int(float(memory_str[:-len(unit)]) * multiplier)
        
        return int(memory_str)
    
    def _calculate_summary_metrics(self, cluster_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate cluster-wide summary metrics"""
        total_nodes = len(cluster_data['nodes'])
        total_pods = len(cluster_data['pods'])
        unused_pvcs = len([pvc for pvc in cluster_data['pvcs'] if pvc['is_unused']])
        unused_services = len([svc for svc in cluster_data['services'] if svc['is_unused']])
        
        # Calculate average utilization
        if cluster_data['pods']:
            avg_cpu_util = sum(pod.cpu_utilization for pod in cluster_data['pods']) / len(cluster_data['pods'])
            avg_memory_util = sum(pod.memory_utilization for pod in cluster_data['pods']) / len(cluster_data['pods'])
        else:
            avg_cpu_util = avg_memory_util = 0
        
        return {
            'total_nodes': total_nodes,
            'total_pods': total_pods,
            'unused_pvcs': unused_pvcs,
            'unused_services': unused_services,
            'average_cpu_utilization': avg_cpu_util,
            'average_memory_utilization': avg_memory_util,
            'optimization_opportunities': unused_pvcs + unused_services + 
                                        len([pod for pod in cluster_data['pods'] 
                                            if pod.cpu_utilization < 20 or pod.memory_utilization < 20])
        }