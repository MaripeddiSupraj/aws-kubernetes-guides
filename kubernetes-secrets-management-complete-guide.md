# Kubernetes Secrets Management: Complete Production Guide

## 🎯 Overview: The Secrets Management Challenge

### The Problem with Native K8s Secrets

**Why Default Secrets Are Insufficient:**
```yaml
# Traditional K8s Secret - Base64 encoded, NOT encrypted
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
type: Opaque
data:
  username: YWRtaW4=  # admin (easily decoded)
  password: cGFzc3dvcmQxMjM=  # password123 (easily decoded)
```

**Security Issues:**
- Base64 encoding ≠ encryption
- Stored in etcd in plaintext
- Visible to anyone with cluster access
- No rotation capabilities
- No audit trail
- Difficult to manage at scale

### Production Requirements

**Enterprise Secrets Management Needs:**
- **Encryption at rest and in transit**
- **Centralized secret storage**
- **Automatic rotation**
- **Audit logging**
- **GitOps compatibility**
- **Multi-environment support**
- **Compliance (SOC2, PCI DSS)**

## 🔐 Solution 1: External Secrets Operator

### What is External Secrets Operator?

**ESO** syncs secrets from external systems (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault, GCP Secret Manager) into Kubernetes secrets automatically.

### Real-World Example: E-commerce Platform

**Scenario**: Multi-environment e-commerce platform with database credentials, API keys, and certificates stored in AWS Secrets Manager.

#### Step 1: Install External Secrets Operator

```bash
# Install via Helm
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

# Create namespace
kubectl create namespace external-secrets-system

# Install ESO
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets-system \
  --set installCRDs=true
```

#### Step 2: AWS Secrets Manager Setup

```bash
# Create secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name "ecommerce/prod/database" \
  --description "Production database credentials" \
  --secret-string '{
    "username": "ecommerce_user",
    "password": "SuperSecurePassword123!",
    "host": "prod-db.cluster-xyz.us-east-1.rds.amazonaws.com",
    "port": "5432",
    "database": "ecommerce_prod"
  }'

aws secretsmanager create-secret \
  --name "ecommerce/prod/redis" \
  --description "Production Redis credentials" \
  --secret-string '{
    "password": "RedisSecurePass456!",
    "host": "prod-redis.abc123.cache.amazonaws.com",
    "port": "6379"
  }'

aws secretsmanager create-secret \
  --name "ecommerce/prod/stripe" \
  --description "Stripe API keys" \
  --secret-string '{
    "publishable_key": "pk_live_51234567890abcdef",
    "secret_key": "sk_live_51234567890abcdef",
    "webhook_secret": "whsec_1234567890abcdef"
  }'
```

#### Step 3: IAM Role and Service Account

```yaml
# iam-role-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:123456789012:secret:ecommerce/prod/*"
      ]
    }
  ]
}
```

```bash
# Create IAM role
aws iam create-role \
  --role-name EKS-ExternalSecrets-Role \
  --assume-role-policy-document file://trust-policy.json

aws iam put-role-policy \
  --role-name EKS-ExternalSecrets-Role \
  --policy-name SecretsManagerAccess \
  --policy-document file://iam-role-policy.json

# Create service account with IRSA
eksctl create iamserviceaccount \
  --cluster=ecommerce-prod \
  --namespace=ecommerce \
  --name=external-secrets-sa \
  --role-name=EKS-ExternalSecrets-Role \
  --attach-policy-arn=arn:aws:iam::123456789012:policy/SecretsManagerAccess \
  --approve
```

#### Step 4: Configure SecretStore

```yaml
# secretstore.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: ecommerce
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        serviceAccount:
          name: external-secrets-sa
---
# Cluster-wide SecretStore for shared secrets
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: aws-secrets-manager-global
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        serviceAccount:
          name: external-secrets-sa
          namespace: external-secrets-system
```

#### Step 5: Create ExternalSecrets

```yaml
# database-external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: ecommerce
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: database-secret
    creationPolicy: Owner
    template:
      type: Opaque
      data:
        # Create connection string from individual fields
        DATABASE_URL: "postgresql://{{ .username }}:{{ .password }}@{{ .host }}:{{ .port }}/{{ .database }}"
        DB_USERNAME: "{{ .username }}"
        DB_PASSWORD: "{{ .password }}"
        DB_HOST: "{{ .host }}"
        DB_PORT: "{{ .port }}"
        DB_NAME: "{{ .database }}"
  data:
  - secretKey: username
    remoteRef:
      key: ecommerce/prod/database
      property: username
  - secretKey: password
    remoteRef:
      key: ecommerce/prod/database
      property: password
  - secretKey: host
    remoteRef:
      key: ecommerce/prod/database
      property: host
  - secretKey: port
    remoteRef:
      key: ecommerce/prod/database
      property: port
  - secretKey: database
    remoteRef:
      key: ecommerce/prod/database
      property: database
---
# redis-external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: redis-credentials
  namespace: ecommerce
spec:
  refreshInterval: 30m
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: redis-secret
    creationPolicy: Owner
  data:
  - secretKey: password
    remoteRef:
      key: ecommerce/prod/redis
      property: password
  - secretKey: host
    remoteRef:
      key: ecommerce/prod/redis
      property: host
  - secretKey: port
    remoteRef:
      key: ecommerce/prod/redis
      property: port
---
# stripe-external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: stripe-credentials
  namespace: ecommerce
spec:
  refreshInterval: 24h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: stripe-secret
    creationPolicy: Owner
  data:
  - secretKey: publishable_key
    remoteRef:
      key: ecommerce/prod/stripe
      property: publishable_key
  - secretKey: secret_key
    remoteRef:
      key: ecommerce/prod/stripe
      property: secret_key
  - secretKey: webhook_secret
    remoteRef:
      key: ecommerce/prod/stripe
      property: webhook_secret
```

#### Step 6: Application Deployment

```yaml
# ecommerce-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecommerce-api
  namespace: ecommerce
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ecommerce-api
  template:
    metadata:
      labels:
        app: ecommerce-api
    spec:
      serviceAccountName: ecommerce-api-sa
      containers:
      - name: api
        image: ecommerce/api:v1.2.3
        ports:
        - containerPort: 8080
        env:
        # Database connection
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: DATABASE_URL
        # Redis connection
        - name: REDIS_HOST
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: host
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: password
        # Stripe configuration
        - name: STRIPE_PUBLISHABLE_KEY
          valueFrom:
            secretKeyRef:
              name: stripe-secret
              key: publishable_key
        - name: STRIPE_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: stripe-secret
              key: secret_key
        - name: STRIPE_WEBHOOK_SECRET
          valueFrom:
            secretKeyRef:
              name: stripe-secret
              key: webhook_secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
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
```

#### Step 7: Monitoring and Troubleshooting

```bash
# Check ExternalSecret status
kubectl get externalsecrets -n ecommerce
kubectl describe externalsecret database-credentials -n ecommerce

# Check generated secrets
kubectl get secrets -n ecommerce
kubectl describe secret database-secret -n ecommerce

# Check ESO logs
kubectl logs -n external-secrets-system -l app.kubernetes.io/name=external-secrets

# Test secret refresh
kubectl annotate externalsecret database-credentials -n ecommerce \
  force-sync=$(date +%s) --overwrite
```

## 🔒 Solution 2: SOPS + KMS (GitOps-Friendly)

### What is SOPS?

**SOPS** (Secrets OPerationS) encrypts files using AWS KMS, allowing you to store encrypted secrets in Git repositories safely.

### Real-World Example: GitOps CI/CD Pipeline

**Scenario**: DevOps team managing secrets across multiple environments using GitOps with ArgoCD.

#### Step 1: Install SOPS

```bash
# Install SOPS
curl -LO https://github.com/mozilla/sops/releases/download/v3.8.1/sops-v3.8.1.linux.amd64
sudo mv sops-v3.8.1.linux.amd64 /usr/local/bin/sops
sudo chmod +x /usr/local/bin/sops

# Install age (alternative to KMS)
curl -LO https://github.com/FiloSottile/age/releases/download/v1.1.1/age-v1.1.1-linux-amd64.tar.gz
tar xzf age-v1.1.1-linux-amd64.tar.gz
sudo mv age/age /usr/local/bin/
sudo mv age/age-keygen /usr/local/bin/
```

#### Step 2: KMS Key Setup

```bash
# Create KMS key for SOPS
aws kms create-key \
  --description "SOPS encryption key for Kubernetes secrets" \
  --key-usage ENCRYPT_DECRYPT \
  --key-spec SYMMETRIC_DEFAULT

# Create alias
aws kms create-alias \
  --alias-name alias/sops-k8s-secrets \
  --target-key-id arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012

# Grant access to specific IAM roles
aws kms put-key-policy \
  --key-id alias/sops-k8s-secrets \
  --policy-name default \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "Enable IAM User Permissions",
        "Effect": "Allow",
        "Principal": {"AWS": "arn:aws:iam::123456789012:root"},
        "Action": "kms:*",
        "Resource": "*"
      },
      {
        "Sid": "Allow SOPS decryption",
        "Effect": "Allow",
        "Principal": {
          "AWS": [
            "arn:aws:iam::123456789012:role/EKS-ArgoCD-Role",
            "arn:aws:iam::123456789012:role/DevOps-CI-Role"
          ]
        },
        "Action": [
          "kms:Decrypt",
          "kms:DescribeKey"
        ],
        "Resource": "*"
      }
    ]
  }'
```

#### Step 3: SOPS Configuration

```yaml
# .sops.yaml (in repository root)
creation_rules:
  # Production secrets
  - path_regex: environments/production/.*\.yaml$
    kms: 'arn:aws:kms:us-east-1:123456789012:alias/sops-k8s-secrets'
    aws_profile: production
  
  # Staging secrets  
  - path_regex: environments/staging/.*\.yaml$
    kms: 'arn:aws:kms:us-east-1:123456789012:alias/sops-k8s-secrets'
    aws_profile: staging
    
  # Development secrets (using age for local dev)
  - path_regex: environments/development/.*\.yaml$
    age: 'age1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
```

#### Step 4: Create Encrypted Secrets

```bash
# Create directory structure
mkdir -p environments/{production,staging,development}/secrets

# Create production database secret
cat > environments/production/secrets/database.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
  namespace: ecommerce
type: Opaque
stringData:
  username: prod_ecommerce_user
  password: SuperSecureProdPassword123!
  host: prod-db.cluster-xyz.us-east-1.rds.amazonaws.com
  port: "5432"
  database: ecommerce_prod
  ssl_mode: require
EOF

# Encrypt the secret
sops --encrypt --in-place environments/production/secrets/database.yaml

# Create staging secret
cat > environments/staging/secrets/database.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
  namespace: ecommerce
type: Opaque
stringData:
  username: staging_ecommerce_user
  password: StagingPassword456!
  host: staging-db.cluster-abc.us-east-1.rds.amazonaws.com
  port: "5432"
  database: ecommerce_staging
  ssl_mode: require
EOF

sops --encrypt --in-place environments/staging/secrets/database.yaml

# Create API keys secret
cat > environments/production/secrets/api-keys.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
  namespace: ecommerce
type: Opaque
stringData:
  stripe_secret_key: sk_live_51234567890abcdef
  stripe_publishable_key: pk_live_51234567890abcdef
  sendgrid_api_key: SG.1234567890abcdef
  jwt_secret: super-secret-jwt-key-for-production
  oauth_client_secret: oauth-client-secret-12345
EOF

sops --encrypt --in-place environments/production/secrets/api-keys.yaml
```

#### Step 5: GitOps Repository Structure

```
k8s-manifests/
├── .sops.yaml
├── applications/
│   ├── ecommerce-api/
│   │   ├── base/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── kustomization.yaml
│   │   └── overlays/
│   │       ├── production/
│   │       │   ├── kustomization.yaml
│   │       │   └── patches/
│   │       └── staging/
│   │           ├── kustomization.yaml
│   │           └── patches/
├── environments/
│   ├── production/
│   │   ├── secrets/
│   │   │   ├── database.yaml (encrypted)
│   │   │   ├── api-keys.yaml (encrypted)
│   │   │   └── certificates.yaml (encrypted)
│   │   └── kustomization.yaml
│   ├── staging/
│   │   ├── secrets/
│   │   │   ├── database.yaml (encrypted)
│   │   │   └── api-keys.yaml (encrypted)
│   │   └── kustomization.yaml
│   └── development/
│       ├── secrets/
│       │   └── database.yaml (encrypted with age)
│       └── kustomization.yaml
└── argocd/
    ├── applications/
    │   ├── ecommerce-prod.yaml
    │   ├── ecommerce-staging.yaml
    │   └── ecommerce-dev.yaml
    └── projects/
        └── ecommerce.yaml
```

#### Step 6: ArgoCD Integration with SOPS

```yaml
# argocd-sops-plugin.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cmp-plugin
  namespace: argocd
data:
  plugin.yaml: |
    apiVersion: argoproj.io/v1alpha1
    kind: ConfigManagementPlugin
    metadata:
      name: sops
    spec:
      version: v1.0
      init:
        command: [sh, -c]
        args: ["sops -d *.yaml > /tmp/sops-decrypted.yaml"]
      generate:
        command: [sh, -c]
        args: ["kustomize build . && cat /tmp/sops-decrypted.yaml"]
      discover:
        find:
          command: [sh, -c]
          args: ["find . -name '*.yaml' -exec grep -l 'sops:' {} \\;"]
---
# ArgoCD Application with SOPS
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ecommerce-production
  namespace: argocd
spec:
  project: ecommerce
  source:
    repoURL: https://github.com/company/k8s-manifests
    targetRevision: main
    path: environments/production
    plugin:
      name: sops
  destination:
    server: https://kubernetes.default.svc
    namespace: ecommerce
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

#### Step 7: CI/CD Pipeline Integration

```yaml
# .github/workflows/deploy.yml
name: Deploy to Kubernetes
on:
  push:
    branches: [main]
    paths: ['environments/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: arn:aws:iam::123456789012:role/DevOps-CI-Role
        aws-region: us-east-1
    
    - name: Install SOPS
      run: |
        curl -LO https://github.com/mozilla/sops/releases/download/v3.8.1/sops-v3.8.1.linux.amd64
        sudo mv sops-v3.8.1.linux.amd64 /usr/local/bin/sops
        sudo chmod +x /usr/local/bin/sops
    
    - name: Decrypt and validate secrets
      run: |
        # Test decryption
        sops -d environments/production/secrets/database.yaml > /tmp/test.yaml
        kubectl --dry-run=client apply -f /tmp/test.yaml
        
    - name: Trigger ArgoCD sync
      run: |
        argocd app sync ecommerce-production --auth-token ${{ secrets.ARGOCD_TOKEN }}
```

## 🏦 Solution 3: Vault Agent Injector

### What is Vault Agent Injector?

**Vault Agent Injector** automatically injects secrets from HashiCorp Vault into pods at runtime using init containers and sidecars.

### Real-World Example: Banking Application

**Scenario**: Highly regulated banking application requiring dynamic secrets, audit trails, and automatic rotation.

#### Step 1: Vault Setup

```bash
# Install Vault via Helm
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# Install Vault in HA mode
helm install vault hashicorp/vault \
  --namespace vault \
  --create-namespace \
  --set server.ha.enabled=true \
  --set server.ha.replicas=3 \
  --set injector.enabled=true \
  --set server.dataStorage.storageClass=gp3 \
  --set server.auditStorage.enabled=true

# Initialize Vault
kubectl exec vault-0 -n vault -- vault operator init -key-shares=5 -key-threshold=3

# Unseal Vault (repeat for all replicas)
kubectl exec vault-0 -n vault -- vault operator unseal <unseal-key-1>
kubectl exec vault-0 -n vault -- vault operator unseal <unseal-key-2>
kubectl exec vault-0 -n vault -- vault operator unseal <unseal-key-3>
```

#### Step 2: Vault Configuration

```bash
# Login to Vault
kubectl exec -it vault-0 -n vault -- vault auth -method=userpass username=admin

# Enable Kubernetes auth
kubectl exec vault-0 -n vault -- vault auth enable kubernetes

# Configure Kubernetes auth
kubectl exec vault-0 -n vault -- vault write auth/kubernetes/config \
  token_reviewer_jwt="$(kubectl get secret vault-auth -o jsonpath='{.data.token}' | base64 -d)" \
  kubernetes_host="https://kubernetes.default.svc:443" \
  kubernetes_ca_cert="$(kubectl get secret vault-auth -o jsonpath='{.data.ca\.crt}' | base64 -d)"

# Enable KV secrets engine
kubectl exec vault-0 -n vault -- vault secrets enable -path=banking kv-v2

# Enable database secrets engine for dynamic credentials
kubectl exec vault-0 -n vault -- vault secrets enable database

# Configure database connection
kubectl exec vault-0 -n vault -- vault write database/config/postgres \
  plugin_name=postgresql-database-plugin \
  connection_url="postgresql://{{username}}:{{password}}@postgres.banking.svc.cluster.local:5432/banking?sslmode=require" \
  allowed_roles="banking-app" \
  username="vault_admin" \
  password="VaultAdminPassword123!"

# Create database role for dynamic credentials
kubectl exec vault-0 -n vault -- vault write database/roles/banking-app \
  db_name=postgres \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl="1h" \
  max_ttl="24h"
```

#### Step 3: Vault Policies and Roles

```bash
# Create policy for banking application
kubectl exec vault-0 -n vault -- vault policy write banking-app - <<EOF
# Read static secrets
path "banking/data/api-keys" {
  capabilities = ["read"]
}

path "banking/data/certificates" {
  capabilities = ["read"]
}

# Generate dynamic database credentials
path "database/creds/banking-app" {
  capabilities = ["read"]
}

# Renew own token
path "auth/token/renew-self" {
  capabilities = ["update"]
}
EOF

# Create Kubernetes role
kubectl exec vault-0 -n vault -- vault write auth/kubernetes/role/banking-app \
  bound_service_account_names=banking-app \
  bound_service_account_namespaces=banking \
  policies=banking-app \
  ttl=24h
```

#### Step 4: Store Secrets in Vault

```bash
# Store static API keys
kubectl exec vault-0 -n vault -- vault kv put banking/api-keys \
  swift_api_key="SWIFT_API_KEY_12345" \
  fed_wire_key="FED_WIRE_KEY_67890" \
  encryption_key="AES256_ENCRYPTION_KEY_ABCDEF" \
  audit_webhook_secret="AUDIT_WEBHOOK_SECRET_123"

# Store certificates
kubectl exec vault-0 -n vault -- vault kv put banking/certificates \
  tls_cert="$(cat banking-tls.crt | base64 -w 0)" \
  tls_key="$(cat banking-tls.key | base64 -w 0)" \
  ca_cert="$(cat ca.crt | base64 -w 0)"

# Store compliance secrets
kubectl exec vault-0 -n vault -- vault kv put banking/compliance \
  pci_dss_key="PCI_DSS_COMPLIANCE_KEY" \
  sox_audit_token="SOX_AUDIT_TOKEN_789" \
  gdpr_encryption_key="GDPR_ENCRYPTION_KEY_ABC"
```

#### Step 5: Banking Application with Vault Injection

```yaml
# banking-app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: banking-api
  namespace: banking
spec:
  replicas: 3
  selector:
    matchLabels:
      app: banking-api
  template:
    metadata:
      labels:
        app: banking-api
      annotations:
        # Enable Vault injection
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "banking-app"
        vault.hashicorp.com/agent-pre-populate-only: "true"
        
        # Inject static API keys
        vault.hashicorp.com/agent-inject-secret-api-keys: "banking/data/api-keys"
        vault.hashicorp.com/agent-inject-template-api-keys: |
          {{- with secret "banking/data/api-keys" -}}
          export SWIFT_API_KEY="{{ .Data.data.swift_api_key }}"
          export FED_WIRE_KEY="{{ .Data.data.fed_wire_key }}"
          export ENCRYPTION_KEY="{{ .Data.data.encryption_key }}"
          export AUDIT_WEBHOOK_SECRET="{{ .Data.data.audit_webhook_secret }}"
          {{- end }}
        
        # Inject dynamic database credentials
        vault.hashicorp.com/agent-inject-secret-db-creds: "database/creds/banking-app"
        vault.hashicorp.com/agent-inject-template-db-creds: |
          {{- with secret "database/creds/banking-app" -}}
          export DB_USERNAME="{{ .Data.username }}"
          export DB_PASSWORD="{{ .Data.password }}"
          export DATABASE_URL="postgresql://{{ .Data.username }}:{{ .Data.password }}@postgres.banking.svc.cluster.local:5432/banking?sslmode=require"
          {{- end }}
        
        # Inject certificates
        vault.hashicorp.com/agent-inject-secret-certs: "banking/data/certificates"
        vault.hashicorp.com/agent-inject-template-certs: |
          {{- with secret "banking/data/certificates" -}}
          {{ .Data.data.tls_cert | base64Decode }}
          {{- end }}
        
        # Inject compliance secrets
        vault.hashicorp.com/agent-inject-secret-compliance: "banking/data/compliance"
        vault.hashicorp.com/agent-inject-template-compliance: |
          {{- with secret "banking/data/compliance" -}}
          export PCI_DSS_KEY="{{ .Data.data.pci_dss_key }}"
          export SOX_AUDIT_TOKEN="{{ .Data.data.sox_audit_token }}"
          export GDPR_ENCRYPTION_KEY="{{ .Data.data.gdpr_encryption_key }}"
          {{- end }}
    spec:
      serviceAccountName: banking-app
      containers:
      - name: banking-api
        image: banking/api:v2.1.0
        ports:
        - containerPort: 8443
        command: ["/bin/sh"]
        args:
        - -c
        - |
          # Source all injected secrets
          source /vault/secrets/api-keys
          source /vault/secrets/db-creds
          source /vault/secrets/compliance
          
          # Start application
          exec /app/banking-api
        volumeMounts:
        - name: tls-certs
          mountPath: /etc/ssl/certs
          readOnly: true
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8443
            scheme: HTTPS
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8443
            scheme: HTTPS
          initialDelaySeconds: 30
          periodSeconds: 10
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
      volumes:
      - name: tls-certs
        secret:
          secretName: banking-tls-certs
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: banking-app
  namespace: banking
```

#### Step 6: Advanced Vault Features

```yaml
# vault-secret-rotation.yaml - Automatic secret rotation
apiVersion: batch/v1
kind: CronJob
metadata:
  name: rotate-database-credentials
  namespace: banking
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        metadata:
          annotations:
            vault.hashicorp.com/agent-inject: "true"
            vault.hashicorp.com/role: "banking-app"
            vault.hashicorp.com/agent-inject-secret-rotate: "database/creds/banking-app"
        spec:
          serviceAccountName: banking-app
          containers:
          - name: credential-rotator
            image: vault:1.15.2
            command:
            - /bin/sh
            - -c
            - |
              # Force credential rotation by requesting new creds
              vault write -force database/rotate-root/postgres
              
              # Restart application pods to pick up new credentials
              kubectl rollout restart deployment/banking-api -n banking
          restartPolicy: OnFailure
---
# vault-audit-policy.yaml - Comprehensive audit logging
apiVersion: v1
kind: ConfigMap
metadata:
  name: vault-audit-config
  namespace: vault
data:
  audit.hcl: |
    # Enable file audit device
    audit "file" {
      file_path = "/vault/audit/audit.log"
      log_raw = false
      hmac_accessor = true
      mode = "0600"
      format = "json"
    }
    
    # Enable syslog audit device for real-time monitoring
    audit "syslog" {
      facility = "AUTH"
      tag = "vault"
      log_raw = false
      hmac_accessor = true
      format = "json"
    }
```

## 🔐 Solution 4: Sealed Secrets

### What are Sealed Secrets?

**Sealed Secrets** encrypt regular Kubernetes secrets using asymmetric cryptography, making them safe to store in Git repositories.

### Real-World Example: Multi-Tenant SaaS Platform

**Scenario**: SaaS platform with multiple customer environments requiring tenant-specific secrets stored in Git.

#### Step 1: Install Sealed Secrets Controller

```bash
# Install Sealed Secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Install kubeseal CLI
wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/kubeseal-0.24.0-linux-amd64.tar.gz
tar xzf kubeseal-0.24.0-linux-amd64.tar.gz
sudo mv kubeseal /usr/local/bin/

# Verify installation
kubectl get pods -n kube-system | grep sealed-secrets
kubeseal --version
```

#### Step 2: Backup and Manage Encryption Keys

```bash
# Backup the master key (CRITICAL - store securely!)
kubectl get secret -n kube-system sealed-secrets-key -o yaml > sealed-secrets-master-key.yaml

# Create additional keys for key rotation
kubectl create secret tls sealed-secrets-key-2024 \
  --cert=tls.crt \
  --key=tls.key \
  --namespace=kube-system

kubectl label secret sealed-secrets-key-2024 \
  sealedsecrets.bitnami.com/sealed-secrets-key=active \
  --namespace=kube-system
```

#### Step 3: Multi-Tenant Secret Management

```bash
# Create tenant-specific namespaces
kubectl create namespace tenant-acme-corp
kubectl create namespace tenant-globex
kubectl create namespace tenant-initech

# Directory structure for multi-tenant secrets
mkdir -p tenants/{acme-corp,globex,initech}/secrets
```

#### Step 4: Create Tenant-Specific Sealed Secrets

```yaml
# tenants/acme-corp/secrets/database-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
  namespace: tenant-acme-corp
type: Opaque
stringData:
  username: acme_corp_user
  password: AcmeCorpSecurePass123!
  host: acme-corp-db.cluster-xyz.us-east-1.rds.amazonaws.com
  port: "5432"
  database: acme_corp_saas
  connection_pool_size: "20"
  ssl_mode: require
```

```bash
# Seal the secret for ACME Corp
kubeseal --format=yaml \
  --namespace=tenant-acme-corp \
  < tenants/acme-corp/secrets/database-secret.yaml \
  > tenants/acme-corp/secrets/database-sealed-secret.yaml

# Clean up plaintext secret
rm tenants/acme-corp/secrets/database-secret.yaml
```

```yaml
# tenants/acme-corp/secrets/api-keys-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
  namespace: tenant-acme-corp
type: Opaque
stringData:
  stripe_secret_key: sk_live_acme_corp_12345
  sendgrid_api_key: SG.acme_corp_67890
  aws_access_key_id: AKIA_ACME_CORP_ACCESS
  aws_secret_access_key: acme_corp_secret_access_key
  jwt_secret: acme-corp-jwt-secret-key
  webhook_secret: acme-corp-webhook-secret
  encryption_key: acme-corp-aes-256-key
```

```bash
# Seal API keys for ACME Corp
kubeseal --format=yaml \
  --namespace=tenant-acme-corp \
  < tenants/acme-corp/secrets/api-keys-secret.yaml \
  > tenants/acme-corp/secrets/api-keys-sealed-secret.yaml

rm tenants/acme-corp/secrets/api-keys-secret.yaml
```

#### Step 5: Tenant Application Deployment

```yaml
# tenants/acme-corp/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: saas-app
  namespace: tenant-acme-corp
  labels:
    tenant: acme-corp
    app: saas-app
spec:
  replicas: 2
  selector:
    matchLabels:
      tenant: acme-corp
      app: saas-app
  template:
    metadata:
      labels:
        tenant: acme-corp
        app: saas-app
    spec:
      containers:
      - name: saas-app
        image: saas-platform/app:v3.2.1
        ports:
        - containerPort: 8080
        env:
        # Database configuration
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: host
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: password
        - name: DB_NAME
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: database
        - name: DB_POOL_SIZE
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: connection_pool_size
        
        # API Keys
        - name: STRIPE_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: stripe_secret_key
        - name: SENDGRID_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: sendgrid_api_key
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: aws_access_key_id
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: aws_secret_access_key
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: jwt_secret
        - name: WEBHOOK_SECRET
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: webhook_secret
        - name: ENCRYPTION_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: encryption_key
        
        # Tenant-specific configuration
        - name: TENANT_ID
          value: "acme-corp"
        - name: TENANT_SUBDOMAIN
          value: "acme-corp"
        - name: TENANT_PLAN
          value: "enterprise"
        
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        
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
          initialDelaySeconds: 10
          periodSeconds: 5
        
        securityContext:
          runAsNonRoot: true
          runAsUser: 1001
          allowPrivilegeEscalation: false
---
apiVersion: v1
kind: Service
metadata:
  name: saas-app-service
  namespace: tenant-acme-corp
spec:
  selector:
    tenant: acme-corp
    app: saas-app
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

#### Step 6: GitOps Integration with Sealed Secrets

```yaml
# .github/workflows/deploy-tenant.yml
name: Deploy Tenant Environment
on:
  push:
    branches: [main]
    paths: ['tenants/**']

jobs:
  deploy-tenants:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        tenant: [acme-corp, globex, initech]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure kubectl
      uses: azure/k8s-set-context@v1
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG }}
    
    - name: Deploy sealed secrets for ${{ matrix.tenant }}
      run: |
        # Apply sealed secrets (they will be automatically decrypted)
        kubectl apply -f tenants/${{ matrix.tenant }}/secrets/
        
        # Wait for secrets to be created
        kubectl wait --for=condition=Ready \
          sealedsecret/database-credentials \
          -n tenant-${{ matrix.tenant }} \
          --timeout=60s
        
        kubectl wait --for=condition=Ready \
          sealedsecret/api-keys \
          -n tenant-${{ matrix.tenant }} \
          --timeout=60s
    
    - name: Deploy application for ${{ matrix.tenant }}
      run: |
        kubectl apply -f tenants/${{ matrix.tenant }}/deployment.yaml
        
        # Wait for deployment to be ready
        kubectl rollout status deployment/saas-app \
          -n tenant-${{ matrix.tenant }} \
          --timeout=300s
    
    - name: Verify deployment
      run: |
        # Check that secrets exist and are properly mounted
        kubectl get secrets -n tenant-${{ matrix.tenant }}
        
        # Test application health
        kubectl get pods -n tenant-${{ matrix.tenant }}
        
        # Port forward and test (in real scenario, use proper ingress)
        kubectl port-forward -n tenant-${{ matrix.tenant }} \
          service/saas-app-service 8080:80 &
        
        sleep 10
        curl -f http://localhost:8080/health || exit 1
```

#### Step 7: Secret Rotation and Management

```bash
# Script for rotating tenant secrets
#!/bin/bash
# rotate-tenant-secrets.sh

TENANT=$1
NAMESPACE="tenant-${TENANT}"

if [ -z "$TENANT" ]; then
  echo "Usage: $0 <tenant-name>"
  exit 1
fi

echo "Rotating secrets for tenant: $TENANT"

# Generate new database password
NEW_DB_PASSWORD=$(openssl rand -base64 32)

# Create new secret with rotated password
cat > /tmp/new-db-secret.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
  namespace: $NAMESPACE
type: Opaque
stringData:
  username: ${TENANT}_user
  password: $NEW_DB_PASSWORD
  host: ${TENANT}-db.cluster-xyz.us-east-1.rds.amazonaws.com
  port: "5432"
  database: ${TENANT}_saas
  connection_pool_size: "20"
  ssl_mode: require
EOF

# Seal the new secret
kubeseal --format=yaml \
  --namespace=$NAMESPACE \
  < /tmp/new-db-secret.yaml \
  > tenants/$TENANT/secrets/database-sealed-secret.yaml

# Update database with new password (using AWS RDS API)
aws rds modify-db-instance \
  --db-instance-identifier ${TENANT}-db \
  --master-user-password $NEW_DB_PASSWORD \
  --apply-immediately

# Commit and push changes
git add tenants/$TENANT/secrets/database-sealed-secret.yaml
git commit -m "Rotate database password for tenant: $TENANT"
git push origin main

# Clean up
rm /tmp/new-db-secret.yaml

echo "Secret rotation completed for tenant: $TENANT"
echo "New sealed secret committed to Git"
echo "Database password updated in RDS"
```

## 📊 Comparison and Recommendations

### Feature Comparison Matrix

| Feature | External Secrets | SOPS + KMS | Vault Injector | Sealed Secrets |
|---------|------------------|------------|----------------|----------------|
| **GitOps Friendly** | ⚠️ Partial | ✅ Excellent | ❌ No | ✅ Excellent |
| **Dynamic Secrets** | ❌ No | ❌ No | ✅ Excellent | ❌ No |
| **Secret Rotation** | ✅ Good | ⚠️ Manual | ✅ Automatic | ⚠️ Manual |
| **Audit Trail** | ⚠️ Limited | ⚠️ Limited | ✅ Excellent | ⚠️ Limited |
| **Multi-Cloud** | ✅ Excellent | ✅ Good | ✅ Good | ✅ Excellent |
| **Complexity** | 🟡 Medium | 🟢 Low | 🔴 High | 🟢 Low |
| **Operational Overhead** | 🟡 Medium | 🟢 Low | 🔴 High | 🟢 Low |
| **Security** | 🟡 Good | 🟡 Good | 🟢 Excellent | 🟡 Good |

### Recommendations by Use Case

#### **E-commerce/Web Applications**
```
✅ External Secrets Operator
- Integrates with existing cloud secret stores
- Good for AWS/GCP/Azure native secrets
- Automatic sync and refresh
- Moderate complexity
```

#### **Financial/Healthcare (Highly Regulated)**
```
✅ Vault Agent Injector
- Dynamic secrets with automatic rotation
- Comprehensive audit logging
- Fine-grained access policies
- Compliance-ready features
```

#### **Startups/Small Teams**
```
✅ Sealed Secrets
- Simple to implement and understand
- GitOps-native workflow
- Low operational overhead
- Cost-effective
```

#### **Enterprise GitOps**
```
✅ SOPS + KMS
- Perfect Git integration
- Environment-specific encryption
- CI/CD pipeline friendly
- Scalable across teams
```

### Implementation Strategy

**Phase 1: Assessment (Week 1)**
- Audit current secret management practices
- Identify compliance requirements
- Evaluate team GitOps maturity
- Choose primary solution

**Phase 2: Pilot (Weeks 2-4)**
- Implement chosen solution in development
- Migrate 2-3 non-critical applications
- Train team on new workflows
- Document procedures

**Phase 3: Production Migration (Weeks 5-8)**
- Migrate critical applications
- Implement monitoring and alerting
- Set up secret rotation procedures
- Conduct security review

**Phase 4: Optimization (Weeks 9-12)**
- Automate secret lifecycle management
- Implement advanced features
- Optimize performance
- Establish ongoing maintenance procedures

This comprehensive guide provides production-ready implementations for all major Kubernetes secrets management solutions, with real-world examples and specific use cases for each approach.