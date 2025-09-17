# EKS PVC & EBS CSI Driver - Complete Mastery Guide

## Table of Contents
1. [EBS CSI Driver Overview](#ebs-csi-driver-overview)
2. [Installation & Configuration](#installation--configuration)
3. [Storage Classes Deep Dive](#storage-classes-deep-dive)
4. [CSI Dynamic Provisioning Parameters](#csi-dynamic-provisioning-parameters)
5. [Reclaim Policies & Volume Lifecycle](#reclaim-policies--volume-lifecycle)
6. [Volume Modes & Block Devices](#volume-modes--block-devices)
7. [Access Modes & Volume Binding](#access-modes--volume-binding)
8. [Volume Limits & Node Constraints](#volume-limits--node-constraints)
9. [CSI Security & Secrets](#csi-security--secrets)
10. [PVC Scenarios & Use Cases](#pvc-scenarios--use-cases)
11. [Volume Types & Performance](#volume-types--performance)
12. [Volume Attachment & Scheduling](#volume-attachment--scheduling)
13. [Backup & Disaster Recovery](#backup--disaster-recovery)
14. [Monitoring & Metrics](#monitoring--metrics)
15. [Cost Management & Quotas](#cost-management--quotas)
16. [Advanced Features](#advanced-features)
17. [Troubleshooting & Monitoring](#troubleshooting--monitoring)
18. [Best Practices](#best-practices)

---

## EBS CSI Driver Overview

### What is EBS CSI Driver?
```
┌─────────────────────────────────────────────────────────────┐
│                    EBS CSI Architecture                     │
├─────────────────────────────────────────────────────────────┤
│ Kubernetes Layer    │ CSI Layer           │ AWS Layer       │
│ - PVC               │ - CSI Controller    │ - EBS Volumes   │
│ - PV                │ - CSI Node Plugin   │ - EC2 API       │
│ - StorageClass      │ - CSI Driver        │ - IAM Roles     │
└─────────────────────────────────────────────────────────────┘
```

### EBS Volume Types Comparison
| Volume Type | Use Case | IOPS | Throughput | Size Range | Cost |
|-------------|----------|------|------------|------------|------|
| **gp3** | General purpose | 3,000-16,000 | 125-1,000 MB/s | 1 GiB - 16 TiB | Low |
| **gp2** | General purpose | 100-16,000 | 128-250 MB/s | 1 GiB - 16 TiB | Low |
| **io1** | High IOPS | 100-64,000 | 1,000 MB/s | 4 GiB - 16 TiB | High |
| **io2** | High IOPS | 100-256,000 | 4,000 MB/s | 4 GiB - 64 TiB | High |
| **st1** | Throughput optimized | 500 | 500 MB/s | 125 GiB - 16 TiB | Medium |
| **sc1** | Cold storage | 250 | 250 MB/s | 125 GiB - 16 TiB | Low |

---

## Installation & Configuration

### 1. EBS CSI Driver Installation

#### Method 1: EKS Add-on (Recommended)
```bash
# Check if add-on is available
aws eks describe-addon-versions --addon-name aws-ebs-csi-driver

# Install EBS CSI driver as EKS add-on
aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name aws-ebs-csi-driver \
  --addon-version v1.25.0-eksbuild.1 \
  --service-account-role-arn arn:aws:iam::123456789012:role/AmazonEKS_EBS_CSI_DriverRole

# Verify installation
kubectl get pods -n kube-system -l app=ebs-csi-controller
kubectl get pods -n kube-system -l app=ebs-csi-node
```

#### Method 2: Helm Installation
```bash
# Add AWS EBS CSI driver Helm repository
helm repo add aws-ebs-csi-driver https://kubernetes-sigs.github.io/aws-ebs-csi-driver
helm repo update

# Install with custom values
helm install aws-ebs-csi-driver aws-ebs-csi-driver/aws-ebs-csi-driver \
  --namespace kube-system \
  --set controller.serviceAccount.annotations."eks\.amazonaws\.com/role-arn"="arn:aws:iam::123456789012:role/AmazonEKS_EBS_CSI_DriverRole"
```

#### Method 3: kubectl Installation
```bash
# Install using kubectl
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=release-1.25"
```

### 2. IAM Role Configuration

#### EBS CSI Driver IAM Policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateSnapshot",
        "ec2:AttachVolume",
        "ec2:DetachVolume",
        "ec2:ModifyVolume",
        "ec2:DescribeAvailabilityZones",
        "ec2:DescribeInstances",
        "ec2:DescribeSnapshots",
        "ec2:DescribeTags",
        "ec2:DescribeVolumes",
        "ec2:DescribeVolumesModifications"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateTags"
      ],
      "Resource": [
        "arn:aws:ec2:*:*:volume/*",
        "arn:aws:ec2:*:*:snapshot/*"
      ],
      "Condition": {
        "StringEquals": {
          "ec2:CreateAction": [
            "CreateVolume",
            "CreateSnapshot"
          ]
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DeleteTags"
      ],
      "Resource": [
        "arn:aws:ec2:*:*:volume/*",
        "arn:aws:ec2:*:*:snapshot/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateVolume"
      ],
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "aws:RequestedRegion": "*"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DeleteVolume"
      ],
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "ec2:ResourceTag/ebs.csi.aws.com/cluster": "true"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DeleteSnapshot"
      ],
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "ec2:ResourceTag/CSIVolumeSnapshotName": "*"
        }
      }
    }
  ]
}
```

#### Create IAM Role with IRSA:
```bash
# Create IAM role for service account
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster my-cluster \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/Amazon_EBS_CSI_DriverPolicy \
  --approve
```

### 3. Verification Commands

#### Check Driver Installation:
```bash
# Verify CSI driver pods
kubectl get pods -n kube-system | grep ebs-csi

# Check CSI driver version
kubectl get csidriver ebs.csi.aws.com -o yaml

# Verify storage classes
kubectl get storageclass

# Check CSI nodes
kubectl get csinodes
```

---

## Storage Classes Deep Dive

### 1. Default Storage Classes

#### GP3 Storage Class (Recommended):
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

#### GP2 Storage Class:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp2
provisioner: ebs.csi.aws.com
parameters:
  type: gp2
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

### 2. High-Performance Storage Classes

#### IO1 for High IOPS:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: io1-high-iops
provisioner: ebs.csi.aws.com
parameters:
  type: io1
  iops: "10000"
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Retain
```

#### IO2 for Ultra High IOPS:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: io2-ultra-high-iops
provisioner: ebs.csi.aws.com
parameters:
  type: io2
  iops: "50000"
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Retain
```

### 3. Throughput-Optimized Storage Classes

#### ST1 for Big Data:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: st1-throughput
provisioner: ebs.csi.aws.com
parameters:
  type: st1
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

#### SC1 for Cold Storage:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: sc1-cold
provisioner: ebs.csi.aws.com
parameters:
  type: sc1
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

### 4. Advanced Storage Class Parameters

#### Multi-AZ Storage Class:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-multi-az
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "4000"
  throughput: "250"
  encrypted: "true"
  # Allow volumes in multiple AZs
allowedTopologies:
- matchLabelExpressions:
  - key: topology.ebs.csi.aws.com/zone
    values:
    - us-west-2a
    - us-west-2b
    - us-west-2c
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

#### KMS Encrypted Storage Class:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-kms-encrypted
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

---

## CSI Dynamic Provisioning Parameters

### 1. Complete EBS CSI Parameters Reference

#### All Available Parameters:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-complete-params
provisioner: ebs.csi.aws.com
parameters:
  # Volume Type (Required)
  type: "gp3"  # gp2, gp3, io1, io2, st1, sc1
  
  # Performance Parameters
  iops: "4000"              # IOPS for gp3, io1, io2
  throughput: "250"         # Throughput for gp3 (MiB/s)
  
  # Encryption
  encrypted: "true"         # Enable encryption
  kmsKeyId: "alias/ebs-key" # KMS key for encryption
  
  # Multi-Attach (io1/io2 only)
  multiAttach: "true"       # Enable multi-attach
  
  # Tagging
  tagSpecification_1: "Name=MyVolume"
  tagSpecification_2: "Environment=Production"
  tagSpecification_3: "Team=Platform"
  tagSpecification_4: "Project=MyApp"
  tagSpecification_5: "CostCenter=Engineering"
  
  # File System
  fsType: "ext4"            # ext4, ext3, xfs
  
  # Block Size (for file system creation)
  blockSize: "4096"         # Block size in bytes
  
  # Inode Settings
  inodeSize: "256"          # Inode size for ext4
  bytesPerInode: "16384"    # Bytes per inode
  
  # Mount Options
  mountOptions: "noatime,nodiratime"
  
# Volume Binding and Reclaim
volumeBindingMode: WaitForFirstConsumer  # Immediate, WaitForFirstConsumer
allowVolumeExpansion: true               # Enable volume expansion
reclaimPolicy: Delete                    # Delete, Retain
```

### 2. Volume Type Specific Parameters

#### GP3 Optimized Configuration:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-optimized
provisioner: ebs.csi.aws.com
parameters:
  type: "gp3"
  # GP3 allows independent IOPS and throughput tuning
  iops: "16000"        # Max: 16,000 IOPS
  throughput: "1000"   # Max: 1,000 MiB/s
  encrypted: "true"
  fsType: "ext4"
  # GP3 specific optimizations
  blockSize: "4096"
  mountOptions: "noatime,nodiratime,data=ordered"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

#### IO2 Block Express Configuration:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: io2-block-express
provisioner: ebs.csi.aws.com
parameters:
  type: "io2"
  # IO2 Block Express automatically enabled for >64,000 IOPS
  iops: "100000"       # Up to 256,000 IOPS
  encrypted: "true"
  fsType: "xfs"        # XFS recommended for high IOPS
  # IO2 optimizations
  mountOptions: "noatime,largeio,inode64,allocsize=16m"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Retain  # Retain for high-value data
```

#### ST1 Throughput Optimized:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: st1-big-data
provisioner: ebs.csi.aws.com
parameters:
  type: "st1"
  encrypted: "true"
  fsType: "xfs"        # XFS better for large files
  # ST1 optimizations for sequential workloads
  blockSize: "65536"   # Larger block size for throughput
  mountOptions: "noatime,largeio,swalloc,allocsize=64m"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

### 3. Encryption Options

#### Default AWS Managed Encryption:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: encrypted-default
provisioner: ebs.csi.aws.com
parameters:
  type: "gp3"
  encrypted: "true"  # Uses AWS managed key
volumeBindingMode: WaitForFirstConsumer
```

#### Customer Managed KMS Key:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: encrypted-custom-kms
provisioner: ebs.csi.aws.com
parameters:
  type: "gp3"
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012"
volumeBindingMode: WaitForFirstConsumer
```

#### KMS Key Alias:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: encrypted-alias
provisioner: ebs.csi.aws.com
parameters:
  type: "gp3"
  encrypted: "true"
  kmsKeyId: "alias/ebs-encryption-key"
volumeBindingMode: WaitForFirstConsumer
```

### 4. Advanced Tagging Strategies

#### Comprehensive Tagging:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: tagged-storage
provisioner: ebs.csi.aws.com
parameters:
  type: "gp3"
  encrypted: "true"
  # Cost allocation tags
  tagSpecification_1: "CostCenter=Engineering"
  tagSpecification_2: "Project=${pvc.namespace}"
  tagSpecification_3: "Application=${pvc.name}"
  # Operational tags
  tagSpecification_4: "Environment=Production"
  tagSpecification_5: "Backup=Required"
  tagSpecification_6: "Retention=90days"
  # Security tags
  tagSpecification_7: "DataClassification=Internal"
  tagSpecification_8: "Compliance=SOX"
volumeBindingMode: WaitForFirstConsumer
```

#### Dynamic Tagging with PVC Metadata:
```yaml
# Note: These are examples of tag patterns
# Actual dynamic tagging requires custom controllers
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: dynamic-tagged
provisioner: ebs.csi.aws.com
parameters:
  type: "gp3"
  encrypted: "true"
  # These would be populated by a custom controller
  tagSpecification_1: "kubernetes.io/cluster/my-cluster=owned"
  tagSpecification_2: "kubernetes.io/namespace=${pvc.namespace}"
  tagSpecification_3: "kubernetes.io/pvc-name=${pvc.name}"
  tagSpecification_4: "kubernetes.io/created-by=ebs-csi-driver"
volumeBindingMode: WaitForFirstConsumer
```

### 5. File System Options

#### EXT4 Optimized:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ext4-optimized
provisioner: ebs.csi.aws.com
parameters:
  type: "gp3"
  fsType: "ext4"
  # EXT4 specific parameters
  blockSize: "4096"      # 4KB blocks (default)
  inodeSize: "256"       # Inode size
  bytesPerInode: "16384" # Bytes per inode (affects max files)
  # EXT4 mount options
  mountOptions: "noatime,nodiratime,data=ordered,barrier=1"
volumeBindingMode: WaitForFirstConsumer
```

#### XFS Optimized:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: xfs-optimized
provisioner: ebs.csi.aws.com
parameters:
  type: "io2"
  fsType: "xfs"
  # XFS mount options for high performance
  mountOptions: "noatime,nodiratime,largeio,inode64,swalloc,allocsize=16m"
volumeBindingMode: WaitForFirstConsumer
```

### 6. Performance Tuning Parameters

#### Database Optimized Storage:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: database-optimized
provisioner: ebs.csi.aws.com
parameters:
  type: "io2"
  iops: "20000"
  encrypted: "true"
  fsType: "ext4"
  # Database optimizations
  blockSize: "4096"      # 4KB for database workloads
  mountOptions: "noatime,nodiratime,data=writeback,barrier=0,commit=30"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Retain
```

#### Big Data Optimized Storage:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: bigdata-optimized
provisioner: ebs.csi.aws.com
parameters:
  type: "st1"
  encrypted: "true"
  fsType: "xfs"
  # Big data optimizations
  blockSize: "65536"     # 64KB blocks for large files
  mountOptions: "noatime,largeio,swalloc,allocsize=64m,logbsize=256k"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### 7. Multi-Attach Configuration

#### Multi-Attach with Raw Block:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: multi-attach-raw
provisioner: ebs.csi.aws.com
parameters:
  type: "io1"
  iops: "5000"
  multiAttach: "true"
  encrypted: "true"
  # No fsType for raw block devices
volumeBindingMode: Immediate  # Required for multi-attach
allowVolumeExpansion: false   # Not supported with multi-attach

---
# Raw block PVC
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: raw-block-pvc
spec:
  accessModes:
    - ReadWriteMany
  volumeMode: Block  # Raw block device
  storageClassName: multi-attach-raw
  resources:
    requests:
      storage: 100Gi
```

### 8. Topology and Zone Constraints

#### Zone-Specific Provisioning:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: zone-constrained
provisioner: ebs.csi.aws.com
parameters:
  type: "gp3"
  encrypted: "true"
# Restrict to specific zones
allowedTopologies:
- matchLabelExpressions:
  - key: topology.ebs.csi.aws.com/zone
    values:
    - us-west-2a
    - us-west-2b
volumeBindingMode: WaitForFirstConsumer
```

#### Multi-Zone with Preferences:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: multi-zone-preferred
provisioner: ebs.csi.aws.com
parameters:
  type: "gp3"
  encrypted: "true"
# Allow all zones but prefer specific ones
allowedTopologies:
- matchLabelExpressions:
  - key: topology.ebs.csi.aws.com/zone
    values:
    - us-west-2a  # Preferred
    - us-west-2b  # Preferred
    - us-west-2c  # Fallback
volumeBindingMode: WaitForFirstConsumer
```

---

## Reclaim Policies & Volume Lifecycle

### 1. Reclaim Policy Options

#### Delete Policy (Default):
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: delete-policy
provisioner: ebs.csi.aws.com
parameters:
  type: "gp3"
  encrypted: "true"
reclaimPolicy: Delete  # Volume deleted when PVC is deleted
volumeBindingMode: WaitForFirstConsumer

# Lifecycle:
# PVC Created → PV Created → Pod Uses Volume → PVC Deleted → PV Deleted → EBS Volume Deleted
```

#### Retain Policy:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: retain-policy
provisioner: ebs.csi.aws.com
parameters:
  type: "io2"
  iops: "10000"
  encrypted: "true"
reclaimPolicy: Retain  # Volume preserved when PVC is deleted
volumeBindingMode: WaitForFirstConsumer

# Lifecycle:
# PVC Created → PV Created → Pod Uses Volume → PVC Deleted → PV Remains → Manual Cleanup Required
```

### 2. Volume Lifecycle Management

#### Complete Lifecycle Example:
```yaml
# Step 1: Create PVC
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: lifecycle-demo
  annotations:
    # Lifecycle annotations
    volume.beta.kubernetes.io/storage-provisioner: ebs.csi.aws.com
    pv.kubernetes.io/bind-completed: "yes"
    pv.kubernetes.io/bound-by-controller: "yes"
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 10Gi

---
# Step 2: Pod uses PVC
apiVersion: v1
kind: Pod
metadata:
  name: lifecycle-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: lifecycle-demo
```

#### Monitoring Volume Lifecycle:
```bash
#!/bin/bash
# monitor-volume-lifecycle.sh

PVC_NAME="lifecycle-demo"
NAMESPACE="default"

echo "=== Volume Lifecycle Monitor ==="

# Check PVC status
echo "1. PVC Status:"
kubectl get pvc $PVC_NAME -n $NAMESPACE -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,VOLUME:.spec.volumeName,CAPACITY:.status.capacity.storage

# Get PV details
PV_NAME=$(kubectl get pvc $PVC_NAME -n $NAMESPACE -o jsonpath='{.spec.volumeName}')
if [ -n "$PV_NAME" ]; then
  echo "\n2. PV Details:"
  kubectl get pv $PV_NAME -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,RECLAIM:.spec.persistentVolumeReclaimPolicy,STORAGECLASS:.spec.storageClassName
  
  # Get EBS volume ID
  VOLUME_ID=$(kubectl get pv $PV_NAME -o jsonpath='{.spec.csi.volumeHandle}')
  echo "\n3. EBS Volume: $VOLUME_ID"
  
  # Check AWS EBS volume
  aws ec2 describe-volumes --volume-ids $VOLUME_ID --query 'Volumes[0].{State:State,Size:Size,VolumeType:VolumeType,Encrypted:Encrypted}' --output table
fi

# Check pod using the volume
echo "\n4. Pods using this PVC:"
kubectl get pods -n $NAMESPACE -o json | jq -r --arg pvc "$PVC_NAME" '.items[] | select(.spec.volumes[]?.persistentVolumeClaim.claimName == $pvc) | .metadata.name'
```

### 3. Volume Deletion Scenarios

#### Graceful Pod Termination:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: graceful-termination
spec:
  terminationGracePeriodSeconds: 30  # Allow time for cleanup
  containers:
  - name: app
    image: myapp:v1.0.0
    lifecycle:
      preStop:
        exec:
          command:
          - /bin/sh
          - -c
          - |
            echo "Flushing data to disk..."
            sync
            echo "Closing database connections..."
            # Application-specific cleanup
            /app/graceful-shutdown.sh
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: app-data
```

#### Force Delete Protection:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: protected-pvc
  finalizers:
  - kubernetes.io/pvc-protection  # Prevents deletion while in use
  annotations:
    # Custom protection annotation
    pvc.kubernetes.io/deletion-protection: "true"
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: retain-policy  # Use retain policy for important data
  resources:
    requests:
      storage: 100Gi
```

### 4. Volume Cleanup Automation

#### Cleanup CronJob:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: volume-cleanup
  namespace: kube-system
spec:
  schedule: "0 2 * * 0"  # Weekly on Sunday at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: volume-cleanup-sa
          containers:
          - name: cleanup
            image: bitnami/kubectl:latest
            command:
            - /bin/sh
            - -c
            - |
              echo "Starting volume cleanup..."
              
              # Find Released PVs (from deleted PVCs with Retain policy)
              kubectl get pv --no-headers | grep Released | while read pv rest; do
                echo "Found released PV: $pv"
                
                # Get volume age
                AGE=$(kubectl get pv $pv -o jsonpath='{.metadata.creationTimestamp}')
                AGE_SECONDS=$(date -d "$AGE" +%s)
                CURRENT_SECONDS=$(date +%s)
                DAYS_OLD=$(( (CURRENT_SECONDS - AGE_SECONDS) / 86400 ))
                
                # Delete PVs older than 30 days
                if [ $DAYS_OLD -gt 30 ]; then
                  echo "Deleting PV $pv (${DAYS_OLD} days old)"
                  kubectl delete pv $pv
                fi
              done
              
              # Find unattached EBS volumes
              aws ec2 describe-volumes \
                --filters "Name=state,Values=available" \
                --query 'Volumes[?Tags[?Key==`kubernetes.io/cluster/my-cluster`]].{VolumeId:VolumeId,CreateTime:CreateTime}' \
                --output text | while read volume_id create_time; do
                
                # Calculate age
                CREATE_SECONDS=$(date -d "$create_time" +%s)
                CURRENT_SECONDS=$(date +%s)
                DAYS_OLD=$(( (CURRENT_SECONDS - CREATE_SECONDS) / 86400 ))
                
                # Delete volumes older than 7 days
                if [ $DAYS_OLD -gt 7 ]; then
                  echo "Deleting unattached volume $volume_id (${DAYS_OLD} days old)"
                  aws ec2 delete-volume --volume-id $volume_id
                fi
              done
              
              echo "Volume cleanup completed"
          restartPolicy: OnFailure
```

### 5. Volume State Transitions

#### PV State Machine:
```
Available → Bound → Released → Failed
    ↑         ↓         ↓        ↓
    └─────────┴─────────┴────────┘
                 (Reclaim)

States:
- Available: PV is available for binding
- Bound: PV is bound to a PVC
- Released: PVC was deleted, but PV not yet reclaimed
- Failed: Automatic reclamation failed
```

#### PVC State Machine:
```
Pending → Bound → Terminating
    ↓       ↓         ↓
   Lost    Lost    Deleted

States:
- Pending: PVC created, waiting for PV
- Bound: PVC bound to PV
- Terminating: PVC deletion in progress
- Lost: PV lost or unavailable
```

### 6. Emergency Volume Recovery

#### Recover from Snapshot:
```yaml
# Create PVC from snapshot
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: recovered-volume
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 100Gi
  dataSource:
    name: emergency-snapshot-20231201
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

#### Manual PV Recovery:
```yaml
# Manually create PV for existing EBS volume
apiVersion: v1
kind: PersistentVolume
metadata:
  name: recovered-pv
spec:
  capacity:
    storage: 100Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: gp3
  csi:
    driver: ebs.csi.aws.com
    volumeHandle: vol-1234567890abcdef0  # Existing EBS volume
    fsType: ext4
```

---

## Volume Modes & Block Devices

### 1. Volume Mode Overview

#### Filesystem vs Block Mode:
| Volume Mode | Description | Use Cases | Mount Type |
|-------------|-------------|-----------|------------|
| **Filesystem** | Volume formatted with file system | Applications, databases, general storage | Directory mount |
| **Block** | Raw block device access | High-performance databases, custom file systems | Block device |

### 2. Filesystem Volume Mode (Default)

#### Standard Filesystem PVC:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: filesystem-pvc
spec:
  accessModes:
    - ReadWriteOnce
  volumeMode: Filesystem  # Default, can be omitted
  storageClassName: gp3
  resources:
    requests:
      storage: 20Gi

---
apiVersion: v1
kind: Pod
metadata:
  name: filesystem-pod
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /usr/share/nginx/html  # Directory mount
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: filesystem-pvc
```

### 3. Block Volume Mode

#### Raw Block Device PVC:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: block-pvc
spec:
  accessModes:
    - ReadWriteOnce
  volumeMode: Block  # Raw block device
  storageClassName: io2-ultra-high-iops
  resources:
    requests:
      storage: 100Gi

---
apiVersion: v1
kind: Pod
metadata:
  name: block-pod
spec:
  containers:
  - name: database
    image: postgres:14
    volumeDevices:  # Note: volumeDevices, not volumeMounts
    - name: data
      devicePath: /dev/xvda  # Block device path
    env:
    - name: PGDATA
      value: "/dev/xvda"  # PostgreSQL can use raw device
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: block-pvc
```

### 4. Block Device Use Cases

#### High-Performance Database:
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql-block
spec:
  serviceName: mysql
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: password
        # Custom script to format and use block device
        command:
        - /bin/bash
        - -c
        - |
          # Format block device if not already formatted
          if ! blkid /dev/xvda; then
            mkfs.ext4 /dev/xvda
          fi
          
          # Mount the device
          mkdir -p /var/lib/mysql-data
          mount /dev/xvda /var/lib/mysql-data
          chown mysql:mysql /var/lib/mysql-data
          
          # Start MySQL
          docker-entrypoint.sh mysqld --datadir=/var/lib/mysql-data
        volumeDevices:
        - name: mysql-data
          devicePath: /dev/xvda
        securityContext:
          privileged: true  # Required for block device access
  volumeClaimTemplates:
  - metadata:
      name: mysql-data
    spec:
      accessModes: ["ReadWriteOnce"]
      volumeMode: Block
      storageClassName: io2-ultra-high-iops
      resources:
        requests:
          storage: 200Gi
```

#### Custom File System:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: custom-filesystem
spec:
  template:
    spec:
      containers:
      - name: formatter
        image: ubuntu:22.04
        command:
        - /bin/bash
        - -c
        - |
          apt-get update && apt-get install -y xfsprogs
          
          # Create XFS filesystem with custom parameters
          mkfs.xfs -f -b size=4096 -s size=4096 -i size=512 /dev/xvda
          
          # Mount and test
          mkdir -p /mnt/test
          mount /dev/xvda /mnt/test
          
          # Create test data
          echo "Custom XFS filesystem created" > /mnt/test/test.txt
          
          # Show filesystem info
          xfs_info /mnt/test
          
          umount /mnt/test
        volumeDevices:
        - name: raw-storage
          devicePath: /dev/xvda
        securityContext:
          privileged: true
      volumes:
      - name: raw-storage
        persistentVolumeClaim:
          claimName: raw-block-pvc
      restartPolicy: Never

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: raw-block-pvc
spec:
  accessModes:
    - ReadWriteOnce
  volumeMode: Block
  storageClassName: gp3
  resources:
    requests:
      storage: 50Gi
```

### 5. Block vs Filesystem Performance

#### Performance Comparison Test:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: block-vs-filesystem-benchmark
spec:
  parallelism: 2
  template:
    spec:
      containers:
      - name: benchmark
        image: ljishen/fio
        env:
        - name: TEST_TYPE
          value: "filesystem"  # Will be overridden
        command:
        - /bin/bash
        - -c
        - |
          if [ "$TEST_TYPE" = "block" ]; then
            # Test raw block device
            fio --name=block-test --ioengine=libaio --iodepth=32 \
                --rw=randwrite --bs=4k --direct=1 --size=10G \
                --numjobs=4 --runtime=60 --group_reporting \
                --filename=/dev/xvda
          else
            # Test filesystem
            fio --name=fs-test --ioengine=libaio --iodepth=32 \
                --rw=randwrite --bs=4k --direct=1 --size=10G \
                --numjobs=4 --runtime=60 --group_reporting \
                --filename=/data/testfile
          fi
        volumeMounts:
        - name: fs-storage
          mountPath: /data
        volumeDevices:
        - name: block-storage
          devicePath: /dev/xvda
      volumes:
      - name: fs-storage
        persistentVolumeClaim:
          claimName: filesystem-benchmark-pvc
      - name: block-storage
        persistentVolumeClaim:
          claimName: block-benchmark-pvc
      restartPolicy: Never
```

---

## Volume Limits & Node Constraints

### 1. EBS Volume Limits per Instance Type

#### Instance Type Volume Limits:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ebs-volume-limits
data:
  limits.yaml: |
    # EBS Volume Attachment Limits by Instance Type
    instance_limits:
      # General Purpose
      t3.micro: 12
      t3.small: 12
      t3.medium: 12
      t3.large: 12
      t3.xlarge: 12
      t3.2xlarge: 12
      
      # Compute Optimized
      c5.large: 12
      c5.xlarge: 12
      c5.2xlarge: 12
      c5.4xlarge: 15
      c5.9xlarge: 15
      c5.12xlarge: 15
      c5.18xlarge: 15
      c5.24xlarge: 15
      
      # Memory Optimized
      r5.large: 12
      r5.xlarge: 12
      r5.2xlarge: 12
      r5.4xlarge: 15
      r5.8xlarge: 15
      r5.12xlarge: 15
      r5.16xlarge: 15
      r5.24xlarge: 15
      
      # Storage Optimized
      i3.large: 12
      i3.xlarge: 12
      i3.2xlarge: 12
      i3.4xlarge: 15
      i3.8xlarge: 15
      i3.16xlarge: 15
      
    # Note: Nitro instances support more attachments
    # Non-Nitro instances are limited to fewer attachments
```

### 2. Node Selector for Volume Constraints

#### Storage-Optimized Node Selector:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: high-iops-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: io2-ultra-high-iops
  resources:
    requests:
      storage: 1Ti

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: high-iops-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: high-iops-app
  template:
    metadata:
      labels:
        app: high-iops-app
    spec:
      nodeSelector:
        node.kubernetes.io/instance-type: r5.24xlarge  # High attachment limit
        topology.kubernetes.io/zone: us-west-2a
      containers:
      - name: app
        image: database:v1.0.0
        volumeMounts:
        - name: data
          mountPath: /data
        resources:
          requests:
            memory: "32Gi"
            cpu: "8000m"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: high-iops-pvc
```

### 3. Volume Attachment Monitoring

#### Check Volume Attachments per Node:
```bash
#!/bin/bash
# check-volume-attachments.sh

echo "=== EBS Volume Attachments per Node ==="

# Get all nodes
kubectl get nodes --no-headers -o custom-columns=NAME:.metadata.name,INSTANCE-TYPE:.metadata.labels.node\.kubernetes\.io/instance-type | while read node instance_type; do
  echo "\nNode: $node ($instance_type)"
  
  # Get instance ID
  INSTANCE_ID=$(kubectl get node $node -o jsonpath='{.spec.providerID}' | cut -d'/' -f5)
  
  # Count attached volumes
  VOLUME_COUNT=$(aws ec2 describe-volumes --filters "Name=attachment.instance-id,Values=$INSTANCE_ID" --query 'length(Volumes)')
  
  echo "  Instance ID: $INSTANCE_ID"
  echo "  Attached Volumes: $VOLUME_COUNT"
  
  # Get volume details
  aws ec2 describe-volumes --filters "Name=attachment.instance-id,Values=$INSTANCE_ID" \
    --query 'Volumes[*].{VolumeId:VolumeId,Size:Size,Type:VolumeType,Device:Attachments[0].Device}' \
    --output table
done
```

### 4. Volume Limit Enforcement

#### Admission Controller for Volume Limits:
```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionWebhook
metadata:
  name: volume-limit-validator
webhooks:
- name: volume-limit.example.com
  clientConfig:
    service:
      name: volume-limit-webhook
      namespace: kube-system
      path: "/validate"
  rules:
  - operations: ["CREATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  admissionReviewVersions: ["v1", "v1beta1"]

---
# Webhook service implementation (pseudo-code)
apiVersion: v1
kind: ConfigMap
metadata:
  name: volume-limit-logic
data:
  webhook.py: |
    def validate_pod(pod):
        # Count PVCs in pod
        pvc_count = len([v for v in pod.spec.volumes if v.persistent_volume_claim])
        
        # Get node selector or affinity
        instance_type = get_target_instance_type(pod)
        
        # Check against limits
        max_volumes = get_instance_volume_limit(instance_type)
        
        if pvc_count > max_volumes:
            return {"allowed": False, "message": f"Pod requests {pvc_count} volumes but instance type {instance_type} supports max {max_volumes}"}
        
        return {"allowed": True}
```

---

## CSI Security & Secrets

### 1. CSI Driver Security Context

#### Secure CSI Driver Configuration:
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: ebs-csi-node-secure
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: ebs-csi-node
  template:
    metadata:
      labels:
        app: ebs-csi-node
    spec:
      serviceAccountName: ebs-csi-node-sa
      securityContext:
        runAsNonRoot: false  # CSI requires root for device operations
        runAsUser: 0
        fsGroup: 0
      containers:
      - name: ebs-plugin
        image: amazon/aws-ebs-csi-driver:v1.25.0
        securityContext:
          privileged: true  # Required for device mounting
          allowPrivilegeEscalation: true
          readOnlyRootFilesystem: true
          capabilities:
            add:
            - SYS_ADMIN  # Required for mount operations
        env:
        - name: CSI_ENDPOINT
          value: unix:///csi/csi.sock
        - name: CSI_NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        volumeMounts:
        - name: kubelet-dir
          mountPath: /var/lib/kubelet
          mountPropagation: Bidirectional
        - name: plugin-dir
          mountPath: /csi
        - name: device-dir
          mountPath: /dev
      volumes:
      - name: kubelet-dir
        hostPath:
          path: /var/lib/kubelet
          type: Directory
      - name: plugin-dir
        hostPath:
          path: /var/lib/kubelet/plugins/ebs.csi.aws.com/
          type: DirectoryOrCreate
      - name: device-dir
        hostPath:
          path: /dev
          type: Directory
```

### 2. Encryption Key Management

#### KMS Key Policy for EBS CSI:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Enable IAM User Permissions",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:root"
      },
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "Allow EBS CSI Driver",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/AmazonEKS_EBS_CSI_DriverRole"
      },
      "Action": [
        "kms:Decrypt",
        "kms:GenerateDataKey",
        "kms:CreateGrant",
        "kms:DescribeKey"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": "ec2.us-west-2.amazonaws.com"
        }
      }
    }
  ]
}
```

### 3. Pod Security Standards with Volumes

#### Restricted Pod with Volume:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod-with-volume
  namespace: restricted-namespace
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
    volumeMounts:
    - name: data
      mountPath: /data
    - name: tmp
      mountPath: /tmp
    - name: cache
      mountPath: /var/cache/nginx
    resources:
      limits:
        memory: "128Mi"
        cpu: "100m"
      requests:
        memory: "64Mi"
        cpu: "50m"
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: secure-app-data
  - name: tmp
    emptyDir: {}
  - name: cache
    emptyDir: {}
```

### 4. Volume Encryption Validation

#### Encryption Verification Job:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: verify-encryption
spec:
  template:
    spec:
      containers:
      - name: verify
        image: amazon/aws-cli:latest
        command:
        - /bin/bash
        - -c
        - |
          # Get volume ID from PV
          VOLUME_ID=$(kubectl get pv $PV_NAME -o jsonpath='{.spec.csi.volumeHandle}')
          
          # Check encryption status
          ENCRYPTED=$(aws ec2 describe-volumes --volume-ids $VOLUME_ID --query 'Volumes[0].Encrypted')
          KMS_KEY=$(aws ec2 describe-volumes --volume-ids $VOLUME_ID --query 'Volumes[0].KmsKeyId' --output text)
          
          echo "Volume ID: $VOLUME_ID"
          echo "Encrypted: $ENCRYPTED"
          echo "KMS Key: $KMS_KEY"
          
          if [ "$ENCRYPTED" = "true" ]; then
            echo "✅ Volume is encrypted"
          else
            echo "❌ Volume is NOT encrypted"
            exit 1
          fi
        env:
        - name: PV_NAME
          value: "pvc-12345678-1234-1234-1234-123456789012"
      restartPolicy: Never
```

---

## Access Modes & Volume Binding

### 1. Access Modes Overview

#### EBS Volume Access Modes Support:
| Access Mode | EBS Support | Description | Use Cases |
|-------------|-------------|-------------|----------|
| **ReadWriteOnce (RWO)** | ✅ Supported | Volume mounted as read-write by single node | Databases, single-pod apps |
| **ReadOnlyMany (ROX)** | ❌ Not Supported | Volume mounted as read-only by many nodes | N/A for EBS |
| **ReadWriteMany (RWX)** | ⚠️ Limited* | Volume mounted as read-write by many nodes | Multi-attach volumes only |
| **ReadWriteOncePod (RWOP)** | ✅ Supported | Volume mounted as read-write by single pod | Kubernetes 1.22+ |

*Multi-attach only available for io1 and io2 volume types

### 2. ReadWriteOnce (RWO) - Most Common

#### Single Pod Database:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-storage
  namespace: database
spec:
  accessModes:
    - ReadWriteOnce  # Only one node can mount this volume
  storageClassName: gp3
  resources:
    requests:
      storage: 20Gi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
  namespace: database
spec:
  replicas: 1  # Must be 1 for RWO
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: password
        volumeMounts:
        - name: mysql-data
          mountPath: /var/lib/mysql
        ports:
        - containerPort: 3306
      volumes:
      - name: mysql-data
        persistentVolumeClaim:
          claimName: mysql-storage
```

#### StatefulSet with RWO (Recommended Pattern):
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
  namespace: database
spec:
  serviceName: postgresql
  replicas: 3
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:14
        env:
        - name: POSTGRES_DB
          value: myapp
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgresql-storage
          mountPath: /var/lib/postgresql/data
        ports:
        - containerPort: 5432
  volumeClaimTemplates:
  - metadata:
      name: postgresql-storage
    spec:
      accessModes: ["ReadWriteOnce"]  # Each pod gets its own volume
      storageClassName: io1-high-iops
      resources:
        requests:
          storage: 50Gi
```

### 3. ReadWriteOncePod (RWOP) - Kubernetes 1.22+

#### Enhanced Security with RWOP:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: secure-app-storage
spec:
  accessModes:
    - ReadWriteOncePod  # Only one pod can mount this volume
  storageClassName: gp3
  resources:
    requests:
      storage: 10Gi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-app
spec:
  replicas: 1  # Enforced by RWOP
  selector:
    matchLabels:
      app: secure-app
  template:
    metadata:
      labels:
        app: secure-app
    spec:
      containers:
      - name: app
        image: secure-app:v1.0.0
        volumeMounts:
        - name: app-data
          mountPath: /data
      volumes:
      - name: app-data
        persistentVolumeClaim:
          claimName: secure-app-storage
```

### 4. ReadWriteMany (RWX) - Multi-Attach Volumes

#### Multi-Attach Storage Class (io1/io2 only):
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: io1-multi-attach
provisioner: ebs.csi.aws.com
parameters:
  type: io1
  iops: "2000"
  encrypted: "true"
  multiAttach: "true"  # Enable multi-attach
volumeBindingMode: Immediate  # Must be Immediate for multi-attach
allowVolumeExpansion: false   # Not supported with multi-attach
```

#### Shared Storage Example:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-storage
spec:
  accessModes:
    - ReadWriteMany  # Multiple pods can mount this volume
  storageClassName: io1-multi-attach
  resources:
    requests:
      storage: 100Gi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shared-app
spec:
  replicas: 3  # Multiple replicas can share the volume
  selector:
    matchLabels:
      app: shared-app
  template:
    metadata:
      labels:
        app: shared-app
    spec:
      containers:
      - name: app
        image: shared-app:v1.0.0
        volumeMounts:
        - name: shared-data
          mountPath: /shared
        # Important: Application must handle concurrent access
        env:
        - name: ENABLE_FILE_LOCKING
          value: "true"
      volumes:
      - name: shared-data
        persistentVolumeClaim:
          claimName: shared-storage
```

#### Multi-Attach Limitations and Considerations:
```yaml
# WARNING: Multi-attach volumes require careful application design
apiVersion: v1
kind: ConfigMap
metadata:
  name: multi-attach-guidelines
data:
  guidelines.md: |
    # Multi-Attach Volume Guidelines
    
    ## Supported Volume Types:
    - io1 volumes only
    - io2 volumes only
    - NOT supported: gp2, gp3, st1, sc1
    
    ## Limitations:
    - Maximum 16 instances per volume
    - Volume expansion not supported
    - Snapshot while attached not recommended
    - Application must handle concurrent access
    
    ## File System Considerations:
    - Use cluster-aware file systems (GFS2, OCFS2)
    - Implement application-level locking
    - Consider using raw block devices
    
    ## Use Cases:
    - Shared configuration data
    - Distributed databases (with proper clustering)
    - High-availability applications
```

### 5. Volume Binding Modes

#### WaitForFirstConsumer (Recommended):
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-wait-for-consumer
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer  # Volume created when pod is scheduled
allowVolumeExpansion: true

# Benefits:
# - Volume created in same AZ as pod
# - Prevents cross-AZ mounting issues
# - Better resource utilization
```

#### Immediate Binding:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-immediate
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
volumeBindingMode: Immediate  # Volume created immediately when PVC is created
allowVolumeExpansion: true

# Use cases:
# - Pre-provisioning volumes
# - Multi-attach volumes (required)
# - When you need volumes ready before pod scheduling
```

### 6. Access Mode Validation Examples

#### Testing Access Modes:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: access-mode-test
spec:
  template:
    spec:
      containers:
      - name: test
        image: busybox
        command:
        - /bin/sh
        - -c
        - |
          echo "Testing volume access modes..."
          
          # Test write access
          echo "test data" > /data/test.txt
          if [ $? -eq 0 ]; then
            echo "✅ Write access: SUCCESS"
          else
            echo "❌ Write access: FAILED"
          fi
          
          # Test read access
          cat /data/test.txt
          if [ $? -eq 0 ]; then
            echo "✅ Read access: SUCCESS"
          else
            echo "❌ Read access: FAILED"
          fi
          
          # Check file system
          df -h /data
          mount | grep /data
          
          sleep 30
        volumeMounts:
        - name: test-volume
          mountPath: /data
      volumes:
      - name: test-volume
        persistentVolumeClaim:
          claimName: test-pvc
      restartPolicy: Never

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 1Gi
```

### 7. Common Access Mode Scenarios

#### Scenario 1: Single Application with Persistent Data
```yaml
# Use Case: Web application with file uploads
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: webapp-uploads
spec:
  accessModes:
    - ReadWriteOnce  # Single pod access
  storageClassName: gp3
  resources:
    requests:
      storage: 50Gi
```

#### Scenario 2: Database Cluster (Each Pod Needs Own Storage)
```yaml
# Use Case: PostgreSQL cluster with separate storage per instance
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-cluster
spec:
  serviceName: postgres
  replicas: 3
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]  # Each pod gets its own volume
      storageClassName: io1-high-iops
      resources:
        requests:
          storage: 100Gi
```

#### Scenario 3: Shared Configuration (Multi-Attach)
```yaml
# Use Case: Shared configuration files across multiple pods
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-config
spec:
  accessModes:
    - ReadWriteMany  # Multiple pods can access
  storageClassName: io1-multi-attach
  resources:
    requests:
      storage: 10Gi
```

### 8. Access Mode Troubleshooting

#### Common Issues and Solutions:
```bash
# Issue: Pod stuck in pending due to access mode mismatch
kubectl describe pod my-pod
# Look for: "pod has unbound immediate PersistentVolumeClaims"

# Check PVC access modes
kubectl get pvc my-pvc -o yaml | grep accessModes -A 3

# Check if volume supports requested access mode
kubectl describe pv my-pv | grep "Access Modes"

# For multi-attach issues:
aws ec2 describe-volumes --volume-ids vol-1234567890abcdef0 \
  --query 'Volumes[0].MultiAttachEnabled'

# Check volume attachment count
aws ec2 describe-volumes --volume-ids vol-1234567890abcdef0 \
  --query 'Volumes[0].Attachments[*].InstanceId'
```

#### Access Mode Validation Script:
```bash
#!/bin/bash
# validate-access-modes.sh

PVC_NAME=$1
NAMESPACE=${2:-default}

echo "Validating access modes for PVC: $PVC_NAME in namespace: $NAMESPACE"

# Get PVC access modes
ACCESS_MODES=$(kubectl get pvc $PVC_NAME -n $NAMESPACE -o jsonpath='{.spec.accessModes[*]}')
echo "Requested access modes: $ACCESS_MODES"

# Get bound PV
PV_NAME=$(kubectl get pvc $PVC_NAME -n $NAMESPACE -o jsonpath='{.spec.volumeName}')
if [ -n "$PV_NAME" ]; then
  echo "Bound to PV: $PV_NAME"
  
  # Get PV access modes
  PV_ACCESS_MODES=$(kubectl get pv $PV_NAME -o jsonpath='{.spec.accessModes[*]}')
  echo "PV access modes: $PV_ACCESS_MODES"
  
  # Get volume ID
  VOLUME_ID=$(kubectl get pv $PV_NAME -o jsonpath='{.spec.csi.volumeHandle}')
  echo "EBS Volume ID: $VOLUME_ID"
  
  # Check multi-attach if RWX is requested
  if [[ "$ACCESS_MODES" == *"ReadWriteMany"* ]]; then
    MULTI_ATTACH=$(aws ec2 describe-volumes --volume-ids $VOLUME_ID --query 'Volumes[0].MultiAttachEnabled')
    echo "Multi-attach enabled: $MULTI_ATTACH"
  fi
else
  echo "PVC is not bound to any PV"
fi
```

---

## PVC Scenarios & Use Cases

### 1. Basic PVC Examples

#### Simple Application Storage:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-storage
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 10Gi
```

#### Database Storage:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-storage
  namespace: database
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: io1-high-iops
  resources:
    requests:
      storage: 100Gi
```

### 2. StatefulSet with PVC Templates

#### PostgreSQL StatefulSet:
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
  namespace: database
spec:
  serviceName: postgresql
  replicas: 3
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:14
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: myapp
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgresql-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
  volumeClaimTemplates:
  - metadata:
      name: postgresql-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: io1-high-iops
      resources:
        requests:
          storage: 50Gi
```

#### MongoDB Replica Set:
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
  namespace: database
spec:
  serviceName: mongodb
  replicas: 3
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:6.0
        ports:
        - containerPort: 27017
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          valueFrom:
            secretKeyRef:
              name: mongodb-secret
              key: username
        - name: MONGO_INITDB_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mongodb-secret
              key: password
        volumeMounts:
        - name: mongodb-storage
          mountPath: /data/db
        - name: mongodb-config
          mountPath: /data/configdb
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      volumes:
      - name: mongodb-config
        emptyDir: {}
  volumeClaimTemplates:
  - metadata:
      name: mongodb-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: gp3
      resources:
        requests:
          storage: 100Gi
```

### 3. Multi-Container Pod with Shared Storage

#### Application with Sidecar:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-sidecar
spec:
  replicas: 2
  selector:
    matchLabels:
      app: app-with-sidecar
  template:
    metadata:
      labels:
        app: app-with-sidecar
    spec:
      containers:
      - name: main-app
        image: myapp:v1.0.0
        volumeMounts:
        - name: shared-storage
          mountPath: /app/data
        - name: logs-storage
          mountPath: /app/logs
      - name: log-processor
        image: log-processor:v1.0.0
        volumeMounts:
        - name: logs-storage
          mountPath: /logs
        - name: processed-logs
          mountPath: /processed
      volumes:
      - name: shared-storage
        persistentVolumeClaim:
          claimName: app-shared-storage
      - name: logs-storage
        persistentVolumeClaim:
          claimName: app-logs-storage
      - name: processed-logs
        persistentVolumeClaim:
          claimName: processed-logs-storage

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-shared-storage
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 20Gi

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-logs-storage
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: st1-throughput
  resources:
    requests:
      storage: 500Gi

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: processed-logs-storage
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: sc1-cold
  resources:
    requests:
      storage: 1Ti
```

### 4. Data Processing Workloads

#### Spark Job with Large Dataset:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: spark-data-storage
  namespace: data-processing
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: st1-throughput
  resources:
    requests:
      storage: 2Ti

---
apiVersion: batch/v1
kind: Job
metadata:
  name: spark-data-processing
  namespace: data-processing
spec:
  template:
    spec:
      containers:
      - name: spark-driver
        image: spark:3.4.0
        command: ["/opt/spark/bin/spark-submit"]
        args:
        - "--class"
        - "com.example.DataProcessor"
        - "/app/data-processor.jar"
        volumeMounts:
        - name: data-storage
          mountPath: /data
        resources:
          requests:
            memory: "4Gi"
            cpu: "2000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
      volumes:
      - name: data-storage
        persistentVolumeClaim:
          claimName: spark-data-storage
      restartPolicy: Never
```

### 5. Backup and Restore Scenarios

#### Application with Backup Sidecar:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-backup
spec:
  replicas: 1
  selector:
    matchLabels:
      app: app-with-backup
  template:
    metadata:
      labels:
        app: app-with-backup
    spec:
      containers:
      - name: application
        image: myapp:v1.0.0
        volumeMounts:
        - name: app-data
          mountPath: /app/data
      - name: backup-agent
        image: backup-agent:v1.0.0
        env:
        - name: BACKUP_SCHEDULE
          value: "0 2 * * *"  # Daily at 2 AM
        - name: S3_BUCKET
          value: "my-app-backups"
        volumeMounts:
        - name: app-data
          mountPath: /data
          readOnly: true
      volumes:
      - name: app-data
        persistentVolumeClaim:
          claimName: app-data-storage

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data-storage
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 50Gi
```

---

## Volume Attachment & Scheduling

### 1. Volume Attachment Lifecycle

#### Attachment State Machine:
```
Detached → Attaching → Attached → Detaching → Detached
    ↑         ↓         ↓         ↓         ↓
    └─────────┴─────────┴─────────┴─────────┘
                    (Error States)

States:
- Detached: Volume not attached to any instance
- Attaching: Volume attachment in progress
- Attached: Volume successfully attached
- Detaching: Volume detachment in progress
```

#### Monitor Attachment Process:
```bash
#!/bin/bash
# monitor-volume-attachment.sh

VOLUME_ID=$1
if [ -z "$VOLUME_ID" ]; then
  echo "Usage: $0 <volume-id>"
  exit 1
fi

echo "Monitoring volume attachment: $VOLUME_ID"

while true; do
  # Get volume state
  STATE=$(aws ec2 describe-volumes --volume-ids $VOLUME_ID --query 'Volumes[0].State' --output text)
  
  # Get attachment info
  ATTACHMENT_INFO=$(aws ec2 describe-volumes --volume-ids $VOLUME_ID \
    --query 'Volumes[0].Attachments[0].{State:State,InstanceId:InstanceId,Device:Device}' \
    --output json)
  
  echo "$(date): Volume State: $STATE"
  echo "Attachment Info: $ATTACHMENT_INFO"
  
  if [ "$STATE" = "in-use" ]; then
    echo "✅ Volume successfully attached"
    break
  elif [ "$STATE" = "error" ]; then
    echo "❌ Volume attachment failed"
    break
  fi
  
  sleep 5
done
```

### 2. Cross-AZ Mounting Issues

#### Zone Mismatch Problem:
```yaml
# This will FAIL - Pod and Volume in different AZs
apiVersion: v1
kind: Pod
metadata:
  name: cross-az-fail
spec:
  nodeSelector:
    topology.kubernetes.io/zone: us-west-2a  # Pod in 2a
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: volume-in-zone-b  # Volume in 2b - WILL FAIL
```

#### Solution - WaitForFirstConsumer:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: zone-aware
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer  # Volume created in same AZ as pod
allowVolumeExpansion: true

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: zone-aware-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: zone-aware  # Uses WaitForFirstConsumer
  resources:
    requests:
      storage: 10Gi

---
apiVersion: v1
kind: Pod
metadata:
  name: zone-aware-pod
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: zone-aware-pvc  # Volume will be created in same AZ
```

### 3. Pod Scheduling with Volume Constraints

#### Volume Topology Spread:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: distributed-app
spec:
  replicas: 6
  selector:
    matchLabels:
      app: distributed-app
  template:
    metadata:
      labels:
        app: distributed-app
    spec:
      topologySpreadConstraints:
      - maxSkew: 2
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: distributed-app
      containers:
      - name: app
        image: myapp:v1.0.0
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: app-data-${POD_NAME}  # Each pod gets its own PVC
```

#### Node Affinity with Volume Requirements:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: volume-affinity-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: node.kubernetes.io/instance-type
            operator: In
            values: ["r5.2xlarge", "r5.4xlarge", "r5.8xlarge"]  # High attachment limit
          - key: topology.kubernetes.io/zone
            operator: In
            values: ["us-west-2a", "us-west-2b"]  # Specific zones
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
          - key: node-type
            operator: In
            values: ["storage-optimized"]
  containers:
  - name: app
    image: database:v1.0.0
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: high-iops-data
```

### 4. Volume Attachment Troubleshooting

#### Attachment Failure Diagnosis:
```bash
#!/bin/bash
# diagnose-attachment-failure.sh

POD_NAME=$1
NAMESPACE=${2:-default}

echo "=== Volume Attachment Diagnosis ==="
echo "Pod: $POD_NAME in namespace: $NAMESPACE"

# Get pod details
echo "\n1. Pod Status:"
kubectl get pod $POD_NAME -n $NAMESPACE -o wide

# Check pod events
echo "\n2. Pod Events:"
kubectl describe pod $POD_NAME -n $NAMESPACE | grep -A 20 "Events:"

# Get PVCs used by pod
echo "\n3. PVCs used by pod:"
PVCS=$(kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.spec.volumes[*].persistentVolumeClaim.claimName}' | tr ' ' '\n' | grep -v '^$')

for pvc in $PVCS; do
  echo "\nPVC: $pvc"
  kubectl get pvc $pvc -n $NAMESPACE -o wide
  
  # Get PV details
  PV_NAME=$(kubectl get pvc $pvc -n $NAMESPACE -o jsonpath='{.spec.volumeName}')
  if [ -n "$PV_NAME" ]; then
    echo "PV: $PV_NAME"
    kubectl get pv $PV_NAME -o wide
    
    # Get volume ID and check AWS
    VOLUME_ID=$(kubectl get pv $PV_NAME -o jsonpath='{.spec.csi.volumeHandle}')
    echo "EBS Volume: $VOLUME_ID"
    
    # Check volume state in AWS
    aws ec2 describe-volumes --volume-ids $VOLUME_ID \
      --query 'Volumes[0].{State:State,Attachments:Attachments}' \
      --output json
  fi
done

# Check node capacity
echo "\n4. Node Volume Capacity:"
NODE_NAME=$(kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.spec.nodeName}')
if [ -n "$NODE_NAME" ]; then
  echo "Node: $NODE_NAME"
  kubectl describe node $NODE_NAME | grep -A 10 "Allocated resources:"
fi

# Check CSI driver logs
echo "\n5. CSI Driver Logs (last 50 lines):"
kubectl logs -n kube-system -l app=ebs-csi-node --tail=50 | grep -i error
```

---

## Backup & Disaster Recovery

### 1. Volume Snapshots

#### Snapshot Class Configuration:
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: ebs-snapshot-class
  annotations:
    snapshot.storage.kubernetes.io/is-default-class: "true"
driver: ebs.csi.aws.com
deletionPolicy: Delete
parameters:
  # Snapshot tagging
  tagSpecification_1: "Name=k8s-snapshot-${snapshot.name}"
  tagSpecification_2: "Namespace=${snapshot.namespace}"
  tagSpecification_3: "SourcePVC=${sourcePVC.name}"
  tagSpecification_4: "CreatedBy=ebs-csi-driver"
  tagSpecification_5: "Environment=production"
```

#### Automated Backup CronJob:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: automated-volume-backup
  namespace: backup-system
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: volume-backup-sa
          containers:
          - name: backup
            image: bitnami/kubectl:latest
            command:
            - /bin/bash
            - -c
            - |
              echo "Starting automated volume backup..."
              
              # Get all PVCs with backup annotation
              kubectl get pvc --all-namespaces \
                -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.metadata.annotations.backup\.enabled}{"\n"}{end}' | \
                grep -E '\ttrue$' | while read namespace pvc_name _; do
                
                echo "Creating snapshot for PVC: $namespace/$pvc_name"
                
                # Create snapshot
                cat <<EOF | kubectl apply -f -
              apiVersion: snapshot.storage.k8s.io/v1
              kind: VolumeSnapshot
              metadata:
                name: ${pvc_name}-$(date +%Y%m%d-%H%M%S)
                namespace: $namespace
                labels:
                  backup.type: automated
                  source.pvc: $pvc_name
              spec:
                volumeSnapshotClassName: ebs-snapshot-class
                source:
                  persistentVolumeClaimName: $pvc_name
              EOF
                
                # Wait for snapshot to be ready
                kubectl wait --for=condition=ReadyToUse \
                  volumesnapshot/${pvc_name}-$(date +%Y%m%d-%H%M%S) \
                  -n $namespace --timeout=300s
              done
              
              # Cleanup old snapshots (keep 7 days)
              kubectl get volumesnapshots --all-namespaces \
                -o json | jq -r '.items[] | select(.metadata.labels."backup.type" == "automated") | select(.metadata.creationTimestamp < "'$(date -d '7 days ago' --iso-8601)'") | "\(.metadata.namespace) \(.metadata.name)"' | \
                while read namespace snapshot_name; do
                  echo "Deleting old snapshot: $namespace/$snapshot_name"
                  kubectl delete volumesnapshot $snapshot_name -n $namespace
                done
              
              echo "Backup completed!"
          restartPolicy: OnFailure
```

#### Point-in-Time Recovery:
```yaml
# Original PVC with data
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: original-data
  annotations:
    backup.enabled: "true"
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 100Gi

---
# Create snapshot for backup
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: backup-before-upgrade
spec:
  volumeSnapshotClassName: ebs-snapshot-class
  source:
    persistentVolumeClaimName: original-data

---
# Restore from snapshot
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: restored-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 100Gi  # Must be >= original size
  dataSource:
    name: backup-before-upgrade
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

### 2. Cross-Region Backup

#### Cross-Region Snapshot Copy:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cross-region-backup
spec:
  schedule: "0 3 * * 0"  # Weekly on Sunday at 3 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cross-region-backup
            image: amazon/aws-cli:latest
            command:
            - /bin/bash
            - -c
            - |
              SOURCE_REGION="us-west-2"
              DEST_REGION="us-east-1"
              
              echo "Starting cross-region backup from $SOURCE_REGION to $DEST_REGION"
              
              # Get snapshots from last 24 hours
              aws ec2 describe-snapshots --region $SOURCE_REGION \
                --owner-ids self \
                --filters "Name=tag:kubernetes.io/cluster/my-cluster,Values=owned" \
                --query 'Snapshots[?StartTime>=`'$(date -d '1 day ago' --iso-8601)'`].SnapshotId' \
                --output text | tr '\t' '\n' | while read snapshot_id; do
                
                if [ -n "$snapshot_id" ]; then
                  echo "Copying snapshot $snapshot_id to $DEST_REGION"
                  
                  # Copy snapshot to destination region
                  NEW_SNAPSHOT_ID=$(aws ec2 copy-snapshot \
                    --region $DEST_REGION \
                    --source-region $SOURCE_REGION \
                    --source-snapshot-id $snapshot_id \
                    --description "Cross-region backup of $snapshot_id" \
                    --query 'SnapshotId' --output text)
                  
                  # Tag the new snapshot
                  aws ec2 create-tags --region $DEST_REGION \
                    --resources $NEW_SNAPSHOT_ID \
                    --tags Key=Name,Value="backup-$snapshot_id" \
                           Key=SourceRegion,Value=$SOURCE_REGION \
                           Key=BackupType,Value=cross-region
                  
                  echo "Created backup snapshot: $NEW_SNAPSHOT_ID"
                fi
              done
            env:
            - name: AWS_DEFAULT_REGION
              value: us-west-2
          restartPolicy: OnFailure
```

### 3. Velero Integration

#### Velero with EBS CSI:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: velero-ebs-config
  namespace: velero
data:
  config.yaml: |
    # Velero configuration for EBS CSI
    apiVersion: v1
    kind: Config
    metadata:
      name: default
    backupStorageLocation:
      bucket: my-velero-backups
      provider: aws
      config:
        region: us-west-2
    volumeSnapshotLocation:
      provider: aws
      config:
        region: us-west-2
        # Use EBS CSI snapshots
        enableSharedConfig: true

---
apiVersion: velero.io/v1
kind: Backup
metadata:
  name: full-cluster-backup
  namespace: velero
spec:
  # Include all namespaces except system ones
  includedNamespaces:
  - production
  - staging
  - development
  
  # Backup PVCs using CSI snapshots
  defaultVolumesToRestic: false
  snapshotVolumes: true
  
  # Retention
  ttl: 720h  # 30 days
  
  # Storage location
  storageLocation: default
  volumeSnapshotLocations:
  - default
```

---

## Monitoring & Metrics

### 1. Volume Performance Metrics

#### CloudWatch Dashboard:
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/EBS", "VolumeReadOps", "VolumeId", "vol-1234567890abcdef0"],
          [".", "VolumeWriteOps", ".", "."],
          [".", "VolumeTotalReadTime", ".", "."],
          [".", "VolumeTotalWriteTime", ".", "."],
          [".", "VolumeQueueLength", ".", "."]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-west-2",
        "title": "EBS Volume Performance",
        "yAxis": {
          "left": {
            "min": 0
          }
        }
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/EBS", "VolumeThroughputPercentage", "VolumeId", "vol-1234567890abcdef0"],
          [".", "VolumeConsumedReadWriteOps", ".", "."]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-west-2",
        "title": "EBS Volume Utilization"
      }
    }
  ]
}
```

#### Prometheus Metrics Collection:
```yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: ebs-csi-metrics
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: ebs-csi-controller
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics

---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: ebs-volume-alerts
  namespace: kube-system
spec:
  groups:
  - name: ebs-volume.rules
    rules:
    - alert: HighVolumeLatency
      expr: aws_ebs_volume_total_read_time / aws_ebs_volume_read_ops > 0.1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High EBS volume read latency"
        description: "Volume {{ $labels.volume_id }} has high read latency: {{ $value }}s"
    
    - alert: VolumeQueueDepthHigh
      expr: aws_ebs_volume_queue_length > 32
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "EBS volume queue depth is high"
        description: "Volume {{ $labels.volume_id }} queue depth: {{ $value }}"
    
    - alert: VolumeIOPSUtilizationHigh
      expr: (aws_ebs_volume_read_ops + aws_ebs_volume_write_ops) / aws_ebs_volume_provisioned_iops > 0.8
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "EBS volume IOPS utilization is high"
        description: "Volume {{ $labels.volume_id }} IOPS utilization: {{ $value | humanizePercentage }}"
```

### 2. Capacity Management

#### Volume Usage Monitoring:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: volume-usage-report
spec:
  schedule: "0 6 * * *"  # Daily at 6 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: usage-reporter
            image: bitnami/kubectl:latest
            command:
            - /bin/bash
            - -c
            - |
              echo "=== Volume Usage Report $(date) ==="
              
              # Get all PVCs and their usage
              kubectl get pvc --all-namespaces -o json | jq -r '.items[] | "\(.metadata.namespace) \(.metadata.name) \(.spec.resources.requests.storage) \(.status.capacity.storage // "N/A")"' | \
              while read namespace pvc_name requested actual; do
                echo "\nPVC: $namespace/$pvc_name"
                echo "  Requested: $requested"
                echo "  Actual: $actual"
                
                # Get pod using this PVC
                POD=$(kubectl get pods -n $namespace -o json | jq -r --arg pvc "$pvc_name" '.items[] | select(.spec.volumes[]?.persistentVolumeClaim.claimName == $pvc) | .metadata.name' | head -1)
                
                if [ -n "$POD" ] && [ "$POD" != "null" ]; then
                  echo "  Used by pod: $POD"
                  
                  # Get actual disk usage from pod
                  USAGE=$(kubectl exec -n $namespace $POD -- df -h 2>/dev/null | grep -E '/data|/var/lib' | awk '{print $3 "/" $2 " (" $5 ")"}' | head -1)
                  if [ -n "$USAGE" ]; then
                    echo "  Disk usage: $USAGE"
                  fi
                else
                  echo "  Status: Unused"
                fi
              done
              
              # Summary statistics
              echo "\n=== Summary ==="
              TOTAL_PVCS=$(kubectl get pvc --all-namespaces --no-headers | wc -l)
              TOTAL_SIZE=$(kubectl get pvc --all-namespaces -o json | jq -r '.items[].spec.resources.requests.storage' | sed 's/Gi//' | awk '{sum+=$1} END {print sum "Gi"}')
              
              echo "Total PVCs: $TOTAL_PVCS"
              echo "Total requested storage: $TOTAL_SIZE"
          restartPolicy: OnFailure
```

---

## Cost Management & Quotas

### 1. Storage Cost Analysis

#### Cost Tracking with Tags:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: cost-tracked-storage
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
  # Cost allocation tags
  tagSpecification_1: "CostCenter=${pvc.annotations['cost.center']}"
  tagSpecification_2: "Project=${pvc.namespace}"
  tagSpecification_3: "Environment=${pvc.labels['environment']}"
  tagSpecification_4: "Team=${pvc.labels['team']}"
volumeBindingMode: WaitForFirstConsumer

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: tracked-storage
  annotations:
    cost.center: "engineering"
  labels:
    environment: "production"
    team: "platform"
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: cost-tracked-storage
  resources:
    requests:
      storage: 100Gi
```

#### Cost Monitoring Dashboard:
```bash
#!/bin/bash
# generate-storage-cost-report.sh

echo "=== EBS Storage Cost Report ==="
echo "Generated: $(date)"

# Get cost by tag
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE Type=TAG,Key=Project \
  --filter '{
    "Dimensions": {
      "Key": "SERVICE",
      "Values": ["Amazon Elastic Block Store"]
    }
  }' \
  --output table

# Get volume costs by type
echo "\n=== Cost by Volume Type ==="
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=USAGE_TYPE \
  --filter '{
    "Dimensions": {
      "Key": "SERVICE",
      "Values": ["Amazon Elastic Block Store"]
    }
  }' \
  --query 'ResultsByTime[0].Groups[?contains(Keys[0], `EBS`)]' \
  --output table

# Calculate cost per GB
echo "\n=== Cost Efficiency Analysis ==="
TOTAL_COST=$(aws ce get-cost-and-usage \
  --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter '{
    "Dimensions": {
      "Key": "SERVICE",
      "Values": ["Amazon Elastic Block Store"]
    }
  }' \
  --query 'ResultsByTime[0].Total.BlendedCost.Amount' --output text)

TOTAL_GB=$(aws ec2 describe-volumes \
  --filters "Name=tag:kubernetes.io/cluster/my-cluster,Values=owned" \
  --query 'sum(Volumes[].Size)' --output text)

if [ -n "$TOTAL_COST" ] && [ -n "$TOTAL_GB" ]; then
  COST_PER_GB=$(echo "scale=4; $TOTAL_COST / $TOTAL_GB" | bc)
  echo "Total EBS Cost (30 days): \$$TOTAL_COST"
  echo "Total Storage: ${TOTAL_GB}GB"
  echo "Cost per GB: \$$COST_PER_GB"
fi
```

### 2. Resource Quotas

#### Storage Resource Quota:
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: storage-quota
  namespace: development
spec:
  hard:
    # Limit total storage requests
    requests.storage: "1Ti"
    
    # Limit number of PVCs
    persistentvolumeclaims: "50"
    
    # Limit by storage class
    gp3.storageclass.storage.k8s.io/requests.storage: "500Gi"
    gp3.storageclass.storage.k8s.io/persistentvolumeclaims: "20"
    
    io2-ultra-high-iops.storageclass.storage.k8s.io/requests.storage: "100Gi"
    io2-ultra-high-iops.storageclass.storage.k8s.io/persistentvolumeclaims: "5"

---
apiVersion: v1
kind: LimitRange
metadata:
  name: storage-limits
  namespace: development
spec:
  limits:
  - type: PersistentVolumeClaim
    max:
      storage: "100Gi"  # Maximum PVC size
    min:
      storage: "1Gi"    # Minimum PVC size
    default:
      storage: "10Gi"   # Default PVC size
    defaultRequest:
      storage: "5Gi"    # Default request
```

#### Quota Monitoring:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: quota-monitor
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: monitor
            image: bitnami/kubectl:latest
            command:
            - /bin/bash
            - -c
            - |
              echo "=== Storage Quota Report ==="
              
              # Check all namespaces with quotas
              kubectl get resourcequota --all-namespaces -o json | \
              jq -r '.items[] | select(.spec.hard | has("requests.storage")) | "\(.metadata.namespace) \(.metadata.name)"' | \
              while read namespace quota_name; do
                echo "\nNamespace: $namespace"
                echo "Quota: $quota_name"
                
                # Get quota status
                kubectl get resourcequota $quota_name -n $namespace -o json | \
                jq -r '.status | to_entries[] | select(.key | contains("storage")) | "  \(.key): \(.value.used // "0") / \(.value.hard)"'
                
                # Calculate usage percentage
                USED=$(kubectl get resourcequota $quota_name -n $namespace -o jsonpath='{.status.used.requests\.storage}' | sed 's/Gi//')
                HARD=$(kubectl get resourcequota $quota_name -n $namespace -o jsonpath='{.status.hard.requests\.storage}' | sed 's/Gi//')
                
                if [ -n "$USED" ] && [ -n "$HARD" ]; then
                  PERCENTAGE=$(echo "scale=1; $USED * 100 / $HARD" | bc)
                  echo "  Usage: ${PERCENTAGE}%"
                  
                  # Alert if usage > 80%
                  if (( $(echo "$PERCENTAGE > 80" | bc -l) )); then
                    echo "  ⚠️ WARNING: High storage usage in $namespace"
                  fi
                fi
              done
          restartPolicy: OnFailure
```

---

## Volume Types & Performance

### 1. Performance Characteristics

#### GP3 Performance Tuning:
```yaml
# High-performance GP3 configuration
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-high-performance
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "16000"        # Maximum IOPS for GP3
  throughput: "1000"   # Maximum throughput for GP3
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

#### IO2 Block Express:
```yaml
# Ultra-high performance IO2 Block Express
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: io2-block-express
provisioner: ebs.csi.aws.com
parameters:
  type: io2
  iops: "256000"       # Maximum IOPS for IO2 Block Express
  encrypted: "true"
  # Block Express is automatically enabled for volumes > 64,000 IOPS
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### 2. Performance Testing

#### FIO Benchmark Job:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: storage-benchmark
spec:
  template:
    spec:
      containers:
      - name: fio
        image: ljishen/fio
        command: ["fio"]
        args:
        - "--name=random-write"
        - "--ioengine=libaio"
        - "--iodepth=32"
        - "--rw=randwrite"
        - "--bs=4k"
        - "--direct=1"
        - "--size=10G"
        - "--numjobs=4"
        - "--runtime=60"
        - "--group_reporting"
        - "--filename=/data/testfile"
        volumeMounts:
        - name: test-storage
          mountPath: /data
        resources:
          requests:
            memory: "1Gi"
            cpu: "1000m"
      volumes:
      - name: test-storage
        persistentVolumeClaim:
          claimName: benchmark-storage
      restartPolicy: Never

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: benchmark-storage
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: io1-high-iops
  resources:
    requests:
      storage: 100Gi
```

### 3. Cost Optimization Strategies

#### Tiered Storage Strategy:
```yaml
# Hot data - High performance
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: hot-data
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "8000"
  throughput: "500"
  encrypted: "true"

---
# Warm data - Balanced performance/cost
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: warm-data
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"

---
# Cold data - Cost optimized
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: cold-data
provisioner: ebs.csi.aws.com
parameters:
  type: sc1
  encrypted: "true"
```

---

## Advanced Features

### 1. Volume Snapshots

#### VolumeSnapshotClass:
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: ebs-snapshot-class
driver: ebs.csi.aws.com
deletionPolicy: Delete
parameters:
  tagSpecification_1: "Name=*"
  tagSpecification_2: "Environment=production"
```

#### Creating Volume Snapshots:
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-snapshot-20231201
  namespace: database
spec:
  volumeSnapshotClassName: ebs-snapshot-class
  source:
    persistentVolumeClaimName: postgresql-storage-postgresql-0
```

#### Restore from Snapshot:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-restored
  namespace: database
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: io1-high-iops
  resources:
    requests:
      storage: 100Gi
  dataSource:
    name: postgres-snapshot-20231201
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

### 2. Volume Cloning

#### Clone Existing PVC:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-clone
  namespace: database
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: io1-high-iops
  resources:
    requests:
      storage: 100Gi
  dataSource:
    name: postgresql-storage-postgresql-0
    kind: PersistentVolumeClaim
```

### 3. Volume Expansion

#### Expandable PVC:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: expandable-storage
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3  # Must have allowVolumeExpansion: true
  resources:
    requests:
      storage: 10Gi
```

#### Expand Volume:
```bash
# Edit PVC to increase size
kubectl patch pvc expandable-storage -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'

# Monitor expansion
kubectl get pvc expandable-storage -w

# Check expansion status
kubectl describe pvc expandable-storage
```

### 4. Multi-Attach Volumes (io1/io2 only)

#### Multi-Attach Storage Class:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: io1-multi-attach
provisioner: ebs.csi.aws.com
parameters:
  type: io1
  iops: "1000"
  encrypted: "true"
  multiAttach: "true"
volumeBindingMode: Immediate
allowVolumeExpansion: false
```

#### Multi-Attach PVC:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-storage
spec:
  accessModes:
    - ReadWriteMany  # Note: ReadWriteMany for multi-attach
  storageClassName: io1-multi-attach
  resources:
    requests:
      storage: 100Gi
```

### 5. Topology-Aware Provisioning

#### Zone-Specific Storage Class:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-zone-specific
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
allowedTopologies:
- matchLabelExpressions:
  - key: topology.ebs.csi.aws.com/zone
    values:
    - us-west-2a
volumeBindingMode: WaitForFirstConsumer
```

---

## Troubleshooting & Monitoring

### 1. Common Issues and Solutions

#### Issue: PVC Stuck in Pending State
```bash
# Check PVC status
kubectl describe pvc my-pvc

# Common causes and solutions:
# 1. No available storage class
kubectl get storageclass

# 2. Insufficient permissions
kubectl logs -n kube-system deployment/ebs-csi-controller

# 3. Zone constraints
kubectl get nodes --show-labels | grep topology.kubernetes.io/zone

# 4. Volume limits exceeded
aws ec2 describe-instances --instance-ids i-1234567890abcdef0 \
  --query 'Reservations[0].Instances[0].BlockDeviceMappings'
```

#### Issue: Volume Mount Failures
```bash
# Check pod events
kubectl describe pod my-pod

# Check CSI node logs
kubectl logs -n kube-system daemonset/ebs-csi-node -c ebs-plugin

# Verify volume attachment
aws ec2 describe-volumes --volume-ids vol-1234567890abcdef0

# Check file system
kubectl exec my-pod -- df -h /data
```

#### Issue: Performance Problems
```bash
# Check volume type and IOPS
aws ec2 describe-volumes --volume-ids vol-1234567890abcdef0 \
  --query 'Volumes[0].{Type:VolumeType,IOPS:Iops,Throughput:Throughput}'

# Monitor I/O metrics
kubectl top pods --containers

# Check for I/O wait
kubectl exec my-pod -- iostat -x 1 5
```

### 2. Monitoring and Metrics

#### CloudWatch Metrics for EBS:
```bash
# Create CloudWatch dashboard for EBS metrics
aws cloudwatch put-dashboard \
  --dashboard-name "EBS-CSI-Metrics" \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/EBS", "VolumeReadOps", "VolumeId", "vol-1234567890abcdef0"],
            [".", "VolumeWriteOps", ".", "."],
            [".", "VolumeTotalReadTime", ".", "."],
            [".", "VolumeTotalWriteTime", ".", "."],
            [".", "VolumeQueueLength", ".", "."]
          ],
          "period": 300,
          "stat": "Average",
          "region": "us-west-2",
          "title": "EBS Volume Performance"
        }
      }
    ]
  }'
```

#### Prometheus Monitoring:
```yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: ebs-csi-metrics
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: ebs-csi-controller
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### 3. Debugging Commands

#### CSI Driver Debugging:
```bash
# Check CSI driver status
kubectl get csidriver

# Verify CSI nodes
kubectl get csinodes

# Check controller logs
kubectl logs -n kube-system deployment/ebs-csi-controller -c ebs-plugin

# Check node logs
kubectl logs -n kube-system daemonset/ebs-csi-node -c ebs-plugin

# List all PVs and their status
kubectl get pv -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,CLAIM:.spec.claimRef.name,STORAGECLASS:.spec.storageClassName,REASON:.status.reason

# Check volume attachments
kubectl get volumeattachments
```

#### AWS CLI Debugging:
```bash
# List EBS volumes
aws ec2 describe-volumes --filters "Name=tag:kubernetes.io/cluster/my-cluster,Values=owned"

# Check volume status
aws ec2 describe-volumes --volume-ids vol-1234567890abcdef0 \
  --query 'Volumes[0].{State:State,Attachments:Attachments}'

# List snapshots
aws ec2 describe-snapshots --owner-ids self \
  --filters "Name=tag:CSIVolumeSnapshotName,Values=*"
```

---

## Best Practices

### 1. Storage Class Design

#### Production Storage Classes:
```yaml
# Production database storage
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: database-storage
  annotations:
    storageclass.kubernetes.io/is-default-class: "false"
provisioner: ebs.csi.aws.com
parameters:
  type: io2
  iops: "10000"
  encrypted: "true"
  kmsKeyId: "alias/ebs-encryption-key"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Retain

---
# General application storage
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: app-storage
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "4000"
  throughput: "250"
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete

---
# Log and temporary data storage
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: logs-storage
provisioner: ebs.csi.aws.com
parameters:
  type: st1
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

### 2. Security Best Practices

#### Encrypted Storage with Custom KMS Key:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: secure-storage
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

#### Pod Security Context with Storage:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
  containers:
  - name: app
    image: myapp:v1.0.0
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    volumeMounts:
    - name: data-storage
      mountPath: /data
    - name: tmp-storage
      mountPath: /tmp
  volumes:
  - name: data-storage
    persistentVolumeClaim:
      claimName: app-data
  - name: tmp-storage
    emptyDir: {}
```

### 3. Performance Optimization

#### Database Optimization:
```yaml
# PostgreSQL with optimized storage
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql-optimized
spec:
  serviceName: postgresql
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:14
        env:
        - name: POSTGRES_DB
          value: myapp
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        # PostgreSQL performance tuning
        - name: POSTGRES_SHARED_BUFFERS
          value: "256MB"
        - name: POSTGRES_EFFECTIVE_CACHE_SIZE
          value: "1GB"
        - name: POSTGRES_RANDOM_PAGE_COST
          value: "1.1"  # Optimized for SSD
        volumeMounts:
        - name: postgresql-data
          mountPath: /var/lib/postgresql/data
        - name: postgresql-wal
          mountPath: /var/lib/postgresql/wal
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
  volumeClaimTemplates:
  - metadata:
      name: postgresql-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: io2-ultra-high-iops
      resources:
        requests:
          storage: 100Gi
  - metadata:
      name: postgresql-wal
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: io2-ultra-high-iops
      resources:
        requests:
          storage: 20Gi
```

### 4. Backup and Disaster Recovery

#### Automated Backup CronJob:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: volume-backup
  namespace: database
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: volume-backup-sa
          containers:
          - name: backup
            image: amazon/aws-cli:latest
            command:
            - /bin/sh
            - -c
            - |
              # Create snapshot
              VOLUME_ID=$(kubectl get pv $(kubectl get pvc postgresql-storage-postgresql-0 -o jsonpath='{.spec.volumeName}') -o jsonpath='{.spec.csi.volumeHandle}')
              SNAPSHOT_ID=$(aws ec2 create-snapshot --volume-id $VOLUME_ID --description "Automated backup $(date)" --query 'SnapshotId' --output text)
              
              # Tag snapshot
              aws ec2 create-tags --resources $SNAPSHOT_ID --tags Key=Name,Value="postgresql-backup-$(date +%Y%m%d)" Key=Environment,Value=production
              
              # Clean up old snapshots (keep 7 days)
              aws ec2 describe-snapshots --owner-ids self --filters "Name=tag:Name,Values=postgresql-backup-*" --query 'Snapshots[?StartTime<=`'$(date -d '7 days ago' --iso-8601)'`].SnapshotId' --output text | xargs -r aws ec2 delete-snapshot --snapshot-id
            env:
            - name: AWS_DEFAULT_REGION
              value: us-west-2
          restartPolicy: OnFailure
```

### 5. Cost Management

#### Storage Cost Monitoring:
```bash
# Create cost allocation tags
kubectl patch storageclass gp3 -p '{"parameters":{"tagSpecification_1":"Project=myapp","tagSpecification_2":"Environment=production","tagSpecification_3":"Team=platform"}}'

# Monitor storage costs
aws ce get-cost-and-usage \
  --time-period Start=2023-11-01,End=2023-12-01 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --filter file://ebs-filter.json

# ebs-filter.json
{
  "Dimensions": {
    "Key": "SERVICE",
    "Values": ["Amazon Elastic Block Store"]
  }
}
```

### 6. Lifecycle Management

#### PVC Cleanup Job:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: pvc-cleanup
  namespace: kube-system
spec:
  schedule: "0 3 * * 0"  # Weekly on Sunday at 3 AM
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: pvc-cleanup-sa
          containers:
          - name: cleanup
            image: bitnami/kubectl:latest
            command:
            - /bin/sh
            - -c
            - |
              # Find unused PVCs (not bound to any pod)
              kubectl get pvc --all-namespaces -o json | jq -r '.items[] | select(.status.phase == "Bound") | select(.metadata.annotations."pvc.kubernetes.io/bind-completed" != null) | "\(.metadata.namespace)/\(.metadata.name)"' | while read pvc; do
                namespace=$(echo $pvc | cut -d'/' -f1)
                name=$(echo $pvc | cut -d'/' -f2)
                
                # Check if PVC is used by any pod
                if ! kubectl get pods -n $namespace -o json | jq -e --arg pvc "$name" '.items[] | select(.spec.volumes[]?.persistentVolumeClaim.claimName == $pvc)' > /dev/null; then
                  echo "Unused PVC found: $pvc"
                  # Add cleanup logic here (be careful!)
                fi
              done
          restartPolicy: OnFailure
```

This comprehensive guide covers all aspects of EKS PVC and EBS CSI driver management, from basic concepts to advanced scenarios and production best practices.