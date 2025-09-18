# EFK Stack with EKS Complete Guide: From Zero to Production

A comprehensive guide for implementing Elasticsearch, Fluent Bit, and Kibana (EFK) on Amazon EKS with real-world e-commerce application examples.

## 📋 Table of Contents

1. [EFK Architecture Overview](#efk-architecture-overview)
2. [Prerequisites & EKS Setup](#prerequisites--eks-setup)
3. [Elasticsearch Installation](#elasticsearch-installation)
4. [Fluent Bit Configuration](#fluent-bit-configuration)
5. [Kibana Setup & Dashboards](#kibana-setup--dashboards)
6. [Real Application Example](#real-application-example)
7. [Index Management & Optimization](#index-management--optimization)
8. [Backup & Recovery](#backup--recovery)
9. [Security & Authentication](#security--authentication)
10. [Monitoring & Alerting](#monitoring--alerting)
11. [Troubleshooting](#troubleshooting)

## 🏗️ EFK Architecture Overview

### What is EFK Stack?
```
┌─────────────────────────────────────────────────────────────┐
│                        EKS Cluster                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ E-commerce  │  │   Payment   │  │   User      │        │
│  │ Frontend    │  │   Service   │  │   Service   │        │
│  │             │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                 │                 │             │
│         └─────────────────┼─────────────────┘             │
│                           │                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  Fluent Bit                            │ │
│  │           (Log Collection & Processing)                 │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Elasticsearch                          │ │
│  │            (Log Storage & Indexing)                    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    Kibana                              │ │
│  │           (Visualization & Analytics)                  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Components
- **Elasticsearch**: Distributed search and analytics engine
- **Fluent Bit**: Lightweight log processor and forwarder
- **Kibana**: Data visualization and exploration tool

## 🚀 Prerequisites & EKS Setup

### Step 1: Create EKS Cluster
```bash
# Create cluster configuration
cat > efk-cluster.yaml <<EOF
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: efk-demo
  region: us-west-2
  version: "1.28"

vpc:
  cidr: "10.0.0.0/16"

nodeGroups:
  - name: efk-nodes
    instanceType: m5.xlarge
    desiredCapacity: 3
    minSize: 1
    maxSize: 5
    volumeSize: 100
    volumeType: gp3
    labels:
      node-type: efk-worker
    tags:
      Environment: production
      Project: efk-demo

addons:
  - name: vpc-cni
  - name: coredns
  - name: kube-proxy
  - name: aws-ebs-csi-driver
EOF

# Create cluster
eksctl create cluster -f efk-cluster.yaml
```

### Step 2: Install Required Tools
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify cluster access
kubectl get nodes
```

## 🔍 Elasticsearch Installation

### Step 1: Create Namespace and Storage Class
```yaml
# efk-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: efk-stack
---
# Storage class for Elasticsearch
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: elasticsearch-storage
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

### Step 2: Elasticsearch Configuration
```yaml
# elasticsearch-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: elasticsearch-config
  namespace: efk-stack
data:
  elasticsearch.yml: |
    cluster.name: efk-cluster
    network.host: 0.0.0.0
    discovery.type: zen
    discovery.zen.minimum_master_nodes: 2
    discovery.zen.ping.unicast.hosts: ["elasticsearch-master-0.elasticsearch-master", "elasticsearch-master-1.elasticsearch-master", "elasticsearch-master-2.elasticsearch-master"]
    
    # Memory settings
    bootstrap.memory_lock: false
    
    # Index settings
    action.auto_create_index: true
    action.destructive_requires_name: true
    
    # Security settings
    xpack.security.enabled: false
    xpack.monitoring.collection.enabled: true
    
    # Performance settings
    thread_pool.write.queue_size: 1000
    thread_pool.search.queue_size: 1000
    
  jvm.options: |
    -Xms2g
    -Xmx2g
    -XX:+UseG1GC
    -XX:G1HeapRegionSize=16m
    -XX:+UseGCOverheadLimit
    -XX:+ExplicitGCInvokesConcurrent
    -Djava.io.tmpdir=${ES_TMPDIR}
    -XX:+HeapDumpOnOutOfMemoryError
```

### Step 3: Elasticsearch Master Nodes
```yaml
# elasticsearch-master.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch-master
  namespace: efk-stack
spec:
  serviceName: elasticsearch-master
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
      role: master
  template:
    metadata:
      labels:
        app: elasticsearch
        role: master
    spec:
      initContainers:
      - name: increase-vm-max-map
        image: busybox:1.35
        command: ["sysctl", "-w", "vm.max_map_count=262144"]
        securityContext:
          privileged: true
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
        ports:
        - containerPort: 9200
          name: http
        - containerPort: 9300
          name: transport
        env:
        - name: node.name
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: cluster.initial_master_nodes
          value: "elasticsearch-master-0,elasticsearch-master-1,elasticsearch-master-2"
        - name: discovery.seed_hosts
          value: "elasticsearch-master-0.elasticsearch-master,elasticsearch-master-1.elasticsearch-master,elasticsearch-master-2.elasticsearch-master"
        - name: ES_JAVA_OPTS
          value: "-Xms2g -Xmx2g"
        - name: node.roles
          value: "master"
        resources:
          requests:
            memory: 3Gi
            cpu: 1000m
          limits:
            memory: 4Gi
            cpu: 2000m
        volumeMounts:
        - name: elasticsearch-data
          mountPath: /usr/share/elasticsearch/data
        - name: elasticsearch-config
          mountPath: /usr/share/elasticsearch/config/elasticsearch.yml
          subPath: elasticsearch.yml
      volumes:
      - name: elasticsearch-config
        configMap:
          name: elasticsearch-config
  volumeClaimTemplates:
  - metadata:
      name: elasticsearch-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: elasticsearch-storage
      resources:
        requests:
          storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch-master
  namespace: efk-stack
spec:
  clusterIP: None
  selector:
    app: elasticsearch
    role: master
  ports:
  - port: 9200
    name: http
  - port: 9300
    name: transport
```

### Step 4: Elasticsearch Data Nodes
```yaml
# elasticsearch-data.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch-data
  namespace: efk-stack
spec:
  serviceName: elasticsearch-data
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
      role: data
  template:
    metadata:
      labels:
        app: elasticsearch
        role: data
    spec:
      initContainers:
      - name: increase-vm-max-map
        image: busybox:1.35
        command: ["sysctl", "-w", "vm.max_map_count=262144"]
        securityContext:
          privileged: true
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
        ports:
        - containerPort: 9200
          name: http
        - containerPort: 9300
          name: transport
        env:
        - name: node.name
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: cluster.initial_master_nodes
          value: "elasticsearch-master-0,elasticsearch-master-1,elasticsearch-master-2"
        - name: discovery.seed_hosts
          value: "elasticsearch-master-0.elasticsearch-master,elasticsearch-master-1.elasticsearch-master,elasticsearch-master-2.elasticsearch-master"
        - name: ES_JAVA_OPTS
          value: "-Xms4g -Xmx4g"
        - name: node.roles
          value: "data,ingest"
        resources:
          requests:
            memory: 6Gi
            cpu: 2000m
          limits:
            memory: 8Gi
            cpu: 4000m
        volumeMounts:
        - name: elasticsearch-data
          mountPath: /usr/share/elasticsearch/data
        - name: elasticsearch-config
          mountPath: /usr/share/elasticsearch/config/elasticsearch.yml
          subPath: elasticsearch.yml
      volumes:
      - name: elasticsearch-config
        configMap:
          name: elasticsearch-config
  volumeClaimTemplates:
  - metadata:
      name: elasticsearch-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: elasticsearch-storage
      resources:
        requests:
          storage: 200Gi
---
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch-data
  namespace: efk-stack
spec:
  clusterIP: None
  selector:
    app: elasticsearch
    role: data
  ports:
  - port: 9200
    name: http
  - port: 9300
    name: transport
```

### Step 5: Elasticsearch Client Service
```yaml
# elasticsearch-client.yaml
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch
  namespace: efk-stack
spec:
  selector:
    app: elasticsearch
  ports:
  - port: 9200
    name: http
    targetPort: 9200
  type: ClusterIP
```

## 📊 Fluent Bit Configuration

### Step 1: Fluent Bit ConfigMap
```yaml
# fluent-bit-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: efk-stack
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

    @INCLUDE input-kubernetes.conf
    @INCLUDE filter-kubernetes.conf
    @INCLUDE output-elasticsearch.conf

  input-kubernetes.conf: |
    [INPUT]
        Name              tail
        Tag               kube.*
        Path              /var/log/containers/*.log
        Parser            cri
        DB                /var/log/flb_kube.db
        Mem_Buf_Limit     50MB
        Skip_Long_Lines   On
        Refresh_Interval  10

  filter-kubernetes.conf: |
    [FILTER]
        Name                kubernetes
        Match               kube.*
        Kube_URL            https://kubernetes.default.svc:443
        Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
        Kube_Tag_Prefix     kube.var.log.containers.
        Merge_Log           On
        Merge_Log_Key       log_processed
        K8S-Logging.Parser  On
        K8S-Logging.Exclude Off
        Annotations         Off
        Labels              On

    [FILTER]
        Name                nest
        Match               kube.*
        Operation           lift
        Nested_under        kubernetes
        Add_prefix          kubernetes_

    [FILTER]
        Name                modify
        Match               kube.*
        Remove              stream
        Remove              kubernetes_pod_id
        Remove              kubernetes_host
        Remove              kubernetes_container_hash

    [FILTER]
        Name                grep
        Match               kube.*
        Exclude             kubernetes_namespace_name ^(kube-system|kube-public|kube-node-lease)$

  output-elasticsearch.conf: |
    [OUTPUT]
        Name            es
        Match           kube.*
        Host            elasticsearch.efk-stack.svc.cluster.local
        Port            9200
        Index           kubernetes-logs
        Type            _doc
        Logstash_Format On
        Logstash_Prefix kubernetes
        Logstash_DateFormat %Y.%m.%d
        Include_Tag_Key On
        Tag_Key         @tag
        Retry_Limit     False
        Suppress_Type_Name On

  parsers.conf: |
    [PARSER]
        Name   apache
        Format regex
        Regex  ^(?<host>[^ ]*) [^ ]* (?<user>[^ ]*) \[(?<time>[^\]]*)\] "(?<method>\S+)(?: +(?<path>[^\"]*?)(?: +\S*)?)?" (?<code>[^ ]*) (?<size>[^ ]*)(?: "(?<referer>[^\"]*)" "(?<agent>[^\"]*)")?$
        Time_Key time
        Time_Format %d/%b/%Y:%H:%M:%S %z

    [PARSER]
        Name   apache2
        Format regex
        Regex  ^(?<host>[^ ]*) [^ ]* (?<user>[^ ]*) \[(?<time>[^\]]*)\] "(?<method>\S+)(?: +(?<path>[^ ]*) +\S*)?" (?<code>[^ ]*) (?<size>[^ ]*)(?: "(?<referer>[^\"]*)" "(?<agent>[^\"]*)")?$
        Time_Key time
        Time_Format %d/%b/%Y:%H:%M:%S %z

    [PARSER]
        Name   apache_error
        Format regex
        Regex  ^\[[^ ]* (?<time>[^\]]*)\] \[(?<level>[^\]]*)\](?: \[pid (?<pid>[^\]]*)\])?( \[client (?<client>[^\]]*)\])? (?<message>.*)$

    [PARSER]
        Name   nginx
        Format regex
        Regex ^(?<remote>[^ ]*) (?<host>[^ ]*) (?<user>[^ ]*) \[(?<time>[^\]]*)\] "(?<method>\S+)(?: +(?<path>[^\"]*?)(?: +\S*)?)?" (?<code>[^ ]*) (?<size>[^ ]*)(?: "(?<referer>[^\"]*)" "(?<agent>[^\"]*)")?$
        Time_Key time
        Time_Format %d/%b/%Y:%H:%M:%S %z

    [PARSER]
        Name   json
        Format json
        Time_Key time
        Time_Format %d/%b/%Y:%H:%M:%S %z

    [PARSER]
        Name        docker
        Format      json
        Time_Key    time
        Time_Format %Y-%m-%dT%H:%M:%S.%L
        Time_Keep   On

    [PARSER]
        Name cri
        Format regex
        Regex ^(?<time>[^ ]+) (?<stream>stdout|stderr) (?<logtag>[^ ]*) (?<message>.*)$
        Time_Key    time
        Time_Format %Y-%m-%dT%H:%M:%S.%L%z
```

### Step 2: Fluent Bit DaemonSet
```yaml
# fluent-bit-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: efk-stack
  labels:
    k8s-app: fluent-bit-logging
    version: v1
    kubernetes.io/cluster-service: "true"
spec:
  selector:
    matchLabels:
      k8s-app: fluent-bit-logging
  template:
    metadata:
      labels:
        k8s-app: fluent-bit-logging
        version: v1
        kubernetes.io/cluster-service: "true"
    spec:
      serviceAccount: fluent-bit
      serviceAccountName: fluent-bit
      tolerations:
      - key: node-role.kubernetes.io/master
        operator: Exists
        effect: NoSchedule
      - operator: "Exists"
        effect: "NoExecute"
      - operator: "Exists"
        effect: "NoSchedule"
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:2.2.0
        imagePullPolicy: Always
        ports:
        - containerPort: 2020
        env:
        - name: FLUENT_ELASTICSEARCH_HOST
          value: "elasticsearch.efk-stack.svc.cluster.local"
        - name: FLUENT_ELASTICSEARCH_PORT
          value: "9200"
        resources:
          limits:
            memory: 200Mi
            cpu: 200m
          requests:
            cpu: 100m
            memory: 100Mi
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
      terminationGracePeriodSeconds: 10
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
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: fluent-bit
  namespace: efk-stack
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: fluent-bit-read
rules:
- apiGroups: [""]
  resources:
  - namespaces
  - pods
  - pods/logs
  - nodes
  - nodes/proxy
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: fluent-bit-read
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: fluent-bit-read
subjects:
- kind: ServiceAccount
  name: fluent-bit
  namespace: efk-stack
```

## 📈 Kibana Setup & Dashboards

### Step 1: Kibana Deployment
```yaml
# kibana.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kibana
  namespace: efk-stack
spec:
  replicas: 2
  selector:
    matchLabels:
      app: kibana
  template:
    metadata:
      labels:
        app: kibana
    spec:
      containers:
      - name: kibana
        image: docker.elastic.co/kibana/kibana:8.11.0
        ports:
        - containerPort: 5601
        env:
        - name: ELASTICSEARCH_HOSTS
          value: "http://elasticsearch.efk-stack.svc.cluster.local:9200"
        - name: SERVER_NAME
          value: "kibana"
        - name: SERVER_HOST
          value: "0.0.0.0"
        - name: XPACK_SECURITY_ENABLED
          value: "false"
        - name: XPACK_MONITORING_UI_CONTAINER_ELASTICSEARCH_ENABLED
          value: "true"
        resources:
          requests:
            memory: 1Gi
            cpu: 500m
          limits:
            memory: 2Gi
            cpu: 1000m
        readinessProbe:
          httpGet:
            path: /api/status
            port: 5601
          initialDelaySeconds: 30
          timeoutSeconds: 10
        livenessProbe:
          httpGet:
            path: /api/status
            port: 5601
          initialDelaySeconds: 60
          timeoutSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: kibana
  namespace: efk-stack
spec:
  selector:
    app: kibana
  ports:
  - port: 5601
    targetPort: 5601
  type: LoadBalancer
```

## 🛒 Real Application Example: E-commerce Platform

### Step 1: Sample E-commerce Application
```yaml
# ecommerce-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecommerce-frontend
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ecommerce-frontend
  template:
    metadata:
      labels:
        app: ecommerce-frontend
        tier: frontend
    spec:
      containers:
      - name: frontend
        image: nginx:1.21
        ports:
        - containerPort: 80
        volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx/nginx.conf
          subPath: nginx.conf
        - name: app-logs
          mountPath: /var/log/nginx
      - name: log-sidecar
        image: busybox:1.35
        command: ["/bin/sh"]
        args: ["-c", "tail -f /var/log/nginx/access.log"]
        volumeMounts:
        - name: app-logs
          mountPath: /var/log/nginx
      volumes:
      - name: nginx-config
        configMap:
          name: nginx-config
      - name: app-logs
        emptyDir: {}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
  namespace: default
data:
  nginx.conf: |
    events {
        worker_connections 1024;
    }
    http {
        log_format json_combined escape=json
        '{'
          '"time_local":"$time_local",'
          '"remote_addr":"$remote_addr",'
          '"remote_user":"$remote_user",'
          '"request":"$request",'
          '"status": "$status",'
          '"body_bytes_sent":"$body_bytes_sent",'
          '"request_time":"$request_time",'
          '"http_referrer":"$http_referer",'
          '"http_user_agent":"$http_user_agent",'
          '"request_id":"$request_id"'
        '}';
        
        access_log /var/log/nginx/access.log json_combined;
        error_log /var/log/nginx/error.log warn;
        
        server {
            listen 80;
            server_name localhost;
            
            location / {
                root /usr/share/nginx/html;
                index index.html;
            }
            
            location /api/products {
                proxy_pass http://product-service:8080;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
            }
            
            location /api/orders {
                proxy_pass http://order-service:8080;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
            }
        }
    }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: product-service
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: product-service
  template:
    metadata:
      labels:
        app: product-service
        tier: backend
    spec:
      containers:
      - name: product-service
        image: node:16-alpine
        ports:
        - containerPort: 8080
        env:
        - name: NODE_ENV
          value: "production"
        - name: LOG_LEVEL
          value: "info"
        command: ["/bin/sh"]
        args: ["-c", "while true; do echo '{\"timestamp\":\"$(date -Iseconds)\",\"level\":\"info\",\"service\":\"product-service\",\"message\":\"Processing product request\",\"user_id\":\"user-$(shuf -i 1-1000 -n 1)\",\"product_id\":\"prod-$(shuf -i 1-100 -n 1)\",\"action\":\"view\"}'; sleep $(shuf -i 1-5 -n 1); done"]
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
        tier: backend
    spec:
      containers:
      - name: order-service
        image: node:16-alpine
        ports:
        - containerPort: 8080
        env:
        - name: NODE_ENV
          value: "production"
        - name: LOG_LEVEL
          value: "info"
        command: ["/bin/sh"]
        args: ["-c", "while true; do echo '{\"timestamp\":\"$(date -Iseconds)\",\"level\":\"info\",\"service\":\"order-service\",\"message\":\"Processing order\",\"user_id\":\"user-$(shuf -i 1-1000 -n 1)\",\"order_id\":\"order-$(shuf -i 1-10000 -n 1)\",\"amount\":$(shuf -i 10-500 -n 1),\"status\":\"completed\"}'; sleep $(shuf -i 2-8 -n 1); done"]
---
apiVersion: v1
kind: Service
metadata:
  name: ecommerce-frontend
  namespace: default
spec:
  selector:
    app: ecommerce-frontend
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
---
apiVersion: v1
kind: Service
metadata:
  name: product-service
  namespace: default
spec:
  selector:
    app: product-service
  ports:
  - port: 8080
    targetPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: order-service
  namespace: default
spec:
  selector:
    app: order-service
  ports:
  - port: 8080
    targetPort: 8080
```

## 🗂️ Index Management & Optimization

### Step 1: Index Templates
```bash
# Create index template for application logs
curl -X PUT "elasticsearch.efk-stack.svc.cluster.local:9200/_index_template/ecommerce-logs" \
-H 'Content-Type: application/json' -d'
{
  "index_patterns": ["ecommerce-*"],
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "index.lifecycle.name": "ecommerce-policy",
      "index.lifecycle.rollover_alias": "ecommerce-logs"
    },
    "mappings": {
      "properties": {
        "@timestamp": {
          "type": "date"
        },
        "kubernetes_namespace_name": {
          "type": "keyword"
        },
        "kubernetes_pod_name": {
          "type": "keyword"
        },
        "kubernetes_container_name": {
          "type": "keyword"
        },
        "log": {
          "type": "text",
          "analyzer": "standard"
        },
        "level": {
          "type": "keyword"
        },
        "service": {
          "type": "keyword"
        },
        "user_id": {
          "type": "keyword"
        },
        "order_id": {
          "type": "keyword"
        },
        "product_id": {
          "type": "keyword"
        },
        "amount": {
          "type": "float"
        },
        "status": {
          "type": "keyword"
        }
      }
    }
  }
}'
```

### Step 2: Index Lifecycle Management (ILM)
```bash
# Create ILM policy
curl -X PUT "elasticsearch.efk-stack.svc.cluster.local:9200/_ilm/policy/ecommerce-policy" \
-H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "10GB",
            "max_age": "7d"
          },
          "set_priority": {
            "priority": 100
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "set_priority": {
            "priority": 50
          },
          "allocate": {
            "number_of_replicas": 0
          },
          "forcemerge": {
            "max_num_segments": 1
          }
        }
      },
      "cold": {
        "min_age": "30d",
        "actions": {
          "set_priority": {
            "priority": 0
          },
          "allocate": {
            "number_of_replicas": 0
          }
        }
      },
      "delete": {
        "min_age": "90d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}'
```

## 💾 Backup & Recovery

### Step 1: S3 Snapshot Repository
```bash
# Install S3 repository plugin (run on each Elasticsearch pod)
kubectl exec -it elasticsearch-master-0 -n efk-stack -- \
  /usr/share/elasticsearch/bin/elasticsearch-plugin install repository-s3

# Create S3 bucket for snapshots
aws s3 mb s3://efk-elasticsearch-snapshots --region us-west-2

# Configure snapshot repository
curl -X PUT "elasticsearch.efk-stack.svc.cluster.local:9200/_snapshot/s3-repository" \
-H 'Content-Type: application/json' -d'
{
  "type": "s3",
  "settings": {
    "bucket": "efk-elasticsearch-snapshots",
    "region": "us-west-2",
    "base_path": "elasticsearch-snapshots"
  }
}'
```

### Step 2: Automated Backup CronJob
```yaml
# elasticsearch-backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: elasticsearch-backup
  namespace: efk-stack
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: curlimages/curl:7.85.0
            command:
            - /bin/sh
            - -c
            - |
              DATE=$(date +%Y%m%d-%H%M%S)
              curl -X PUT "elasticsearch.efk-stack.svc.cluster.local:9200/_snapshot/s3-repository/snapshot-$DATE?wait_for_completion=true" \
              -H 'Content-Type: application/json' -d'
              {
                "indices": "kubernetes-*,ecommerce-*",
                "ignore_unavailable": true,
                "include_global_state": false,
                "metadata": {
                  "taken_by": "automated-backup",
                  "taken_because": "daily backup"
                }
              }'
          restartPolicy: OnFailure
```

### Step 3: Backup Monitoring
```yaml
# backup-monitoring.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backup-check-script
  namespace: efk-stack
data:
  check-backup.sh: |
    #!/bin/bash
    
    # Check latest snapshot
    LATEST_SNAPSHOT=$(curl -s "elasticsearch.efk-stack.svc.cluster.local:9200/_snapshot/s3-repository/_all" | \
      jq -r '.snapshots | sort_by(.start_time) | last | .snapshot')
    
    # Check snapshot status
    STATUS=$(curl -s "elasticsearch.efk-stack.svc.cluster.local:9200/_snapshot/s3-repository/$LATEST_SNAPSHOT" | \
      jq -r '.snapshots[0].state')
    
    if [ "$STATUS" != "SUCCESS" ]; then
      echo "Backup failed: $LATEST_SNAPSHOT - Status: $STATUS"
      exit 1
    else
      echo "Backup successful: $LATEST_SNAPSHOT"
    fi
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-check
  namespace: efk-stack
spec:
  schedule: "0 3 * * *"  # Check at 3 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup-check
            image: curlimages/curl:7.85.0
            command: ["/bin/sh", "/scripts/check-backup.sh"]
            volumeMounts:
            - name: backup-check-script
              mountPath: /scripts
          volumes:
          - name: backup-check-script
            configMap:
              name: backup-check-script
              defaultMode: 0755
          restartPolicy: OnFailure
```

## 🔒 Security & Authentication

### Step 1: Enable Elasticsearch Security
```yaml
# elasticsearch-security-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: elasticsearch-security-config
  namespace: efk-stack
data:
  elasticsearch.yml: |
    cluster.name: efk-cluster
    network.host: 0.0.0.0
    
    # Security settings
    xpack.security.enabled: true
    xpack.security.transport.ssl.enabled: true
    xpack.security.transport.ssl.verification_mode: certificate
    xpack.security.transport.ssl.keystore.path: certs/elastic-certificates.p12
    xpack.security.transport.ssl.truststore.path: certs/elastic-certificates.p12
    
    # HTTP SSL
    xpack.security.http.ssl.enabled: true
    xpack.security.http.ssl.keystore.path: certs/elastic-certificates.p12
    
    # Authentication
    xpack.security.authc:
      realms:
        native:
          native1:
            order: 0
```

### Step 2: Create SSL Certificates
```bash
# Generate certificates
kubectl create secret generic elastic-certificates \
  --from-file=elastic-certificates.p12 \
  -n efk-stack

# Create bootstrap password
kubectl create secret generic elastic-credentials \
  --from-literal=password=changeme \
  --from-literal=username=elastic \
  -n efk-stack
```

### Step 3: Network Policies
```yaml
# network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: elasticsearch-netpol
  namespace: efk-stack
spec:
  podSelector:
    matchLabels:
      app: elasticsearch
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: kibana
    - podSelector:
        matchLabels:
          k8s-app: fluent-bit-logging
    ports:
    - protocol: TCP
      port: 9200
    - protocol: TCP
      port: 9300
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: elasticsearch
    ports:
    - protocol: TCP
      port: 9300
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kibana-netpol
  namespace: efk-stack
spec:
  podSelector:
    matchLabels:
      app: kibana
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from: []
    ports:
    - protocol: TCP
      port: 5601
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: elasticsearch
    ports:
    - protocol: TCP
      port: 9200
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
```

## 📊 Monitoring & Alerting

### Step 1: Prometheus Monitoring
```yaml
# elasticsearch-servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: elasticsearch
  namespace: efk-stack
spec:
  selector:
    matchLabels:
      app: elasticsearch
  endpoints:
  - port: http
    path: /_prometheus/metrics
    interval: 30s
---
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch-metrics
  namespace: efk-stack
  labels:
    app: elasticsearch
spec:
  selector:
    app: elasticsearch
  ports:
  - port: 9200
    name: http
```

### Step 2: Alerting Rules
```yaml
# elasticsearch-alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: elasticsearch-alerts
  namespace: efk-stack
spec:
  groups:
  - name: elasticsearch
    rules:
    - alert: ElasticsearchClusterRed
      expr: elasticsearch_cluster_health_status{color="red"} == 1
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Elasticsearch cluster status is RED"
        description: "Elasticsearch cluster {{ $labels.cluster }} status is RED"
    
    - alert: ElasticsearchClusterYellow
      expr: elasticsearch_cluster_health_status{color="yellow"} == 1
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Elasticsearch cluster status is YELLOW"
        description: "Elasticsearch cluster {{ $labels.cluster }} status is YELLOW"
    
    - alert: ElasticsearchHighMemoryUsage
      expr: elasticsearch_jvm_memory_used_bytes / elasticsearch_jvm_memory_max_bytes > 0.9
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Elasticsearch high memory usage"
        description: "Elasticsearch node {{ $labels.instance }} memory usage is above 90%"
    
    - alert: ElasticsearchDiskSpaceLow
      expr: elasticsearch_filesystem_data_available_bytes / elasticsearch_filesystem_data_size_bytes < 0.1
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Elasticsearch low disk space"
        description: "Elasticsearch node {{ $labels.instance }} has less than 10% disk space available"
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Issue 1: Elasticsearch Pods Not Starting
```bash
# Check pod status
kubectl get pods -n efk-stack

# Check pod logs
kubectl logs elasticsearch-master-0 -n efk-stack

# Check events
kubectl describe pod elasticsearch-master-0 -n efk-stack

# Common fixes:
# 1. Increase vm.max_map_count
kubectl patch daemonset elasticsearch-master -n efk-stack -p '{"spec":{"template":{"spec":{"initContainers":[{"name":"increase-vm-max-map","image":"busybox:1.35","command":["sysctl","-w","vm.max_map_count=262144"],"securityContext":{"privileged":true}}]}}}}'

# 2. Check storage class
kubectl get storageclass

# 3. Verify node resources
kubectl describe nodes
```

#### Issue 2: Fluent Bit Not Collecting Logs
```bash
# Check Fluent Bit pods
kubectl get pods -n efk-stack -l k8s-app=fluent-bit-logging

# Check Fluent Bit logs
kubectl logs -f daemonset/fluent-bit -n efk-stack

# Test Fluent Bit configuration
kubectl exec -it fluent-bit-xxx -n efk-stack -- /fluent-bit/bin/fluent-bit --config=/fluent-bit/etc/fluent-bit.conf --dry-run

# Check if logs are reaching Elasticsearch
curl -X GET "elasticsearch.efk-stack.svc.cluster.local:9200/_cat/indices?v"
```

#### Issue 3: Kibana Connection Issues
```bash
# Check Kibana logs
kubectl logs deployment/kibana -n efk-stack

# Test Elasticsearch connectivity from Kibana pod
kubectl exec -it kibana-xxx -n efk-stack -- curl -X GET "elasticsearch.efk-stack.svc.cluster.local:9200/_cluster/health"

# Check service endpoints
kubectl get endpoints -n efk-stack
```

### Performance Tuning

#### Elasticsearch Optimization
```yaml
# elasticsearch-performance-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: elasticsearch-performance-config
  namespace: efk-stack
data:
  elasticsearch.yml: |
    # Thread pool settings
    thread_pool:
      write:
        queue_size: 1000
      search:
        queue_size: 1000
      
    # Index settings
    index:
      number_of_shards: 3
      number_of_replicas: 1
      refresh_interval: 30s
      
    # Memory settings
    indices.memory.index_buffer_size: 20%
    indices.memory.min_index_buffer_size: 96mb
    
    # Query cache
    indices.queries.cache.size: 20%
    
    # Field data cache
    indices.fielddata.cache.size: 40%
```

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] EKS cluster with sufficient resources (minimum 3 nodes, 8GB RAM each)
- [ ] Storage class configured for persistent volumes
- [ ] Network policies planned for security
- [ ] Backup strategy defined (S3 bucket created)

### Deployment Steps
- [ ] Deploy Elasticsearch cluster (master and data nodes)
- [ ] Verify Elasticsearch cluster health
- [ ] Deploy Fluent Bit DaemonSet
- [ ] Verify log collection is working
- [ ] Deploy Kibana
- [ ] Configure index patterns and dashboards
- [ ] Set up monitoring and alerting

### Post-Deployment
- [ ] Configure index lifecycle management
- [ ] Set up automated backups
- [ ] Create Kibana dashboards for application logs
- [ ] Configure alerting rules
- [ ] Document access procedures and troubleshooting steps

## 🎯 Best Practices

1. **Resource Planning**: Size Elasticsearch nodes based on log volume (1GB RAM per 10GB daily logs)
2. **Index Management**: Use ILM policies to manage index lifecycle and storage costs
3. **Security**: Enable authentication and use network policies in production
4. **Monitoring**: Set up comprehensive monitoring for cluster health and performance
5. **Backup**: Implement automated daily backups with retention policies
6. **Performance**: Tune JVM heap size (50% of available RAM, max 32GB)
7. **Scaling**: Use horizontal scaling for data nodes, vertical for master nodes

---

**Note**: This guide provides a production-ready EFK stack setup. Always test configurations in non-production environments first and adjust resource allocations based on your specific log volume and retention requirements.