# On-Premise to AWS Migration Guide: EC2 & EKS

A comprehensive guide for migrating applications from on-premise infrastructure to AWS EC2 or EKS with real-world examples and best practices.

## 📋 Migration Assessment Framework

### 1. Discovery & Assessment Phase

#### Application Inventory
```bash
# Document current infrastructure
- Application dependencies
- Database connections
- Network configurations
- Storage requirements
- Performance baselines
- Security requirements
```

#### Migration Readiness Assessment
| Factor | EC2 Migration | EKS Migration |
|--------|---------------|---------------|
| **Application Architecture** | Monolithic/Legacy apps | Microservices/Cloud-native |
| **Containerization** | Not required | Required |
| **Complexity** | Low-Medium | Medium-High |
| **Timeline** | 2-8 weeks | 3-6 months |
| **Skills Required** | Basic AWS | Kubernetes + AWS |

## 🎯 Migration Strategies

### Strategy 1: Lift & Shift (Rehost) - EC2
**Best for**: Legacy applications, quick migration, minimal changes

### Strategy 2: Containerize & Modernize - EKS
**Best for**: Applications ready for microservices, long-term scalability

## 📊 Real-World Migration Examples

### Example 1: E-commerce Application (Lift & Shift to EC2)

#### Current On-Premise Setup
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Server    │    │  App Server     │    │   Database      │
│   (Apache)      │────│   (Tomcat)      │────│   (MySQL)       │
│   2 vCPU, 4GB   │    │   4 vCPU, 8GB   │    │   4 vCPU, 16GB  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### Target AWS Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      ALB        │    │      EC2        │    │      RDS        │
│   (Load Bal.)   │────│   (t3.large)    │────│   (db.t3.large) │
│                 │    │   Multi-AZ      │    │   Multi-AZ      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### Migration Steps

**Phase 1: Pre-Migration (Week 1)**
```bash
# 1. AWS Account Setup
aws configure
aws sts get-caller-identity

# 2. VPC Creation
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=migration-vpc}]'

# 3. Create subnets
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24 --availability-zone us-east-1a
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.2.0/24 --availability-zone us-east-1b
```

**Phase 2: Database Migration (Week 2)**
```bash
# 1. Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier ecommerce-db \
  --db-instance-class db.t3.large \
  --engine mysql \
  --master-username admin \
  --master-user-password SecurePass123! \
  --allocated-storage 100 \
  --vpc-security-group-ids sg-xxx \
  --db-subnet-group-name default

# 2. Database migration using DMS
aws dms create-replication-instance \
  --replication-instance-identifier ecommerce-migration \
  --replication-instance-class dms.t3.micro
```

**Phase 3: Application Migration (Week 3-4)**
```bash
# 1. Create AMI from on-premise server
# Use AWS Server Migration Service (SMS) or manual process

# 2. Launch EC2 instances
aws ec2 run-instances \
  --image-id ami-xxx \
  --count 2 \
  --instance-type t3.large \
  --key-name my-key \
  --security-group-ids sg-xxx \
  --subnet-id subnet-xxx \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ecommerce-app}]'

# 3. Create Application Load Balancer
aws elbv2 create-load-balancer \
  --name ecommerce-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx
```

### Example 2: Microservices Application (Containerize to EKS)

#### Current On-Premise Setup
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Service  │    │  Order Service  │    │ Payment Service │
│   (Java Spring) │    │   (Node.js)     │    │   (Python)      │
│   VM: 2GB RAM   │    │   VM: 1GB RAM   │    │   VM: 1GB RAM   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### Target EKS Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                        EKS Cluster                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ User Service│  │Order Service│  │Payment Svc  │        │
│  │   (Pod)     │  │   (Pod)     │  │   (Pod)     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

#### Migration Steps

**Phase 1: Containerization (Month 1)**
```dockerfile
# User Service Dockerfile
FROM openjdk:11-jre-slim
COPY target/user-service.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app.jar"]
```

```dockerfile
# Order Service Dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

**Phase 2: EKS Cluster Setup (Month 2)**
```bash
# 1. Create EKS cluster
eksctl create cluster \
  --name microservices-cluster \
  --version 1.28 \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 4

# 2. Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name microservices-cluster
```

**Phase 3: Application Deployment (Month 3)**
```yaml
# user-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: your-account.dkr.ecr.us-east-1.amazonaws.com/user-service:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user-service
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

## 🔧 Migration Tools & Services

### AWS Native Tools
```bash
# 1. AWS Application Migration Service (MGN)
aws mgn initialize-service

# 2. AWS Database Migration Service (DMS)
aws dms describe-replication-instances

# 3. AWS Server Migration Service (SMS)
aws sms get-servers

# 4. AWS DataSync for file transfers
aws datasync create-location-s3 --s3-bucket-arn arn:aws:s3:::my-bucket
```

### Third-Party Tools
- **CloudEndure**: Continuous replication
- **Velostrata**: Live migration
- **Carbonite**: Data protection during migration

## 📈 Migration Timeline & Phases

### EC2 Migration Timeline (6-8 weeks)
```
Week 1-2: Assessment & Planning
├── Infrastructure discovery
├── Dependency mapping
├── AWS account setup
└── Network design

Week 3-4: Database Migration
├── RDS setup
├── Data migration (DMS)
├── Testing & validation
└── Cutover planning

Week 5-6: Application Migration
├── Server replication
├── Application deployment
├── Load balancer setup
└── DNS cutover

Week 7-8: Optimization & Go-Live
├── Performance tuning
├── Security hardening
├── Monitoring setup
└── Production cutover
```

### EKS Migration Timeline (3-6 months)
```
Month 1: Containerization
├── Application analysis
├── Dockerfile creation
├── Container registry setup
└── Local testing

Month 2: EKS Setup
├── Cluster provisioning
├── Networking configuration
├── Security setup (RBAC)
└── CI/CD pipeline

Month 3: Deployment & Testing
├── Kubernetes manifests
├── Service mesh (optional)
├── Monitoring & logging
└── Load testing

Month 4-6: Optimization & Production
├── Auto-scaling setup
├── Cost optimization
├── Security hardening
└── Production deployment
```

## 🛡️ Security Considerations

### Network Security
```bash
# Security Groups for EC2
aws ec2 create-security-group \
  --group-name web-tier-sg \
  --description "Web tier security group"

aws ec2 authorize-security-group-ingress \
  --group-id sg-xxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0
```

### EKS Security
```yaml
# Network Policy for EKS
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

## 💰 Cost Optimization

### EC2 Cost Optimization
```bash
# Reserved Instances
aws ec2 describe-reserved-instances-offerings \
  --instance-type t3.large \
  --product-description "Linux/UNIX"

# Spot Instances for non-critical workloads
aws ec2 request-spot-instances \
  --spot-price "0.05" \
  --instance-count 2 \
  --type "one-time" \
  --launch-specification file://specification.json
```

### EKS Cost Optimization
```yaml
# Cluster Autoscaler
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  template:
    spec:
      containers:
      - image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.21.0
        name: cluster-autoscaler
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/microservices-cluster
```

## 📊 Monitoring & Observability

### CloudWatch Setup
```bash
# Create custom metrics
aws cloudwatch put-metric-data \
  --namespace "Migration/Performance" \
  --metric-data MetricName=ResponseTime,Value=200,Unit=Milliseconds
```

### EKS Monitoring
```yaml
# Prometheus & Grafana setup
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
```

## 🚨 Rollback Strategy

### EC2 Rollback Plan
```bash
# 1. DNS rollback
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789 \
  --change-batch file://rollback-dns.json

# 2. Database rollback using point-in-time recovery
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier prod-db \
  --target-db-instance-identifier rollback-db \
  --restore-time 2024-01-15T10:00:00Z
```

### EKS Rollback Plan
```bash
# Kubernetes rollback
kubectl rollout undo deployment/user-service
kubectl rollout status deployment/user-service
```

## 📋 Migration Checklist

### Pre-Migration
- [ ] Complete application discovery
- [ ] Document dependencies
- [ ] Create AWS account and setup billing alerts
- [ ] Design target architecture
- [ ] Setup VPC and networking
- [ ] Create security groups and NACLs
- [ ] Plan DNS migration strategy

### During Migration
- [ ] Migrate databases first
- [ ] Test database connectivity
- [ ] Migrate applications in phases
- [ ] Update application configurations
- [ ] Test each component thoroughly
- [ ] Setup monitoring and alerting

### Post-Migration
- [ ] Performance validation
- [ ] Security audit
- [ ] Cost optimization review
- [ ] Documentation update
- [ ] Team training
- [ ] Decommission on-premise infrastructure

## 🎯 Success Metrics

### Technical Metrics
- **Availability**: Target 99.9% uptime
- **Performance**: <200ms response time
- **Scalability**: Handle 2x current load
- **Recovery**: RTO <1 hour, RPO <15 minutes

### Business Metrics
- **Cost Reduction**: 20-30% infrastructure savings
- **Time to Market**: 50% faster deployments
- **Operational Efficiency**: 40% reduction in manual tasks

## 🔗 Additional Resources

- [AWS Migration Hub](https://aws.amazon.com/migration-hub/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)
- [AWS Migration Whitepaper](https://docs.aws.amazon.com/whitepapers/latest/aws-migration-whitepaper/aws-migration-whitepaper.html)

---

**Note**: This guide provides a framework for migration planning. Always conduct thorough testing in non-production environments before implementing in production. Consider engaging AWS Professional Services or certified partners for complex migrations.