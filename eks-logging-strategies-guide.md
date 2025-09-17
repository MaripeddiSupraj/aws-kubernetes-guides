# EKS Logging Strategies - Complete Guide

## Table of Contents
1. [Logging Architecture Overview](#logging-architecture-overview)
2. [Logging Patterns & Approaches](#logging-patterns--approaches)
3. [EKS Control Plane Logging](#eks-control-plane-logging)
4. [Application Logging Strategies](#application-logging-strategies)
5. [Log Aggregation Solutions](#log-aggregation-solutions)
6. [Real-World Example: E-commerce Application](#real-world-example-e-commerce-application)
7. [Cost Optimization](#cost-optimization)
8. [Monitoring and Alerting](#monitoring-and-alerting)
9. [Best Practices](#best-practices)

---

## Logging Architecture Overview

### EKS Logging Layers
```
┌─────────────────────────────────────────────────────────────┐
│                    EKS Logging Stack                        │
├─────────────────────────────────────────────────────────────┤
│ Application Logs    │ System Logs     │ Security Logs       │
│ - Stdout/Stderr     │ - kubelet       │ - Audit logs        │
│ - File logs         │ - kube-proxy    │ - Authentication    │
│ - Structured logs   │ - Container     │ - Authorization     │
├─────────────────────────────────────────────────────────────┤
│              Log Collection Layer                           │
│ - Fluent Bit        │ - Fluentd       │ - Filebeat         │
│ - CloudWatch Agent  │ - Promtail      │ - Vector           │
├─────────────────────────────────────────────────────────────┤
│              Log Storage & Analysis                         │
│ - CloudWatch Logs   │ - OpenSearch    │ - S3               │
│ - ELK Stack         │ - Grafana Loki  │ - Third-party      │
└─────────────────────────────────────────────────────────────┘
```

### Logging Strategy Decision Matrix
| Use Case | Volume | Retention | Cost | Recommended Solution |
|----------|--------|-----------|------|---------------------|
| Development | Low | 7-30 days | Low | CloudWatch Logs |
| Production | Medium | 90 days | Medium | CloudWatch + S3 |
| Compliance | High | 7+ years | High | S3 + Glacier |
| Real-time Analytics | High | 30 days | Medium | OpenSearch |
| Cost-Optimized | High | Variable | Low | Loki + S3 |

---

## Logging Patterns & Approaches

### Logging Pattern Comparison

| Pattern | Pros | Cons | Best For | Resource Usage |
|---------|------|------|----------|----------------|
| **Direct Logging** | Simple, low overhead | Tight coupling, limited flexibility | Simple apps, development | Low |
| **Sidecar Pattern** | Decoupled, flexible, language agnostic | Higher resource usage | Production, multi-language | Medium-High |
| **DaemonSet** | Efficient, centralized | Node-level dependency | Large clusters, standardization | Low-Medium |
| **Init Container** | One-time setup, clean | Limited to initialization | Log setup, configuration | Very Low |

### 1. Direct Logging Pattern (Stdout/Stderr)

#### When to Use:
- Simple applications
- Development environments
- Microservices with minimal logging requirements
- Cost-sensitive deployments

#### Implementation:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: simple-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: simple-app
  template:
    metadata:
      labels:
        app: simple-app
      annotations:
        # Fluent Bit will automatically collect stdout/stderr
        fluentbit.io/parser: json
    spec:
      containers:
      - name: app
        image: simple-app:v1.0.0
        env:
        - name: LOG_FORMAT
          value: "json"
        - name: LOG_LEVEL
          value: "info"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
```

#### Application Code (Node.js):
```javascript
// Simple stdout logging
const logger = {
  info: (message, meta = {}) => {
    console.log(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'info',
      message,
      service: 'simple-app',
      ...meta
    }));
  },
  error: (message, error = {}) => {
    console.error(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'error',
      message,
      service: 'simple-app',
      error: error.message,
      stack: error.stack
    }));
  }
};

// Usage
logger.info('Application started', { port: 3000 });
logger.error('Database connection failed', new Error('Connection timeout'));
```

### 2. Sidecar Logging Pattern

#### When to Use:
- Production environments
- Applications with complex logging requirements
- Multi-language microservices
- Need for log preprocessing/enrichment
- Compliance requirements

#### Advantages:
- **Separation of Concerns**: Application focuses on business logic
- **Language Agnostic**: Works with any programming language
- **Flexible Processing**: Transform, filter, enrich logs before shipping
- **Independent Scaling**: Log processing scales independently
- **Failure Isolation**: Log failures don't affect main application

#### Basic Sidecar Implementation:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-sidecar
spec:
  replicas: 3
  selector:
    matchLabels:
      app: app-with-sidecar
  template:
    metadata:
      labels:
        app: app-with-sidecar
    spec:
      containers:
      # Main application container
      - name: app
        image: my-app:v2.0.0
        volumeMounts:
        - name: app-logs
          mountPath: /var/log/app
        - name: shared-data
          mountPath: /tmp/shared
        env:
        - name: LOG_FILE
          value: "/var/log/app/application.log"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      
      # Logging sidecar container
      - name: log-shipper
        image: fluent/fluent-bit:2.2.0
        volumeMounts:
        - name: app-logs
          mountPath: /var/log/app
          readOnly: true
        - name: fluent-bit-config
          mountPath: /fluent-bit/etc
        - name: shared-data
          mountPath: /tmp/shared
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
        env:
        - name: FLUENT_ELASTICSEARCH_HOST
          value: "elasticsearch.logging.svc.cluster.local"
        - name: FLUENT_ELASTICSEARCH_PORT
          value: "9200"
      
      volumes:
      - name: app-logs
        emptyDir: {}
      - name: shared-data
        emptyDir: {}
      - name: fluent-bit-config
        configMap:
          name: fluent-bit-sidecar-config
```

#### Advanced Sidecar with Log Processing:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-sidecar-config
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         5
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf
        HTTP_Server   On
        HTTP_Listen   0.0.0.0
        HTTP_Port     2020

    [INPUT]
        Name              tail
        Path              /var/log/app/*.log
        Parser            json
        Tag               app.logs
        Refresh_Interval  5
        Mem_Buf_Limit     5MB
        Skip_Long_Lines   On

    # Enrich logs with Kubernetes metadata
    [FILTER]
        Name                kubernetes
        Match               app.*
        Kube_URL            https://kubernetes.default.svc:443
        Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
        Merge_Log           On
        Keep_Log            Off

    # Add custom fields
    [FILTER]
        Name                modify
        Match               app.*
        Add                 cluster_name ${CLUSTER_NAME}
        Add                 environment production
        Add                 log_source sidecar

    # Parse and structure logs
    [FILTER]
        Name                parser
        Match               app.*
        Key_Name            log
        Parser              app_parser
        Reserve_Data        On

    # Filter sensitive data
    [FILTER]
        Name                modify
        Match               app.*
        Remove              password
        Remove              token
        Remove              credit_card

    # Route to different outputs based on log level
    [OUTPUT]
        Name                es
        Match               app.*
        Host                ${FLUENT_ELASTICSEARCH_HOST}
        Port                ${FLUENT_ELASTICSEARCH_PORT}
        Index               app-logs-${ENVIRONMENT}
        Type                _doc
        Retry_Limit         3
        Replace_Dots        On
        Logstash_Format     On
        Logstash_Prefix     app-logs
        Logstash_DateFormat %Y.%m.%d

    # Send critical errors to alerting system
    [OUTPUT]
        Name                http
        Match_Regex         .*level.*error.*
        Host                alert-manager.monitoring.svc.cluster.local
        Port                9093
        URI                 /api/v1/alerts
        Format              json

  parsers.conf: |
    [PARSER]
        Name        json
        Format      json
        Time_Key    timestamp
        Time_Format %Y-%m-%dT%H:%M:%S.%L
        Time_Keep   On

    [PARSER]
        Name        app_parser
        Format      regex
        Regex       ^(?<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z) \[(?<level>\w+)\] (?<message>.*)
        Time_Key    timestamp
        Time_Format %Y-%m-%dT%H:%M:%S.%L
```

### 3. Specialized Sidecar Patterns

#### A. Multi-File Logging Sidecar:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multi-log-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: complex-app:v1.0.0
        volumeMounts:
        - name: app-logs
          mountPath: /var/log
        env:
        - name: ACCESS_LOG_FILE
          value: "/var/log/access.log"
        - name: ERROR_LOG_FILE
          value: "/var/log/error.log"
        - name: AUDIT_LOG_FILE
          value: "/var/log/audit.log"
      
      # Separate sidecar for each log type
      - name: access-log-shipper
        image: fluent/fluent-bit:2.2.0
        command:
        - /fluent-bit/bin/fluent-bit
        - --config=/fluent-bit/etc/access-logs.conf
        volumeMounts:
        - name: app-logs
          mountPath: /var/log
          readOnly: true
        - name: access-log-config
          mountPath: /fluent-bit/etc
      
      - name: error-log-shipper
        image: fluent/fluent-bit:2.2.0
        command:
        - /fluent-bit/bin/fluent-bit
        - --config=/fluent-bit/etc/error-logs.conf
        volumeMounts:
        - name: app-logs
          mountPath: /var/log
          readOnly: true
        - name: error-log-config
          mountPath: /fluent-bit/etc
      
      volumes:
      - name: app-logs
        emptyDir: {}
      - name: access-log-config
        configMap:
          name: access-log-config
      - name: error-log-config
        configMap:
          name: error-log-config
```

#### B. Log Aggregation Sidecar:
```yaml
# Sidecar that aggregates logs from multiple sources
apiVersion: apps/v1
kind: Deployment
metadata:
  name: log-aggregator-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: my-app:v1.0.0
        volumeMounts:
        - name: app-logs
          mountPath: /var/log/app
      
      - name: nginx
        image: nginx:alpine
        volumeMounts:
        - name: nginx-logs
          mountPath: /var/log/nginx
      
      # Aggregating sidecar
      - name: log-aggregator
        image: fluent/fluent-bit:2.2.0
        volumeMounts:
        - name: app-logs
          mountPath: /var/log/app
          readOnly: true
        - name: nginx-logs
          mountPath: /var/log/nginx
          readOnly: true
        - name: aggregator-config
          mountPath: /fluent-bit/etc
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
      
      volumes:
      - name: app-logs
        emptyDir: {}
      - name: nginx-logs
        emptyDir: {}
      - name: aggregator-config
        configMap:
          name: log-aggregator-config
```

### 4. DaemonSet Logging Pattern

#### When to Use:
- Large clusters with many pods
- Standardized logging across all nodes
- Resource efficiency is critical
- Centralized log collection management

#### Implementation:
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: logging
spec:
  selector:
    matchLabels:
      name: fluent-bit
  template:
    metadata:
      labels:
        name: fluent-bit
    spec:
      serviceAccountName: fluent-bit
      tolerations:
      - key: node-role.kubernetes.io/master
        operator: Exists
        effect: NoSchedule
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:2.2.0
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
        - name: fluent-bit-config
          mountPath: /fluent-bit/etc/
        - name: mnt
          mountPath: /mnt
          readOnly: true
        resources:
          limits:
            memory: 200Mi
            cpu: 200m
          requests:
            memory: 100Mi
            cpu: 100m
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
      - name: fluent-bit-config
        configMap:
          name: fluent-bit-config
      - name: mnt
        hostPath:
          path: /mnt
```

### 5. Init Container Pattern

#### When to Use:
- Log configuration setup
- Log directory preparation
- Certificate/credential setup for logging

#### Implementation:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-log-init
spec:
  template:
    spec:
      initContainers:
      - name: log-setup
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          # Create log directories
          mkdir -p /var/log/app/{access,error,audit}
          
          # Set permissions
          chmod 755 /var/log/app
          chmod 644 /var/log/app/*
          
          # Create log rotation config
          cat > /var/log/app/logrotate.conf << EOF
          /var/log/app/*.log {
            daily
            rotate 7
            compress
            delaycompress
            missingok
            notifempty
            create 644 app app
          }
          EOF
          
          echo "Log setup completed"
        volumeMounts:
        - name: app-logs
          mountPath: /var/log/app
      
      containers:
      - name: app
        image: my-app:v1.0.0
        volumeMounts:
        - name: app-logs
          mountPath: /var/log/app
      
      volumes:
      - name: app-logs
        emptyDir: {}
```

### 6. Logging Pattern Decision Tree

```
Start: What type of application?
├── Simple/Development
│   └── Use Direct Logging (stdout/stderr)
│       ├── Pros: Simple, low overhead
│       └── Cons: Limited flexibility
├── Production Microservice
│   ├── Single language/simple logs?
│   │   └── Use DaemonSet Pattern
│   │       ├── Pros: Resource efficient
│   │       └── Cons: Less flexibility
│   └── Multi-language/complex processing?
│       └── Use Sidecar Pattern
│           ├── Pros: Maximum flexibility
│           └── Cons: Higher resource usage
└── Enterprise/Compliance
    └── Use Advanced Sidecar + DaemonSet
        ├── Sidecar: Application-specific processing
        └── DaemonSet: Infrastructure logs
```

### 7. Resource Usage Comparison

#### Resource Overhead Analysis:
```yaml
# Direct Logging: ~0 additional resources
resources:
  requests:
    memory: "256Mi"  # Application only
    cpu: "250m"

# Sidecar Pattern: +50-100Mi memory, +50-100m CPU per pod
resources:
  app:
    requests:
      memory: "256Mi"
      cpu: "250m"
  sidecar:
    requests:
      memory: "64Mi"   # Additional overhead
      cpu: "50m"

# DaemonSet: ~100-200Mi memory, ~100-200m CPU per node
resources:
  requests:
    memory: "100Mi"  # Shared across all pods on node
    cpu: "100m"
```

### 8. Performance Benchmarks

#### Logging Throughput Comparison:
| Pattern | Logs/sec/pod | Memory Usage | CPU Usage | Network I/O |
|---------|--------------|--------------|-----------|-------------|
| Direct | 10,000+ | Low | Low | Medium |
| Sidecar | 5,000-8,000 | Medium | Medium | Low |
| DaemonSet | 15,000+ | Low (shared) | Low (shared) | High |

#### Latency Impact:
```yaml
# Benchmark results (average log processing latency)
Direct Logging:    ~1ms   (stdout → container runtime)
Sidecar Pattern:   ~5ms   (file → sidecar → destination)
DaemonSet:         ~3ms   (file → daemonset → destination)
```

### 9. Hybrid Approach (Recommended for Production)

#### Best of Both Worlds:
```yaml
# Use DaemonSet for infrastructure logs
# Use Sidecar for application-specific processing
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hybrid-logging-app
spec:
  template:
    metadata:
      annotations:
        # DaemonSet will collect these automatically
        logging.kubernetes.io/collect-stdout: "true"
        # Sidecar will handle application-specific logs
        logging.kubernetes.io/sidecar-enabled: "true"
    spec:
      containers:
      - name: app
        image: my-app:v1.0.0
        # Structured logs to stdout (collected by DaemonSet)
        env:
        - name: LOG_STDOUT
          value: "true"
        - name: LOG_LEVEL
          value: "info"
        # Application-specific logs to files (processed by sidecar)
        - name: AUDIT_LOG_FILE
          value: "/var/log/app/audit.log"
        - name: METRICS_LOG_FILE
          value: "/var/log/app/metrics.log"
        volumeMounts:
        - name: app-logs
          mountPath: /var/log/app
      
      # Sidecar only for special log processing
      - name: audit-log-processor
        image: fluent/fluent-bit:2.2.0
        command:
        - /fluent-bit/bin/fluent-bit
        - --config=/fluent-bit/etc/audit-only.conf
        volumeMounts:
        - name: app-logs
          mountPath: /var/log/app
          readOnly: true
        - name: audit-config
          mountPath: /fluent-bit/etc
        resources:
          requests:
            memory: "32Mi"  # Minimal resources for specific processing
            cpu: "25m"
      
      volumes:
      - name: app-logs
        emptyDir: {}
      - name: audit-config
        configMap:
          name: audit-log-config
```

### 10. Pattern Selection Guidelines

#### Choose Direct Logging When:
- ✅ Development/testing environments
- ✅ Simple applications with basic logging needs
- ✅ Cost is the primary concern
- ✅ Minimal log processing required
- ❌ Avoid for: Complex log processing, compliance requirements

#### Choose Sidecar Pattern When:
- ✅ Production environments with complex requirements
- ✅ Need log preprocessing/enrichment
- ✅ Multi-language microservices
- ✅ Compliance/audit requirements
- ✅ Application-specific log routing
- ❌ Avoid for: Resource-constrained environments, simple applications

#### Choose DaemonSet Pattern When:
- ✅ Large clusters (100+ nodes)
- ✅ Standardized logging requirements
- ✅ Resource efficiency is critical
- ✅ Infrastructure/system log collection
- ❌ Avoid for: Application-specific processing, diverse log formats

#### Choose Hybrid Approach When:
- ✅ Enterprise production environments
- ✅ Mixed workload types
- ✅ Need both efficiency and flexibility
- ✅ Complex compliance requirements
- ✅ Large-scale deployments

---

## EKS Control Plane Logging

### 1. Enable All Control Plane Logs

#### CLI Command:
```bash
aws eks update-cluster-config \
  --name my-cluster \
  --logging '{
    "clusterLogging": [
      {
        "types": ["api", "audit", "authenticator", "controllerManager", "scheduler"],
        "enabled": true
      }
    ]
  }'
```

#### CloudFormation Template:
```yaml
EKSCluster:
  Type: AWS::EKS::Cluster
  Properties:
    Name: production-cluster
    Logging:
      ClusterLogging:
        EnabledTypes:
          - Type: api
          - Type: audit
          - Type: authenticator
          - Type: controllerManager
          - Type: scheduler
```

### 2. Control Plane Log Types Explained

#### API Server Logs
```bash
# View API server logs
aws logs filter-log-events \
  --log-group-name /aws/eks/my-cluster/cluster \
  --filter-pattern "{ $.verb = \"create\" || $.verb = \"delete\" }" \
  --start-time 1640995200000
```

#### Audit Logs Analysis
```bash
# Find failed authentication attempts
aws logs filter-log-events \
  --log-group-name /aws/eks/my-cluster/cluster \
  --filter-pattern "{ $.verb = \"*\" && $.objectRef.apiVersion = \"*\" && $.responseStatus.code >= 400 }"
```

#### Custom Audit Policy
```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
# Log all requests at Metadata level
- level: Metadata
  omitStages:
    - RequestReceived
# Log secrets and configmaps at Request level
- level: Request
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
# Don't log system requests
- level: None
  users: ["system:kube-proxy"]
  verbs: ["watch"]
  resources:
  - group: ""
    resources: ["endpoints", "services"]
```

---

## Application Logging Strategies

### 1. Structured Logging Best Practices

#### JSON Structured Logging (Node.js Example):
```javascript
// logger.js
const winston = require('winston');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: {
    service: 'ecommerce-api',
    version: process.env.APP_VERSION || '1.0.0',
    environment: process.env.NODE_ENV || 'development'
  },
  transports: [
    new winston.transports.Console()
  ]
});

// Usage in application
app.use((req, res, next) => {
  logger.info('HTTP Request', {
    method: req.method,
    url: req.url,
    userAgent: req.get('User-Agent'),
    ip: req.ip,
    requestId: req.headers['x-request-id']
  });
  next();
});

// Error logging
app.use((err, req, res, next) => {
  logger.error('Application Error', {
    error: err.message,
    stack: err.stack,
    requestId: req.headers['x-request-id'],
    userId: req.user?.id
  });
  res.status(500).json({ error: 'Internal Server Error' });
});
```

#### Python Structured Logging:
```python
# logger.py
import logging
import json
import os
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'service': 'ecommerce-api',
            'version': os.getenv('APP_VERSION', '1.0.0'),
            'environment': os.getenv('ENVIRONMENT', 'development')
        }
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
            
        return json.dumps(log_entry)

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
    format='%(message)s'
)

logger = logging.getLogger(__name__)
logger.handlers[0].setFormatter(JSONFormatter())

# Usage
def process_order(order_id, user_id):
    logger.info(
        "Processing order",
        extra={
            'request_id': 'req-123',
            'user_id': user_id,
            'order_id': order_id
        }
    )
```

### 2. Application Deployment with Logging

#### Deployment with Logging Configuration:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecommerce-api
  labels:
    app: ecommerce-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ecommerce-api
  template:
    metadata:
      labels:
        app: ecommerce-api
      annotations:
        # Fluent Bit parsing
        fluentbit.io/parser: json
        # Exclude from certain log collection
        fluentbit.io/exclude: "false"
    spec:
      containers:
      - name: api
        image: ecommerce-api:v1.2.0
        env:
        - name: LOG_LEVEL
          value: "info"
        - name: APP_VERSION
          value: "v1.2.0"
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        # Log to stdout/stderr
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        # Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: tmp
        emptyDir: {}
```

---

## Log Aggregation Solutions

### 1. CloudWatch Container Insights (AWS Native)

#### Installation:
```bash
# Install CloudWatch agent and Fluent Bit
curl https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml | sed "s/{{cluster_name}}/my-cluster/" | kubectl apply -f -
```

#### Custom Fluent Bit Configuration:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: amazon-cloudwatch
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         5
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf
        HTTP_Server   On
        HTTP_Listen   0.0.0.0
        HTTP_Port     2020

    @INCLUDE application-log.conf
    @INCLUDE dataplane-log.conf

  application-log.conf: |
    [INPUT]
        Name              tail
        Tag               application.*
        Exclude_Path      /var/log/containers/cloudwatch-agent*, /var/log/containers/fluent-bit*
        Path              /var/log/containers/*.log
        Parser            docker
        DB                /var/fluent-bit/state/flb_container.db
        Mem_Buf_Limit     50MB
        Skip_Long_Lines   On
        Refresh_Interval  10

    [FILTER]
        Name                kubernetes
        Match               application.*
        Kube_URL            https://kubernetes.default.svc:443
        Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
        Kube_Tag_Prefix     application.var.log.containers.
        Merge_Log           On
        Keep_Log            Off
        K8S-Logging.Parser  On
        K8S-Logging.Exclude On

    # Parse JSON logs
    [FILTER]
        Name                parser
        Match               application.*
        Key_Name            log
        Parser              json
        Reserve_Data        On

    # Add custom fields
    [FILTER]
        Name                modify
        Match               application.*
        Add                 cluster_name my-cluster
        Add                 log_source kubernetes

    [OUTPUT]
        Name                cloudwatch_logs
        Match               application.*
        region              ${AWS_REGION}
        log_group_name      /aws/containerinsights/${CLUSTER_NAME}/application
        log_stream_prefix   ${HOST_NAME}-
        auto_create_group   On
        retry_limit         2

  parsers.conf: |
    [PARSER]
        Name        json
        Format      json
        Time_Key    timestamp
        Time_Format %Y-%m-%dT%H:%M:%S.%L
        Time_Keep   On

    [PARSER]
        Name        docker
        Format      json
        Time_Key    time
        Time_Format %Y-%m-%dT%H:%M:%S.%L
        Time_Keep   On
```

### 2. ELK Stack on EKS

#### Elasticsearch Deployment:
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: logging
spec:
  serviceName: elasticsearch
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
        env:
        - name: cluster.name
          value: "k8s-logs"
        - name: node.name
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: discovery.seed_hosts
          value: "elasticsearch-0.elasticsearch,elasticsearch-1.elasticsearch,elasticsearch-2.elasticsearch"
        - name: cluster.initial_master_nodes
          value: "elasticsearch-0,elasticsearch-1,elasticsearch-2"
        - name: ES_JAVA_OPTS
          value: "-Xms512m -Xmx512m"
        - name: xpack.security.enabled
          value: "false"
        ports:
        - containerPort: 9200
          name: rest
        - containerPort: 9300
          name: inter-node
        volumeMounts:
        - name: data
          mountPath: /usr/share/elasticsearch/data
        resources:
          limits:
            memory: 1Gi
            cpu: 1000m
          requests:
            memory: 512Mi
            cpu: 500m
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: gp3
      resources:
        requests:
          storage: 10Gi
```

#### Fluentd Configuration:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: logging
data:
  fluent.conf: |
    <source>
      @type tail
      @id in_tail_container_logs
      path /var/log/containers/*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      read_from_head true
      <parse>
        @type json
        time_format %Y-%m-%dT%H:%M:%S.%NZ
      </parse>
    </source>

    <filter kubernetes.**>
      @type kubernetes_metadata
      @id filter_kube_metadata
      kubernetes_url "#{ENV['KUBERNETES_SERVICE_HOST']}:#{ENV['KUBERNETES_SERVICE_PORT_HTTPS']}"
      verify_ssl "#{ENV['KUBERNETES_VERIFY_SSL'] || true}"
      ca_file "#{ENV['KUBERNETES_CA_FILE']}"
      skip_labels false
      skip_container_metadata false
      skip_master_url false
      skip_namespace_metadata false
    </filter>

    # Parse application logs
    <filter kubernetes.var.log.containers.ecommerce-api**>
      @type parser
      key_name log
      reserve_data true
      remove_key_name_field true
      <parse>
        @type json
      </parse>
    </filter>

    # Add environment info
    <filter kubernetes.**>
      @type record_transformer
      <record>
        cluster_name "#{ENV['CLUSTER_NAME']}"
        environment "#{ENV['ENVIRONMENT']}"
      </record>
    </filter>

    <match kubernetes.**>
      @type elasticsearch
      @id out_es
      @log_level info
      include_tag_key true
      host "#{ENV['FLUENT_ELASTICSEARCH_HOST']}"
      port "#{ENV['FLUENT_ELASTICSEARCH_PORT']}"
      path "#{ENV['FLUENT_ELASTICSEARCH_PATH']}"
      scheme "#{ENV['FLUENT_ELASTICSEARCH_SCHEME'] || 'http'}"
      ssl_verify "#{ENV['FLUENT_ELASTICSEARCH_SSL_VERIFY'] || 'true'}"
      ssl_version "#{ENV['FLUENT_ELASTICSEARCH_SSL_VERSION'] || 'TLSv1_2'}"
      reload_connections false
      reconnect_on_error true
      reload_on_failure true
      log_es_400_reason false
      logstash_prefix logstash
      logstash_dateformat %Y.%m.%d
      logstash_format true
      index_name fluentd
      type_name fluentd
      <buffer>
        flush_thread_count 8
        flush_interval 5s
        chunk_limit_size 2M
        queue_limit_length 32
        retry_max_interval 30
        retry_forever true
      </buffer>
    </match>
```

### 3. Grafana Loki (Cost-Effective Alternative)

#### Loki Deployment:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: loki-config
  namespace: logging
data:
  loki.yaml: |
    auth_enabled: false
    
    server:
      http_listen_port: 3100
      
    common:
      path_prefix: /loki
      storage:
        filesystem:
          chunks_directory: /loki/chunks
          rules_directory: /loki/rules
      replication_factor: 1
      ring:
        instance_addr: 127.0.0.1
        kvstore:
          store: inmemory
          
    schema_config:
      configs:
        - from: 2020-10-24
          store: boltdb-shipper
          object_store: filesystem
          schema: v11
          index:
            prefix: index_
            period: 24h
            
    ruler:
      alertmanager_url: http://localhost:9093

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: loki
  namespace: logging
spec:
  replicas: 1
  selector:
    matchLabels:
      app: loki
  template:
    metadata:
      labels:
        app: loki
    spec:
      containers:
      - name: loki
        image: grafana/loki:2.9.0
        args:
        - -config.file=/etc/loki/loki.yaml
        ports:
        - containerPort: 3100
          name: http-metrics
        volumeMounts:
        - name: config
          mountPath: /etc/loki
        - name: storage
          mountPath: /loki
        resources:
          limits:
            memory: 512Mi
            cpu: 500m
          requests:
            memory: 256Mi
            cpu: 250m
      volumes:
      - name: config
        configMap:
          name: loki-config
      - name: storage
        emptyDir: {}
```

#### Promtail Configuration:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: promtail-config
  namespace: logging
data:
  promtail.yaml: |
    server:
      http_listen_port: 9080
      grpc_listen_port: 0

    positions:
      filename: /tmp/positions.yaml

    clients:
      - url: http://loki:3100/loki/api/v1/push

    scrape_configs:
    - job_name: kubernetes-pods
      kubernetes_sd_configs:
      - role: pod
      pipeline_stages:
      - docker: {}
      - json:
          expressions:
            timestamp: timestamp
            level: level
            message: message
            service: service
            request_id: request_id
      - timestamp:
          source: timestamp
          format: RFC3339Nano
      - labels:
          level:
          service:
          request_id:
      relabel_configs:
      - source_labels:
        - __meta_kubernetes_pod_controller_name
        regex: ([0-9a-z-.]+?)(-[0-9a-f]{8,10})?
        action: replace
        target_label: __tmp_controller_name
      - source_labels:
        - __meta_kubernetes_pod_label_app_kubernetes_io_name
        - __meta_kubernetes_pod_label_app
        - __tmp_controller_name
        - __meta_kubernetes_pod_name
        regex: ^;*([^;]+)(;.*)?$
        action: replace
        target_label: app
      - source_labels:
        - __meta_kubernetes_pod_label_app_kubernetes_io_component
        - __meta_kubernetes_pod_label_component
        regex: ^;*([^;]+)(;.*)?$
        action: replace
        target_label: component
      - action: replace
        source_labels:
        - __meta_kubernetes_pod_node_name
        target_label: node_name
      - action: replace
        source_labels:
        - __meta_kubernetes_namespace
        target_label: namespace
      - action: replace
        replacement: $1
        separator: /
        source_labels:
        - namespace
        - app
        target_label: job
      - action: replace
        source_labels:
        - __meta_kubernetes_pod_name
        target_label: pod
      - action: replace
        source_labels:
        - __meta_kubernetes_pod_container_name
        target_label: container
      - action: replace
        replacement: /var/log/pods/*$1/*.log
        separator: /
        source_labels:
        - __meta_kubernetes_pod_uid
        - __meta_kubernetes_pod_container_name
        target_label: __path__
```

---

## Real-World Example: E-commerce Application

### Application Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                 E-commerce Microservices                    │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Frontend      │   API Gateway   │   User Service          │
│   (React)       │   (Kong/Nginx)  │   (Node.js)             │
├─────────────────┼─────────────────┼─────────────────────────┤
│ Product Service │ Order Service   │ Payment Service         │
│ (Python)        │ (Java)          │ (Go)                    │
├─────────────────┼─────────────────┼─────────────────────────┤
│   Database      │   Cache         │   Message Queue         │
│   (PostgreSQL)  │   (Redis)       │   (RabbitMQ)            │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### 1. Frontend Logging (React/Nginx)

#### Nginx Configuration with JSON Logging:
```nginx
# nginx.conf
http {
    log_format json_combined escape=json
    '{'
        '"timestamp":"$time_iso8601",'
        '"remote_addr":"$remote_addr",'
        '"request_method":"$request_method",'
        '"request_uri":"$request_uri",'
        '"status":$status,'
        '"body_bytes_sent":$body_bytes_sent,'
        '"request_time":$request_time,'
        '"http_referrer":"$http_referer",'
        '"http_user_agent":"$http_user_agent",'
        '"http_x_forwarded_for":"$http_x_forwarded_for",'
        '"service":"frontend",'
        '"environment":"production"'
    '}';

    access_log /var/log/nginx/access.log json_combined;
    error_log /var/log/nginx/error.log warn;
}
```

#### Frontend Deployment:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
      annotations:
        fluentbit.io/parser: json
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
        volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx/nginx.conf
          subPath: nginx.conf
        - name: logs
          mountPath: /var/log/nginx
      - name: log-sidecar
        image: busybox
        command: ["tail", "-f", "/var/log/nginx/access.log"]
        volumeMounts:
        - name: logs
          mountPath: /var/log/nginx
      volumes:
      - name: nginx-config
        configMap:
          name: nginx-config
      - name: logs
        emptyDir: {}
```

### 2. API Gateway Logging (Kong)

#### Kong Configuration:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kong-config
data:
  kong.conf: |
    log_level = info
    proxy_access_log = /dev/stdout
    proxy_error_log = /dev/stderr
    admin_access_log = /dev/stdout
    admin_error_log = /dev/stderr
    
    # JSON logging plugin
    plugins = bundled,json-log

---
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: json-log
config:
  http_endpoint: "http://log-collector:8080/logs"
  method: "POST"
  timeout: 1000
  keepalive: 1000
plugin: http-log
```

### 3. Microservices Logging

#### User Service (Node.js):
```javascript
// user-service/logger.js
const winston = require('winston');
const { v4: uuidv4 } = require('uuid');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: {
    service: 'user-service',
    version: process.env.SERVICE_VERSION,
    environment: process.env.NODE_ENV
  },
  transports: [
    new winston.transports.Console()
  ]
});

// Middleware for request logging
const requestLogger = (req, res, next) => {
  req.requestId = req.headers['x-request-id'] || uuidv4();
  res.setHeader('x-request-id', req.requestId);
  
  logger.info('Request started', {
    requestId: req.requestId,
    method: req.method,
    url: req.url,
    userAgent: req.get('User-Agent'),
    ip: req.ip
  });
  
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    logger.info('Request completed', {
      requestId: req.requestId,
      statusCode: res.statusCode,
      duration: duration
    });
  });
  
  next();
};

// Business logic logging
const createUser = async (userData) => {
  const requestId = userData.requestId;
  
  try {
    logger.info('Creating user', {
      requestId,
      email: userData.email,
      action: 'user_creation_started'
    });
    
    const user = await User.create(userData);
    
    logger.info('User created successfully', {
      requestId,
      userId: user.id,
      email: user.email,
      action: 'user_creation_completed'
    });
    
    return user;
  } catch (error) {
    logger.error('User creation failed', {
      requestId,
      email: userData.email,
      error: error.message,
      stack: error.stack,
      action: 'user_creation_failed'
    });
    throw error;
  }
};

module.exports = { logger, requestLogger, createUser };
```

#### Product Service (Python):
```python
# product-service/logger.py
import logging
import json
import uuid
from datetime import datetime
from flask import request, g

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'service': 'product-service',
            'version': os.getenv('SERVICE_VERSION'),
            'environment': os.getenv('ENVIRONMENT')
        }
        
        # Add request context if available
        if hasattr(g, 'request_id'):
            log_entry['request_id'] = g.request_id
        if hasattr(g, 'user_id'):
            log_entry['user_id'] = g.user_id
            
        # Add extra fields
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
            
        return json.dumps(log_entry)

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.handlers = [handler]

# Flask middleware
@app.before_request
def before_request():
    g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    g.start_time = datetime.utcnow()
    
    logger.info("Request started", extra={
        'method': request.method,
        'url': request.url,
        'user_agent': request.user_agent.string,
        'remote_addr': request.remote_addr
    })

@app.after_request
def after_request(response):
    duration = (datetime.utcnow() - g.start_time).total_seconds() * 1000
    
    logger.info("Request completed", extra={
        'status_code': response.status_code,
        'duration_ms': duration
    })
    
    response.headers['X-Request-ID'] = g.request_id
    return response

# Business logic logging
def get_product(product_id):
    try:
        logger.info("Fetching product", extra={
            'product_id': product_id,
            'action': 'product_fetch_started'
        })
        
        product = Product.query.get(product_id)
        if not product:
            logger.warning("Product not found", extra={
                'product_id': product_id,
                'action': 'product_not_found'
            })
            return None
            
        logger.info("Product fetched successfully", extra={
            'product_id': product_id,
            'product_name': product.name,
            'action': 'product_fetch_completed'
        })
        
        return product
        
    except Exception as e:
        logger.error("Product fetch failed", extra={
            'product_id': product_id,
            'error': str(e),
            'action': 'product_fetch_failed'
        })
        raise
```

#### Order Service (Java/Spring Boot):
```java
// OrderService.java
@Service
@Slf4j
public class OrderService {
    
    private static final String SERVICE_NAME = "order-service";
    
    @Autowired
    private ObjectMapper objectMapper;
    
    public Order createOrder(CreateOrderRequest request) {
        String requestId = MDC.get("requestId");
        
        try {
            logInfo("Order creation started", Map.of(
                "action", "order_creation_started",
                "userId", request.getUserId(),
                "itemCount", request.getItems().size()
            ));
            
            Order order = new Order();
            order.setUserId(request.getUserId());
            order.setItems(request.getItems());
            order.setStatus(OrderStatus.PENDING);
            
            Order savedOrder = orderRepository.save(order);
            
            logInfo("Order created successfully", Map.of(
                "action", "order_creation_completed",
                "orderId", savedOrder.getId(),
                "userId", savedOrder.getUserId(),
                "totalAmount", savedOrder.getTotalAmount()
            ));
            
            return savedOrder;
            
        } catch (Exception e) {
            logError("Order creation failed", Map.of(
                "action", "order_creation_failed",
                "userId", request.getUserId(),
                "error", e.getMessage()
            ), e);
            throw e;
        }
    }
    
    private void logInfo(String message, Map<String, Object> extra) {
        try {
            Map<String, Object> logEntry = createLogEntry(message, "INFO", extra);
            log.info(objectMapper.writeValueAsString(logEntry));
        } catch (Exception e) {
            log.error("Failed to log message", e);
        }
    }
    
    private void logError(String message, Map<String, Object> extra, Exception e) {
        try {
            Map<String, Object> logEntry = createLogEntry(message, "ERROR", extra);
            logEntry.put("stack", ExceptionUtils.getStackTrace(e));
            log.error(objectMapper.writeValueAsString(logEntry));
        } catch (Exception ex) {
            log.error("Failed to log error", ex);
        }
    }
    
    private Map<String, Object> createLogEntry(String message, String level, Map<String, Object> extra) {
        Map<String, Object> logEntry = new HashMap<>();
        logEntry.put("timestamp", Instant.now().toString());
        logEntry.put("level", level);
        logEntry.put("message", message);
        logEntry.put("service", SERVICE_NAME);
        logEntry.put("version", System.getenv("SERVICE_VERSION"));
        logEntry.put("environment", System.getenv("ENVIRONMENT"));
        logEntry.put("requestId", MDC.get("requestId"));
        logEntry.put("userId", MDC.get("userId"));
        logEntry.putAll(extra);
        return logEntry;
    }
}

// Request filter for MDC
@Component
public class LoggingFilter implements Filter {
    
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        
        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;
        
        String requestId = httpRequest.getHeader("X-Request-ID");
        if (requestId == null) {
            requestId = UUID.randomUUID().toString();
        }
        
        MDC.put("requestId", requestId);
        httpResponse.setHeader("X-Request-ID", requestId);
        
        long startTime = System.currentTimeMillis();
        
        try {
            chain.doFilter(request, response);
        } finally {
            long duration = System.currentTimeMillis() - startTime;
            
            Map<String, Object> logEntry = Map.of(
                "timestamp", Instant.now().toString(),
                "level", "INFO",
                "message", "Request completed",
                "service", "order-service",
                "method", httpRequest.getMethod(),
                "url", httpRequest.getRequestURL().toString(),
                "statusCode", httpResponse.getStatus(),
                "duration", duration,
                "requestId", requestId
            );
            
            try {
                ObjectMapper mapper = new ObjectMapper();
                log.info(mapper.writeValueAsString(logEntry));
            } catch (Exception e) {
                log.error("Failed to log request completion", e);
            }
            
            MDC.clear();
        }
    }
}
```

### 4. Database and Infrastructure Logging

#### PostgreSQL Logging Configuration:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-config
data:
  postgresql.conf: |
    # Logging configuration
    log_destination = 'stderr'
    logging_collector = on
    log_directory = '/var/log/postgresql'
    log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
    log_rotation_age = 1d
    log_rotation_size = 100MB
    
    # What to log
    log_min_messages = info
    log_min_error_statement = error
    log_min_duration_statement = 1000  # Log queries > 1 second
    
    # Log format
    log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
    log_checkpoints = on
    log_connections = on
    log_disconnections = on
    log_lock_waits = on
    log_statement = 'mod'  # Log all modifications
    
    # Slow query logging
    log_duration = on
    log_statement_stats = off
```

#### Redis Logging:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
data:
  redis.conf: |
    # Logging
    loglevel notice
    logfile ""  # Log to stdout
    
    # Slow log
    slowlog-log-slower-than 10000  # 10ms
    slowlog-max-len 128
    
    # Command logging (be careful in production)
    # rename-command FLUSHDB ""
    # rename-command FLUSHALL ""
```

---

## Cost Optimization

### 1. Log Retention Strategies

#### CloudWatch Logs Retention:
```bash
# Set retention for different log groups
aws logs put-retention-policy \
  --log-group-name /aws/eks/my-cluster/cluster \
  --retention-in-days 90

aws logs put-retention-policy \
  --log-group-name /aws/containerinsights/my-cluster/application \
  --retention-in-days 30

aws logs put-retention-policy \
  --log-group-name /aws/containerinsights/my-cluster/performance \
  --retention-in-days 7
```

#### Automated Log Lifecycle:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: log-cleanup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: log-cleanup
            image: amazon/aws-cli:latest
            command:
            - /bin/sh
            - -c
            - |
              # Export old logs to S3
              aws logs create-export-task \
                --log-group-name /aws/containerinsights/my-cluster/application \
                --from $(date -d '30 days ago' +%s)000 \
                --to $(date -d '7 days ago' +%s)000 \
                --destination s3-bucket-name \
                --destination-prefix logs/application/
              
              # Delete old log streams
              aws logs describe-log-streams \
                --log-group-name /aws/containerinsights/my-cluster/application \
                --order-by LastEventTime \
                --query 'logStreams[?lastEventTime < `'$(date -d '30 days ago' +%s)'000`].logStreamName' \
                --output text | xargs -I {} aws logs delete-log-stream \
                --log-group-name /aws/containerinsights/my-cluster/application \
                --log-stream-name {}
          restartPolicy: OnFailure
```

### 2. Log Sampling and Filtering

#### Fluent Bit Sampling Configuration:
```yaml
# Sample high-volume logs
[FILTER]
    Name                sampling
    Match               application.var.log.containers.high-volume-app*
    Rate                10  # Keep 1 in 10 logs

# Filter out health check logs
[FILTER]
    Name                grep
    Match               application.*
    Exclude             log /health|/ready|/metrics

# Filter by log level
[FILTER]
    Name                grep
    Match               application.*
    Regex               level (ERROR|WARN|INFO)
```

### 3. Cost Monitoring

#### CloudWatch Cost Dashboard:
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Logs", "IncomingBytes", "LogGroupName", "/aws/containerinsights/my-cluster/application"],
          [".", "IncomingLogEvents", ".", "."]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "Log Ingestion Volume"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Logs", "StoredBytes", "LogGroupName", "/aws/containerinsights/my-cluster/application"]
        ],
        "period": 86400,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Log Storage Usage"
      }
    }
  ]
}
```

---

## Monitoring and Alerting

### 1. Log-Based Alerts

#### CloudWatch Alarms:
```bash
# Alert on error rate
aws cloudwatch put-metric-alarm \
  --alarm-name "High-Error-Rate" \
  --alarm-description "Alert when error rate exceeds 5%" \
  --metric-name "ErrorRate" \
  --namespace "ECommerce/Application" \
  --statistic Average \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# Alert on failed orders
aws logs put-metric-filter \
  --log-group-name "/aws/containerinsights/my-cluster/application" \
  --filter-name "FailedOrders" \
  --filter-pattern '{ $.service = "order-service" && $.action = "order_creation_failed" }' \
  --metric-transformations \
    metricName=FailedOrders,metricNamespace=ECommerce/Orders,metricValue=1
```

#### Prometheus Alerting Rules:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-alerts
data:
  alerts.yml: |
    groups:
    - name: application.rules
      rules:
      - alert: HighErrorRate
        expr: rate(log_entries{level="ERROR"}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
      
      - alert: ServiceDown
        expr: up{job="kubernetes-pods"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"
      
      - alert: SlowRequests
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "95th percentile latency is high"
          description: "95th percentile latency is {{ $value }}s"
```

### 2. Log Analytics Queries

#### CloudWatch Insights Queries:
```sql
-- Top error messages
fields @timestamp, service, message, error
| filter level = "ERROR"
| stats count() by error
| sort count desc
| limit 10

-- Request latency analysis
fields @timestamp, service, duration, url
| filter service = "api-gateway"
| stats avg(duration), max(duration), min(duration) by url
| sort avg desc

-- User activity tracking
fields @timestamp, user_id, action, request_id
| filter action like /user_/
| stats count() by user_id, action
| sort count desc

-- Failed authentication attempts
fields @timestamp, remote_addr, user_agent
| filter message like /authentication failed/
| stats count() by remote_addr
| sort count desc
| limit 20
```

#### Elasticsearch Queries:
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"level": "ERROR"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  },
  "aggs": {
    "services": {
      "terms": {"field": "service"},
      "aggs": {
        "error_types": {
          "terms": {"field": "error.keyword"}
        }
      }
    }
  }
}
```

---

## Best Practices

### 1. Logging Standards

#### Log Level Guidelines:
- **ERROR**: System errors, exceptions, failed operations
- **WARN**: Deprecated features, recoverable errors, performance issues
- **INFO**: Business events, user actions, system state changes
- **DEBUG**: Detailed execution flow, variable values (dev/staging only)

#### Structured Logging Schema:
```json
{
  "timestamp": "2023-12-01T10:30:00.000Z",
  "level": "INFO",
  "service": "order-service",
  "version": "v1.2.3",
  "environment": "production",
  "request_id": "req-123-456-789",
  "user_id": "user-456",
  "session_id": "sess-789",
  "message": "Order created successfully",
  "action": "order_creation_completed",
  "order_id": "ord-123",
  "total_amount": 99.99,
  "duration_ms": 150,
  "metadata": {
    "payment_method": "credit_card",
    "shipping_method": "express"
  }
}
```

### 2. Security Considerations

#### Sensitive Data Handling:
```javascript
// Bad - logging sensitive data
logger.info('User login', {
  username: 'john@example.com',
  password: 'secret123',  // Never log passwords
  creditCard: '4111-1111-1111-1111'  // Never log PII
});

// Good - sanitized logging
logger.info('User login', {
  username: hashEmail('john@example.com'),
  userId: 'user-123',
  loginMethod: 'password',
  success: true
});

// Sanitization function
function sanitizeLogData(data) {
  const sensitiveFields = ['password', 'token', 'creditCard', 'ssn'];
  const sanitized = { ...data };
  
  sensitiveFields.forEach(field => {
    if (sanitized[field]) {
      sanitized[field] = '[REDACTED]';
    }
  });
  
  return sanitized;
}
```

### 3. Performance Optimization

#### Asynchronous Logging:
```javascript
// Node.js async logging
const winston = require('winston');

const logger = winston.createLogger({
  transports: [
    new winston.transports.Console({
      handleExceptions: true,
      handleRejections: true
    })
  ],
  exitOnError: false
});

// Batch logging for high-volume scenarios
class BatchLogger {
  constructor(batchSize = 100, flushInterval = 5000) {
    this.batch = [];
    this.batchSize = batchSize;
    this.flushInterval = flushInterval;
    
    setInterval(() => this.flush(), this.flushInterval);
  }
  
  log(entry) {
    this.batch.push(entry);
    if (this.batch.length >= this.batchSize) {
      this.flush();
    }
  }
  
  flush() {
    if (this.batch.length > 0) {
      logger.info('Batch log entries', { entries: this.batch });
      this.batch = [];
    }
  }
}
```

### 4. Troubleshooting Guide

#### Common Issues and Solutions:

**High Log Volume:**
```bash
# Check log volume by service
kubectl top pods --sort-by=cpu | head -10

# Implement log sampling
[FILTER]
    Name                sampling
    Match               application.*
    Rate                10
```

**Missing Logs:**
```bash
# Check Fluent Bit status
kubectl logs -n amazon-cloudwatch -l k8s-app=fluent-bit

# Verify log group permissions
aws logs describe-log-groups --log-group-name-prefix /aws/containerinsights
```

**Log Parsing Errors:**
```bash
# Test JSON parsing
echo '{"level":"info","message":"test"}' | jq .

# Validate Fluent Bit parser
kubectl exec -n amazon-cloudwatch fluent-bit-xxx -- fluent-bit --test-config
```

This comprehensive guide provides everything needed to implement robust logging strategies for EKS workloads, from basic setup to advanced analytics and cost optimization.