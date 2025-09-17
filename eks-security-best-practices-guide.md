# EKS Security Best Practices - Complete Guide

## Table of Contents
1. [Cluster Access Control](#cluster-access-control)
2. [Authentication & Authorization](#authentication--authorization)
3. [Network Security](#network-security)
4. [Pod Security](#pod-security)
5. [Secrets Management](#secrets-management)
6. [Monitoring & Logging](#monitoring--logging)
7. [Image Security](#image-security)
8. [Compliance & Governance](#compliance--governance)

---

## Cluster Access Control

### 1. IAM Roles for Service Accounts (IRSA)

#### Best Practice: Use IRSA instead of storing AWS credentials in pods

```yaml
# ServiceAccount with IRSA
apiVersion: v1
kind: ServiceAccount
metadata:
  name: s3-access-sa
  namespace: default
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/EKS-S3-Access-Role
```

#### IAM Role Trust Policy for IRSA:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B716D3041E"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B716D3041E:sub": "system:serviceaccount:default:s3-access-sa",
          "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B716D3041E:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
```

#### CLI Commands to Set Up IRSA:
```bash
# Create OIDC identity provider
eksctl utils associate-iam-oidc-provider \
  --cluster my-cluster \
  --approve

# Create service account with IAM role
eksctl create iamserviceaccount \
  --name s3-access-sa \
  --namespace default \
  --cluster my-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess \
  --approve
```

### 2. Cluster Endpoint Access Control

#### Private Endpoint Configuration:
```bash
# Update cluster endpoint access
aws eks update-cluster-config \
  --name my-cluster \
  --resources-vpc-config endpointConfigPrivateAccess=true,endpointConfigPublicAccess=false

# With public access restrictions
aws eks update-cluster-config \
  --name my-cluster \
  --resources-vpc-config \
    endpointConfigPrivateAccess=true,endpointConfigPublicAccess=true,publicAccessCidrs=["203.0.113.0/24"]
```

#### CloudFormation Template for Secure Cluster:
```yaml
EKSCluster:
  Type: AWS::EKS::Cluster
  Properties:
    Name: secure-cluster
    Version: "1.28"
    RoleArn: !GetAtt EKSClusterRole.Arn
    ResourcesVpcConfig:
      SecurityGroupIds:
        - !Ref EKSClusterSecurityGroup
      SubnetIds:
        - !Ref PrivateSubnet1
        - !Ref PrivateSubnet2
      EndpointConfigPrivateAccess: true
      EndpointConfigPublicAccess: false
    EncryptionConfig:
      - Resources: ["secrets"]
        Provider:
          KeyId: !Ref EKSKMSKey
    Logging:
      ClusterLogging:
        EnabledTypes:
          - Type: api
          - Type: audit
          - Type: authenticator
          - Type: controllerManager
          - Type: scheduler
```

---

## Authentication & Authorization

### 1. AWS IAM Authenticator Configuration

#### ConfigMap for aws-auth:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    - rolearn: arn:aws:iam::123456789012:role/EKS-NodeGroup-Role
      username: system:node:{{EC2PrivateDNSName}}
      groups:
        - system:bootstrappers
        - system:nodes
    - rolearn: arn:aws:iam::123456789012:role/EKS-Admin-Role
      username: admin
      groups:
        - system:masters
    - rolearn: arn:aws:iam::123456789012:role/EKS-Developer-Role
      username: developer
      groups:
        - developers
  mapUsers: |
    - userarn: arn:aws:iam::123456789012:user/john.doe
      username: john.doe
      groups:
        - developers
    - userarn: arn:aws:iam::123456789012:user/jane.admin
      username: jane.admin
      groups:
        - system:masters
```

### 2. Role-Based Access Control (RBAC)

#### Developer Role Example:
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: development
  name: developer-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["pods/log", "pods/exec"]
  verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer-binding
  namespace: development
subjects:
- kind: Group
  name: developers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: developer-role
  apiGroup: rbac.authorization.k8s.io
```

#### Read-Only Cluster Role:
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: readonly-cluster-role
rules:
- apiGroups: [""]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps", "extensions"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: readonly-binding
subjects:
- kind: Group
  name: readonly-users
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: readonly-cluster-role
  apiGroup: rbac.authorization.k8s.io
```

### 3. Multi-Factor Authentication Setup

#### IAM Policy for MFA Requirement:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowViewAccountInfo",
      "Effect": "Allow",
      "Action": [
        "iam:GetAccountPasswordPolicy",
        "iam:ListVirtualMFADevices"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AllowManageOwnPasswords",
      "Effect": "Allow",
      "Action": [
        "iam:ChangePassword",
        "iam:GetUser"
      ],
      "Resource": "arn:aws:iam::*:user/${aws:username}"
    },
    {
      "Sid": "AllowManageOwnMFA",
      "Effect": "Allow",
      "Action": [
        "iam:CreateVirtualMFADevice",
        "iam:DeleteVirtualMFADevice",
        "iam:EnableMFADevice",
        "iam:ListMFADevices",
        "iam:ResyncMFADevice"
      ],
      "Resource": "arn:aws:iam::*:mfa/${aws:username}"
    },
    {
      "Sid": "DenyAllExceptUnlessMFAAuthenticated",
      "Effect": "Deny",
      "NotAction": [
        "iam:CreateVirtualMFADevice",
        "iam:EnableMFADevice",
        "iam:GetUser",
        "iam:ListMFADevices",
        "iam:ListVirtualMFADevices",
        "iam:ResyncMFADevice",
        "sts:GetSessionToken"
      ],
      "Resource": "*",
      "Condition": {
        "BoolIfExists": {
          "aws:MultiFactorAuthPresent": "false"
        }
      }
    }
  ]
}
```

---

## Network Security

### 1. VPC and Subnet Configuration

#### Secure VPC Setup:
```yaml
# Private subnets for worker nodes
PrivateSubnet1:
  Type: AWS::EC2::Subnet
  Properties:
    VpcId: !Ref VPC
    CidrBlock: 10.0.1.0/24
    AvailabilityZone: !Select [0, !GetAZs '']
    MapPublicIpOnLaunch: false

PrivateSubnet2:
  Type: AWS::EC2::Subnet
  Properties:
    VpcId: !Ref VPC
    CidrBlock: 10.0.2.0/24
    AvailabilityZone: !Select [1, !GetAZs '']
    MapPublicIpOnLaunch: false

# Public subnets for load balancers only
PublicSubnet1:
  Type: AWS::EC2::Subnet
  Properties:
    VpcId: !Ref VPC
    CidrBlock: 10.0.101.0/24
    AvailabilityZone: !Select [0, !GetAZs '']
    MapPublicIpOnLaunch: true
```

### 2. Security Groups Configuration

#### EKS Cluster Security Group:
```yaml
EKSClusterSecurityGroup:
  Type: AWS::EC2::SecurityGroup
  Properties:
    GroupDescription: Security group for EKS cluster control plane
    VpcId: !Ref VPC
    SecurityGroupIngress:
      - IpProtocol: tcp
        FromPort: 443
        ToPort: 443
        SourceSecurityGroupId: !Ref EKSNodeSecurityGroup
        Description: Allow HTTPS from worker nodes
    SecurityGroupEgress:
      - IpProtocol: tcp
        FromPort: 1025
        ToPort: 65535
        DestinationSecurityGroupId: !Ref EKSNodeSecurityGroup
        Description: Allow kubelet communication to worker nodes
```

#### Worker Node Security Group:
```yaml
EKSNodeSecurityGroup:
  Type: AWS::EC2::SecurityGroup
  Properties:
    GroupDescription: Security group for EKS worker nodes
    VpcId: !Ref VPC
    SecurityGroupIngress:
      - IpProtocol: tcp
        FromPort: 1025
        ToPort: 65535
        SourceSecurityGroupId: !Ref EKSClusterSecurityGroup
        Description: Allow communication from cluster control plane
      - IpProtocol: tcp
        FromPort: 443
        ToPort: 443
        SourceSecurityGroupId: !Ref EKSNodeSecurityGroup
        Description: Allow pods to communicate with cluster API
      - IpProtocol: -1
        SourceSecurityGroupId: !Ref EKSNodeSecurityGroup
        Description: Allow worker nodes to communicate with each other
```

### 3. Network Policies

#### Deny All Network Policy:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

#### Allow Specific Communication:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

#### Database Access Policy:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-access
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: backend
    ports:
    - protocol: TCP
      port: 5432
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
```

---

## Pod Security

### 1. Pod Security Standards

#### Restricted Pod Security Policy:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: secure-namespace
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### 2. Security Contexts

#### Secure Pod Configuration:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: nginx:1.21
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 1000
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
    resources:
      limits:
        memory: "128Mi"
        cpu: "100m"
      requests:
        memory: "64Mi"
        cpu: "50m"
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: cache
      mountPath: /var/cache/nginx
  volumes:
  - name: tmp
    emptyDir: {}
  - name: cache
    emptyDir: {}
```

### 3. Admission Controllers

#### OPA Gatekeeper Policy Example:
```yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8srequiredsecuritycontext
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredSecurityContext
      validation:
        properties:
          runAsNonRoot:
            type: boolean
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredsecuritycontext
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.securityContext.runAsNonRoot
          msg := "Container must run as non-root user"
        }
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          container.securityContext.allowPrivilegeEscalation
          msg := "Container must not allow privilege escalation"
        }

---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredSecurityContext
metadata:
  name: must-run-as-nonroot
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
  parameters:
    runAsNonRoot: true
```

---

## Secrets Management

### 1. AWS Secrets Manager Integration

#### External Secrets Operator Configuration:
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
        secretRef:
          accessKeyID:
            name: awssm-secret
            key: access-key
          secretAccessKey:
            name: awssm-secret
            key: secret-access-key

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
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
      key: prod/database
      property: username
  - secretKey: password
    remoteRef:
      key: prod/database
      property: password
```

### 2. Sealed Secrets

#### Sealed Secret Example:
```bash
# Install sealed-secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/controller.yaml

# Create sealed secret
echo -n mypassword | kubectl create secret generic mysecret --dry-run=client --from-file=password=/dev/stdin -o yaml | kubeseal -o yaml > mysealedsecret.yaml
```

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: mysecret
  namespace: default
spec:
  encryptedData:
    password: AgBy3i4OJSWK+PiTySYZZA9rO43cGDEQAx...
  template:
    metadata:
      name: mysecret
      namespace: default
```

### 3. Kubernetes Secrets Encryption

#### KMS Key for EKS Encryption:
```yaml
EKSKMSKey:
  Type: AWS::KMS::Key
  Properties:
    Description: KMS key for EKS secrets encryption
    KeyPolicy:
      Statement:
        - Sid: Enable IAM User Permissions
          Effect: Allow
          Principal:
            AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:root'
          Action: 'kms:*'
          Resource: '*'
        - Sid: Allow EKS Service
          Effect: Allow
          Principal:
            Service: eks.amazonaws.com
          Action:
            - kms:Decrypt
            - kms:GenerateDataKey
          Resource: '*'
```

---

## Monitoring & Logging

### 1. CloudWatch Container Insights

#### Fluent Bit Configuration:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: amazon-cloudwatch
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf
        HTTP_Server   On
        HTTP_Listen   0.0.0.0
        HTTP_Port     2020

    @INCLUDE application-log.conf
    @INCLUDE dataplane-log.conf
    @INCLUDE host-log.conf

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

    [OUTPUT]
        Name                cloudwatch_logs
        Match               application.*
        region              ${AWS_REGION}
        log_group_name      /aws/containerinsights/${CLUSTER_NAME}/application
        log_stream_prefix   ${HOST_NAME}-
        auto_create_group   On
```

### 2. Audit Logging Configuration

#### Enable Audit Logs:
```bash
aws eks update-cluster-config \
  --name my-cluster \
  --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'
```

#### Custom Audit Policy:
```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: None
  users: ["system:kube-proxy"]
  verbs: ["watch"]
  resources:
  - group: ""
    resources: ["endpoints", "services", "services/status"]
- level: None
  users: ["system:unsecured"]
  namespaces: ["kube-system"]
  verbs: ["get"]
  resources:
  - group: ""
    resources: ["configmaps"]
- level: None
  users: ["kubelet"]
  verbs: ["get"]
  resources:
  - group: ""
    resources: ["nodes", "nodes/status"]
- level: Request
  omitStages:
  - RequestReceived
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
- level: Metadata
  omitStages:
  - RequestReceived
```

### 3. Prometheus and Grafana Setup

#### Prometheus Configuration:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "kubernetes.rules"
    
    scrape_configs:
    - job_name: 'kubernetes-apiservers'
      kubernetes_sd_configs:
      - role: endpoints
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https
    
    - job_name: 'kubernetes-nodes'
      kubernetes_sd_configs:
      - role: node
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
```

---

## Image Security

### 1. ECR Image Scanning

#### Enable Image Scanning:
```bash
# Create ECR repository with scan on push
aws ecr create-repository \
  --repository-name my-app \
  --image-scanning-configuration scanOnPush=true

# Enable enhanced scanning
aws ecr put-registry-scanning-configuration \
  --scan-type ENHANCED \
  --rules '[{
    "scanFrequency": "SCAN_ON_PUSH",
    "repositoryFilters": [
      {
        "filter": "*",
        "filterType": "WILDCARD"
      }
    ]
  }]'
```

### 2. Admission Controller for Image Security

#### Image Policy Webhook:
```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionWebhook
metadata:
  name: image-policy-webhook
webhooks:
- name: image-policy.example.com
  clientConfig:
    service:
      name: image-policy-webhook
      namespace: default
      path: "/validate"
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  admissionReviewVersions: ["v1", "v1beta1"]
```

### 3. Falco Runtime Security

#### Falco Rules for Container Security:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: falco-config
  namespace: falco
data:
  falco.yaml: |
    rules_file:
      - /etc/falco/falco_rules.yaml
      - /etc/falco/falco_rules.local.yaml
      - /etc/falco/k8s_audit_rules.yaml
    
    json_output: true
    json_include_output_property: true
    
    http_output:
      enabled: true
      url: "http://falcosidekick:2801/"
    
    grpc:
      enabled: true
      bind_address: "0.0.0.0:5060"
      threadiness: 8
    
    grpc_output:
      enabled: true

  custom_rules.yaml: |
    - rule: Detect crypto miners
      desc: Detect cryptocurrency miners
      condition: >
        spawned_process and
        (proc.name in (crypto_miners) or
         proc.cmdline contains "stratum" or
         proc.cmdline contains "mining")
      output: >
        Cryptocurrency mining detected (user=%user.name command=%proc.cmdline
        container=%container.name image=%container.image.repository)
      priority: CRITICAL
      tags: [cryptocurrency, mining]
```

---

## Compliance & Governance

### 1. CIS Kubernetes Benchmark

#### kube-bench Security Scan:
```bash
# Run kube-bench as a job
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job-eks.yaml

# Check results
kubectl logs job/kube-bench
```

#### Example kube-bench Job:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: kube-bench
spec:
  template:
    spec:
      hostPID: true
      nodeSelector:
        kubernetes.io/os: linux
      tolerations:
      - key: node-role.kubernetes.io/master
        operator: Exists
        effect: NoSchedule
      containers:
      - name: kube-bench
        image: aquasec/kube-bench:latest
        command: ["kube-bench", "--benchmark", "eks-1.0.1"]
        volumeMounts:
        - name: var-lib-etcd
          mountPath: /var/lib/etcd
          readOnly: true
        - name: var-lib-kubelet
          mountPath: /var/lib/kubelet
          readOnly: true
        - name: etc-systemd
          mountPath: /etc/systemd
          readOnly: true
        - name: etc-kubernetes
          mountPath: /etc/kubernetes
          readOnly: true
        - name: usr-bin
          mountPath: /usr/local/mount-from-host/bin
          readOnly: true
      restartPolicy: Never
      volumes:
      - name: var-lib-etcd
        hostPath:
          path: "/var/lib/etcd"
      - name: var-lib-kubelet
        hostPath:
          path: "/var/lib/kubelet"
      - name: etc-systemd
        hostPath:
          path: "/etc/systemd"
      - name: etc-kubernetes
        hostPath:
          path: "/etc/kubernetes"
      - name: usr-bin
        hostPath:
          path: "/usr/bin"
```

### 2. Policy as Code with OPA

#### Gatekeeper Installation:
```bash
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.14/deploy/gatekeeper.yaml
```

#### Resource Limits Policy:
```yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8srequiredresources
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredResources
      validation:
        properties:
          limits:
            type: array
            items:
              type: string
          requests:
            type: array
            items:
              type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredresources
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          required := input.parameters.limits
          missing := required[_]
          not container.resources.limits[missing]
          msg := sprintf("Container <%v> is missing required limit <%v>", [container.name, missing])
        }
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          required := input.parameters.requests
          missing := required[_]
          not container.resources.requests[missing]
          msg := sprintf("Container <%v> is missing required request <%v>", [container.name, missing])
        }

---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredResources
metadata:
  name: must-have-resources
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
  parameters:
    limits: ["memory", "cpu"]
    requests: ["memory", "cpu"]
```

### 3. AWS Config Rules for EKS

#### Config Rule for EKS Security:
```yaml
EKSClusterConfigRule:
  Type: AWS::Config::ConfigRule
  Properties:
    ConfigRuleName: eks-cluster-security-check
    Description: Checks if EKS clusters have security best practices enabled
    Source:
      Owner: AWS
      SourceIdentifier: EKS_CLUSTER_SUPPORTED_VERSION
    DependsOn: ConfigurationRecorder
```

---

## Security Checklist

### Cluster Level Security
- [ ] Enable private endpoint access
- [ ] Restrict public endpoint access with CIDR blocks
- [ ] Enable envelope encryption for etcd
- [ ] Enable all CloudWatch logging types
- [ ] Use latest Kubernetes version
- [ ] Enable GuardDuty for EKS protection

### Authentication & Authorization
- [ ] Configure aws-auth ConfigMap properly
- [ ] Implement RBAC with least privilege
- [ ] Use IAM roles for service accounts (IRSA)
- [ ] Enable MFA for IAM users
- [ ] Regular audit of permissions

### Network Security
- [ ] Deploy worker nodes in private subnets
- [ ] Configure security groups with minimal access
- [ ] Implement network policies
- [ ] Use VPC endpoints for AWS services
- [ ] Enable VPC Flow Logs

### Pod Security
- [ ] Enforce pod security standards
- [ ] Use non-root containers
- [ ] Enable read-only root filesystem
- [ ] Drop all capabilities and add only required ones
- [ ] Set resource limits and requests
- [ ] Use admission controllers

### Secrets Management
- [ ] Never store secrets in container images
- [ ] Use external secret management (AWS Secrets Manager)
- [ ] Enable secrets encryption at rest
- [ ] Rotate secrets regularly
- [ ] Use sealed secrets for GitOps

### Image Security
- [ ] Enable ECR image scanning
- [ ] Use minimal base images
- [ ] Scan images for vulnerabilities
- [ ] Sign container images
- [ ] Use private registries

### Monitoring & Logging
- [ ] Enable audit logging
- [ ] Monitor with CloudWatch Container Insights
- [ ] Set up security alerts
- [ ] Use runtime security tools (Falco)
- [ ] Regular security assessments

### Compliance
- [ ] Run CIS Kubernetes benchmark
- [ ] Implement policy as code
- [ ] Regular compliance audits
- [ ] Document security procedures
- [ ] Incident response plan

---

## CLI Commands Reference

### Cluster Management
```bash
# Create cluster with encryption
eksctl create cluster \
  --name secure-cluster \
  --version 1.28 \
  --region us-east-1 \
  --nodegroup-name workers \
  --node-type m5.large \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 4 \
  --ssh-access \
  --ssh-public-key my-key \
  --enable-ssm \
  --asg-access \
  --external-dns-access \
  --full-ecr-access \
  --appmesh-access \
  --alb-ingress-access

# Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name secure-cluster

# Enable logging
aws eks update-cluster-config \
  --name secure-cluster \
  --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'
```

### Security Scanning
```bash
# Run kube-hunter security scan
kubectl create -f https://raw.githubusercontent.com/aquasecurity/kube-hunter/master/job.yaml

# Run Polaris security validation
kubectl apply -f https://github.com/FairwindsOps/polaris/releases/latest/download/dashboard.yaml

# Install and run kube-score
kube-score score my-deployment.yaml
```

This comprehensive guide covers all aspects of EKS security with practical examples and real-world configurations. Each section includes working code examples that you can adapt to your specific requirements.