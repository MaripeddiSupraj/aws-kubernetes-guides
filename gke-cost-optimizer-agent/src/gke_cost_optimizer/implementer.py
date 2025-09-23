"""
Cost Optimization Implementer - Applies recommendations step by step
"""

import subprocess
import yaml
from typing import Dict, List, Any
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
from rich.table import Table

console = Console()

class CostOptimizationImplementer:
    def __init__(self, project_id: str, cluster_name: str, zone: str):
        self.project_id = project_id
        self.cluster_name = cluster_name
        self.zone = zone
    
    def implement_recommendations(self, recommendations: Dict[str, List[Any]]):
        """Implement cost optimization recommendations step by step"""
        
        console.print("🚀 GKE Cost Optimization Implementation", style="bold green")
        console.print("=" * 50)
        
        # Step 1: Committed Use Discounts
        if recommendations.get('cost_optimization'):
            self._implement_cuds(recommendations['cost_optimization'])
        
        # Step 2: Memory Rightsizing
        if recommendations.get('rightsizing'):
            self._implement_rightsizing(recommendations['rightsizing'])
        
        # Step 3: Node Optimization
        if recommendations.get('node_optimization'):
            self._implement_node_optimization(recommendations['node_optimization'])
        
        console.print("\n✅ Implementation complete!", style="bold green")
    
    def _implement_cuds(self, cud_recommendations: List[Any]):
        """Implement Committed Use Discounts"""
        
        panel = Panel(
            "💰 Step 1: Committed Use Discounts\n\n"
            "Potential Savings: $1,484/month\n"
            "Risk: Low | Effort: Low\n\n"
            "This will purchase 1-year compute commitments for 30% discount.",
            title="Committed Use Discounts",
            border_style="green"
        )
        console.print(panel)
        
        if Confirm.ask("Do you want to implement Committed Use Discounts?"):
            console.print("📋 CUD Implementation Steps:")
            console.print("1. Analyzing current usage patterns...")
            
            # Get current usage
            usage_cmd = f"gcloud compute commitments list --project={self.project_id}"
            console.print(f"   Running: {usage_cmd}")
            
            console.print("2. Recommended CUD purchase:")
            console.print("   • 1-year commitment for e2-standard-4 instances")
            console.print("   • Region: us-east1")
            console.print("   • vCPUs: 12 (3 nodes × 4 vCPUs)")
            
            if Confirm.ask("   Execute CUD purchase command?"):
                cud_cmd = (
                    f"gcloud compute commitments create gke-cluster-commitment "
                    f"--project={self.project_id} "
                    f"--region=us-east1 "
                    f"--plan=12-month "
                    f"--type=general-purpose-e2 "
                    f"--resources=vcpu=12,memory=48GB"
                )
                console.print(f"   Command: {cud_cmd}")
                
                if Confirm.ask("   Confirm execution?"):
                    try:
                        result = subprocess.run(cud_cmd.split(), capture_output=True, text=True)
                        if result.returncode == 0:
                            console.print("   ✅ CUD created successfully!", style="green")
                            console.print("   💰 Expected savings: $1,484/month")
                        else:
                            console.print(f"   ❌ Error: {result.stderr}", style="red")
                    except Exception as e:
                        console.print(f"   ❌ Error executing command: {e}", style="red")
                else:
                    console.print("   ⏭️  Skipped CUD creation")
            else:
                console.print("   ⏭️  Skipped CUD purchase")
        else:
            console.print("⏭️  Skipped Committed Use Discounts")
    
    def _implement_rightsizing(self, rightsizing_recommendations: List[Any]):
        """Implement pod rightsizing recommendations"""
        
        panel = Panel(
            "🎯 Step 2: Pod Memory Rightsizing\n\n"
            "Potential Savings: $1.01/month\n"
            "Risk: Medium | Effort: Low\n\n"
            "This will reduce memory requests for over-provisioned pods.",
            title="Memory Rightsizing",
            border_style="yellow"
        )
        console.print(panel)
        
        for rec in rightsizing_recommendations:
            console.print(f"\n📦 Pod: {rec.get('title', 'Unknown')}")
            console.print(f"   Savings: ${rec.get('monthly_savings', 0):.2f}/month")
            console.print(f"   Current: 2.00GB → Recommended: 0.33GB")
            
            if Confirm.ask(f"   Implement rightsizing for this pod?"):
                self._rightsize_pod(rec)
            else:
                console.print("   ⏭️  Skipped this pod")
    
    def _rightsize_pod(self, recommendation: Dict[str, Any]):
        """Rightsize a specific pod"""
        
        # Extract pod and namespace info
        resources_affected = recommendation.get('resources_affected', [])
        if not resources_affected:
            console.print("   ❌ No resource information found", style="red")
            return
        
        resource = resources_affected[0]  # e.g., "harness-delegate-ng/kubernetes-delegate-7c47b5b4f7-pkgtz"
        
        if '/' in resource:
            namespace, pod_name = resource.split('/', 1)
            
            # Get the deployment name (remove replica set suffix)
            deployment_name = pod_name.rsplit('-', 2)[0] if '-' in pod_name else pod_name
            
            console.print(f"   📝 Updating deployment: {deployment_name}")
            console.print(f"   📍 Namespace: {namespace}")
            
            # Get current deployment
            get_cmd = f"kubectl get deployment {deployment_name} -n {namespace} -o yaml"
            console.print(f"   Getting deployment: {get_cmd}")
            
            try:
                result = subprocess.run(get_cmd.split(), capture_output=True, text=True)
                if result.returncode == 0:
                    # Parse and modify the deployment
                    deployment = yaml.safe_load(result.stdout)
                    
                    # Update memory request
                    containers = deployment['spec']['template']['spec']['containers']
                    for container in containers:
                        if 'resources' not in container:
                            container['resources'] = {}
                        if 'requests' not in container['resources']:
                            container['resources']['requests'] = {}
                        
                        # Update memory request
                        container['resources']['requests']['memory'] = '350Mi'  # 0.33GB ≈ 350Mi
                    
                    # Save to temp file
                    temp_file = f"/tmp/{deployment_name}-updated.yaml"
                    with open(temp_file, 'w') as f:
                        yaml.dump(deployment, f)
                    
                    console.print(f"   💾 Saved updated deployment to: {temp_file}")
                    
                    if Confirm.ask("   Apply the updated deployment?"):
                        apply_cmd = f"kubectl apply -f {temp_file}"
                        apply_result = subprocess.run(apply_cmd.split(), capture_output=True, text=True)
                        
                        if apply_result.returncode == 0:
                            console.print("   ✅ Deployment updated successfully!", style="green")
                            console.print("   📊 Monitor pod for OOMKilled events")
                            console.print(f"   💰 Expected savings: ${recommendation.get('monthly_savings', 0):.2f}/month")
                        else:
                            console.print(f"   ❌ Error applying deployment: {apply_result.stderr}", style="red")
                    else:
                        console.print("   ⏭️  Skipped deployment update")
                        console.print(f"   📄 Manual file available at: {temp_file}")
                
                else:
                    console.print(f"   ❌ Error getting deployment: {result.stderr}", style="red")
                    
            except Exception as e:
                console.print(f"   ❌ Error processing deployment: {e}", style="red")
    
    def _implement_node_optimization(self, node_recommendations: List[Any]):
        """Implement node optimization recommendations"""
        
        panel = Panel(
            "🖥️  Step 3: Node Optimization\n\n"
            "Potential Savings: $2,283/month\n"
            "Risk: High | Effort: Medium-High\n\n"
            "This includes node consolidation and preemptible instances.",
            title="Node Optimization",
            border_style="red"
        )
        console.print(panel)
        
        for rec in node_recommendations:
            title = rec.get('title', 'Unknown')
            savings = rec.get('monthly_savings', 0)
            
            console.print(f"\n🎯 {title}")
            console.print(f"   Savings: ${savings:.2f}/month")
            console.print(f"   Effort: {rec.get('effort', 'unknown')}")
            
            if 'consolidate' in title.lower():
                self._implement_node_consolidation(rec)
            elif 'preemptible' in title.lower():
                self._implement_preemptible_nodes(rec)
    
    def _implement_node_consolidation(self, recommendation: Dict[str, Any]):
        """Implement node consolidation"""
        
        console.print("   📋 Node Consolidation Steps:")
        console.print("   1. Enable cluster autoscaler")
        console.print("   2. Set minimum nodes to 1")
        console.print("   3. Monitor pod scheduling")
        
        if Confirm.ask("   Enable cluster autoscaler?"):
            autoscaler_cmd = (
                f"gcloud container clusters update {self.cluster_name} "
                f"--project={self.project_id} "
                f"--zone={self.zone} "
                f"--enable-autoscaling "
                f"--min-nodes=1 "
                f"--max-nodes=5"
            )
            
            console.print(f"   Command: {autoscaler_cmd}")
            
            if Confirm.ask("   Execute autoscaler command?"):
                try:
                    result = subprocess.run(autoscaler_cmd.split(), capture_output=True, text=True)
                    if result.returncode == 0:
                        console.print("   ✅ Cluster autoscaler enabled!", style="green")
                        console.print("   📊 Monitor for automatic node scaling")
                    else:
                        console.print(f"   ❌ Error: {result.stderr}", style="red")
                except Exception as e:
                    console.print(f"   ❌ Error: {e}", style="red")
            else:
                console.print("   ⏭️  Skipped autoscaler setup")
        else:
            console.print("   ⏭️  Skipped node consolidation")
    
    def _implement_preemptible_nodes(self, recommendation: Dict[str, Any]):
        """Implement preemptible node pool"""
        
        console.print("   📋 Preemptible Nodes Steps:")
        console.print("   1. Create preemptible node pool")
        console.print("   2. Add node selectors to suitable workloads")
        console.print("   3. Test workload resilience")
        
        if Confirm.ask("   Create preemptible node pool?"):
            pool_cmd = (
                f"gcloud container node-pools create preemptible-pool "
                f"--project={self.project_id} "
                f"--cluster={self.cluster_name} "
                f"--zone={self.zone} "
                f"--machine-type=e2-standard-2 "
                f"--preemptible "
                f"--num-nodes=1 "
                f"--enable-autoscaling "
                f"--min-nodes=0 "
                f"--max-nodes=3"
            )
            
            console.print(f"   Command: {pool_cmd}")
            
            if Confirm.ask("   Execute node pool creation?"):
                try:
                    result = subprocess.run(pool_cmd.split(), capture_output=True, text=True)
                    if result.returncode == 0:
                        console.print("   ✅ Preemptible node pool created!", style="green")
                        console.print("   📝 Next: Add nodeSelector to suitable workloads")
                        console.print("   💡 Example: nodeSelector: { 'cloud.google.com/gke-preemptible': 'true' }")
                    else:
                        console.print(f"   ❌ Error: {result.stderr}", style="red")
                except Exception as e:
                    console.print(f"   ❌ Error: {e}", style="red")
            else:
                console.print("   ⏭️  Skipped node pool creation")
        else:
            console.print("   ⏭️  Skipped preemptible nodes")
    
    def show_implementation_summary(self, recommendations: Dict[str, List[Any]]):
        """Show implementation summary"""
        
        table = Table(title="🎯 Implementation Summary")
        table.add_column("Step", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Savings", justify="right", style="green")
        table.add_column("Risk", style="yellow")
        
        total_savings = 0
        
        # Add each recommendation type
        for category, recs in recommendations.items():
            if recs:
                category_savings = sum(rec.get('monthly_savings', 0) for rec in recs)
                total_savings += category_savings
                
                table.add_row(
                    category.replace('_', ' ').title(),
                    "Ready",
                    f"${category_savings:.2f}/month",
                    "Low-High"
                )
        
        console.print(table)
        console.print(f"\n💰 Total Potential Savings: ${total_savings:.2f}/month", style="bold green")
        console.print(f"📈 Annual Savings: ${total_savings * 12:.2f}", style="bold green")