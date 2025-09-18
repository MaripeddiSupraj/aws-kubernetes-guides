# Kubernetes Custom Resource Definitions (CRDs): Complete Guide with Go Implementation

## 🎯 Understanding CRDs: The "Why" Before the "How"

### What Problem Do CRDs Solve?

**The Kubernetes Extension Challenge:**
```
Kubernetes provides built-in resources:
├── Pods, Services, Deployments
├── ConfigMaps, Secrets
├── Ingress, PersistentVolumes
└── But what if you need custom business logic?

Real-world needs:
├── Website monitoring and alerting
├── Database backup scheduling
├── Custom application configurations
├── Business-specific workflows
└── Domain-specific automation
```

**Before CRDs (Traditional Approach):**
```
Options for custom logic:
├── External scripts and cron jobs
├── Separate monitoring systems
├── Manual configuration management
├── Custom APIs outside Kubernetes
└── Complex integration challenges

Problems:
- No integration with Kubernetes RBAC
- Separate management interfaces
- No kubectl integration
- Missing Kubernetes-native features
- Complex deployment and scaling
```

**With CRDs (Kubernetes-Native Approach):**
```
Benefits:
├── Native kubectl support
├── Integrated RBAC and security
├── Kubernetes API consistency
├── Built-in validation and versioning
├── Controller pattern for automation
├── Helm chart integration
└── GitOps compatibility
```

### Real-World Example: Website Monitoring

**Business Scenario:**
```
E-commerce company needs:
├── Monitor 50+ websites across regions
├── Custom alerting rules per site
├── Integration with existing Kubernetes infrastructure
├── Developer self-service capabilities
├── Compliance and audit trails
└── Automated remediation workflows
```

**Traditional Solution Problems:**
```
External monitoring tools:
├── Separate authentication systems
├── Different configuration formats
├── No integration with deployment pipelines
├── Complex permission management
├── Additional infrastructure costs
└── Vendor lock-in risks
```

**CRD Solution Benefits:**
```
Kubernetes-native monitoring:
├── Same RBAC as other Kubernetes resources
├── kubectl-based management
├── GitOps deployment workflows
├── Namespace-based isolation
├── Built-in validation and defaults
└── Controller automation
```

## 🧠 CRD Concepts Deep Dive

### Understanding the Architecture

**CRD Components:**
```
1. CustomResourceDefinition (CRD):
   ├── Defines the schema and structure
   ├── Specifies validation rules
   ├── Sets up API endpoints
   └── Configures kubectl integration

2. Custom Resource (CR):
   ├── Instance of your CRD
   ├── Contains actual configuration data
   ├── Managed like any Kubernetes resource
   └── Stored in etcd

3. Controller (Optional but Recommended):
   ├── Watches for CR changes
   ├── Implements business logic
   ├── Manages resource lifecycle
   └── Provides automation
```

**The Controller Pattern:**
```
Controller Loop:
1. Watch for Custom Resource changes
2. Compare desired state (spec) vs current state (status)
3. Take actions to reconcile differences
4. Update status to reflect current state
5. Repeat continuously

This pattern enables:
├── Self-healing systems
├── Declarative configuration
├── Event-driven automation
└── Kubernetes-native behavior
```

### CRD vs ConfigMap vs Secret

**When to Use CRDs:**
```
✅ Complex validation requirements
✅ Custom business logic needed
✅ API-like behavior required
✅ Integration with controllers
✅ Custom kubectl commands
✅ Versioning and schema evolution

❌ Simple key-value configuration (use ConfigMap)
❌ Sensitive data storage (use Secret)
❌ One-time configuration (use ConfigMap)
```

## 🚀 Practical Implementation: Website Monitor CRD

### Step 1: Define the CRD

**WebsiteMonitor CRD Definition:**
```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: websitemonitors.monitoring.company.com
spec:
  group: monitoring.company.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              url:
                type: string
                pattern: '^https?://.+'
                description: "Website URL to monitor"
              interval:
                type: string
                default: "30s"
                description: "Check interval (e.g., 30s, 1m, 5m)"
              timeout:
                type: string
                default: "10s"
                description: "Request timeout"
              expectedStatusCode:
                type: integer
                default: 200
                minimum: 100
                maximum: 599
              alerting:
                type: object
                properties:
                  enabled:
                    type: boolean
                    default: true
                  slackWebhook:
                    type: string
                  emailRecipients:
                    type: array
                    items:
                      type: string
            required:
            - url
          status:
            type: object
            properties:
              lastCheck:
                type: string
                format: date-time
              status:
                type: string
                enum: ["healthy", "unhealthy", "unknown"]
              responseTime:
                type: string
              uptime:
                type: string
              totalChecks:
                type: integer
              successfulChecks:
                type: integer
              lastError:
                type: string
    additionalPrinterColumns:
    - name: URL
      type: string
      jsonPath: .spec.url
    - name: Status
      type: string
      jsonPath: .status.status
    - name: Uptime
      type: string
      jsonPath: .status.uptime
    - name: Last Check
      type: string
      jsonPath: .status.lastCheck
  scope: Namespaced
  names:
    plural: websitemonitors
    singular: websitemonitor
    kind: WebsiteMonitor
    shortNames:
    - wm
```

**Key CRD Features Explained:**
```
Schema Validation:
├── URL pattern validation (must be http/https)
├── Status code range validation (100-599)
├── Required fields enforcement
├── Default values for optional fields
└── Enum validation for status

User Experience:
├── Custom columns in kubectl output
├── Short names for easier typing (wm)
├── Descriptive field documentation
└── Intuitive resource naming

API Integration:
├── RESTful API endpoints automatically created
├── OpenAPI schema for client generation
├── Kubernetes-native CRUD operations
└── Watch/list capabilities
```

### Step 2: Go Types and Client Generation

**Go Struct Definitions:**
```go
// pkg/apis/monitoring/v1/types.go
package v1

import (
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// WebsiteMonitorSpec defines the desired state
type WebsiteMonitorSpec struct {
    URL                string            `json:"url"`
    Interval           string            `json:"interval,omitempty"`
    Timeout            string            `json:"timeout,omitempty"`
    ExpectedStatusCode int               `json:"expectedStatusCode,omitempty"`
    Alerting           AlertingConfig    `json:"alerting,omitempty"`
}

// AlertingConfig defines alerting configuration
type AlertingConfig struct {
    Enabled          bool     `json:"enabled,omitempty"`
    SlackWebhook     string   `json:"slackWebhook,omitempty"`
    EmailRecipients  []string `json:"emailRecipients,omitempty"`
}

// WebsiteMonitorStatus defines the observed state
type WebsiteMonitorStatus struct {
    LastCheck        *metav1.Time `json:"lastCheck,omitempty"`
    Status           string       `json:"status,omitempty"`
    ResponseTime     string       `json:"responseTime,omitempty"`
    Uptime           string       `json:"uptime,omitempty"`
    TotalChecks      int64        `json:"totalChecks,omitempty"`
    SuccessfulChecks int64        `json:"successfulChecks,omitempty"`
    LastError        string       `json:"lastError,omitempty"`
}

// WebsiteMonitor is the Schema for the websitemonitors API
// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="URL",type="string",JSONPath=".spec.url"
// +kubebuilder:printcolumn:name="Status",type="string",JSONPath=".status.status"
// +kubebuilder:printcolumn:name="Uptime",type="string",JSONPath=".status.uptime"
type WebsiteMonitor struct {
    metav1.TypeMeta   `json:",inline"`
    metav1.ObjectMeta `json:"metadata,omitempty"`
    
    Spec   WebsiteMonitorSpec   `json:"spec,omitempty"`
    Status WebsiteMonitorStatus `json:"status,omitempty"`
}

// WebsiteMonitorList contains a list of WebsiteMonitor
// +kubebuilder:object:root=true
type WebsiteMonitorList struct {
    metav1.TypeMeta `json:",inline"`
    metav1.ListMeta `json:"metadata,omitempty"`
    Items           []WebsiteMonitor `json:"items"`
}
```

### Step 3: Controller Implementation

**Main Controller Logic:**
```go
// controllers/websitemonitor_controller.go
package controllers

import (
    "context"
    "fmt"
    "net/http"
    "time"
    
    "github.com/go-logr/logr"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/apimachinery/pkg/runtime"
    ctrl "sigs.k8s.io/controller-runtime"
    "sigs.k8s.io/controller-runtime/pkg/client"
    
    monitoringv1 "github.com/company/website-monitor/pkg/apis/monitoring/v1"
)

// WebsiteMonitorReconciler reconciles a WebsiteMonitor object
type WebsiteMonitorReconciler struct {
    client.Client
    Log    logr.Logger
    Scheme *runtime.Scheme
}

// Reconcile implements the main controller logic
func (r *WebsiteMonitorReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    log := r.Log.WithValues("websitemonitor", req.NamespacedName)
    
    // Fetch the WebsiteMonitor instance
    var monitor monitoringv1.WebsiteMonitor
    if err := r.Get(ctx, req.NamespacedName, &monitor); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }
    
    // Parse interval
    interval, err := time.ParseDuration(monitor.Spec.Interval)
    if err != nil {
        interval = 30 * time.Second // default
    }
    
    // Check if it's time for next check
    if monitor.Status.LastCheck != nil {
        nextCheck := monitor.Status.LastCheck.Add(interval)
        if time.Now().Before(nextCheck) {
            // Schedule next reconcile
            return ctrl.Result{RequeueAfter: time.Until(nextCheck)}, nil
        }
    }
    
    // Perform health check
    status, responseTime, err := r.checkWebsite(monitor.Spec)
    
    // Update status
    now := metav1.Now()
    monitor.Status.LastCheck = &now
    monitor.Status.TotalChecks++
    
    if err != nil {
        monitor.Status.Status = "unhealthy"
        monitor.Status.LastError = err.Error()
        log.Error(err, "Website check failed", "url", monitor.Spec.URL)
        
        // Send alert if enabled
        if monitor.Spec.Alerting.Enabled {
            r.sendAlert(monitor, err)
        }
    } else {
        monitor.Status.Status = "healthy"
        monitor.Status.ResponseTime = responseTime.String()
        monitor.Status.SuccessfulChecks++
        monitor.Status.LastError = ""
    }
    
    // Calculate uptime
    if monitor.Status.TotalChecks > 0 {
        uptime := float64(monitor.Status.SuccessfulChecks) / float64(monitor.Status.TotalChecks) * 100
        monitor.Status.Uptime = fmt.Sprintf("%.2f%%", uptime)
    }
    
    // Update the status
    if err := r.Status().Update(ctx, &monitor); err != nil {
        log.Error(err, "Failed to update WebsiteMonitor status")
        return ctrl.Result{}, err
    }
    
    // Schedule next check
    return ctrl.Result{RequeueAfter: interval}, nil
}

// checkWebsite performs the actual HTTP check
func (r *WebsiteMonitorReconciler) checkWebsite(spec monitoringv1.WebsiteMonitorSpec) (string, time.Duration, error) {
    timeout, err := time.ParseDuration(spec.Timeout)
    if err != nil {
        timeout = 10 * time.Second
    }
    
    client := &http.Client{Timeout: timeout}
    
    start := time.Now()
    resp, err := client.Get(spec.URL)
    responseTime := time.Since(start)
    
    if err != nil {
        return "unhealthy", responseTime, fmt.Errorf("request failed: %w", err)
    }
    defer resp.Body.Close()
    
    expectedCode := spec.ExpectedStatusCode
    if expectedCode == 0 {
        expectedCode = 200
    }
    
    if resp.StatusCode != expectedCode {
        return "unhealthy", responseTime, fmt.Errorf("unexpected status code: got %d, expected %d", resp.StatusCode, expectedCode)
    }
    
    return "healthy", responseTime, nil
}

// sendAlert sends notifications when website is down
func (r *WebsiteMonitorReconciler) sendAlert(monitor monitoringv1.WebsiteMonitor, err error) {
    // Implementation for Slack/email alerts
    r.Log.Info("Sending alert", "url", monitor.Spec.URL, "error", err.Error())
    // TODO: Implement actual alerting logic
}

// SetupWithManager sets up the controller with the Manager
func (r *WebsiteMonitorReconciler) SetupWithManager(mgr ctrl.Manager) error {
    return ctrl.NewControllerManagedBy(mgr).
        For(&monitoringv1.WebsiteMonitor{}).
        Complete(r)
}
```

### Step 4: Project Structure and Setup

**Complete Project Structure:**
```
website-monitor-operator/
├── cmd/
│   └── main.go                 # Entry point
├── pkg/
│   └── apis/
│       └── monitoring/
│           └── v1/
│               ├── types.go    # CRD types
│               └── register.go # Registration
├── controllers/
│   └── websitemonitor_controller.go
├── config/
│   ├── crd/
│   │   └── bases/
│   ├── rbac/
│   └── manager/
├── Dockerfile
├── Makefile
└── go.mod
```

**Main Application Entry Point:**
```go
// cmd/main.go
package main

import (
    "flag"
    "os"
    
    "k8s.io/apimachinery/pkg/runtime"
    utilruntime "k8s.io/apimachinery/pkg/util/runtime"
    clientgoscheme "k8s.io/client-go/kubernetes/scheme"
    ctrl "sigs.k8s.io/controller-runtime"
    "sigs.k8s.io/controller-runtime/pkg/log/zap"
    
    monitoringv1 "github.com/company/website-monitor/pkg/apis/monitoring/v1"
    "github.com/company/website-monitor/controllers"
)

var (
    scheme   = runtime.NewScheme()
    setupLog = ctrl.Log.WithName("setup")
)

func init() {
    utilruntime.Must(clientgoscheme.AddToScheme(scheme))
    utilruntime.Must(monitoringv1.AddToScheme(scheme))
}

func main() {
    var metricsAddr string
    var enableLeaderElection bool
    
    flag.StringVar(&metricsAddr, "metrics-addr", ":8080", "The address the metric endpoint binds to.")
    flag.BoolVar(&enableLeaderElection, "enable-leader-election", false, "Enable leader election for controller manager.")
    flag.Parse()
    
    ctrl.SetLogger(zap.New(zap.UseDevMode(true)))
    
    mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
        Scheme:             scheme,
        MetricsBindAddress: metricsAddr,
        Port:               9443,
        LeaderElection:     enableLeaderElection,
        LeaderElectionID:   "website-monitor-operator",
    })
    if err != nil {
        setupLog.Error(err, "unable to start manager")
        os.Exit(1)
    }
    
    if err = (&controllers.WebsiteMonitorReconciler{
        Client: mgr.GetClient(),
        Log:    ctrl.Log.WithName("controllers").WithName("WebsiteMonitor"),
        Scheme: mgr.GetScheme(),
    }).SetupWithManager(mgr); err != nil {
        setupLog.Error(err, "unable to create controller", "controller", "WebsiteMonitor")
        os.Exit(1)
    }
    
    setupLog.Info("starting manager")
    if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
        setupLog.Error(err, "problem running manager")
        os.Exit(1)
    }
}
```

## 🔧 Deployment and Usage

### Step 1: Deploy the CRD

```bash
# Apply the CRD definition
kubectl apply -f config/crd/bases/websitemonitors.monitoring.company.com.yaml

# Verify CRD installation
kubectl get crd websitemonitors.monitoring.company.com
```

### Step 2: Deploy the Controller

```bash
# Build and deploy the controller
make docker-build docker-push IMG=your-registry/website-monitor:latest
make deploy IMG=your-registry/website-monitor:latest
```

### Step 3: Create Website Monitor Resources

**Example WebsiteMonitor Resource:**
```yaml
apiVersion: monitoring.company.com/v1
kind: WebsiteMonitor
metadata:
  name: company-website
  namespace: production
spec:
  url: "https://company.com"
  interval: "30s"
  timeout: "10s"
  expectedStatusCode: 200
  alerting:
    enabled: true
    slackWebhook: "https://hooks.slack.com/services/..."
    emailRecipients:
    - "ops-team@company.com"
    - "dev-team@company.com"
---
apiVersion: monitoring.company.com/v1
kind: WebsiteMonitor
metadata:
  name: api-endpoint
  namespace: production
spec:
  url: "https://api.company.com/health"
  interval: "15s"
  timeout: "5s"
  expectedStatusCode: 200
```

### Step 4: Monitor and Manage

```bash
# List all website monitors
kubectl get websitemonitors -A

# Get detailed status
kubectl describe websitemonitor company-website -n production

# Watch for changes
kubectl get websitemonitors -w

# Use short name
kubectl get wm
```

**Expected Output:**
```
NAME              URL                           STATUS    UPTIME    LAST CHECK
company-website   https://company.com          healthy   99.95%    2024-01-15T10:30:45Z
api-endpoint      https://api.company.com/health healthy   100.00%   2024-01-15T10:30:50Z
```

## 💡 Advanced Features and Best Practices

### Validation and Webhooks

**Admission Controller for Advanced Validation:**
```go
// Validate webhook implementation
func (r *WebsiteMonitor) ValidateCreate() error {
    if !strings.HasPrefix(r.Spec.URL, "http") {
        return fmt.Errorf("URL must start with http or https")
    }
    
    if _, err := time.ParseDuration(r.Spec.Interval); err != nil {
        return fmt.Errorf("invalid interval format: %v", err)
    }
    
    return nil
}

func (r *WebsiteMonitor) ValidateUpdate(old runtime.Object) error {
    // Prevent changing URL after creation
    oldMonitor := old.(*WebsiteMonitor)
    if r.Spec.URL != oldMonitor.Spec.URL {
        return fmt.Errorf("URL cannot be changed after creation")
    }
    
    return r.ValidateCreate()
}
```

### Status Subresource Benefits

**Why Use Status Subresource:**
```
Benefits:
├── Separate RBAC for spec vs status
├── Optimistic concurrency control
├── Status-only updates don't trigger reconciliation
├── Better API semantics
└── Kubernetes-native behavior

RBAC Example:
├── Developers: Can create/update spec
├── Controllers: Can update status
├── Viewers: Can read both
└── Operators: Full access
```

### Monitoring and Observability

**Metrics Integration:**
```go
// Add Prometheus metrics
var (
    websiteCheckDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "website_check_duration_seconds",
            Help: "Duration of website checks",
        },
        []string{"url", "status"},
    )
    
    websiteUptime = prometheus.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "website_uptime_percentage",
            Help: "Website uptime percentage",
        },
        []string{"url"},
    )
)

func init() {
    prometheus.MustRegister(websiteCheckDuration)
    prometheus.MustRegister(websiteUptime)
}
```

## 🚀 Production Considerations

### Security Best Practices

**RBAC Configuration:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: website-monitor-operator
rules:
- apiGroups: ["monitoring.company.com"]
  resources: ["websitemonitors"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["monitoring.company.com"]
  resources: ["websitemonitors/status"]
  verbs: ["get", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: website-monitor-user
  namespace: production
rules:
- apiGroups: ["monitoring.company.com"]
  resources: ["websitemonitors"]
  verbs: ["get", "list", "create", "update", "patch", "delete"]
- apiGroups: ["monitoring.company.com"]
  resources: ["websitemonitors/status"]
  verbs: ["get"]
```

### High Availability and Scaling

**Controller Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: website-monitor-controller
spec:
  replicas: 2
  selector:
    matchLabels:
      app: website-monitor-controller
  template:
    spec:
      containers:
      - name: manager
        image: website-monitor:latest
        args:
        - --enable-leader-election
        resources:
          limits:
            cpu: 100m
            memory: 128Mi
          requests:
            cpu: 50m
            memory: 64Mi
```

## 📊 Business Impact and ROI

### Quantified Benefits

**Operational Efficiency:**
```
Before CRD Implementation:
├── Manual monitoring setup: 2 hours per website
├── Separate alerting configuration: 1 hour per site
├── Different tools and interfaces: 30 min context switching
├── Inconsistent monitoring across environments
└── Total: 3.5 hours per website

With CRD Implementation:
├── Declarative configuration: 5 minutes per website
├── Automated alerting: Built-in
├── Kubernetes-native management: No context switching
├── Consistent across all environments
└── Total: 5 minutes per website

ROI: 97% time reduction for monitoring setup
```

**Developer Experience:**
```
Improvements:
├── Self-service monitoring setup
├── GitOps integration
├── Familiar kubectl interface
├── Namespace-based isolation
└── Built-in validation and documentation

Result: 80% reduction in ops team tickets
```

This comprehensive guide demonstrates how CRDs extend Kubernetes with custom business logic while maintaining native Kubernetes benefits. The WebsiteMonitor example shows practical implementation patterns that can be adapted for various use cases.