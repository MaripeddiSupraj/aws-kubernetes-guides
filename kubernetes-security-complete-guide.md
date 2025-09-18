# Kubernetes Security Complete Guide for DevOps Engineers

A comprehensive guide covering essential Kubernetes security concepts with practical examples, real-world scenarios, and step-by-step implementations.

## 📋 Table of Contents

1. [Security Context - Running Non-Root Pods](#1-security-context---running-non-root-pods)
2. [Seccomp in Kubernetes](#2-seccomp-in-kubernetes)
3. [AppArmor in Kubernetes](#3-apparmor-in-kubernetes)
4. [Linux Capabilities in K8s](#4-linux-capabilities-in-k8s)
5. [Pod Security Standards](#5-pod-security-standards)
6. [Policy Engines (Kyverno, OPA Gatekeeper)](#6-policy-engines)
7. [Pod Sandboxing with gVisor](#7-pod-sandboxing-with-gvisor)
8. [Real-World Security Scenarios](#8-real-world-security-scenarios)

---

## 1. Security Context - Running Non-Root Pods

### What is Security Context?
Think of Security Context as a "security ID card" for your containers. It tells Kubernetes:
- Who can run the container (which user)
- What permissions they have
- What they're allowed to do

### Why Avoid Root?
Running as root is like giving someone admin access to your computer - they can do anything, including damage your system.

### Basic Non-Root Pod Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsUser: 1000          # Run as user ID 1000 (not root)
    runAsGroup: 1000         # Run as group ID 1000
    runAsNonRoot: true       # Kubernetes will reject if tries to run as root
    fsGroup: 1000            # File system group ownership
  containers:
  - name: app
    image: nginx:alpine
    securityContext:
      allowPrivilegeEscalation: false  # Can't gain more privileges
      readOnlyRootFilesystem: true     # Can't write to root filesystem
      capabilities:
        drop:
        - ALL                          # Remove all Linux capabilities
```

### Container-Level Security Context

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: secure-app
  template:
    metadata:
      labels:
        app: secure-app
    spec:
      containers:
      - name: web-server
        image: nginx:alpine
        securityContext:
          runAsUser: 101                    # nginx user
          runAsNonRoot: true
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
            add:
            - NET_BIND_SERVICE             # Only allow binding to ports
        volumeMounts:
        - name: tmp-volume
          mountPath: /tmp                  # Writable temp directory
        - name: cache-volume
          mountPath: /var/cache/nginx      # Writable cache directory
      volumes:
      - name: tmp-volume
        emptyDir: {}
      - name: cache-volume
        emptyDir: {}
```

### Testing Security Context

```bash
# Deploy the secure pod
kubectl apply -f secure-pod.yaml

# Check the running user
kubectl exec secure-pod -- id
# Output: uid=1000 gid=1000 groups=1000

# Try to write to root filesystem (should fail)
kubectl exec secure-pod -- touch /test-file
# Output: touch: /test-file: Read-only file system
```

---

## 2. Seccomp in Kubernetes

### What is Seccomp?
Seccomp (Secure Computing) is like a bouncer at a club - it decides which system calls (requests to the operating system) your container can make.

### Why Use Seccomp?
- Prevents containers from making dangerous system calls
- Reduces attack surface
- Blocks privilege escalation attempts

### Default Seccomp Profile

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: seccomp-pod
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault    # Use container runtime's default seccomp profile
  containers:
  - name: app
    image: alpine:latest
    command: ["sleep", "3600"]
```

### Custom Seccomp Profile

First, create a custom seccomp profile:

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "read",
        "write",
        "open",
        "close",
        "stat",
        "fstat",
        "lstat",
        "poll",
        "lseek",
        "mmap",
        "mprotect",
        "munmap",
        "brk",
        "rt_sigaction",
        "rt_sigprocmask",
        "rt_sigreturn",
        "ioctl",
        "pread64",
        "pwrite64",
        "readv",
        "writev",
        "access",
        "pipe",
        "select",
        "sched_yield",
        "mremap",
        "msync",
        "mincore",
        "madvise",
        "shmget",
        "shmat",
        "shmctl",
        "dup",
        "dup2",
        "pause",
        "nanosleep",
        "getitimer",
        "alarm",
        "setitimer",
        "getpid",
        "sendfile",
        "socket",
        "connect",
        "accept",
        "sendto",
        "recvfrom",
        "sendmsg",
        "recvmsg",
        "shutdown",
        "bind",
        "listen",
        "getsockname",
        "getpeername",
        "socketpair",
        "setsockopt",
        "getsockopt",
        "clone",
        "fork",
        "vfork",
        "execve",
        "exit",
        "wait4",
        "kill",
        "uname",
        "semget",
        "semop",
        "semctl",
        "shmdt",
        "msgget",
        "msgsnd",
        "msgrcv",
        "msgctl",
        "fcntl",
        "flock",
        "fsync",
        "fdatasync",
        "truncate",
        "ftruncate",
        "getdents",
        "getcwd",
        "chdir",
        "fchdir",
        "rename",
        "mkdir",
        "rmdir",
        "creat",
        "link",
        "unlink",
        "symlink",
        "readlink",
        "chmod",
        "fchmod",
        "chown",
        "fchown",
        "lchown",
        "umask",
        "gettimeofday",
        "getrlimit",
        "getrusage",
        "sysinfo",
        "times",
        "ptrace",
        "getuid",
        "syslog",
        "getgid",
        "setuid",
        "setgid",
        "geteuid",
        "getegid",
        "setpgid",
        "getppid",
        "getpgrp",
        "setsid",
        "setreuid",
        "setregid",
        "getgroups",
        "setgroups",
        "setresuid",
        "getresuid",
        "setresgid",
        "getresgid",
        "getpgid",
        "setfsuid",
        "setfsgid",
        "getsid",
        "capget",
        "capset",
        "rt_sigpending",
        "rt_sigtimedwait",
        "rt_sigqueueinfo",
        "rt_sigsuspend",
        "sigaltstack",
        "utime",
        "mknod",
        "uselib",
        "personality",
        "ustat",
        "statfs",
        "fstatfs",
        "sysfs",
        "getpriority",
        "setpriority",
        "sched_setparam",
        "sched_getparam",
        "sched_setscheduler",
        "sched_getscheduler",
        "sched_get_priority_max",
        "sched_get_priority_min",
        "sched_rr_get_interval",
        "mlock",
        "munlock",
        "mlockall",
        "munlockall",
        "vhangup",
        "modify_ldt",
        "pivot_root",
        "_sysctl",
        "prctl",
        "arch_prctl",
        "adjtimex",
        "setrlimit",
        "chroot",
        "sync",
        "acct",
        "settimeofday",
        "mount",
        "umount2",
        "swapon",
        "swapoff",
        "reboot",
        "sethostname",
        "setdomainname",
        "iopl",
        "ioperm",
        "create_module",
        "init_module",
        "delete_module",
        "get_kernel_syms",
        "query_module",
        "quotactl",
        "nfsservctl",
        "getpmsg",
        "putpmsg",
        "afs_syscall",
        "tuxcall",
        "security",
        "gettid",
        "readahead",
        "setxattr",
        "lsetxattr",
        "fsetxattr",
        "getxattr",
        "lgetxattr",
        "fgetxattr",
        "listxattr",
        "llistxattr",
        "flistxattr",
        "removexattr",
        "lremovexattr",
        "fremovexattr",
        "tkill",
        "time",
        "futex",
        "sched_setaffinity",
        "sched_getaffinity",
        "set_thread_area",
        "io_setup",
        "io_destroy",
        "io_getevents",
        "io_submit",
        "io_cancel",
        "get_thread_area",
        "lookup_dcookie",
        "epoll_create",
        "epoll_ctl_old",
        "epoll_wait_old",
        "remap_file_pages",
        "getdents64",
        "set_tid_address",
        "restart_syscall",
        "semtimedop",
        "fadvise64",
        "timer_create",
        "timer_settime",
        "timer_gettime",
        "timer_getoverrun",
        "timer_delete",
        "clock_settime",
        "clock_gettime",
        "clock_getres",
        "clock_nanosleep",
        "exit_group",
        "epoll_wait",
        "epoll_ctl",
        "tgkill",
        "utimes",
        "vserver",
        "mbind",
        "set_mempolicy",
        "get_mempolicy",
        "mq_open",
        "mq_unlink",
        "mq_timedsend",
        "mq_timedreceive",
        "mq_notify",
        "mq_getsetattr",
        "kexec_load",
        "waitid",
        "add_key",
        "request_key",
        "keyctl",
        "ioprio_set",
        "ioprio_get",
        "inotify_init",
        "inotify_add_watch",
        "inotify_rm_watch",
        "migrate_pages",
        "openat",
        "mkdirat",
        "mknodat",
        "fchownat",
        "futimesat",
        "newfstatat",
        "unlinkat",
        "renameat",
        "linkat",
        "symlinkat",
        "readlinkat",
        "fchmodat",
        "faccessat",
        "pselect6",
        "ppoll",
        "unshare",
        "set_robust_list",
        "get_robust_list",
        "splice",
        "tee",
        "sync_file_range",
        "vmsplice",
        "move_pages",
        "utimensat",
        "epoll_pwait",
        "signalfd",
        "timerfd_create",
        "eventfd",
        "fallocate",
        "timerfd_settime",
        "timerfd_gettime",
        "accept4",
        "signalfd4",
        "eventfd2",
        "epoll_create1",
        "dup3",
        "pipe2",
        "inotify_init1",
        "preadv",
        "pwritev",
        "rt_tgsigqueueinfo",
        "perf_event_open",
        "recvmmsg",
        "fanotify_init",
        "fanotify_mark",
        "prlimit64",
        "name_to_handle_at",
        "open_by_handle_at",
        "clock_adjtime",
        "syncfs",
        "sendmmsg",
        "setns",
        "getcpu",
        "process_vm_readv",
        "process_vm_writev",
        "kcmp",
        "finit_module"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

Save this as `/var/lib/kubelet/seccomp/profiles/custom-profile.json` on your nodes.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-seccomp-pod
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/custom-profile.json
  containers:
  - name: app
    image: alpine:latest
    command: ["sleep", "3600"]
```

### Testing Seccomp

```bash
# Deploy pod with seccomp
kubectl apply -f seccomp-pod.yaml

# Test allowed system call
kubectl exec seccomp-pod -- ls /
# Should work fine

# Test restricted system call (if using restrictive profile)
kubectl exec seccomp-pod -- strace ls
# May be blocked depending on profile
```

---

## 3. AppArmor in Kubernetes

### What is AppArmor?
AppArmor is like a security guard that watches what files and resources your container can access. It creates a "profile" of allowed actions.

### Checking AppArmor Status

```bash
# Check if AppArmor is enabled on nodes
kubectl get nodes -o wide

# SSH to node and check AppArmor
sudo aa-status
```

### Creating AppArmor Profile

Create an AppArmor profile on your nodes:

```bash
# Create profile file: /etc/apparmor.d/k8s-nginx
sudo tee /etc/apparmor.d/k8s-nginx << 'EOF'
#include <tunables/global>

profile k8s-nginx flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  
  # Allow network access
  network inet tcp,
  network inet udp,
  
  # Allow reading configuration files
  /etc/nginx/** r,
  /etc/passwd r,
  /etc/group r,
  
  # Allow access to nginx directories
  /usr/share/nginx/** r,
  /var/log/nginx/** w,
  /var/cache/nginx/** rw,
  /run/nginx.pid w,
  
  # Allow temporary files
  /tmp/** rw,
  
  # Deny access to sensitive directories
  deny /etc/shadow r,
  deny /root/** rw,
  deny /home/** rw,
  deny /var/log/auth.log r,
  
  # Allow basic system access
  /bin/bash ix,
  /usr/sbin/nginx ix,
  /lib/x86_64-linux-gnu/** mr,
  /usr/lib/x86_64-linux-gnu/** mr,
}
EOF

# Load the profile
sudo apparmor_parser -r /etc/apparmor.d/k8s-nginx

# Verify profile is loaded
sudo aa-status | grep k8s-nginx
```

### Using AppArmor in Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: apparmor-pod
  annotations:
    container.apparmor.security.beta.kubernetes.io/nginx: localhost/k8s-nginx
spec:
  containers:
  - name: nginx
    image: nginx:alpine
    ports:
    - containerPort: 80
```

### AppArmor with Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-nginx
spec:
  replicas: 2
  selector:
    matchLabels:
      app: secure-nginx
  template:
    metadata:
      labels:
        app: secure-nginx
      annotations:
        container.apparmor.security.beta.kubernetes.io/nginx: localhost/k8s-nginx
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
        securityContext:
          runAsUser: 101
          runAsNonRoot: true
          allowPrivilegeEscalation: false
```

### Testing AppArmor

```bash
# Deploy the pod
kubectl apply -f apparmor-pod.yaml

# Test allowed access
kubectl exec apparmor-pod -- ls /etc/nginx/
# Should work

# Test denied access
kubectl exec apparmor-pod -- cat /etc/shadow
# Should be denied by AppArmor

# Check AppArmor logs
sudo dmesg | grep -i apparmor
```

---

## 4. Linux Capabilities in K8s

### What are Linux Capabilities?
Think of capabilities as specific "superpowers" you can give to containers. Instead of giving full admin rights (root), you give only the specific powers needed.

### Common Capabilities

| Capability | What it does | Example use case |
|------------|--------------|------------------|
| NET_BIND_SERVICE | Bind to ports < 1024 | Web servers on port 80/443 |
| SYS_TIME | Change system time | NTP services |
| NET_ADMIN | Network administration | VPN, routing software |
| SYS_ADMIN | System administration | Container runtimes |
| CHOWN | Change file ownership | File management tools |

### Dropping All Capabilities (Most Secure)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: no-caps-pod
spec:
  containers:
  - name: app
    image: alpine:latest
    command: ["sleep", "3600"]
    securityContext:
      capabilities:
        drop:
        - ALL                    # Remove all capabilities
```

### Adding Specific Capabilities

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-server-pod
spec:
  containers:
  - name: nginx
    image: nginx:alpine
    ports:
    - containerPort: 80
    securityContext:
      runAsUser: 101
      capabilities:
        drop:
        - ALL                    # First drop all
        add:
        - NET_BIND_SERVICE       # Then add only what's needed
```

### Real-World Example: Monitoring Agent

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: monitoring-agent
spec:
  selector:
    matchLabels:
      app: monitoring-agent
  template:
    metadata:
      labels:
        app: monitoring-agent
    spec:
      containers:
      - name: agent
        image: monitoring-agent:latest
        securityContext:
          capabilities:
            drop:
            - ALL
            add:
            - SYS_PTRACE         # Read process information
            - DAC_READ_SEARCH    # Read files for monitoring
        volumeMounts:
        - name: proc
          mountPath: /host/proc
          readOnly: true
        - name: sys
          mountPath: /host/sys
          readOnly: true
      volumes:
      - name: proc
        hostPath:
          path: /proc
      - name: sys
        hostPath:
          path: /sys
```

### Testing Capabilities

```bash
# Deploy pod without capabilities
kubectl apply -f no-caps-pod.yaml

# Try to bind to privileged port (should fail)
kubectl exec no-caps-pod -- nc -l -p 80
# Output: nc: bind: Permission denied

# Deploy pod with NET_BIND_SERVICE
kubectl apply -f web-server-pod.yaml

# Try to bind to privileged port (should work)
kubectl exec web-server-pod -- nginx -t
# Should work fine
```

---

## 5. Pod Security Standards

### What are Pod Security Standards?
Pod Security Standards are like "security templates" that define different levels of security restrictions. They replaced the older Pod Security Policies.

### Three Security Levels

1. **Privileged** - No restrictions (not recommended for production)
2. **Baseline** - Minimal restrictions, prevents known privilege escalations
3. **Restricted** - Heavily restricted, follows security best practices

### Namespace-Level Enforcement

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

### Baseline Security Standard Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: baseline-pod
  namespace: secure-namespace
spec:
  securityContext:
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: nginx:alpine
    securityContext:
      runAsUser: 1000
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
```

### Restricted Security Standard Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: restricted-pod
  namespace: secure-namespace
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
    image: nginx:alpine
    securityContext:
      runAsUser: 1000
      runAsNonRoot: true
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    resources:
      limits:
        memory: "128Mi"
        cpu: "100m"
      requests:
        memory: "64Mi"
        cpu: "50m"
    volumeMounts:
    - name: tmp-volume
      mountPath: /tmp
  volumes:
  - name: tmp-volume
    emptyDir: {}
```

### Gradual Migration Strategy

```yaml
# Step 1: Start with warn mode
apiVersion: v1
kind: Namespace
metadata:
  name: migration-namespace
  labels:
    pod-security.kubernetes.io/warn: baseline
    pod-security.kubernetes.io/audit: baseline
---
# Step 2: After fixing warnings, add enforce
apiVersion: v1
kind: Namespace
metadata:
  name: migration-namespace
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted
---
# Step 3: Finally enforce restricted
apiVersion: v1
kind: Namespace
metadata:
  name: migration-namespace
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Testing Pod Security Standards

```bash
# Create namespace with restrictions
kubectl apply -f secure-namespace.yaml

# Try to deploy non-compliant pod
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: bad-pod
  namespace: secure-namespace
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      runAsUser: 0  # This will be rejected
EOF

# Should see error about security policy violation
```

---

## 6. Policy Engines

### What are Policy Engines?
Policy engines are like "security robots" that automatically check if your Kubernetes resources follow your organization's security rules.

## Kyverno Examples

### Installing Kyverno

```bash
# Install Kyverno
kubectl create -f https://github.com/kyverno/kyverno/releases/latest/download/install.yaml

# Verify installation
kubectl get pods -n kyverno
```

### Require Non-Root Containers

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-non-root
spec:
  validationFailureAction: enforce
  background: true
  rules:
  - name: check-non-root
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Containers must run as non-root user"
      pattern:
        spec:
          securityContext:
            runAsNonRoot: true
          containers:
          - securityContext:
              runAsNonRoot: true
```

### Require Resource Limits

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-resource-limits
spec:
  validationFailureAction: enforce
  background: true
  rules:
  - name: check-resource-limits
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "All containers must have resource limits"
      pattern:
        spec:
          containers:
          - name: "*"
            resources:
              limits:
                memory: "?*"
                cpu: "?*"
```

### Auto-Add Security Context

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: add-security-context
spec:
  rules:
  - name: add-security-context
    match:
      any:
      - resources:
          kinds:
          - Pod
    mutate:
      patchStrategicMerge:
        spec:
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
          containers:
          - (name): "*"
            securityContext:
              allowPrivilegeEscalation: false
              readOnlyRootFilesystem: true
              capabilities:
                drop:
                - ALL
```

## OPA Gatekeeper Examples

### Installing OPA Gatekeeper

```bash
# Install Gatekeeper
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.14/deploy/gatekeeper.yaml

# Verify installation
kubectl get pods -n gatekeeper-system
```

### Constraint Template for Required Labels

```yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        type: object
        properties:
          labels:
            type: array
            items:
              type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels
        
        violation[{"msg": msg}] {
          required := input.parameters.labels
          provided := input.review.object.metadata.labels
          missing := required[_]
          not provided[missing]
          msg := sprintf("Missing required label: %v", [missing])
        }
```

### Using the Constraint

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: must-have-environment
spec:
  match:
    kinds:
      - apiGroups: ["apps"]
        kinds: ["Deployment"]
  parameters:
    labels: ["environment", "team", "version"]
```

### Block Privileged Containers

```yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8sblockprivileged
spec:
  crd:
    spec:
      names:
        kind: K8sBlockPrivileged
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8sblockprivileged
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          container.securityContext.privileged == true
          msg := "Privileged containers are not allowed"
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sBlockPrivileged
metadata:
  name: block-privileged-containers
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
      - apiGroups: ["apps"]
        kinds: ["Deployment"]
```

### Testing Policy Engines

```bash
# Test Kyverno policy
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: app
    image: nginx
    # Missing security context - should be rejected or auto-fixed
EOF

# Test Gatekeeper constraint
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
  # Missing required labels - should be rejected
spec:
  selector:
    matchLabels:
      app: test
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - name: app
        image: nginx
EOF
```

---

## 7. Pod Sandboxing with gVisor

### What is gVisor?
gVisor is like putting your container in a "virtual jail cell" - it creates an extra layer of isolation between your container and the host system.

### Installing gVisor (runsc)

```bash
# Download and install runsc
curl -fsSL https://gvisor.dev/archive.key | sudo gpg --dearmor -o /usr/share/keyrings/gvisor-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] https://storage.googleapis.com/gvisor/releases release main" | sudo tee /etc/apt/sources.list.d/gvisor.list > /dev/null

sudo apt-get update && sudo apt-get install -y runsc

# Configure containerd to use runsc
sudo tee /etc/containerd/config.toml << 'EOF'
version = 2
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runsc]
  runtime_type = "io.containerd.runsc.v1"
EOF

sudo systemctl restart containerd
```

### RuntimeClass for gVisor

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
```

### Using gVisor Runtime

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gvisor-pod
spec:
  runtimeClassName: gvisor    # Use gVisor runtime
  containers:
  - name: app
    image: nginx:alpine
    securityContext:
      runAsUser: 1000
      runAsNonRoot: true
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
```

### High-Security Workload Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-payment-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
    spec:
      runtimeClassName: gvisor
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: payment-app
        image: payment-service:v1.0
        securityContext:
          runAsUser: 1000
          runAsNonRoot: true
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "250m"
        volumeMounts:
        - name: tmp-volume
          mountPath: /tmp
        - name: app-data
          mountPath: /app/data
      volumes:
      - name: tmp-volume
        emptyDir: {}
      - name: app-data
        emptyDir: {}
```

### Testing gVisor

```bash
# Deploy gVisor pod
kubectl apply -f gvisor-pod.yaml

# Check runtime being used
kubectl describe pod gvisor-pod | grep "Runtime Class"

# Test isolation - try to access host information
kubectl exec gvisor-pod -- cat /proc/version
# Should show gVisor kernel, not host kernel

# Compare with regular pod
kubectl run regular-pod --image=alpine:latest --command -- sleep 3600
kubectl exec regular-pod -- cat /proc/version
# Should show host kernel version
```

---

## 8. Real-World Security Scenarios

### Scenario 1: Multi-Tenant E-commerce Platform

**Challenge**: Different teams deploying services with varying security requirements.

**Solution**: Namespace-based security with different Pod Security Standards

```yaml
# Namespace for payment services (highest security)
apiVersion: v1
kind: Namespace
metadata:
  name: payment-services
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
# Namespace for frontend services (moderate security)
apiVersion: v1
kind: Namespace
metadata:
  name: frontend-services
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
# Payment service deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-processor
  namespace: payment-services
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payment-processor
  template:
    metadata:
      labels:
        app: payment-processor
    spec:
      runtimeClassName: gvisor
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: processor
        image: payment-processor:v2.1
        securityContext:
          runAsUser: 1000
          runAsNonRoot: true
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        resources:
          limits:
            memory: "1Gi"
            cpu: "500m"
          requests:
            memory: "512Mi"
            cpu: "250m"
        env:
        - name: DB_CONNECTION_ENCRYPTED
          value: "true"
        volumeMounts:
        - name: tmp-volume
          mountPath: /tmp
      volumes:
      - name: tmp-volume
        emptyDir: {}
```

### Scenario 2: CI/CD Pipeline Security

**Challenge**: Build agents need specific capabilities but should be contained.

**Solution**: Dedicated namespace with custom security policies

```yaml
# CI/CD namespace with baseline security
apiVersion: v1
kind: Namespace
metadata:
  name: ci-cd
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/audit: baseline
    pod-security.kubernetes.io/warn: baseline
---
# Kyverno policy for CI/CD workloads
apiVersion: kyverno.io/v1
kind: Policy
metadata:
  name: ci-cd-security
  namespace: ci-cd
spec:
  validationFailureAction: enforce
  rules:
  - name: require-resource-limits
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "CI/CD pods must have resource limits"
      pattern:
        spec:
          containers:
          - name: "*"
            resources:
              limits:
                memory: "?*"
                cpu: "?*"
  - name: limit-build-time
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Build pods must have activeDeadlineSeconds"
      pattern:
        spec:
          activeDeadlineSeconds: "<=3600"  # Max 1 hour
---
# Build agent deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: build-agent
  namespace: ci-cd
spec:
  replicas: 2
  selector:
    matchLabels:
      app: build-agent
  template:
    metadata:
      labels:
        app: build-agent
    spec:
      activeDeadlineSeconds: 3600
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
      - name: builder
        image: build-agent:v1.5
        securityContext:
          runAsUser: 1000
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
            add:
            - DAC_OVERRIDE  # For file operations during build
        resources:
          limits:
            memory: "4Gi"
            cpu: "2"
          requests:
            memory: "2Gi"
            cpu: "1"
        volumeMounts:
        - name: docker-socket
          mountPath: /var/run/docker.sock
          readOnly: true
        - name: build-cache
          mountPath: /build-cache
      volumes:
      - name: docker-socket
        hostPath:
          path: /var/run/docker.sock
      - name: build-cache
        emptyDir:
          sizeLimit: 10Gi
```

### Scenario 3: Compliance and Audit Requirements

**Challenge**: Need to demonstrate security compliance for audit.

**Solution**: Comprehensive security monitoring and policy enforcement

```yaml
# Audit namespace with strict policies
apiVersion: v1
kind: Namespace
metadata:
  name: compliance-workloads
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
    compliance.company.com/level: "high"
---
# Comprehensive security policy
apiVersion: kyverno.io/v1
kind: Policy
metadata:
  name: compliance-policy
  namespace: compliance-workloads
spec:
  validationFailureAction: enforce
  background: true
  rules:
  - name: require-security-context
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Security context is required for compliance"
      pattern:
        spec:
          securityContext:
            runAsNonRoot: true
            runAsUser: ">0"
            seccompProfile:
              type: RuntimeDefault
          containers:
          - securityContext:
              allowPrivilegeEscalation: false
              readOnlyRootFilesystem: true
              capabilities:
                drop:
                - ALL
  - name: require-resource-limits
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Resource limits required for compliance"
      pattern:
        spec:
          containers:
          - resources:
              limits:
                memory: "?*"
                cpu: "?*"
  - name: require-labels
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Compliance labels are required"
      pattern:
        metadata:
          labels:
            compliance.company.com/reviewed: "true"
            compliance.company.com/owner: "?*"
---
# Compliant application deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: compliant-app
  namespace: compliance-workloads
  labels:
    compliance.company.com/reviewed: "true"
    compliance.company.com/owner: "security-team"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: compliant-app
  template:
    metadata:
      labels:
        app: compliant-app
        compliance.company.com/reviewed: "true"
        compliance.company.com/owner: "security-team"
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
        image: compliant-app:v1.0
        securityContext:
          runAsUser: 1000
          runAsNonRoot: true
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        resources:
          limits:
            memory: "512Mi"
            cpu: "250m"
          requests:
            memory: "256Mi"
            cpu: "125m"
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
        volumeMounts:
        - name: tmp-volume
          mountPath: /tmp
        - name: app-data
          mountPath: /app/data
      volumes:
      - name: tmp-volume
        emptyDir: {}
      - name: app-data
        emptyDir: {}
```

## 🔧 Security Checklist

### Pre-Deployment Security Checklist

```bash
#!/bin/bash
# security-check.sh - Run before deploying any workload

echo "🔍 Kubernetes Security Pre-Deployment Checklist"
echo "================================================"

# Check 1: Security Context
echo "✅ Checking Security Context..."
if kubectl get pod $POD_NAME -o jsonpath='{.spec.securityContext.runAsNonRoot}' | grep -q "true"; then
    echo "   ✓ Running as non-root"
else
    echo "   ❌ Not running as non-root"
fi

# Check 2: Resource Limits
echo "✅ Checking Resource Limits..."
if kubectl get pod $POD_NAME -o jsonpath='{.spec.containers[*].resources.limits}' | grep -q "memory\|cpu"; then
    echo "   ✓ Resource limits set"
else
    echo "   ❌ No resource limits"
fi

# Check 3: Capabilities
echo "✅ Checking Capabilities..."
if kubectl get pod $POD_NAME -o jsonpath='{.spec.containers[*].securityContext.capabilities.drop}' | grep -q "ALL"; then
    echo "   ✓ All capabilities dropped"
else
    echo "   ❌ Capabilities not properly restricted"
fi

# Check 4: Read-only filesystem
echo "✅ Checking Filesystem..."
if kubectl get pod $POD_NAME -o jsonpath='{.spec.containers[*].securityContext.readOnlyRootFilesystem}' | grep -q "true"; then
    echo "   ✓ Read-only root filesystem"
else
    echo "   ❌ Root filesystem is writable"
fi

# Check 5: Seccomp profile
echo "✅ Checking Seccomp..."
if kubectl get pod $POD_NAME -o jsonpath='{.spec.securityContext.seccompProfile.type}' | grep -q "RuntimeDefault"; then
    echo "   ✓ Seccomp profile applied"
else
    echo "   ❌ No seccomp profile"
fi

echo "================================================"
echo "Security check complete!"
```

### Runtime Security Monitoring

```yaml
# Security monitoring deployment
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: security-monitor
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: security-monitor
  template:
    metadata:
      labels:
        app: security-monitor
    spec:
      hostPID: true
      hostNetwork: true
      containers:
      - name: monitor
        image: security-monitor:v1.0
        securityContext:
          privileged: true  # Required for monitoring
        volumeMounts:
        - name: proc
          mountPath: /host/proc
          readOnly: true
        - name: sys
          mountPath: /host/sys
          readOnly: true
        env:
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
      volumes:
      - name: proc
        hostPath:
          path: /proc
      - name: sys
        hostPath:
          path: /sys
```

## 📊 Security Metrics and Monitoring

### Key Security Metrics to Track

1. **Pod Security Compliance**
   - Percentage of pods running as non-root
   - Pods with resource limits
   - Pods with security contexts

2. **Policy Violations**
   - Number of policy violations per day
   - Most common violation types
   - Violation trends over time

3. **Runtime Security Events**
   - Privilege escalation attempts
   - Suspicious system calls
   - Network policy violations

### Monitoring Dashboard Query Examples

```yaml
# Prometheus queries for security metrics
apiVersion: v1
kind: ConfigMap
metadata:
  name: security-queries
data:
  non_root_pods.prom: |
    # Percentage of pods running as non-root
    (
      count(kube_pod_container_info{container!="POD", runAsNonRoot="true"})
      /
      count(kube_pod_container_info{container!="POD"})
    ) * 100
  
  resource_limits.prom: |
    # Pods without resource limits
    count(
      kube_pod_container_info{container!="POD"}
      unless
      kube_pod_container_resource_limits{resource="memory"}
    )
  
  security_violations.prom: |
    # Security policy violations per hour
    increase(gatekeeper_violations_total[1h])
```

## 🚨 Incident Response

### Security Incident Playbook

```bash
#!/bin/bash
# incident-response.sh - Security incident response

echo "🚨 Security Incident Response"
echo "============================="

# Step 1: Isolate the affected pod
echo "1. Isolating affected pod..."
kubectl label pod $AFFECTED_POD security.incident=isolated
kubectl annotate pod $AFFECTED_POD security.incident.time=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Step 2: Collect forensic data
echo "2. Collecting forensic data..."
kubectl logs $AFFECTED_POD --previous > incident-logs-$(date +%s).log
kubectl describe pod $AFFECTED_POD > incident-describe-$(date +%s).yaml
kubectl get events --field-selector involvedObject.name=$AFFECTED_POD > incident-events-$(date +%s).log

# Step 3: Network isolation
echo "3. Applying network isolation..."
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-$AFFECTED_POD
  namespace: $NAMESPACE
spec:
  podSelector:
    matchLabels:
      security.incident: isolated
  policyTypes:
  - Ingress
  - Egress
  # No ingress or egress rules = deny all traffic
EOF

# Step 4: Scale down deployment if needed
echo "4. Scaling down deployment..."
kubectl scale deployment $DEPLOYMENT_NAME --replicas=0

echo "Incident response complete. Review collected data."
```

## 📚 Additional Resources

### Essential Security Tools

1. **Falco** - Runtime security monitoring
2. **Trivy** - Vulnerability scanning
3. **Polaris** - Configuration validation
4. **Kubesec** - Security risk analysis
5. **Kube-bench** - CIS benchmark testing

### Security Best Practices Summary

1. **Always run containers as non-root**
2. **Use read-only root filesystems**
3. **Drop all capabilities, add only what's needed**
4. **Apply resource limits**
5. **Use Pod Security Standards**
6. **Implement network policies**
7. **Regular security scanning**
8. **Monitor runtime behavior**
9. **Keep Kubernetes updated**
10. **Regular security audits**

### Learning Path

1. Start with Security Context and non-root containers
2. Learn about Linux capabilities and how to restrict them
3. Understand Pod Security Standards
4. Implement policy engines (Kyverno or OPA Gatekeeper)
5. Explore advanced topics like AppArmor and Seccomp
6. Practice with gVisor for high-security workloads
7. Set up comprehensive monitoring and alerting

---

**Remember**: Security is not a one-time setup but an ongoing process. Regularly review and update your security policies, monitor for new threats, and keep your knowledge current with the latest Kubernetes security features and best practices.

This guide provides a solid foundation for implementing Kubernetes security in production environments. Start with the basics and gradually implement more advanced security measures as your understanding and requirements grow.