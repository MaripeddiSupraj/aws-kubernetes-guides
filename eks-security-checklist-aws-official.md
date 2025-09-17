# EKS Security Checklist - AWS Official Best Practices

## Overview
This checklist is based on AWS official documentation and security best practices for Amazon EKS. Follow these checks to ensure your EKS cluster meets AWS security standards.

---

## 🔐 Cluster Configuration Security

### ✅ Control Plane Security
- [ ] **Enable private endpoint access**
  ```bash
  aws eks update-cluster-config --name CLUSTER_NAME \
    --resources-vpc-config endpointConfigPrivateAccess=true
  ```
  
- [ ] **Restrict public endpoint access** (if needed)
  ```bash
  aws eks update-cluster-config --name CLUSTER_NAME \
    --resources-vpc-config publicAccessCidrs=["YOUR_IP/32"]
  ```

- [ ] **Enable envelope encryption for Kubernetes secrets**
  ```yaml
  EncryptionConfig:
    - Resources: ["secrets"]
      Provider:
        KeyId: arn:aws:kms:region:account:key/key-id
  ```

- [ ] **Use latest supported Kubernetes version**
  ```bash
  aws eks describe-cluster --name CLUSTER_NAME --query cluster.version
  ```

- [ ] **Enable all CloudWatch logging types**
  ```bash
  aws eks update-cluster-config --name CLUSTER_NAME \
    --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'
  ```

### ✅ Cluster Access Verification
- [ ] **Verify cluster endpoint configuration**
  ```bash
  aws eks describe-cluster --name CLUSTER_NAME \
    --query 'cluster.resourcesVpcConfig.{PrivateAccess:endpointConfigPrivateAccess,PublicAccess:endpointConfigPublicAccess,PublicCidrs:publicAccessCidrs}'
  ```

- [ ] **Check encryption status**
  ```bash
  aws eks describe-cluster --name CLUSTER_NAME \
    --query 'cluster.encryptionConfig'
  ```

---

## 🔑 Identity and Access Management

### ✅ IAM Roles for Service Accounts (IRSA)
- [ ] **Associate OIDC identity provider**
  ```bash
  eksctl utils associate-iam-oidc-provider --cluster CLUSTER_NAME --approve
  ```

- [ ] **Verify OIDC provider exists**
  ```bash
  aws iam list-open-id-connect-providers
  ```

- [ ] **Create service accounts with IAM roles (no hardcoded credentials)**
  ```bash
  eksctl create iamserviceaccount \
    --name SERVICE_ACCOUNT_NAME \
    --namespace NAMESPACE \
    --cluster CLUSTER_NAME \
    --attach-policy-arn POLICY_ARN \
    --approve
  ```

### ✅ AWS Auth Configuration
- [ ] **Review aws-auth ConfigMap**
  ```bash
  kubectl get configmap aws-auth -n kube-system -o yaml
  ```

- [ ] **Verify no unnecessary admin access**
  ```bash
  kubectl get configmap aws-auth -n kube-system -o yaml | grep -A 10 "system:masters"
  ```

- [ ] **Implement least privilege IAM policies**
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:GetObject"
        ],
        "Resource": "arn:aws:s3:::specific-bucket/*"
      }
    ]
  }
  ```

### ✅ RBAC Configuration
- [ ] **Implement Role-Based Access Control**
  ```bash
  kubectl get clusterrolebindings | grep system:masters
  kubectl get rolebindings --all-namespaces
  ```

- [ ] **Remove default service account permissions**
  ```yaml
  apiVersion: v1
  kind: ServiceAccount
  metadata:
    name: default
  automountServiceAccountToken: false
  ```

- [ ] **Create namespace-specific roles**
  ```yaml
  apiVersion: rbac.authorization.k8s.io/v1
  kind: Role
  metadata:
    namespace: production
    name: pod-reader
  rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "watch", "list"]
  ```

---

## 🌐 Network Security

### ✅ VPC Configuration
- [ ] **Deploy worker nodes in private subnets**
  ```bash
  aws ec2 describe-subnets --subnet-ids SUBNET_ID \
    --query 'Subnets[0].MapPublicIpOnLaunch'
  ```

- [ ] **Verify VPC has private subnets in multiple AZs**
  ```bash
  aws ec2 describe-subnets --filters "Name=vpc-id,Values=VPC_ID" \
    --query 'Subnets[?MapPublicIpOnLaunch==`false`].[SubnetId,AvailabilityZone]'
  ```

- [ ] **Enable VPC Flow Logs**
  ```bash
  aws ec2 create-flow-logs \
    --resource-type VPC \
    --resource-ids VPC_ID \
    --traffic-type ALL \
    --log-destination-type cloud-watch-logs \
    --log-group-name VPCFlowLogs
  ```

### ✅ Security Groups
- [ ] **Review cluster security group rules**
  ```bash
  aws eks describe-cluster --name CLUSTER_NAME \
    --query 'cluster.resourcesVpcConfig.clusterSecurityGroupId'
  
  aws ec2 describe-security-groups --group-ids SECURITY_GROUP_ID
  ```

- [ ] **Verify node group security groups**
  ```bash
  aws eks describe-nodegroup --cluster-name CLUSTER_NAME \
    --nodegroup-name NODEGROUP_NAME \
    --query 'nodegroup.resources.remoteAccessSecurityGroup'
  ```

- [ ] **Ensure minimal required ports only**
  - Control plane to nodes: 1025-65535
  - Nodes to control plane: 443
  - Node to node: All traffic within security group

### ✅ Network Policies
- [ ] **Install network policy provider (Calico/Cilium)**
  ```bash
  kubectl apply -f https://raw.githubusercontent.com/aws/amazon-vpc-cni-k8s/master/config/master/calico-operator.yaml
  kubectl apply -f https://raw.githubusercontent.com/aws/amazon-vpc-cni-k8s/master/config/master/calico-crs.yaml
  ```

- [ ] **Implement default deny-all policy**
  ```yaml
  apiVersion: networking.k8s.io/v1
  kind: NetworkPolicy
  metadata:
    name: default-deny-all
    namespace: production
  spec:
    podSelector: {}
    policyTypes:
    - Ingress
    - Egress
  ```

- [ ] **Create specific allow policies**
  ```yaml
  apiVersion: networking.k8s.io/v1
  kind: NetworkPolicy
  metadata:
    name: allow-frontend-to-backend
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

---

## 🛡️ Pod Security

### ✅ Pod Security Standards
- [ ] **Enable Pod Security Standards**
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

- [ ] **Verify pod security policies are enforced**
  ```bash
  kubectl get ns -o yaml | grep pod-security
  ```

### ✅ Security Contexts
- [ ] **Enforce non-root containers**
  ```yaml
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
  ```

- [ ] **Enable read-only root filesystem**
  ```yaml
  securityContext:
    readOnlyRootFilesystem: true
  ```

- [ ] **Drop all capabilities and add only required ones**
  ```yaml
  securityContext:
    capabilities:
      drop:
      - ALL
      add:
      - NET_BIND_SERVICE
  ```

- [ ] **Disable privilege escalation**
  ```yaml
  securityContext:
    allowPrivilegeEscalation: false
  ```

### ✅ Resource Management
- [ ] **Set resource limits and requests**
  ```yaml
  resources:
    limits:
      memory: "128Mi"
      cpu: "100m"
    requests:
      memory: "64Mi"
      cpu: "50m"
  ```

- [ ] **Implement LimitRanges**
  ```yaml
  apiVersion: v1
  kind: LimitRange
  metadata:
    name: mem-limit-range
  spec:
    limits:
    - default:
        memory: "512Mi"
        cpu: "200m"
      defaultRequest:
        memory: "256Mi"
        cpu: "100m"
      type: Container
  ```

---

## 🔒 Secrets Management

### ✅ Kubernetes Secrets
- [ ] **Never store secrets in container images**
  ```bash
  # Check for hardcoded secrets
  docker history IMAGE_NAME --no-trunc | grep -i secret
  ```

- [ ] **Use Kubernetes secrets properly**
  ```yaml
  apiVersion: v1
  kind: Secret
  metadata:
    name: mysecret
  type: Opaque
  data:
    username: YWRtaW4=
    password: MWYyZDFlMmU2N2Rm
  ```

- [ ] **Mount secrets as volumes, not environment variables**
  ```yaml
  volumeMounts:
  - name: secret-volume
    mountPath: "/etc/secret-volume"
    readOnly: true
  volumes:
  - name: secret-volume
    secret:
      secretName: mysecret
  ```

### ✅ External Secrets Management
- [ ] **Integrate with AWS Secrets Manager**
  ```bash
  helm repo add external-secrets https://charts.external-secrets.io
  helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
  ```

- [ ] **Configure External Secrets Operator**
  ```yaml
  apiVersion: external-secrets.io/v1beta1
  kind: SecretStore
  metadata:
    name: aws-secrets-manager
  spec:
    provider:
      aws:
        service: SecretsManager
        region: us-east-1
        auth:
          serviceAccount:
            name: external-secrets-sa
  ```

### ✅ Secrets Rotation
- [ ] **Enable automatic secrets rotation**
  ```bash
  aws secretsmanager update-secret --secret-id SECRET_NAME \
    --description "Auto-rotating secret" \
    --rotation-lambda-arn LAMBDA_ARN \
    --rotation-rules AutomaticallyAfterDays=30
  ```

---

## 🖼️ Container Image Security

### ✅ Image Scanning
- [ ] **Enable ECR image scanning**
  ```bash
  aws ecr put-image-scanning-configuration \
    --repository-name REPO_NAME \
    --image-scanning-configuration scanOnPush=true
  ```

- [ ] **Enable enhanced scanning**
  ```bash
  aws ecr put-registry-scanning-configuration \
    --scan-type ENHANCED \
    --rules '[{"scanFrequency":"SCAN_ON_PUSH","repositoryFilters":[{"filter":"*","filterType":"WILDCARD"}]}]'
  ```

- [ ] **Review scan results**
  ```bash
  aws ecr describe-image-scan-findings \
    --repository-name REPO_NAME \
    --image-id imageTag=latest
  ```

### ✅ Image Security Policies
- [ ] **Use minimal base images**
  ```dockerfile
  FROM alpine:3.18
  # or
  FROM scratch
  ```

- [ ] **Implement image admission policies**
  ```yaml
  apiVersion: kyverno.io/v1
  kind: ClusterPolicy
  metadata:
    name: require-image-signature
  spec:
    validationFailureAction: enforce
    background: false
    rules:
    - name: check-image
      match:
        any:
        - resources:
            kinds:
            - Pod
      validate:
        message: "Images must be from trusted registry"
        pattern:
          spec:
            containers:
            - image: "123456789012.dkr.ecr.us-east-1.amazonaws.com/*"
  ```

### ✅ Runtime Security
- [ ] **Install Falco for runtime monitoring**
  ```bash
  helm repo add falcosecurity https://falcosecurity.github.io/charts
  helm install falco falcosecurity/falco
  ```

- [ ] **Configure Falco rules**
  ```yaml
  - rule: Detect crypto miners
    desc: Detect cryptocurrency miners
    condition: >
      spawned_process and
      (proc.name in (crypto_miners) or
       proc.cmdline contains "stratum")
    output: >
      Cryptocurrency mining detected (user=%user.name command=%proc.cmdline
      container=%container.name image=%container.image.repository)
    priority: CRITICAL
  ```

---

## 📊 Monitoring and Logging

### ✅ CloudWatch Integration
- [ ] **Enable Container Insights**
  ```bash
  curl https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml | sed "s/{{cluster_name}}/CLUSTER_NAME/" | kubectl apply -f -
  ```

- [ ] **Verify CloudWatch agent is running**
  ```bash
  kubectl get pods -n amazon-cloudwatch
  ```

### ✅ Audit Logging
- [ ] **Enable audit logging**
  ```bash
  aws eks update-cluster-config --name CLUSTER_NAME \
    --logging '{"clusterLogging":[{"types":["audit"],"enabled":true}]}'
  ```

- [ ] **Review audit logs**
  ```bash
  aws logs filter-log-events \
    --log-group-name /aws/eks/CLUSTER_NAME/cluster \
    --filter-pattern "{ $.verb = \"create\" || $.verb = \"delete\" }"
  ```

### ✅ Security Monitoring
- [ ] **Enable GuardDuty for EKS**
  ```bash
  aws guardduty create-detector --enable
  aws guardduty update-detector --detector-id DETECTOR_ID \
    --kubernetes '{"AuditLogs":{"Enable":true}}'
  ```

- [ ] **Set up CloudWatch alarms**
  ```bash
  aws cloudwatch put-metric-alarm \
    --alarm-name "EKS-Failed-Logins" \
    --alarm-description "Alert on failed authentication attempts" \
    --metric-name "cluster.authentication.failure" \
    --namespace "AWS/EKS" \
    --statistic Sum \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold
  ```

---

## 🔍 Compliance and Governance

### ✅ Security Benchmarks
- [ ] **Run CIS Kubernetes Benchmark**
  ```bash
  kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job-eks.yaml
  kubectl logs job/kube-bench
  ```

- [ ] **Install and run kube-hunter**
  ```bash
  kubectl create -f https://raw.githubusercontent.com/aquasecurity/kube-hunter/master/job.yaml
  kubectl logs job/kube-hunter
  ```

### ✅ Policy as Code
- [ ] **Install OPA Gatekeeper**
  ```bash
  kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.14/deploy/gatekeeper.yaml
  ```

- [ ] **Implement security policies**
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
    targets:
      - target: admission.k8s.gatekeeper.sh
        rego: |
          package k8srequiredsecuritycontext
          violation[{"msg": msg}] {
            container := input.review.object.spec.containers[_]
            not container.securityContext.runAsNonRoot
            msg := "Container must run as non-root user"
          }
  ```

### ✅ AWS Config Rules
- [ ] **Enable AWS Config**
  ```bash
  aws configservice put-configuration-recorder \
    --configuration-recorder name=default,roleARN=CONFIG_ROLE_ARN \
    --recording-group allSupported=true,includeGlobalResourceTypes=true
  ```

- [ ] **Deploy EKS-specific Config rules**
  ```bash
  aws configservice put-config-rule \
    --config-rule '{
      "ConfigRuleName": "eks-cluster-supported-version",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "EKS_CLUSTER_SUPPORTED_VERSION"
      }
    }'
  ```

---

## 🚀 Node Group Security

### ✅ Node Configuration
- [ ] **Use managed node groups**
  ```bash
  aws eks create-nodegroup \
    --cluster-name CLUSTER_NAME \
    --nodegroup-name managed-nodes \
    --subnets subnet-12345 subnet-67890 \
    --instance-types m5.large \
    --ami-type AL2_x86_64 \
    --node-role NODE_INSTANCE_ROLE_ARN
  ```

- [ ] **Enable IMDSv2 only**
  ```yaml
  LaunchTemplate:
    MetadataOptions:
      HttpTokens: required
      HttpPutResponseHopLimit: 2
  ```

- [ ] **Disable SSH access or restrict it**
  ```bash
  aws eks create-nodegroup \
    --cluster-name CLUSTER_NAME \
    --nodegroup-name secure-nodes \
    --remote-access '{"ec2SshKey":"","sourceSecurityGroups":[]}'
  ```

### ✅ Node Updates
- [ ] **Keep nodes updated**
  ```bash
  aws eks update-nodegroup-version \
    --cluster-name CLUSTER_NAME \
    --nodegroup-name NODEGROUP_NAME
  ```

- [ ] **Enable automatic updates**
  ```yaml
  updateConfig:
    maxUnavailable: 1
  ```

---

## 📋 Security Validation Commands

### Daily Security Checks
```bash
#!/bin/bash
# EKS Security Daily Check Script

echo "=== EKS Cluster Security Check ==="

# Check cluster version
echo "Cluster Version:"
aws eks describe-cluster --name $CLUSTER_NAME --query cluster.version

# Check endpoint configuration
echo "Endpoint Configuration:"
aws eks describe-cluster --name $CLUSTER_NAME \
  --query 'cluster.resourcesVpcConfig.{Private:endpointConfigPrivateAccess,Public:endpointConfigPublicAccess}'

# Check encryption
echo "Encryption Status:"
aws eks describe-cluster --name $CLUSTER_NAME --query cluster.encryptionConfig

# Check logging
echo "Logging Configuration:"
aws eks describe-cluster --name $CLUSTER_NAME --query cluster.logging

# Check for pods running as root
echo "Pods running as root:"
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.securityContext.runAsUser}{"\n"}{end}' | grep -E '\t0$|\t$'

# Check for privileged pods
echo "Privileged pods:"
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.containers[*].securityContext.privileged}{"\n"}{end}' | grep true

# Check network policies
echo "Network Policies:"
kubectl get networkpolicies --all-namespaces

# Check RBAC
echo "ClusterRoleBindings with system:masters:"
kubectl get clusterrolebindings -o json | jq -r '.items[] | select(.roleRef.name=="cluster-admin") | .metadata.name'
```

### Weekly Security Audit
```bash
#!/bin/bash
# Weekly EKS Security Audit

# Run kube-bench
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job-eks.yaml
sleep 30
kubectl logs job/kube-bench > kube-bench-results.txt

# Check for image vulnerabilities
aws ecr describe-image-scan-findings --repository-name $REPO_NAME --image-id imageTag=latest

# Review IAM roles and policies
aws iam list-roles --query 'Roles[?contains(RoleName, `eks`) || contains(RoleName, `EKS`)]'

# Check GuardDuty findings
aws guardduty list-findings --detector-id $DETECTOR_ID --finding-criteria '{"Criterion":{"service.serviceName":{"Eq":["EKS"]}}}'

# Audit secrets
kubectl get secrets --all-namespaces -o json | jq -r '.items[] | select(.type != "kubernetes.io/service-account-token") | "\(.metadata.namespace)/\(.metadata.name)"'
```

---

## 🎯 Priority Security Actions

### Immediate (Day 1)
1. Enable private endpoint access
2. Enable envelope encryption
3. Enable all CloudWatch logging
4. Set up IRSA
5. Configure aws-auth with least privilege

### Week 1
1. Implement network policies
2. Configure pod security standards
3. Set up image scanning
4. Enable Container Insights
5. Run security benchmarks

### Month 1
1. Implement comprehensive RBAC
2. Set up external secrets management
3. Deploy runtime security monitoring
4. Establish security monitoring and alerting
5. Create incident response procedures

### Ongoing
1. Regular security audits
2. Keep cluster and nodes updated
3. Review and rotate secrets
4. Monitor security findings
5. Update security policies

---

## 📚 AWS Documentation References

- [EKS Security Best Practices](https://docs.aws.amazon.com/eks/latest/userguide/security.html)
- [EKS Cluster Endpoint Access Control](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html)
- [IAM Roles for Service Accounts](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
- [EKS Pod Security Policy](https://docs.aws.amazon.com/eks/latest/userguide/pod-security-policy.html)
- [EKS Network Security](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html)
- [EKS Logging and Monitoring](https://docs.aws.amazon.com/eks/latest/userguide/logging-monitoring.html)

This checklist ensures comprehensive security coverage for your EKS cluster following AWS official recommendations and industry best practices.