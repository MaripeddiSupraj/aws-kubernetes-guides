# EKS Secrets Management: Complete Security Guide

A comprehensive guide covering all secure methods for accessing secrets in EKS workloads, from basic Kubernetes secrets to enterprise-grade solutions.

## 🔐 Overview of Secret Management Methods

### 1. **AWS Secrets Manager + IRSA** (Recommended)
### 2. **External Secrets Operator (ESO)** (Most Popular)
### 3. **Secrets Store CSI Driver** (File-based)
### 4. **HashiCorp Vault Integration** (Enterprise)
### 5. **Kubernetes Native Secrets** (Basic)
### 6. **AWS Parameter Store Integration** (Cost-effective)
### 7. **Sealed Secrets** (GitOps)
### 8. **Bank-Vaults Operator** (Vault Automation)
### 9. **Conjur Secrets Manager** (CyberArk)
### 10. **Azure Key Vault + Workload Identity** (Multi-cloud)
### 11. **Google Secret Manager** (GCP Integration)
### 12. **Doppler Secrets Manager** (Developer-focused)

---

## Method 1: AWS Secrets Manager with IRSA

**Best for**: Direct AWS integration, fine-grained IAM control

### Setup IRSA (IAM Roles for Service Accounts)

```bash
# Create OIDC provider
eksctl utils associate-iam-oidc-provider --cluster my-cluster --approve

# Create service account with IAM role
eksctl create iamserviceaccount \
  --name secrets-sa \
  --namespace default \
  --cluster my-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite \
  --approve
```

### Application Code Example

```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
db_creds = get_secret('prod/database/credentials')
```

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-secrets
spec:
  template:
    spec:
      serviceAccountName: secrets-sa  # IRSA enabled
      containers:
      - name: app
        image: my-app:latest
        env:
        - name: SECRET_NAME
          value: "prod/database/credentials"
```

---

## Method 2: External Secrets Operator (ESO)

**Best for**: Multi-cloud, GitOps, centralized secret management

### Install ESO

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
```

### Create SecretStore

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: default
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
```

### Create ExternalSecret

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-secret
  namespace: default
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: db-credentials
    creationPolicy: Owner
  data:
  - secretKey: username
    remoteRef:
      key: prod/database/credentials
      property: username
  - secretKey: password
    remoteRef:
      key: prod/database/credentials
      property: password
```

### Use in Pod

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-eso
spec:
  template:
    spec:
      containers:
      - name: app
        image: my-app:latest
        envFrom:
        - secretRef:
            name: db-credentials
```

---

## Method 3: Secrets Store CSI Driver

**Best for**: File-based secrets, volume mounts

### Install CSI Driver

```bash
helm repo add secrets-store-csi-driver https://kubernetes-sigs.github.io/secrets-store-csi-driver/charts
helm install csi-secrets-store secrets-store-csi-driver/secrets-store-csi-driver --namespace kube-system

# Install AWS provider
kubectl apply -f https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml
```

### Create SecretProviderClass

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: aws-secrets
  namespace: default
spec:
  provider: aws
  parameters:
    objects: |
      - objectName: "prod/database/credentials"
        objectType: "secretsmanager"
        jmesPath:
          - path: "username"
            objectAlias: "db-username"
          - path: "password"
            objectAlias: "db-password"
  secretObjects:
  - secretName: db-secret
    type: Opaque
    data:
    - objectName: db-username
      key: username
    - objectName: db-password
      key: password
```

### Mount in Pod

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-csi
spec:
  template:
    spec:
      serviceAccountName: secrets-sa
      containers:
      - name: app
        image: my-app:latest
        volumeMounts:
        - name: secrets-store
          mountPath: "/mnt/secrets"
          readOnly: true
        env:
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: username
      volumes:
      - name: secrets-store
        csi:
          driver: secrets-store.csi.k8s.io
          readOnly: true
          volumeAttributes:
            secretProviderClass: "aws-secrets"
```

---

## Method 4: HashiCorp Vault Integration

**Best for**: Enterprise environments, advanced secret rotation

### Install Vault

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm install vault hashicorp/vault --namespace vault --create-namespace \
  --set "server.dev.enabled=true"
```

### Configure Vault Auth

```bash
# Enable Kubernetes auth
vault auth enable kubernetes

# Configure auth method
vault write auth/kubernetes/config \
    token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
    kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443" \
    kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

### Create Vault Policy and Role

```bash
# Create policy
vault policy write myapp-policy - <<EOF
path "secret/data/myapp/*" {
  capabilities = ["read"]
}
EOF

# Create role
vault write auth/kubernetes/role/myapp \
    bound_service_account_names=vault-sa \
    bound_service_account_namespaces=default \
    policies=myapp-policy \
    ttl=24h
```

### Vault Agent Sidecar

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-vault
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "myapp"
        vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
        vault.hashicorp.com/agent-inject-template-config: |
          {{- with secret "secret/data/myapp/config" -}}
          export DB_USERNAME="{{ .Data.data.username }}"
          export DB_PASSWORD="{{ .Data.data.password }}"
          {{- end }}
    spec:
      serviceAccountName: vault-sa
      containers:
      - name: app
        image: my-app:latest
        command: ["/bin/sh"]
        args: ["-c", "source /vault/secrets/config && exec my-app"]
```

---

## Method 5: Kubernetes Native Secrets

**Best for**: Simple use cases, development environments

### Create Secret

```bash
# From literal values
kubectl create secret generic db-secret \
  --from-literal=username=admin \
  --from-literal=password=secretpassword

# From file
kubectl create secret generic app-config --from-file=config.json
```

### Use in Pod

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-k8s-secrets
spec:
  template:
    spec:
      containers:
      - name: app
        image: my-app:latest
        env:
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: password
        volumeMounts:
        - name: config-volume
          mountPath: /etc/config
      volumes:
      - name: config-volume
        secret:
          secretName: app-config
```

---

## Method 6: AWS Parameter Store Integration

**Best for**: Configuration management, cost-effective secrets

### Using ESO with Parameter Store

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-parameter-store
spec:
  provider:
    aws:
      service: ParameterStore
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-config
spec:
  secretStoreRef:
    name: aws-parameter-store
    kind: SecretStore
  target:
    name: app-config-secret
  data:
  - secretKey: database-url
    remoteRef:
      key: /myapp/prod/database-url
  - secretKey: api-key
    remoteRef:
      key: /myapp/prod/api-key
```

---

## Method 7: Sealed Secrets (GitOps)

**Best for**: GitOps workflows, encrypted secrets in Git

### Install Sealed Secrets Controller

```bash
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/controller.yaml

# Install kubeseal CLI
wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/kubeseal-0.18.0-linux-amd64.tar.gz
tar -xvzf kubeseal-0.18.0-linux-amd64.tar.gz
sudo install -m 755 kubeseal /usr/local/bin/kubeseal
```

### Create Sealed Secret

```bash
# Create regular secret (don't apply)
kubectl create secret generic db-secret \
  --from-literal=username=admin \
  --from-literal=password=secretpassword \
  --dry-run=client -o yaml > secret.yaml

# Seal the secret
kubeseal -f secret.yaml -w sealed-secret.yaml

# Apply sealed secret (safe to commit to Git)
kubectl apply -f sealed-secret.yaml
```

### Sealed Secret Manifest

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: db-secret
  namespace: default
spec:
  encryptedData:
    username: AgBy3i4OJSWK+PiTySYZZA9rO43cGDEQAx...
    password: AhA5bGUvQTqKWQIDAQABAoIBAQDHwl5w...
  template:
    metadata:
      name: db-secret
      namespace: default
    type: Opaque
```

---

## Method 8: Bank-Vaults Operator

**Best for**: Automated Vault management, Kubernetes-native Vault

### Install Bank-Vaults

```bash
helm repo add banzaicloud-stable https://kubernetes-charts.banzaicloud.com
helm install vault-operator banzaicloud-stable/vault-operator
```

### Vault Custom Resource

```yaml
apiVersion: vault.banzaicloud.com/v1alpha1
kind: Vault
metadata:
  name: vault
spec:
  size: 1
  image: vault:1.12.0
  bankVaultsImage: banzaicloud/bank-vaults:latest
  
  # Automatic unsealing
  unsealConfig:
    aws:
      kmsKeyId: "alias/vault-kms-unseal"
      region: "us-east-1"
  
  # External configuration
  externalConfig:
    policies:
      - name: allow_secrets
        rules: path "secret/*" {
          capabilities = ["create", "read", "update", "delete", "list"]
        }
    auth:
      - type: kubernetes
        roles:
          - name: default
            bound_service_account_names: ["default"]
            bound_service_account_namespaces: ["default"]
            policies: ["allow_secrets"]
            ttl: 1h
```

---

## Method 9: CyberArk Conjur

**Best for**: Enterprise security, privileged access management

### Install Conjur

```bash
helm repo add cyberark https://cyberark.github.io/helm-charts
helm install conjur cyberark/conjur-oss --namespace conjur --create-namespace
```

### Conjur Authenticator

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-conjur
spec:
  template:
    spec:
      containers:
      - name: conjur-authenticator
        image: cyberark/conjur-authn-k8s-client:latest
        env:
        - name: CONTAINER_MODE
          value: sidecar
        - name: MY_POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: MY_POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        volumeMounts:
        - name: conjur-access-token
          mountPath: /run/conjur
      - name: app
        image: my-app:latest
        env:
        - name: CONJUR_AUTHN_TOKEN_FILE
          value: /run/conjur/access-token
        volumeMounts:
        - name: conjur-access-token
          mountPath: /run/conjur
      volumes:
      - name: conjur-access-token
        emptyDir:
          medium: Memory
```

---

## Method 10: Azure Key Vault (Multi-cloud)

**Best for**: Multi-cloud deployments, Azure integration

### Install Azure Key Vault Provider

```bash
helm repo add csi-secrets-store-provider-azure https://azure.github.io/secrets-store-csi-driver-provider-azure/charts
helm install csi csi-secrets-store-provider-azure/csi-secrets-store-provider-azure
```

### SecretProviderClass for Azure

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: azure-keyvault
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "client-id"
    keyvaultName: "mykeyvault"
    objects: |
      array:
        - |
          objectName: secret1
          objectType: secret
          objectVersion: ""
    tenantId: "tenant-id"
```

---

## Method 11: Google Secret Manager

**Best for**: GCP integration, multi-cloud secrets

### Using ESO with Google Secret Manager

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: gcpsm-secret-store
spec:
  provider:
    gcpsm:
      projectId: "my-project"
      auth:
        workloadIdentity:
          clusterLocation: us-central1
          clusterName: my-cluster
          serviceAccountRef:
            name: external-secrets-sa
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: gcp-secret
spec:
  secretStoreRef:
    name: gcpsm-secret-store
    kind: SecretStore
  target:
    name: myapp-secret
  data:
  - secretKey: password
    remoteRef:
      key: database-password
```

---

## Method 12: Doppler Secrets Manager

**Best for**: Developer experience, environment management

### Install Doppler Kubernetes Operator

```bash
kubectl apply -f https://github.com/DopplerHQ/kubernetes-operator/releases/latest/download/recommended.yaml
```

### Doppler Secret Sync

```yaml
apiVersion: secrets.doppler.com/v1alpha1
kind: DopplerSecret
metadata:
  name: doppler-secret
  namespace: default
spec:
  tokenSecret:
    name: doppler-token-secret
  managedSecret:
    name: doppler-managed-secret
    namespace: default
  project: my-project
  config: prd
---
apiVersion: v1
kind: Secret
metadata:
  name: doppler-token-secret
type: Opaque
data:
  dopplerToken: <base64-encoded-service-token>
```

---

## Advanced Security Patterns

### 1. **Secret Injection at Runtime**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: runtime-injection
spec:
  template:
    spec:
      initContainers:
      - name: secret-fetcher
        image: aws-cli:latest
        command:
        - /bin/sh
        - -c
        - |
          aws secretsmanager get-secret-value \
            --secret-id prod/database/credentials \
            --query SecretString --output text > /shared/secrets.json
        volumeMounts:
        - name: shared-secrets
          mountPath: /shared
      containers:
      - name: app
        image: my-app:latest
        volumeMounts:
        - name: shared-secrets
          mountPath: /etc/secrets
      volumes:
      - name: shared-secrets
        emptyDir:
          medium: Memory
```

### 2. **Secret Rotation with Reloader**

```bash
# Install Reloader
kubectl apply -f https://raw.githubusercontent.com/stakater/Reloader/master/deployments/kubernetes/reloader.yaml
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-reloader
  annotations:
    reloader.stakater.com/auto: "true"
spec:
  template:
    spec:
      containers:
      - name: app
        image: my-app:latest
        envFrom:
        - secretRef:
            name: auto-rotated-secret
```

### 3. **Secret Encryption at Rest (etcd)**

```yaml
# EncryptionConfiguration
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  providers:
  - aescbc:
      keys:
      - name: key1
        secret: <32-byte-base64-encoded-key>
  - identity: {}
```

### 4. **Network Policies for Secret Access**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-external-secrets-access
spec:
  podSelector:
    matchLabels:
      app: external-secrets
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: external-secrets-system
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS only
```

### 5. **Pod Security Standards**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: secure-secrets
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-app
  namespace: secure-secrets
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: app
        image: my-app:latest
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          capabilities:
            drop:
            - ALL
```

---

### 1. **Principle of Least Privilege**
```yaml
# Specific IAM policy for secrets access
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/myapp/*"
    }
  ]
}
```

### 2. **Secret Rotation**
```yaml
# ESO with automatic refresh
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: rotating-secret
spec:
  refreshInterval: 5m  # Check every 5 minutes
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
```

### 3. **Namespace Isolation**
```yaml
# Separate SecretStore per namespace
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: prod-secrets
  namespace: production
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
```

### 4. **Audit and Monitoring**
```yaml
# CloudWatch logging for secret access
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
data:
  fluent-bit.conf: |
    [INPUT]
        Name tail
        Path /var/log/containers/*external-secrets*.log
        Parser docker
        Tag secrets.access
```

### 5. **Zero-Trust Secret Access**
```yaml
# Service mesh with mTLS
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: secrets-access
  namespace: production
spec:
  selector:
    matchLabels:
      app: external-secrets
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/external-secrets-sa"]
```

### 6. **Compliance and Governance**
```yaml
# OPA Gatekeeper policy for secret management
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: requiredsecretannotations
spec:
  crd:
    spec:
      names:
        kind: RequiredSecretAnnotations
      validation:
        properties:
          annotations:
            type: array
            items:
              type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package requiredsecretannotations
        
        violation[{"msg": msg}] {
          required := input.parameters.annotations
          provided := input.review.object.metadata.annotations
          missing := required[_]
          not provided[missing]
          msg := sprintf("Missing required annotation: %v", [missing])
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: RequiredSecretAnnotations
metadata:
  name: must-have-secret-annotations
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Secret"]
  parameters:
    annotations:
      - "security.company.com/classification"
      - "security.company.com/owner"
```

### 7. **Secret Scanning and Detection**
```bash
# Install secret scanning tools
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm install falco falcosecurity/falco \
  --set falco.grpc.enabled=true \
  --set falco.grpcOutput.enabled=true

# Custom Falco rule for secret detection
echo '
- rule: Detect Secret Access
  desc: Detect when secrets are accessed
  condition: >
    spawned_process and
    (proc.cmdline contains "kubectl get secret" or
     proc.cmdline contains "aws secretsmanager get-secret-value")
  output: >
    Secret access detected (user=%user.name command=%proc.cmdline)
  priority: WARNING
' >> /etc/falco/falco_rules.local.yaml
```

### 8. **Disaster Recovery for Secrets**
```yaml
# Cross-region secret replication
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: aws-secrets-dr
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-west-2  # DR region
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
            namespace: external-secrets-system
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: dr-backup-secret
spec:
  refreshInterval: 24h
  secretStoreRef:
    name: aws-secrets-dr
    kind: ClusterSecretStore
  target:
    name: dr-secret-backup
    template:
      metadata:
        annotations:
          replicator.v1.mittwald.de/replicate-to: "*"
```

---

## 📊 Comparison Matrix

| Method | Complexity | Security | GitOps | Multi-Cloud | Cost | Enterprise |
|--------|------------|----------|--------|-------------|------|------------|
| IRSA + Secrets Manager | Low | High | Medium | No | Low | ✅ |
| External Secrets Operator | Medium | High | High | Yes | Low | ✅ |
| CSI Driver | Medium | High | Medium | No | Low | ✅ |
| Vault | High | Very High | High | Yes | Medium | ✅ |
| K8s Secrets | Very Low | Low | High | Yes | Free | ❌ |
| Parameter Store | Low | Medium | High | No | Very Low | ✅ |
| Sealed Secrets | Medium | Medium | Very High | Yes | Free | ✅ |
| Bank-Vaults | High | Very High | High | Yes | Medium | ✅ |
| Conjur | Very High | Very High | Medium | Yes | High | ✅ |
| Azure Key Vault | Medium | High | Medium | Yes | Low | ✅ |
| Google Secret Manager | Medium | High | Medium | Yes | Low | ✅ |
| Doppler | Low | High | High | Yes | Medium | ✅ |

---

## 🚀 Implementation Recommendations

### **For Startups/Small Teams**:
1. Start with **Kubernetes Secrets** for development
2. Move to **ESO + AWS Secrets Manager** for production

### **For Enterprise**:
1. **Vault** for multi-cloud and advanced features
2. **ESO** as universal interface
3. **CSI Driver** for file-based secrets

### **For GitOps-First**:
1. **Sealed Secrets** for encrypted secrets in Git
2. **ESO** for external secret synchronization

### **For AWS-Native**:
1. **IRSA + Secrets Manager** for simplicity
2. **Parameter Store** for configuration

---

## 🛠 Production Deployment Example

Complete production setup with ESO:

```bash
# 1. Install ESO
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets-system --create-namespace

# 2. Create IRSA
eksctl create iamserviceaccount \
  --name external-secrets-sa \
  --namespace external-secrets-system \
  --cluster my-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite \
  --approve

# 3. Apply SecretStore and ExternalSecret manifests
kubectl apply -f secretstore.yaml
kubectl apply -f externalsecret.yaml

# 4. Verify secret creation
kubectl get secrets
kubectl describe externalsecret database-secret
```

---

## 🔍 Troubleshooting Guide

### Common Issues:

**ESO not syncing secrets**:
```bash
kubectl logs -n external-secrets-system deployment/external-secrets
kubectl describe externalsecret my-secret
```

**IRSA permissions**:
```bash
# Test from pod
aws sts get-caller-identity
aws secretsmanager get-secret-value --secret-id my-secret
```

**CSI Driver mount issues**:
```bash
kubectl describe pod my-pod
kubectl logs -n kube-system daemonset/secrets-store-csi-driver
```

---

This guide covers all major methods for secure secret management in EKS. Choose the method that best fits your security requirements, operational complexity, and team expertise.