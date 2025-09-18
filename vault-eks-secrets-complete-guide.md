# HashiCorp Vault with EKS: Complete Secrets Management Guide

## 🎯 Understanding the Secrets Management Challenge

### The Kubernetes Secrets Problem

**Traditional Kubernetes Secrets Limitations:**

**Built-in Kubernetes Secrets Issues:**
• Base64 encoding (not encryption)
• Stored in etcd without encryption at rest
• No secret rotation capabilities
• Limited access control granularity
• No audit trail for secret access
• Manual secret lifecycle management
• Compliance and governance challenges

**Real-world impact:**
• Security breaches due to exposed secrets
• Compliance failures (SOX, PCI DSS, HIPAA)
• Manual secret rotation leading to outages
• Lack of centralized secret management
• Developer productivity bottlenecks

**Enterprise Secrets Management Requirements:**

**Security Requirements:**
• Encryption at rest and in transit
• Dynamic secret generation
• Automatic secret rotation
• Fine-grained access control
• Comprehensive audit logging
• Zero-trust security model

**Operational Requirements:**
• Centralized secret management
• Self-service secret access
• Integration with CI/CD pipelines
• Multi-environment support
• Disaster recovery capabilities

**Compliance Requirements:**
• SOX: Financial data protection
• PCI DSS: Payment card data security
• HIPAA: Healthcare data privacy
• GDPR: Personal data protection
• SOC 2: Security controls audit

### Why HashiCorp Vault?

**Vault's Value Proposition:**

**Security Features:**
• AES-256 encryption for all data
• Dynamic secrets with TTL
• Automatic secret rotation
• Identity-based access control
• Comprehensive audit logging
• Secure secret sharing
• Compliance-ready architecture

**Operational Benefits:**
• Centralized secret management
• API-driven automation
• Multi-cloud support
• High availability and scaling
• Developer-friendly workflows
• Enterprise-grade reliability

**Business Impact Examples:**

**Financial Services Company:**
• Challenge: Manual database password rotation
• Risk: 48-hour rotation window with potential outages
• Solution: Vault dynamic database secrets
• Result: Zero-downtime rotation, 99.99% uptime

**E-commerce Platform:**
• Challenge: API keys scattered across environments
• Risk: Security breaches, compliance violations
• Solution: Centralized Vault secret management
• Result: 75% reduction in security incidents

**Healthcare SaaS:**
• Challenge: HIPAA compliance for patient data access
• Risk: Regulatory fines, reputation damage
• Solution: Vault identity-based access control
• Result: Successful HIPAA audit, zero violations

## 🏗️ Vault Architecture and Integration Patterns

### Understanding Vault Components

**Vault Core Architecture:**

**Vault Server Components:**
• Storage Backend (Consul, DynamoDB, S3)
• Authentication Methods (AWS IAM, Kubernetes, LDAP)
• Secret Engines (KV, Database, AWS, PKI)
• Policy Engine (Path-based access control)
• Audit Devices (File, Syslog, Socket)
• API Gateway (RESTful API interface)

**High Availability Setup:**
• Multiple Vault servers in cluster
• Raft consensus for coordination
• Load balancer for client access
• Auto-unsealing with AWS KMS
• Cross-region replication

**Vault Integration with EKS - Four Main Approaches:**

**1. Vault Secrets Operator (VSO) - RECOMMENDED**

**What it is:** A Kubernetes operator that creates Custom Resources (CRDs)

**How it works:**
• You create VaultStaticSecret or VaultDynamicSecret resources
• VSO watches these resources and fetches secrets from Vault
• VSO creates standard Kubernetes Secrets automatically
• Your pods consume secrets as normal environment variables
• VSO handles rotation and updates automatically

**Think of it as:** "Vault-aware Kubernetes that automatically manages secrets"

**Best for:**
• New cloud-native applications
• Teams comfortable with Kubernetes CRDs
• GitOps workflows
• When you want Kubernetes to handle everything

**2. Vault Agent Sidecar**

**What it is:** A separate container running alongside your main application

**How it works:**
• Sidecar container runs Vault Agent process
• Agent authenticates to Vault and fetches secrets
• Agent writes secrets to shared filesystem as files
• Your main application reads secrets from files
• Agent handles authentication and renewal automatically

**Think of it as:** "Personal Vault assistant for each pod"

**Best for:**
• Legacy applications that read config files
• Applications that can't be modified
• Complex secret templating needs
• When you need file-based secret delivery

**3. External Secrets Operator (ESO)**

**What it is:** Third-party operator that supports multiple secret backends

**How it works:**
• You create ExternalSecret resources pointing to Vault
• ESO fetches secrets from Vault (and other providers)
• ESO creates standard Kubernetes Secrets
• Your pods consume secrets as environment variables
• Works with Vault, AWS Secrets Manager, Azure Key Vault, etc.

**Think of it as:** "Universal translator for different secret systems"

**Best for:**
• Multi-cloud environments
• Migration from other secret managers
• When you need multiple secret backends
• Existing ESO infrastructure

**4. Direct API Integration**

**What it is:** Your application code directly calls Vault APIs

**How it works:**
• Your application authenticates to Vault using SDK
• Application makes HTTP calls to Vault API endpoints
• Application handles secret caching and renewal
• No additional Kubernetes components needed
• Full control over secret lifecycle

**Think of it as:** "Your app talks directly to Vault like a database"

**Best for:**
• Maximum control over secret handling
• Custom caching and retry logic
• Applications with specific secret requirements
• When you want minimal infrastructure dependencies

### Authentication Methods Comparison

**AWS IAM Authentication (Recommended for EKS):**

**Benefits:**
• Leverages existing AWS IAM roles
• No additional credentials to manage
• Seamless EKS integration
• Fine-grained permissions
• Audit trail through CloudTrail

**How it works:**
1. Pod assumes IAM role via IRSA
2. Vault validates IAM role against policy
3. Issues Vault token with appropriate permissions
4. Pod uses token to access secrets

**Kubernetes Authentication:**

**Benefits:**
• Native Kubernetes integration
• Service account-based access
• Namespace-level isolation
• RBAC integration
• No external dependencies

**Use cases:**
• Pure Kubernetes environments
• Multi-cloud deployments
• When AWS IAM is not available
• Development environments

## 🚀 Complete Implementation: E-commerce Application

### Business Scenario

**Application Requirements:**

**E-commerce Microservices Platform:**
• User Service: Needs database credentials
• Payment Service: Requires payment gateway API keys
• Inventory Service: Needs Redis connection details
• Notification Service: Requires email service credentials
• Analytics Service: Needs data warehouse access
• Admin Service: Requires elevated database permissions

**Security Requirements:**
• PCI DSS compliance for payment data
• Dynamic database credentials
• API key rotation every 30 days
• Audit trail for all secret access
• Namespace-based isolation
• Zero-trust security model

### Step 1: Vault Infrastructure Setup

**Vault Deployment on EKS:**
```yaml
# vault-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: vault-system
  labels:
    name: vault-system
---
# vault-storage-class.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: vault-storage
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
---
# vault-helm-values.yaml
# This would be used with: helm install vault hashicorp/vault -f vault-helm-values.yaml
global:
  enabled: true
  tlsDisable: false

server:
  image:
    repository: "hashicorp/vault"
    tag: "1.15.2"
  
  # High Availability configuration
  ha:
    enabled: true
    replicas: 3
    raft:
      enabled: true
      setNodeId: true
      config: |
        ui = true
        listener "tcp" {
          tls_disable = 0
          address = "[::]:8200"
          cluster_address = "[::]:8201"
          tls_cert_file = "/vault/userconfig/vault-tls/tls.crt"
          tls_key_file = "/vault/userconfig/vault-tls/tls.key"
        }
        
        storage "raft" {
          path = "/vault/data"
          retry_join {
            leader_api_addr = "https://vault-0.vault-internal:8200"
          }
          retry_join {
            leader_api_addr = "https://vault-1.vault-internal:8200"
          }
          retry_join {
            leader_api_addr = "https://vault-2.vault-internal:8200"
          }
        }
        
        seal "awskms" {
          region = "us-west-2"
          kms_key_id = "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012"
        }
        
        service_registration "kubernetes" {}

  # Resource requirements
  resources:
    requests:
      memory: 256Mi
      cpu: 250m
    limits:
      memory: 512Mi
      cpu: 500m

  # Storage configuration
  dataStorage:
    enabled: true
    size: 10Gi
    storageClass: vault-storage
    accessMode: ReadWriteOnce

  # Service configuration
  service:
    enabled: true
    type: LoadBalancer
    annotations:
      service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
      service.beta.kubernetes.io/aws-load-balancer-internal: "true"

  # Ingress configuration
  ingress:
    enabled: true
    annotations:
      kubernetes.io/ingress.class: "alb"
      alb.ingress.kubernetes.io/scheme: internal
      alb.ingress.kubernetes.io/target-type: ip
      alb.ingress.kubernetes.io/certificate-arn: "arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012"
    hosts:
      - host: vault.internal.company.com
        paths:
          - /
    tls:
      - secretName: vault-tls
        hosts:
          - vault.internal.company.com

# UI configuration
ui:
  enabled: true
  serviceType: "ClusterIP"

# Vault Secrets Operator
csi:
  enabled: false

# Injector (we'll use VSO instead)
injector:
  enabled: false
```

**Vault Initialization and Configuration:**
```bash
# Initialize Vault cluster
kubectl exec -n vault-system vault-0 -- vault operator init \
  -key-shares=5 \
  -key-threshold=3 \
  -format=json > vault-init.json

# Extract unseal keys and root token
VAULT_UNSEAL_KEY_1=$(cat vault-init.json | jq -r ".unseal_keys_b64[0]")
VAULT_UNSEAL_KEY_2=$(cat vault-init.json | jq -r ".unseal_keys_b64[1]")
VAULT_UNSEAL_KEY_3=$(cat vault-init.json | jq -r ".unseal_keys_b64[2]")
VAULT_ROOT_TOKEN=$(cat vault-init.json | jq -r ".root_token")

# Unseal all Vault instances (if not using auto-unseal)
for i in {0..2}; do
  kubectl exec -n vault-system vault-$i -- vault operator unseal $VAULT_UNSEAL_KEY_1
  kubectl exec -n vault-system vault-$i -- vault operator unseal $VAULT_UNSEAL_KEY_2
  kubectl exec -n vault-system vault-$i -- vault operator unseal $VAULT_UNSEAL_KEY_3
done

# Login to Vault
kubectl exec -n vault-system vault-0 -- vault auth -method=token token=$VAULT_ROOT_TOKEN
```

### Step 2: Configure Authentication and Secret Engines

**AWS IAM Authentication Setup:**
```bash
# Enable AWS auth method
kubectl exec -n vault-system vault-0 -- vault auth enable aws

# Configure AWS auth method
kubectl exec -n vault-system vault-0 -- vault write auth/aws/config/client \
  access_key=$AWS_ACCESS_KEY_ID \
  secret_key=$AWS_SECRET_ACCESS_KEY \
  region=us-west-2

# Create IAM role for EKS pods
kubectl exec -n vault-system vault-0 -- vault write auth/aws/role/ecommerce-app \
  auth_type=iam \
  bound_iam_principal_arn="arn:aws:iam::123456789012:role/EKSPodRole" \
  policies="ecommerce-policy" \
  ttl=1h \
  max_ttl=24h
```

**Secret Engines Configuration:**
```bash
# Enable KV v2 secret engine for static secrets
kubectl exec -n vault-system vault-0 -- vault secrets enable -path=ecommerce kv-v2

# Enable database secret engine for dynamic credentials
kubectl exec -n vault-system vault-0 -- vault secrets enable database

# Configure PostgreSQL database connection
kubectl exec -n vault-system vault-0 -- vault write database/config/ecommerce-db \
  plugin_name=postgresql-database-plugin \
  connection_url="postgresql://{{username}}:{{password}}@postgres.ecommerce.svc.cluster.local:5432/ecommerce?sslmode=require" \
  allowed_roles="ecommerce-readonly,ecommerce-readwrite" \
  username="vault-admin" \
  password="secure-admin-password"

# Create database roles
kubectl exec -n vault-system vault-0 -- vault write database/roles/ecommerce-readonly \
  db_name=ecommerce-db \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="24h"

kubectl exec -n vault-system vault-0 -- vault write database/roles/ecommerce-readwrite \
  db_name=ecommerce-db \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="24h"
```

**Policies Configuration:**
```bash
# Create policy for ecommerce application
kubectl exec -n vault-system vault-0 -- vault policy write ecommerce-policy - <<EOF
# Read static secrets
path "ecommerce/data/user-service/*" {
  capabilities = ["read"]
}

path "ecommerce/data/payment-service/*" {
  capabilities = ["read"]
}

path "ecommerce/data/shared/*" {
  capabilities = ["read"]
}

# Generate dynamic database credentials
path "database/creds/ecommerce-readonly" {
  capabilities = ["read"]
}

path "database/creds/ecommerce-readwrite" {
  capabilities = ["read"]
}

# Renew own tokens
path "auth/token/renew-self" {
  capabilities = ["update"]
}
EOF
```

### Step 3: Deploy Vault Secrets Operator

**VSO Installation:**
```yaml
# vault-secrets-operator.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: vault-secrets-operator-system
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vault-secrets-operator
  namespace: vault-secrets-operator-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vault-secrets-operator
  template:
    metadata:
      labels:
        app: vault-secrets-operator
    spec:
      serviceAccountName: vault-secrets-operator
      containers:
      - name: manager
        image: hashicorp/vault-secrets-operator:0.4.0
        args:
        - --leader-elect
        env:
        - name: OPERATOR_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        resources:
          limits:
            cpu: 500m
            memory: 128Mi
          requests:
            cpu: 10m
            memory: 64Mi
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          capabilities:
            drop:
            - ALL
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vault-secrets-operator
  namespace: vault-secrets-operator-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: vault-secrets-operator
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["create", "delete", "get", "list", "patch", "update", "watch"]
- apiGroups: ["secrets.hashicorp.com"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: vault-secrets-operator
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: vault-secrets-operator
subjects:
- kind: ServiceAccount
  name: vault-secrets-operator
  namespace: vault-secrets-operator-system
```

### Step 4: Configure Vault Connection and Authentication

**VaultConnection Resource:**
```yaml
# vault-connection.yaml
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultConnection
metadata:
  name: vault-connection
  namespace: ecommerce
spec:
  # Vault server address
  address: "https://vault.internal.company.com:8200"
  
  # TLS configuration
  tlsConfig:
    skipVerify: false
    serverName: "vault.internal.company.com"
    caCertSecretRef: "vault-ca-cert"
  
  # Headers for additional configuration
  headers:
    X-Vault-Namespace: "ecommerce"
```

**VaultAuth Resource for AWS IAM:**
```yaml
# vault-auth-aws.yaml
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultAuth
metadata:
  name: vault-auth-aws
  namespace: ecommerce
spec:
  # Reference to VaultConnection
  vaultConnectionRef: vault-connection
  
  # AWS IAM authentication method
  method: aws
  mount: aws
  
  # AWS IAM configuration
  aws:
    role: "ecommerce-app"
    region: "us-west-2"
    # Use IRSA (IAM Roles for Service Accounts)
    irsaServiceAccount: "ecommerce-service-account"
```

**Service Account with IRSA:**
```yaml
# ecommerce-service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ecommerce-service-account
  namespace: ecommerce
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::123456789012:role/EKSPodRole"
```

### Step 5: Application Implementation with Secret Access

**User Service with Dynamic Database Credentials:**
```yaml
# user-service-secrets.yaml
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultDynamicSecret
metadata:
  name: user-service-db-creds
  namespace: ecommerce
spec:
  # Vault connection and authentication
  vaultAuthRef: vault-auth-aws
  
  # Database secret engine path
  mount: database
  path: creds/ecommerce-readonly
  
  # Destination Kubernetes secret
  destination:
    name: user-service-db-secret
    create: true
    
  # Renewal configuration
  renewalPercent: 67  # Renew when 67% of TTL has passed
  
  # Rollout restart for deployments using this secret
  rolloutRestartTargets:
  - kind: Deployment
    name: user-service
---
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultStaticSecret
metadata:
  name: user-service-config
  namespace: ecommerce
spec:
  # Vault connection and authentication
  vaultAuthRef: vault-auth-aws
  
  # KV v2 secret engine path
  mount: ecommerce
  path: user-service/config
  
  # Destination Kubernetes secret
  destination:
    name: user-service-config-secret
    create: true
  
  # Refresh interval for static secrets
  refreshAfter: 30m
  
  # Rollout restart for deployments using this secret
  rolloutRestartTargets:
  - kind: Deployment
    name: user-service
```

**User Service Deployment:**
```yaml
# user-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  namespace: ecommerce
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      serviceAccountName: ecommerce-service-account
      containers:
      - name: user-service
        image: ecommerce/user-service:v1.2.0
        ports:
        - containerPort: 8080
        env:
        # Database credentials from Vault dynamic secret
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: user-service-db-secret
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: user-service-db-secret
              key: password
        - name: DB_HOST
          value: "postgres.ecommerce.svc.cluster.local"
        - name: DB_PORT
          value: "5432"
        - name: DB_NAME
          value: "ecommerce"
        
        # Application configuration from Vault static secret
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: user-service-config-secret
              key: jwt_secret
        - name: ENCRYPTION_KEY
          valueFrom:
            secretKeyRef:
              name: user-service-config-secret
              key: encryption_key
        
        # Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        
        # Resource limits
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        
        # Security context
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1000
```

**User Service Application Code (Go):**
```go
// user-service/main.go
package main

import (
    "database/sql"
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "os"
    "time"
    
    "github.com/gorilla/mux"
    _ "github.com/lib/pq"
)

type Config struct {
    DBHost       string
    DBPort       string
    DBName       string
    DBUsername   string
    DBPassword   string
    JWTSecret    string
    EncryptionKey string
}

type UserService struct {
    db     *sql.DB
    config *Config
}

type User struct {
    ID       int    `json:"id"`
    Username string `json:"username"`
    Email    string `json:"email"`
    Created  time.Time `json:"created"`
}

func loadConfig() *Config {
    return &Config{
        DBHost:       getEnv("DB_HOST", "localhost"),
        DBPort:       getEnv("DB_PORT", "5432"),
        DBName:       getEnv("DB_NAME", "ecommerce"),
        DBUsername:   getEnv("DB_USERNAME", ""),
        DBPassword:   getEnv("DB_PASSWORD", ""),
        JWTSecret:    getEnv("JWT_SECRET", ""),
        EncryptionKey: getEnv("ENCRYPTION_KEY", ""),
    }
}

func getEnv(key, defaultValue string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultValue
}

func (us *UserService) initDB() error {
    connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=require",
        us.config.DBHost, us.config.DBPort, us.config.DBUsername, 
        us.config.DBPassword, us.config.DBName)
    
    var err error
    us.db, err = sql.Open("postgres", connStr)
    if err != nil {
        return fmt.Errorf("failed to connect to database: %w", err)
    }
    
    // Test connection
    if err := us.db.Ping(); err != nil {
        return fmt.Errorf("failed to ping database: %w", err)
    }
    
    log.Printf("Connected to database as user: %s", us.config.DBUsername)
    return nil
}

func (us *UserService) getUsers(w http.ResponseWriter, r *http.Request) {
    rows, err := us.db.Query("SELECT id, username, email, created_at FROM users LIMIT 100")
    if err != nil {
        http.Error(w, fmt.Sprintf("Database query failed: %v", err), http.StatusInternalServerError)
        return
    }
    defer rows.Close()
    
    var users []User
    for rows.Next() {
        var user User
        if err := rows.Scan(&user.ID, &user.Username, &user.Email, &user.Created); err != nil {
            log.Printf("Error scanning user row: %v", err)
            continue
        }
        users = append(users, user)
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(users)
}

func (us *UserService) healthCheck(w http.ResponseWriter, r *http.Request) {
    // Check database connection
    if err := us.db.Ping(); err != nil {
        w.WriteHeader(http.StatusServiceUnavailable)
        json.NewEncoder(w).Encode(map[string]string{
            "status": "unhealthy",
            "error":  err.Error(),
        })
        return
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]string{
        "status": "healthy",
        "timestamp": time.Now().Format(time.RFC3339),
    })
}

func (us *UserService) readinessCheck(w http.ResponseWriter, r *http.Request) {
    // Verify all required configuration is present
    if us.config.DBUsername == "" || us.config.DBPassword == "" {
        w.WriteHeader(http.StatusServiceUnavailable)
        json.NewEncoder(w).Encode(map[string]string{
            "status": "not ready",
            "error":  "missing database credentials",
        })
        return
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]string{
        "status": "ready",
    })
}

func main() {
    config := loadConfig()
    
    // Validate required configuration
    if config.DBUsername == "" || config.DBPassword == "" {
        log.Fatal("Database credentials not provided")
    }
    
    userService := &UserService{config: config}
    
    // Initialize database connection
    if err := userService.initDB(); err != nil {
        log.Fatalf("Failed to initialize database: %v", err)
    }
    defer userService.db.Close()
    
    // Setup routes
    router := mux.NewRouter()
    router.HandleFunc("/users", userService.getUsers).Methods("GET")
    router.HandleFunc("/health", userService.healthCheck).Methods("GET")
    router.HandleFunc("/ready", userService.readinessCheck).Methods("GET")
    
    // Start server
    log.Println("User service starting on port 8080")
    log.Fatal(http.ListenAndServe(":8080", router))
}
```

### Step 6: Payment Service with API Key Management

**Payment Service Secrets Configuration:**
```yaml
# payment-service-secrets.yaml
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultStaticSecret
metadata:
  name: payment-service-secrets
  namespace: ecommerce
spec:
  vaultAuthRef: vault-auth-aws
  mount: ecommerce
  path: payment-service/api-keys
  
  destination:
    name: payment-service-secrets
    create: true
  
  # Refresh every 30 minutes to get updated secrets
  refreshAfter: 30m
  
  rolloutRestartTargets:
  - kind: Deployment
    name: payment-service
---
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultDynamicSecret
metadata:
  name: payment-service-db-creds
  namespace: ecommerce
spec:
  vaultAuthRef: vault-auth-aws
  mount: database
  path: creds/ecommerce-readwrite  # Payment service needs write access
  
  destination:
    name: payment-service-db-secret
    create: true
    
  renewalPercent: 67
  
  rolloutRestartTargets:
  - kind: Deployment
    name: payment-service
```

**Payment Service Deployment:**
```yaml
# payment-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
  namespace: ecommerce
spec:
  replicas: 2
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
    spec:
      serviceAccountName: ecommerce-service-account
      containers:
      - name: payment-service
        image: ecommerce/payment-service:v1.2.0
        ports:
        - containerPort: 8080
        env:
        # Database credentials
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: payment-service-db-secret
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: payment-service-db-secret
              key: password
        
        # Payment gateway API keys
        - name: STRIPE_API_KEY
          valueFrom:
            secretKeyRef:
              name: payment-service-secrets
              key: stripe_api_key
        - name: PAYPAL_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: payment-service-secrets
              key: paypal_client_id
        - name: PAYPAL_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: payment-service-secrets
              key: paypal_client_secret
        
        # PCI DSS compliance configurations
        - name: ENCRYPTION_KEY
          valueFrom:
            secretKeyRef:
              name: payment-service-secrets
              key: encryption_key
        - name: SIGNING_KEY
          valueFrom:
            secretKeyRef:
              name: payment-service-secrets
              key: signing_key
        
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "400m"
        
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1000
```

## 🔄 Alternative Approaches and Patterns

### Approach 1: Vault Agent Sidecar Pattern

**What is Vault Agent Sidecar?**
```
Concept: A helper container that sits next to your main application

How it works:
┌─────────────────────────────────────┐
│              Pod                    │
│  ┌─────────────┐  ┌─────────────┐   │
│  │ Vault Agent │  │    Your     │   │
│  │  Sidecar    │  │    App      │   │
│  │             │  │             │   │
│  │ ┌─────────┐ │  │ ┌─────────┐ │   │
│  │ │ Vault   │ │  │ │ Reads   │ │   │
│  │ │ API     │ │  │ │ Files   │ │   │
│  │ │ Client  │ │  │ │         │ │   │
│  │ └─────────┘ │  │ └─────────┘ │   │
│  └─────────────┘  └─────────────┘   │
│           │              │          │
│           └──────────────┘          │
│         Shared File System          │
└─────────────────────────────────────┘

Step-by-step process:
1. Vault Agent authenticates to Vault server
2. Agent fetches secrets using templates
3. Agent writes secrets to shared files
4. Your app reads secrets from files
5. Agent automatically renews secrets
```

**When to Use:**
```
Perfect for:
├── Legacy applications that read config files
├── Applications you cannot modify
├── When you need complex secret formatting
├── Multiple secrets from different Vault paths
└── Applications expecting file-based configuration

Real example:
├── Old Java app that reads database.properties file
├── Python script that expects .env file
├── Legacy C++ application with config.ini
└── Any app that does: config = readFile("/etc/config.json")
```

**Implementation:**
```yaml
# vault-agent-sidecar.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: legacy-app-with-vault-agent
  namespace: ecommerce
spec:
  replicas: 1
  selector:
    matchLabels:
      app: legacy-app
  template:
    metadata:
      labels:
        app: legacy-app
    spec:
      serviceAccountName: ecommerce-service-account
      
      # Shared volume for secrets
      volumes:
      - name: vault-secrets
        emptyDir: {}
      - name: vault-config
        configMap:
          name: vault-agent-config
      
      # Init container for initial secret fetch
      initContainers:
      - name: vault-agent-init
        image: hashicorp/vault:1.15.2
        command: ["vault", "agent", "-config=/vault/config/agent.hcl", "-exit-after-auth"]
        volumeMounts:
        - name: vault-secrets
          mountPath: /vault/secrets
        - name: vault-config
          mountPath: /vault/config
        env:
        - name: VAULT_ADDR
          value: "https://vault.internal.company.com:8200"
      
      containers:
      # Vault Agent sidecar
      - name: vault-agent
        image: hashicorp/vault:1.15.2
        command: ["vault", "agent", "-config=/vault/config/agent.hcl"]
        volumeMounts:
        - name: vault-secrets
          mountPath: /vault/secrets
        - name: vault-config
          mountPath: /vault/config
        env:
        - name: VAULT_ADDR
          value: "https://vault.internal.company.com:8200"
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
      
      # Main application container
      - name: legacy-app
        image: ecommerce/legacy-app:v1.0.0
        volumeMounts:
        - name: vault-secrets
          mountPath: /etc/secrets
          readOnly: true
        env:
        - name: CONFIG_FILE
          value: "/etc/secrets/app-config.json"
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "400m"
---
# Vault Agent configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: vault-agent-config
  namespace: ecommerce
data:
  agent.hcl: |
    pid_file = "/tmp/pidfile"
    
    auto_auth {
      method "aws" {
        mount_path = "auth/aws"
        config = {
          type = "iam"
          role = "ecommerce-app"
        }
      }
      
      sink "file" {
        config = {
          path = "/tmp/vault-token"
        }
      }
    }
    
    cache {
      use_auto_auth_token = true
    }
    
    listener "tcp" {
      address = "127.0.0.1:8007"
      tls_disable = true
    }
    
    template {
      source = "/vault/config/app-config.tpl"
      destination = "/vault/secrets/app-config.json"
      perms = 0644
    }
    
    vault {
      address = "https://vault.internal.company.com:8200"
    }
  
  app-config.tpl: |
    {
      "database": {
        {{- with secret "database/creds/ecommerce-readonly" }}
        "username": "{{ .Data.username }}",
        "password": "{{ .Data.password }}",
        {{- end }}
        "host": "postgres.ecommerce.svc.cluster.local",
        "port": 5432,
        "database": "ecommerce"
      },
      "api_keys": {
        {{- with secret "ecommerce/data/legacy-app/config" }}
        "external_api_key": "{{ .Data.data.external_api_key }}",
        "webhook_secret": "{{ .Data.data.webhook_secret }}"
        {{- end }}
      }
    }
```

### Approach 2: External Secrets Operator (ESO)

**What is External Secrets Operator?**
```
Concept: A "universal translator" for different secret management systems

How it works:
┌─────────────────────────────────────────────────────┐
│                 Kubernetes Cluster                  │
│                                                     │
│  ┌─────────────────┐    ┌─────────────────────┐    │
│  │ ExternalSecret  │    │  Kubernetes Secret  │    │
│  │   Resource      │───▶│    (Created by      │    │
│  │                 │    │        ESO)         │    │
│  └─────────────────┘    └─────────────────────┘    │
│           │                        │               │
│           ▼                        ▼               │
│  ┌─────────────────┐    ┌─────────────────────┐    │
│  │      ESO        │    │     Your Pods      │    │
│  │   Controller    │    │  (Read K8s Secret) │    │
│  └─────────────────┘    └─────────────────────┘    │
└─────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│              External Secret Systems                │
│  ┌─────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │  Vault  │ │ AWS Secrets │ │ Azure Key Vault │   │
│  │         │ │   Manager   │ │                 │   │
│  └─────────┘ └─────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────┘

Step-by-step process:
1. You create ExternalSecret resource pointing to Vault
2. ESO reads the ExternalSecret specification
3. ESO connects to Vault (or AWS/Azure/etc.) to fetch secrets
4. ESO creates a regular Kubernetes Secret
5. Your pods use the Kubernetes Secret normally
```

**When to Use:**
```
Perfect for:
├── Companies using multiple cloud providers
├── Migration scenarios (moving from AWS Secrets Manager to Vault)
├── Teams already familiar with ESO
├── When you need one tool for all secret backends
└── Standardizing secret access across different systems

Real example:
├── Secrets in AWS Secrets Manager (legacy)
├── New secrets in HashiCorp Vault
├── Some secrets in Azure Key Vault
└── ESO provides one consistent interface for all
```

**Implementation:**
```yaml
# external-secrets-operator.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-secret-store
  namespace: ecommerce
spec:
  provider:
    vault:
      server: "https://vault.internal.company.com:8200"
      path: "ecommerce"
      version: "v2"
      auth:
        aws:
          region: "us-west-2"
          role: "ecommerce-app"
          secretRef:
            accessKeyID:
              name: "aws-credentials"
              key: "access-key-id"
            secretAccessKey:
              name: "aws-credentials"
              key: "secret-access-key"
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: user-service-external-secret
  namespace: ecommerce
spec:
  refreshInterval: 30m
  secretStoreRef:
    name: vault-secret-store
    kind: SecretStore
  
  target:
    name: user-service-config-secret
    creationPolicy: Owner
  
  data:
  - secretKey: jwt_secret
    remoteRef:
      key: user-service/config
      property: jwt_secret
  - secretKey: encryption_key
    remoteRef:
      key: user-service/config
      property: encryption_key
```

### Approach 3: Vault CSI Provider

**When to Use:**
```
Scenarios:
├── File-based secret consumption
├── High-performance secret access
├── Minimal application changes
├── Secrets as mounted files
└── Legacy application integration

Benefits:
├── Native Kubernetes volume integration
├── Automatic secret rotation
├── File-based secret delivery
├── No sidecar containers needed
└── CSI driver ecosystem compatibility
```

**Implementation:**
```yaml
# vault-csi-provider.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-csi-secrets
  namespace: ecommerce
spec:
  replicas: 1
  selector:
    matchLabels:
      app: app-with-csi-secrets
  template:
    metadata:
      labels:
        app: app-with-csi-secrets
    spec:
      serviceAccountName: ecommerce-service-account
      
      volumes:
      - name: secrets-store
        csi:
          driver: secrets-store.csi.k8s.io
          readOnly: true
          volumeAttributes:
            secretProviderClass: "vault-secrets"
      
      containers:
      - name: app
        image: ecommerce/sample-app:v1.0.0
        volumeMounts:
        - name: secrets-store
          mountPath: "/mnt/secrets-store"
          readOnly: true
        env:
        - name: DB_PASSWORD_FILE
          value: "/mnt/secrets-store/db-password"
        - name: API_KEY_FILE
          value: "/mnt/secrets-store/api-key"
---
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: vault-secrets
  namespace: ecommerce
spec:
  provider: vault
  parameters:
    vaultAddress: "https://vault.internal.company.com:8200"
    roleName: "ecommerce-app"
    objects: |
      - objectName: "db-password"
        secretPath: "database/creds/ecommerce-readonly"
        secretKey: "password"
      - objectName: "api-key"
        secretPath: "ecommerce/data/shared/config"
        secretKey: "api_key"
```

### Approach 4: Direct Vault API Integration

**What is Direct API Integration?**
```
Concept: Your application code directly talks to Vault like a database

How it works:
┌─────────────────────────────────────────────────────┐
│                 Kubernetes Cluster                  │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │              Your Pod                       │    │
│  │                                             │    │
│  │  ┌─────────────────────────────────────┐    │    │
│  │  │         Your Application            │    │    │
│  │  │                                     │    │    │
│  │  │  ┌─────────────────────────────┐    │    │    │
│  │  │  │     Vault SDK/Client        │    │    │    │
│  │  │  │  (Go, Java, Python, etc.)  │    │    │    │
│  │  │  └─────────────────────────────┘    │    │    │
│  │  └─────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
           │
           │ HTTPS API Calls
           ▼
┌─────────────────────────────────────────────────────┐
│                 Vault Server                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │   Auth      │ │   Secrets   │ │   Policies  │   │
│  │  Methods    │ │   Engines   │ │             │   │
│  └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────┘

Step-by-step process:
1. Your app imports Vault SDK (like importing database driver)
2. App authenticates to Vault (gets token)
3. App makes API calls: client.Read("secret/myapp/config")
4. App handles caching, retries, token renewal
5. App uses secrets directly in business logic
```

**When to Use:**
```
Perfect for:
├── Applications needing maximum control
├── Custom secret caching strategies
├── Dynamic secret path generation
├── Complex error handling and retry logic
└── When you want minimal infrastructure dependencies

Real example:
├── Multi-tenant SaaS app: secrets at "tenant/{id}/config"
├── Gaming app: different secrets per game region
├── Financial app: secrets based on user risk level
└── Any app where secret path depends on runtime data
```

**Implementation:**
```go
// vault-client/client.go
package main

import (
    "context"
    "fmt"
    "log"
    "os"
    "time"
    
    "github.com/hashicorp/vault/api"
    "github.com/hashicorp/vault/api/auth/aws"
)

type VaultClient struct {
    client *api.Client
    config *VaultConfig
}

type VaultConfig struct {
    Address    string
    Role       string
    MountPath  string
    Region     string
}

type DatabaseCredentials struct {
    Username string `json:"username"`
    Password string `json:"password"`
    TTL      int    `json:"lease_duration"`
}

func NewVaultClient() (*VaultClient, error) {
    config := &VaultConfig{
        Address:   getEnv("VAULT_ADDR", "https://vault.internal.company.com:8200"),
        Role:      getEnv("VAULT_ROLE", "ecommerce-app"),
        MountPath: getEnv("VAULT_AUTH_MOUNT", "aws"),
        Region:    getEnv("AWS_REGION", "us-west-2"),
    }
    
    // Create Vault client
    vaultConfig := api.DefaultConfig()
    vaultConfig.Address = config.Address
    
    client, err := api.NewClient(vaultConfig)
    if err != nil {
        return nil, fmt.Errorf("failed to create Vault client: %w", err)
    }
    
    return &VaultClient{
        client: client,
        config: config,
    }, nil
}

func (vc *VaultClient) Authenticate(ctx context.Context) error {
    // Configure AWS auth method
    awsAuth, err := aws.NewAWSAuth(
        aws.WithRole(vc.config.Role),
        aws.WithMountPath(vc.config.MountPath),
        aws.WithRegion(vc.config.Region),
    )
    if err != nil {
        return fmt.Errorf("failed to initialize AWS auth: %w", err)
    }
    
    // Authenticate with Vault
    authInfo, err := vc.client.Auth().Login(ctx, awsAuth)
    if err != nil {
        return fmt.Errorf("failed to authenticate with Vault: %w", err)
    }
    
    log.Printf("Successfully authenticated with Vault, token TTL: %d seconds", authInfo.Auth.LeaseDuration)
    return nil
}

func (vc *VaultClient) GetDatabaseCredentials(ctx context.Context, role string) (*DatabaseCredentials, error) {
    path := fmt.Sprintf("database/creds/%s", role)
    
    secret, err := vc.client.Logical().ReadWithContext(ctx, path)
    if err != nil {
        return nil, fmt.Errorf("failed to read database credentials: %w", err)
    }
    
    if secret == nil || secret.Data == nil {
        return nil, fmt.Errorf("no data returned from Vault")
    }
    
    username, ok := secret.Data["username"].(string)
    if !ok {
        return nil, fmt.Errorf("username not found in secret")
    }
    
    password, ok := secret.Data["password"].(string)
    if !ok {
        return nil, fmt.Errorf("password not found in secret")
    }
    
    return &DatabaseCredentials{
        Username: username,
        Password: password,
        TTL:      secret.LeaseDuration,
    }, nil
}

func (vc *VaultClient) GetStaticSecret(ctx context.Context, path string) (map[string]interface{}, error) {
    secret, err := vc.client.Logical().ReadWithContext(ctx, path)
    if err != nil {
        return nil, fmt.Errorf("failed to read static secret: %w", err)
    }
    
    if secret == nil || secret.Data == nil {
        return nil, fmt.Errorf("no data returned from Vault")
    }
    
    // Handle KV v2 format
    if data, ok := secret.Data["data"].(map[string]interface{}); ok {
        return data, nil
    }
    
    // Handle KV v1 format
    return secret.Data, nil
}

func (vc *VaultClient) RenewToken(ctx context.Context) error {
    secret, err := vc.client.Auth().Token().RenewSelfWithContext(ctx, 0)
    if err != nil {
        return fmt.Errorf("failed to renew token: %w", err)
    }
    
    log.Printf("Token renewed, new TTL: %d seconds", secret.Auth.LeaseDuration)
    return nil
}

func (vc *VaultClient) StartTokenRenewal(ctx context.Context) {
    ticker := time.NewTicker(30 * time.Minute)
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            if err := vc.RenewToken(ctx); err != nil {
                log.Printf("Failed to renew token: %v", err)
                // Attempt re-authentication
                if err := vc.Authenticate(ctx); err != nil {
                    log.Printf("Failed to re-authenticate: %v", err)
                }
            }
        }
    }
}

func getEnv(key, defaultValue string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultValue
}

// Example usage in application
func main() {
    ctx := context.Background()
    
    // Initialize Vault client
    vaultClient, err := NewVaultClient()
    if err != nil {
        log.Fatalf("Failed to create Vault client: %v", err)
    }
    
    // Authenticate with Vault
    if err := vaultClient.Authenticate(ctx); err != nil {
        log.Fatalf("Failed to authenticate with Vault: %v", err)
    }
    
    // Start token renewal in background
    go vaultClient.StartTokenRenewal(ctx)
    
    // Get database credentials
    dbCreds, err := vaultClient.GetDatabaseCredentials(ctx, "ecommerce-readonly")
    if err != nil {
        log.Fatalf("Failed to get database credentials: %v", err)
    }
    
    log.Printf("Database credentials obtained: username=%s, TTL=%d", dbCreds.Username, dbCreds.TTL)
    
    // Get static secrets
    appConfig, err := vaultClient.GetStaticSecret(ctx, "ecommerce/data/user-service/config")
    if err != nil {
        log.Fatalf("Failed to get application config: %v", err)
    }
    
    log.Printf("Application config loaded: %+v", appConfig)
    
    // Your application logic here...
}
```

## 🔒 Security Best Practices and Compliance

### Security Hardening

**Vault Server Security:**
```yaml
# vault-security-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: vault-network-policy
  namespace: vault-system
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: vault
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: vault-secrets-operator-system
    - namespaceSelector:
        matchLabels:
          name: ecommerce
    ports:
    - protocol: TCP
      port: 8200
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS outbound
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53   # DNS
---
apiVersion: v1
kind: Pod
metadata:
  name: vault-security-scanner
  namespace: vault-system
spec:
  containers:
  - name: scanner
    image: aquasec/trivy:latest
    command: ["trivy", "image", "hashicorp/vault:1.15.2"]
  restartPolicy: Never
```

**RBAC and Access Control:**
```bash
# Vault policies for different roles
kubectl exec -n vault-system vault-0 -- vault policy write developer-policy - <<EOF
# Developers can read their team's secrets
path "ecommerce/data/+/config" {
  capabilities = ["read"]
}

path "ecommerce/data/shared/*" {
  capabilities = ["read"]
}

# Cannot access production database credentials
path "database/creds/ecommerce-readwrite" {
  capabilities = ["deny"]
}
EOF

kubectl exec -n vault-system vault-0 -- vault policy write production-policy - <<EOF
# Production applications can access all necessary secrets
path "ecommerce/data/*/config" {
  capabilities = ["read"]
}

path "database/creds/*" {
  capabilities = ["read"]
}

path "auth/token/renew-self" {
  capabilities = ["update"]
}
EOF

kubectl exec -n vault-system vault-0 -- vault policy write admin-policy - <<EOF
# Administrators have full access
path "*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}
EOF
```

### Compliance and Auditing

**Audit Logging Configuration:**
```bash
# Enable audit logging
kubectl exec -n vault-system vault-0 -- vault audit enable file file_path=/vault/logs/audit.log

# Configure structured logging
kubectl exec -n vault-system vault-0 -- vault write sys/config/auditing \
  default_lease_ttl=768h \
  max_lease_ttl=8760h
```

**Compliance Monitoring:**
```yaml
# compliance-monitoring.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: compliance-checks
  namespace: vault-system
data:
  check-script.sh: |
    #!/bin/bash
    
    # Check 1: Verify encryption at rest
    echo "Checking encryption at rest..."
    kubectl exec -n vault-system vault-0 -- vault read sys/config/encryption
    
    # Check 2: Verify audit logging is enabled
    echo "Checking audit logging..."
    kubectl exec -n vault-system vault-0 -- vault audit list
    
    # Check 3: Check token TTL policies
    echo "Checking token policies..."
    kubectl exec -n vault-system vault-0 -- vault read sys/config/auth
    
    # Check 4: Verify TLS configuration
    echo "Checking TLS configuration..."
    kubectl exec -n vault-system vault-0 -- vault read sys/config/listener
    
    # Check 5: Review active policies
    echo "Reviewing policies..."
    kubectl exec -n vault-system vault-0 -- vault policy list
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: compliance-check
  namespace: vault-system
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: compliance-checker
            image: alpine:latest
            command: ["/bin/sh", "/scripts/check-script.sh"]
            volumeMounts:
            - name: check-script
              mountPath: /scripts
          volumes:
          - name: check-script
            configMap:
              name: compliance-checks
              defaultMode: 0755
          restartPolicy: OnFailure
```

## 📊 Monitoring and Observability

### Vault Metrics and Monitoring

**Prometheus Integration:**
```yaml
# vault-monitoring.yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: vault-metrics
  namespace: vault-system
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: vault
  endpoints:
  - port: http-metrics
    path: /v1/sys/metrics
    params:
      format: ['prometheus']
    bearerTokenSecret:
      name: vault-metrics-token
      key: token
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: vault-alerts
  namespace: vault-system
spec:
  groups:
  - name: vault.rules
    rules:
    - alert: VaultDown
      expr: up{job="vault"} == 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Vault server is down"
        description: "Vault server {{ $labels.instance }} has been down for more than 5 minutes"
    
    - alert: VaultSealed
      expr: vault_core_unsealed == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Vault is sealed"
        description: "Vault instance {{ $labels.instance }} is sealed"
    
    - alert: VaultHighRequestLatency
      expr: vault_core_handle_request{quantile="0.99"} > 1000
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "High Vault request latency"
        description: "99th percentile latency is {{ $value }}ms"
```

### Application Metrics

**Secret Access Monitoring:**
```go
// metrics/vault_metrics.go
package metrics

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    VaultRequestsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "vault_requests_total",
            Help: "Total number of requests to Vault",
        },
        []string{"method", "path", "status"},
    )
    
    VaultRequestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "vault_request_duration_seconds",
            Help: "Duration of Vault requests",
            Buckets: prometheus.DefBuckets,
        },
        []string{"method", "path"},
    )
    
    SecretRotationTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "secret_rotation_total",
            Help: "Total number of secret rotations",
        },
        []string{"secret_type", "status"},
    )
)

func RecordVaultRequest(method, path, status string, duration float64) {
    VaultRequestsTotal.WithLabelValues(method, path, status).Inc()
    VaultRequestDuration.WithLabelValues(method, path).Observe(duration)
}

func RecordSecretRotation(secretType, status string) {
    SecretRotationTotal.WithLabelValues(secretType, status).Inc()
}
```

## 💰 Cost Optimization and ROI Analysis

### Cost Comparison Analysis

**Traditional Secrets Management Costs:**
```
Manual Secret Management:
├── DevOps engineer time: 20 hours/month × $100/hour = $2,000/month
├── Security incidents: 2/year × $50,000 = $100,000/year
├── Compliance audit failures: 1/year × $25,000 = $25,000/year
├── Downtime due to secret issues: 4 hours/year × $10,000/hour = $40,000/year
└── Total annual cost: $189,000

External Secret Management Service:
├── Service subscription: $5,000/month = $60,000/year
├── Integration and maintenance: 10 hours/month × $100/hour = $12,000/year
├── Training and certification: $10,000/year
└── Total annual cost: $82,000
```

**Vault Implementation Costs:**
```
HashiCorp Vault Enterprise:
├── Vault Enterprise license: $36,000/year
├── Infrastructure costs (EKS): $18,000/year
├── Implementation and setup: $25,000 (one-time)
├── Ongoing maintenance: 5 hours/month × $100/hour = $6,000/year
├── Training: $5,000/year
└── Total first-year cost: $90,000
└── Total ongoing annual cost: $65,000

ROI Calculation:
├── Traditional approach: $189,000/year
├── Vault approach: $65,000/year
├── Annual savings: $124,000
├── ROI: 190% in first year, 290% ongoing
```

### Performance Optimization

**Vault Performance Tuning:**
```bash
# Optimize Vault configuration for high throughput
kubectl exec -n vault-system vault-0 -- vault write sys/config/performance \
  max_request_size=33554432 \
  max_request_duration=90s

# Configure connection pooling
kubectl exec -n vault-system vault-0 -- vault write sys/config/connection \
  max_idle_connections=100 \
  max_connections_per_host=10

# Enable response caching
kubectl exec -n vault-system vault-0 -- vault write sys/config/cache \
  size=1000000 \
  ttl=300s
```

**Application-Level Optimizations:**
```go
// optimized-vault-client.go
type OptimizedVaultClient struct {
    client *api.Client
    cache  map[string]CachedSecret
    mutex  sync.RWMutex
}

type CachedSecret struct {
    Data      map[string]interface{}
    ExpiresAt time.Time
}

func (vc *OptimizedVaultClient) GetSecretWithCache(ctx context.Context, path string) (map[string]interface{}, error) {
    vc.mutex.RLock()
    if cached, exists := vc.cache[path]; exists && time.Now().Before(cached.ExpiresAt) {
        vc.mutex.RUnlock()
        return cached.Data, nil
    }
    vc.mutex.RUnlock()
    
    // Fetch from Vault
    secret, err := vc.GetStaticSecret(ctx, path)
    if err != nil {
        return nil, err
    }
    
    // Cache the result
    vc.mutex.Lock()
    vc.cache[path] = CachedSecret{
        Data:      secret,
        ExpiresAt: time.Now().Add(5 * time.Minute),
    }
    vc.mutex.Unlock()
    
    return secret, nil
}
```

This comprehensive guide demonstrates how to implement enterprise-grade secrets management with HashiCorp Vault and EKS, covering multiple integration patterns, security best practices, and real-world implementation scenarios. The approach prioritizes security, compliance, and operational efficiency while providing practical code examples and deployment strategies.