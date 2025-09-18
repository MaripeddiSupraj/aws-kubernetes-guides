# Cilium with EKS Complete Guide: Advanced Networking & Security

A comprehensive guide for implementing Cilium CNI on Amazon EKS with all major features, real-world examples, and production-ready configurations.

## 📋 Table of Contents

1. [Cilium Overview & Architecture](#cilium-overview--architecture)
2. [EKS Cluster Setup with Cilium](#eks-cluster-setup-with-cilium)
3. [Network Policies](#network-policies)
4. [Service Mesh Features](#service-mesh-features)
5. [Load Balancing & Ingress](#load-balancing--ingress)
6. [Observability & Monitoring](#observability--monitoring)
7. [Security Features](#security-features)
8. [Multi-Cluster Networking](#multi-cluster-networking)
9. [Troubleshooting](#troubleshooting)

## 🏗️ Cilium Overview & Architecture

### What is Cilium?
Cilium is an eBPF-based networking, observability, and security solution for Kubernetes that provides:
- High-performance networking
- Advanced network policies
- Service mesh capabilities
- Deep observability
- Multi-cluster connectivity

### Real-World Use Case: E-commerce Platform
```
┌─────────────────────────────────────────────────────────────┐
│                    EKS Cluster with Cilium                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Frontend  │  │   Backend   │  │  Database   │        │
│  │   (React)   │──│   (API)     │──│  (PostgreSQL)│        │
│  │             │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                 │                 │             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Cilium eBPF Data Path                     │ │
│  │  • Network Policies  • Load Balancing                  │ │
│  │  • Service Mesh      • Observability                   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 EKS Cluster Setup with Cilium

### Step 1: Create EKS Cluster without Default CNI
```bash
# Create cluster configuration
cat > cilium-cluster.yaml <<EOF
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: cilium-demo
  region: us-west-2
  version: "1.28"

vpc:
  cidr: "10.0.0.0/16"
  nat:
    gateway: Single

nodeGroups:
  - name: cilium-nodes
    instanceType: m5.large
    desiredCapacity: 3
    minSize: 1
    maxSize: 5
    volumeSize: 50
    ssh:
      allow: true
    labels:
      node-type: cilium-worker
    tags:
      Environment: production
      Project: cilium-demo

# Disable default VPC CNI
addons:
  - name: vpc-cni
    version: latest
    configurationValues: |-
      env:
        ENABLE_POD_ENI: "false"
EOF

# Create cluster
eksctl create cluster -f cilium-cluster.yaml --without-nodegroup
eksctl create nodegroup -f cilium-cluster.yaml
```

### Step 2: Install Cilium CNI
```bash
# Add Cilium Helm repository
helm repo add cilium https://helm.cilium.io/
helm repo update

# Install Cilium with EKS-specific configuration
helm install cilium cilium/cilium \
  --version 1.14.5 \
  --namespace kube-system \
  --set eni.enabled=true \
  --set ipam.mode=eni \
  --set egressMasqueradeInterfaces=eth0 \
  --set tunnel=disabled \
  --set nodeinit.enabled=true \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true \
  --set prometheus.enabled=true \
  --set operator.prometheus.enabled=true \
  --set envoy.enabled=true \
  --set loadBalancer.algorithm=maglev \
  --set bpf.masquerade=true \
  --set encryption.enabled=true \
  --set encryption.type=wireguard
```

### Step 3: Verify Installation
```bash
# Check Cilium status
cilium status --wait

# Verify connectivity
cilium connectivity test

# Check Hubble status
cilium hubble port-forward &
hubble status
```

## 🛡️ Network Policies

### 1. Basic Network Policy - Deny All
```yaml
# deny-all-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to: []
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
```

### 2. Cilium Network Policy - Advanced L7 Rules
```yaml
# l7-http-policy.yaml
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: frontend-backend-l7
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: backend-api
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:
        - method: "GET"
          path: "/api/v1/.*"
        - method: "POST"
          path: "/api/v1/orders"
          headers:
          - "Content-Type: application/json"
        - method: "PUT"
          path: "/api/v1/users/[0-9]+"
```

### 3. Database Access Policy
```yaml
# database-policy.yaml
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: database-access
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: postgresql
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: backend-api
    - matchLabels:
        app: analytics-service
    toPorts:
    - ports:
      - port: "5432"
        protocol: TCP
  egress:
  - toEndpoints:
    - matchLabels:
        k8s:io.kubernetes.pod.namespace: kube-system
        k8s-app: kube-dns
    toPorts:
    - ports:
      - port: "53"
        protocol: UDP
```

### 4. External Service Access Policy
```yaml
# external-api-policy.yaml
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: external-api-access
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: payment-service
  egress:
  - toFQDNs:
    - matchName: "api.stripe.com"
    - matchName: "api.paypal.com"
    - matchPattern: "*.amazonaws.com"
  - toServices:
    - k8sService:
        serviceName: payment-gateway
        namespace: production
  - toCIDR:
    - "203.0.113.0/24"  # Partner API network
    toPorts:
    - ports:
      - port: "443"
        protocol: TCP
```

## 🔗 Service Mesh Features

### 1. Enable Envoy Proxy
```bash
# Enable Envoy for service mesh features
helm upgrade cilium cilium/cilium \
  --namespace kube-system \
  --reuse-values \
  --set envoy.enabled=true \
  --set loadBalancer.l7.backend=envoy
```

### 2. Ingress Controller with Cilium
```yaml
# cilium-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ecommerce-ingress
  namespace: production
  annotations:
    ingress.cilium.io/loadbalancer-mode: shared
    ingress.cilium.io/service-type: LoadBalancer
spec:
  ingressClassName: cilium
  rules:
  - host: api.ecommerce.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8080
  tls:
  - hosts:
    - api.ecommerce.com
    secretName: ecommerce-tls
```

### 3. Traffic Management with CiliumEnvoyConfig
```yaml
# traffic-management.yaml
apiVersion: cilium.io/v2
kind: CiliumEnvoyConfig
metadata:
  name: backend-traffic-management
  namespace: production
spec:
  services:
  - name: backend-service
    namespace: production
  resources:
  - "@type": type.googleapis.com/envoy.config.route.v3.RouteConfiguration
    name: backend-route
    virtual_hosts:
    - name: backend
      domains: ["*"]
      routes:
      - match:
          prefix: "/api/v1"
        route:
          weighted_clusters:
            clusters:
            - name: backend-v1
              weight: 80
            - name: backend-v2
              weight: 20
      - match:
          prefix: "/health"
        route:
          cluster: backend-v1
        timeout: 5s
```

### 4. Rate Limiting Configuration
```yaml
# rate-limiting.yaml
apiVersion: cilium.io/v2
kind: CiliumEnvoyConfig
metadata:
  name: api-rate-limiting
  namespace: production
spec:
  services:
  - name: backend-service
  resources:
  - "@type": type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
    stat_prefix: local_rate_limiter
    token_bucket:
      max_tokens: 100
      tokens_per_fill: 100
      fill_interval: 60s
    filter_enabled:
      runtime_key: local_rate_limit_enabled
      default_value:
        numerator: 100
        denominator: HUNDRED
    filter_enforced:
      runtime_key: local_rate_limit_enforced
      default_value:
        numerator: 100
        denominator: HUNDRED
```

## ⚖️ Load Balancing & Ingress

### 1. Cilium Load Balancer Configuration
```yaml
# cilium-lb-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cilium-config
  namespace: kube-system
data:
  enable-l7-proxy: "true"
  enable-envoy-config: "true"
  kube-proxy-replacement: "strict"
  enable-host-reachable-services: "true"
  enable-external-ips: "true"
  enable-node-port: "true"
  enable-health-check-nodeport: "true"
  node-port-bind-protection: "true"
  enable-auto-protect-node-port-range: "true"
  bpf-lb-algorithm: "maglev"
  bpf-lb-mode: "snat"
  bpf-lb-acceleration: "native"
```

### 2. Gateway API Implementation
```yaml
# gateway-api.yaml
apiVersion: gateway.networking.k8s.io/v1beta1
kind: Gateway
metadata:
  name: ecommerce-gateway
  namespace: production
spec:
  gatewayClassName: cilium
  listeners:
  - name: http
    port: 80
    protocol: HTTP
    hostname: "*.ecommerce.com"
  - name: https
    port: 443
    protocol: HTTPS
    hostname: "*.ecommerce.com"
    tls:
      mode: Terminate
      certificateRefs:
      - name: ecommerce-cert
---
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: ecommerce-routes
  namespace: production
spec:
  parentRefs:
  - name: ecommerce-gateway
  hostnames:
  - "api.ecommerce.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api/v1/products
    backendRefs:
    - name: product-service
      port: 8080
      weight: 100
  - matches:
    - path:
        type: PathPrefix
        value: /api/v1/orders
    backendRefs:
    - name: order-service
      port: 8080
      weight: 90
    - name: order-service-canary
      port: 8080
      weight: 10
```

### 3. Multi-Protocol Load Balancing
```yaml
# multi-protocol-lb.yaml
apiVersion: v1
kind: Service
metadata:
  name: grpc-service
  namespace: production
  annotations:
    service.cilium.io/lb-l4: "true"
    service.cilium.io/lb-l7: "grpc"
spec:
  type: LoadBalancer
  selector:
    app: grpc-backend
  ports:
  - name: grpc
    port: 9090
    targetPort: 9090
    protocol: TCP
---
apiVersion: cilium.io/v2
kind: CiliumEnvoyConfig
metadata:
  name: grpc-lb-config
  namespace: production
spec:
  services:
  - name: grpc-service
  resources:
  - "@type": type.googleapis.com/envoy.config.listener.v3.Listener
    name: grpc-listener
    address:
      socket_address:
        address: 0.0.0.0
        port_value: 9090
    filter_chains:
    - filters:
      - name: envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          codec_type: AUTO
          stat_prefix: grpc_stats
          http2_protocol_options:
            max_concurrent_streams: 100
```

## 📊 Observability & Monitoring

### 1. Hubble Configuration
```bash
# Enable Hubble with advanced features
helm upgrade cilium cilium/cilium \
  --namespace kube-system \
  --reuse-values \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true \
  --set hubble.metrics.enabled="{dns,drop,tcp,flow,icmp,http}" \
  --set hubble.export.fileMaxSizeMb=10 \
  --set hubble.export.fileMaxBackups=5
```

### 2. Prometheus Integration
```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-cilium-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'cilium-agent'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_k8s_app]
        action: keep
        regex: cilium
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
    - job_name: 'cilium-operator'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_name]
        action: keep
        regex: cilium-operator
    - job_name: 'hubble'
      kubernetes_sd_configs:
      - role: service
      relabel_configs:
      - source_labels: [__meta_kubernetes_service_name]
        action: keep
        regex: hubble-metrics
```

### 3. Grafana Dashboards
```yaml
# grafana-dashboard-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cilium-dashboards
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  cilium-overview.json: |
    {
      "dashboard": {
        "id": null,
        "title": "Cilium Overview",
        "panels": [
          {
            "title": "Network Policy Drops",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(cilium_drop_count_total[5m])",
                "legendFormat": "{{reason}}"
              }
            ]
          },
          {
            "title": "BPF Map Pressure",
            "type": "graph",
            "targets": [
              {
                "expr": "cilium_bpf_map_pressure",
                "legendFormat": "{{map_name}}"
              }
            ]
          }
        ]
      }
    }
```

### 4. Custom Metrics and Alerts
```yaml
# cilium-alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: cilium-alerts
  namespace: monitoring
spec:
  groups:
  - name: cilium
    rules:
    - alert: CiliumAgentDown
      expr: up{job="cilium-agent"} == 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Cilium agent is down"
        description: "Cilium agent on {{ $labels.instance }} has been down for more than 5 minutes"
    
    - alert: HighNetworkPolicyDrops
      expr: rate(cilium_drop_count_total[5m]) > 10
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "High network policy drop rate"
        description: "Network policy drops are {{ $value }} per second on {{ $labels.instance }}"
    
    - alert: BPFMapPressureHigh
      expr: cilium_bpf_map_pressure > 0.8
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "BPF map pressure is high"
        description: "BPF map {{ $labels.map_name }} pressure is {{ $value }} on {{ $labels.instance }}"
```

## 🔒 Security Features

### 1. Transparent Encryption with WireGuard
```bash
# Enable WireGuard encryption
helm upgrade cilium cilium/cilium \
  --namespace kube-system \
  --reuse-values \
  --set encryption.enabled=true \
  --set encryption.type=wireguard \
  --set encryption.wireguard.userspaceFallback=true

# Verify encryption
cilium status | grep Encryption
kubectl -n kube-system exec ds/cilium -- cilium encrypt status
```

### 2. Identity-Based Security
```yaml
# identity-policy.yaml
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: identity-based-policy
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: payment-service
  ingress:
  - fromEndpoints:
    - matchLabels:
        security.cilium.io/class: "trusted"
        app: order-service
  egress:
  - toEndpoints:
    - matchLabels:
        security.cilium.io/class: "database"
        app: postgresql
  - toFQDNs:
    - matchName: "secure-api.bank.com"
    toPorts:
    - ports:
      - port: "443"
        protocol: TCP
```

### 3. Runtime Security with Tetragon
```bash
# Install Tetragon for runtime security
helm repo add cilium https://helm.cilium.io
helm install tetragon cilium/tetragon \
  --namespace kube-system \
  --set tetragon.enabled=true \
  --set tetragon.grpc.enabled=true \
  --set tetragon.prometheus.enabled=true
```

```yaml
# tetragon-policy.yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: file-access-monitoring
spec:
  kprobes:
  - call: "security_file_open"
    syscall: false
    args:
    - index: 0
      type: "file"
    - index: 1
      type: "int"
    selectors:
    - matchArgs:
      - index: 0
        operator: "Prefix"
        values:
        - "/etc/passwd"
        - "/etc/shadow"
        - "/root/.ssh/"
      matchActions:
      - action: Sigkill
```

### 4. Mutual TLS (mTLS) Configuration
```yaml
# mtls-policy.yaml
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: mtls-policy
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: secure-service
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: client-service
    toPorts:
    - ports:
      - port: "8443"
        protocol: TCP
      rules:
        http:
        - headers:
          - "X-Client-Cert-Present: true"
        - method: "GET"
          path: "/secure/.*"
  authentication:
    mode: "required"
```

## 🌐 Multi-Cluster Networking

### 1. Cluster Mesh Setup
```bash
# Enable cluster mesh on first cluster
cilium clustermesh enable --context cluster1 --service-type LoadBalancer

# Enable cluster mesh on second cluster
cilium clustermesh enable --context cluster2 --service-type LoadBalancer

# Connect clusters
cilium clustermesh connect --context cluster1 --destination-context cluster2
```

### 2. Cross-Cluster Service Discovery
```yaml
# global-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: global-api-service
  namespace: production
  annotations:
    service.cilium.io/global: "true"
    service.cilium.io/shared: "true"
spec:
  type: ClusterIP
  selector:
    app: api-service
  ports:
  - port: 80
    targetPort: 8080
---
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: cross-cluster-policy
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: api-service
  ingress:
  - fromEndpoints:
    - matchLabels:
        "k8s:io.cilium.k8s.policy.cluster": "cluster2"
        app: frontend
```

### 3. Multi-Cluster Load Balancing
```yaml
# multi-cluster-lb.yaml
apiVersion: "cilium.io/v2"
kind: CiliumGlobalService
metadata:
  name: global-load-balancer
spec:
  service:
    name: api-service
    namespace: production
  clusters:
  - name: cluster1
    endpoints:
    - ip: "10.0.1.100"
      port: 8080
  - name: cluster2
    endpoints:
    - ip: "10.0.2.100"
      port: 8080
  loadBalancing:
    algorithm: "round_robin"
    healthCheck:
      enabled: true
      path: "/health"
      interval: "10s"
```

## 🔧 Advanced Configuration

### 1. Custom eBPF Programs
```yaml
# custom-ebpf.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: custom-ebpf-program
  namespace: kube-system
data:
  program.c: |
    #include <linux/bpf.h>
    #include <linux/if_ether.h>
    #include <linux/ip.h>
    #include <linux/tcp.h>
    
    SEC("tc")
    int custom_traffic_filter(struct __sk_buff *skb) {
        void *data = (void *)(long)skb->data;
        void *data_end = (void *)(long)skb->data_end;
        
        struct ethhdr *eth = data;
        if ((void *)(eth + 1) > data_end)
            return TC_ACT_OK;
        
        if (eth->h_proto != __constant_htons(ETH_P_IP))
            return TC_ACT_OK;
        
        struct iphdr *ip = (void *)(eth + 1);
        if ((void *)(ip + 1) > data_end)
            return TC_ACT_OK;
        
        // Custom logic here
        if (ip->protocol == IPPROTO_TCP) {
            // Log TCP traffic
            bpf_trace_printk("TCP packet from %x\n", ip->saddr);
        }
        
        return TC_ACT_OK;
    }
    
    char _license[] SEC("license") = "GPL";
```

### 2. Performance Tuning
```yaml
# performance-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cilium-performance-config
  namespace: kube-system
data:
  # BPF configuration
  bpf-ct-global-tcp-max: "1000000"
  bpf-ct-global-any-max: "500000"
  bpf-nat-global-max: "500000"
  bpf-neigh-global-max: "500000"
  bpf-policy-map-max: "65536"
  
  # Datapath configuration
  enable-bpf-clock-probe: "true"
  enable-bandwidth-manager: "true"
  enable-local-redirect-policy: "true"
  
  # Performance optimizations
  kube-proxy-replacement: "strict"
  enable-host-legacy-routing: "false"
  install-no-conntrack-iptables-rules: "true"
  
  # Memory management
  bpf-map-dynamic-size-ratio: "0.25"
  enable-bpf-masquerade: "true"
```

## 🐛 Troubleshooting

### 1. Connectivity Issues
```bash
# Check Cilium agent status
kubectl -n kube-system get pods -l k8s-app=cilium

# Detailed status check
cilium status --verbose

# Connectivity test
cilium connectivity test --verbose

# Check BPF maps
kubectl -n kube-system exec ds/cilium -- cilium bpf tunnel list
kubectl -n kube-system exec ds/cilium -- cilium bpf endpoint list
```

### 2. Network Policy Debugging
```bash
# Enable policy verdict logs
kubectl -n kube-system patch configmap cilium-config --patch '{"data":{"debug-verbose":"policy"}}'

# Check policy enforcement
kubectl -n kube-system exec ds/cilium -- cilium policy get

# Monitor policy decisions
hubble observe --verdict DENIED --follow
```

### 3. Performance Debugging
```bash
# Check BPF map utilization
kubectl -n kube-system exec ds/cilium -- cilium bpf metrics list

# Monitor datapath performance
kubectl -n kube-system exec ds/cilium -- cilium monitor --type drop

# Check for BPF program issues
kubectl -n kube-system exec ds/cilium -- cilium bpf fs show
```

### 4. Common Issues and Solutions

#### Issue: Pods can't reach external services
```bash
# Check masquerading
kubectl -n kube-system exec ds/cilium -- cilium bpf nat list

# Verify routing
kubectl -n kube-system exec ds/cilium -- cilium bpf tunnel list
```

#### Issue: High memory usage
```yaml
# Optimize BPF map sizes
apiVersion: v1
kind: ConfigMap
metadata:
  name: cilium-config
  namespace: kube-system
data:
  bpf-ct-global-tcp-max: "262144"
  bpf-ct-global-any-max: "131072"
  bpf-nat-global-max: "131072"
```

## 📋 Production Checklist

### Pre-Deployment
- [ ] EKS cluster version compatibility verified
- [ ] Node instance types support eBPF features
- [ ] VPC CNI properly disabled
- [ ] Security groups configured for Cilium
- [ ] Helm charts and versions validated

### Security Configuration
- [ ] Network policies implemented and tested
- [ ] Encryption enabled (WireGuard/IPSec)
- [ ] Identity-based policies configured
- [ ] Runtime security (Tetragon) deployed
- [ ] mTLS configured for sensitive services

### Observability Setup
- [ ] Hubble enabled with appropriate metrics
- [ ] Prometheus integration configured
- [ ] Grafana dashboards imported
- [ ] Alerting rules defined
- [ ] Log aggregation configured

### Performance Optimization
- [ ] BPF map sizes tuned for workload
- [ ] Kube-proxy replacement enabled
- [ ] Load balancing algorithm optimized
- [ ] Bandwidth management configured
- [ ] Memory limits appropriately set

### Multi-Cluster (if applicable)
- [ ] Cluster mesh connectivity tested
- [ ] Cross-cluster policies validated
- [ ] Global services configured
- [ ] Load balancing verified

## 🎯 Best Practices

1. **Start Simple**: Begin with basic network policies before advanced features
2. **Monitor Performance**: Use Hubble and Prometheus for continuous monitoring
3. **Test Thoroughly**: Use connectivity tests in staging environments
4. **Security First**: Enable encryption and implement least-privilege policies
5. **Version Management**: Keep Cilium versions aligned with EKS compatibility
6. **Resource Planning**: Size BPF maps based on cluster scale
7. **Documentation**: Maintain network policy documentation
8. **Backup Policies**: Have rollback procedures for policy changes

## 🔗 Additional Resources

- [Cilium Documentation](https://docs.cilium.io/)
- [EKS Best Practices - Networking](https://aws.github.io/aws-eks-best-practices/networking/)
- [Hubble Observability](https://github.com/cilium/hubble)
- [Tetragon Runtime Security](https://github.com/cilium/tetragon)
- [Cilium Service Mesh](https://docs.cilium.io/en/stable/gettingstarted/servicemesh/)

---

**Note**: This guide covers advanced Cilium features. Always test configurations in non-production environments first and ensure your team has adequate eBPF and networking knowledge before implementing in production.