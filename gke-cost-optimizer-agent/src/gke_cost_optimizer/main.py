#!/usr/bin/env python3
"""
GKE Cost Optimizer Agent - Main Entry Point
Orchestrates cluster scanning, cost analysis, and optimization recommendations.
"""

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

from .cluster_scanner import ClusterScanner
from .cost_analyzer import CostAnalyzer
from .optimizer import CostOptimizer
from .reporter import ReportGenerator
from .implementer import CostOptimizationImplementer

# Load environment variables
load_dotenv()

console = Console()

class GKECostOptimizerAgent:
    def __init__(self, project_id: str, cluster_name: str, zone: str):
        self.project_id = project_id
        self.cluster_name = cluster_name
        self.zone = zone
        
        # Initialize components
        self.scanner = ClusterScanner(project_id, cluster_name, zone)
        self.cost_analyzer = CostAnalyzer(project_id)
        self.optimizer = CostOptimizer()
        self.reporter = ReportGenerator()
    
    async def run_optimization_cycle(self):
        """Run a complete optimization cycle"""
        console.print("🚀 Starting GKE Cost Optimization Analysis...", style="bold green")
        
        try:
            # Step 1: Scan cluster resources
            console.print("📊 Scanning cluster resources...")
            cluster_data = await self.scanner.scan_cluster()
            
            # Step 2: Analyze costs
            console.print("💰 Analyzing cost data...")
            cost_data = await self.cost_analyzer.get_cluster_costs()
            
            # Step 3: Generate optimization recommendations
            console.print("🎯 Generating optimization recommendations...")
            recommendations = self.optimizer.analyze_and_recommend(cluster_data, cost_data)
            
            # Step 4: Generate report
            console.print("📋 Generating optimization report...")
            report = self.reporter.generate_report(recommendations, cluster_data, cost_data)
            
            # Display summary
            self._display_summary(recommendations)
            
            return {
                'recommendations': recommendations,
                'cluster_data': cluster_data,
                'cost_data': cost_data,
                'report': report
            }
            
        except Exception as e:
            console.print(f"❌ Error during optimization cycle: {str(e)}", style="bold red")
            raise

    def _display_summary(self, recommendations):
        """Display optimization summary"""
        table = Table(title="💡 Cost Optimization Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Issues Found", justify="right")
        table.add_column("Potential Savings", justify="right", style="green")
        
        total_savings = 0
        for category, items in recommendations.items():
            if items:
                savings = sum(getattr(item, 'monthly_savings', 0) for item in items)
                total_savings += savings
                table.add_row(
                    category.replace('_', ' ').title(),
                    str(len(items)),
                    f"${savings:.2f}/month"
                )
        
        console.print(table)
        console.print(f"\n💰 Total Potential Monthly Savings: ${total_savings:.2f}", style="bold green")

@click.command()
@click.option('--project-id', default=lambda: os.getenv('GCP_PROJECT_ID'), 
              help='GCP Project ID')
@click.option('--cluster-name', default=lambda: os.getenv('GKE_CLUSTER_NAME'), 
              help='GKE Cluster Name')
@click.option('--zone', default=lambda: os.getenv('GCP_ZONE'), 
              help='GCP Zone')
@click.option('--continuous', is_flag=True, 
              help='Run in continuous mode (every 6 hours)')
@click.option('--output', default='reports', 
              help='Output directory for reports')
@click.option('--implement', is_flag=True,
              help='Implement recommendations step by step')
def main(project_id, cluster_name, zone, continuous, output, implement):
    """GKE Cost Optimizer Agent - Intelligent cluster cost optimization"""
    
    if not all([project_id, cluster_name, zone]):
        console.print("❌ Missing required parameters. Set environment variables or use CLI options.", 
                     style="bold red")
        console.print("Required: GCP_PROJECT_ID, GKE_CLUSTER_NAME, GCP_ZONE")
        sys.exit(1)
    
    # Create output directory
    Path(output).mkdir(exist_ok=True)
    
    agent = GKECostOptimizerAgent(project_id, cluster_name, zone)
    
    if implement:
        # Run analysis first, then implement
        report = asyncio.run(agent.run_optimization_cycle())
        
        # Implement recommendations
        implementer = CostOptimizationImplementer(project_id, cluster_name, zone)
        implementer.implement_recommendations(report.get('recommendations', {}))
        
    elif continuous:
        console.print("🔄 Running in continuous mode (every 6 hours)...")
        while True:
            try:
                asyncio.run(agent.run_optimization_cycle())
                console.print("😴 Sleeping for 6 hours...", style="dim")
                asyncio.sleep(6 * 3600)  # 6 hours
            except KeyboardInterrupt:
                console.print("\n👋 Stopping continuous mode...", style="yellow")
                break
    else:
        # Single run
        asyncio.run(agent.run_optimization_cycle())

if __name__ == "__main__":
    main()