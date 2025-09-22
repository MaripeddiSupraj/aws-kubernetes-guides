# Google Cloud KMS: Complete Data Encryption Guide with Real Application

## 🎯 Understanding Cloud Key Management: The "Why" Before the "How"

### The Data Encryption Challenge

**Traditional Encryption Problems:**
```
Common encryption mistakes in applications:
• Hardcoded encryption keys in source code
• Keys stored in configuration files
• Same key used across all environments
• No key rotation strategy
• Keys accessible to all developers
• Manual key management processes
• No audit trail for key usage
• Compliance violations (GDPR, HIPAA, PCI DSS)
```

**Real-World Impact:**
```
Data breach statistics:
• 83% of breaches involve hardcoded credentials
• Average cost of data breach: $4.45 million
• 95% of successful cyber attacks are due to human error
• Compliance fines: Up to 4% of annual revenue (GDPR)
• Recovery time: 287 days average to identify and contain
```

**Business Requirements for Enterprise Encryption:**
```
Security Requirements:
• Centralized key management
• Hardware Security Module (HSM) protection
• Automatic key rotation
• Fine-grained access control
• Comprehensive audit logging
• Multi-region key availability

Compliance Requirements:
• GDPR: Personal data protection
• HIPAA: Healthcare data encryption
• PCI DSS: Payment card data security
• SOX: Financial data integrity
• ISO 27001: Information security management
```

### Why Google Cloud KMS?

**Google Cloud KMS Value Proposition:**

**Security Features:**
• FIPS 140-2 Level 3 certified HSMs
• Automatic key rotation
• Envelope encryption for large data
• Integration with Google Cloud services
• Zero-knowledge architecture
• Global key replication

**Operational Benefits:**
• Centralized key management
• API-driven automation
• Integration with IAM
• Audit logging with Cloud Audit Logs
• Multi-cloud key management
• Cost-effective pricing model

**Business Impact Examples:**

**Healthcare SaaS Company:**
• Challenge: HIPAA compliance for patient data
• Risk: $1.5M potential fines, reputation damage
• Solution: GCP KMS for patient data encryption
• Result: Successful HIPAA audit, zero violations

**Financial Services Platform:**
• Challenge: PCI DSS compliance for payment data
• Risk: Loss of payment processing license
• Solution: KMS envelope encryption for card data
• Result: PCI DSS Level 1 certification achieved

**E-commerce Marketplace:**
• Challenge: GDPR compliance for EU customer data
• Risk: 4% of annual revenue in fines
• Solution: KMS with regional key management
• Result: GDPR compliance, customer trust increased

## 🏗️ Google Cloud KMS Architecture Deep Dive

### Understanding KMS Components

**KMS Hierarchy:**
```
Organization
└── Project
    └── Location (Region/Global)
        └── Key Ring
            └── Key
                └── Key Version
```

**Key Components Explained:**

**Key Ring:**
• Logical grouping of keys
• Defines location and access policies
• Cannot be deleted (only disabled)
• Used for organizing keys by purpose/environment

**Cryptographic Key:**
• The actual encryption key
• Has multiple versions for rotation
• Supports different algorithms (AES256, RSA, EC)
• Can be symmetric or asymmetric

**Key Version:**
• Specific instance of a key
• Enables key rotation
• Can be enabled, disabled, or destroyed
• Primary version used for new operations

**Key Types:**

**Symmetric Keys:**
• Same key for encryption and decryption
• Faster performance
• Used for data encryption
• AES-256 algorithm

**Asymmetric Keys:**
• Different keys for encryption/decryption
• Public/private key pairs
• Used for digital signatures
• RSA or Elliptic Curve algorithms

### Envelope Encryption Pattern

**How Envelope Encryption Works:**
```
1. Application generates Data Encryption Key (DEK)
2. DEK encrypts your actual data (fast, local operation)
3. KMS Key Encryption Key (KEK) encrypts the DEK
4. Store encrypted data + encrypted DEK together
5. To decrypt: KMS decrypts DEK, DEK decrypts data
```

**Benefits of Envelope Encryption:**
• Reduces KMS API calls (cost optimization)
• Enables offline encryption/decryption
• Better performance for large data
• Supports key rotation without re-encrypting data
• Network latency doesn't affect data operations

## 🚀 Real-World Implementation: Customer Data Management System

### Business Scenario

**Application Requirements:**
```
Customer Management SaaS Platform:
• Store customer personal information (PII)
• Handle payment card data (PCI DSS)
• Support EU customers (GDPR compliance)
• Multi-tenant architecture
• Real-time data access requirements
• Audit trail for all data access
```

**Security Requirements:**
```
Data Classification:
• Level 1: Public data (no encryption needed)
• Level 2: Internal data (basic encryption)
• Level 3: Sensitive PII (KMS encryption required)
• Level 4: Payment data (KMS + additional controls)

Compliance Requirements:
• GDPR: Right to be forgotten
• PCI DSS: Card data encryption
• SOX: Financial data integrity
• HIPAA: Healthcare data protection (if applicable)
```

### Step 1: GCP KMS Setup and Configuration

**Enable Required APIs:**
```bash
# Enable Cloud KMS API
gcloud services enable cloudkms.googleapis.com

# Enable Cloud Resource Manager API
gcloud services enable cloudresourcemanager.googleapis.com

# Enable IAM API
gcloud services enable iam.googleapis.com
```

**Create Key Ring and Keys:**
```bash
# Set project and location variables
export PROJECT_ID="your-project-id"
export LOCATION="us-central1"
export KEY_RING_NAME="customer-data-keyring"

# Create key ring for customer data
gcloud kms keyrings create $KEY_RING_NAME \
    --location=$LOCATION \
    --project=$PROJECT_ID

# Create symmetric key for PII data encryption
gcloud kms keys create customer-pii-key \
    --location=$LOCATION \
    --keyring=$KEY_RING_NAME \
    --purpose=encryption \
    --rotation-period=90d \
    --next-rotation-time=$(date -d "+90 days" +%Y-%m-%dT%H:%M:%S%z)

# Create key for payment data (higher security)
gcloud kms keys create payment-data-key \
    --location=$LOCATION \
    --keyring=$KEY_RING_NAME \
    --purpose=encryption \
    --rotation-period=30d \
    --next-rotation-time=$(date -d "+30 days" +%Y-%m-%dT%H:%M:%S%z)

# Create asymmetric key for digital signatures
gcloud kms keys create audit-signature-key \
    --location=$LOCATION \
    --keyring=$KEY_RING_NAME \
    --purpose=asymmetric-signing \
    --default-algorithm=rsa-sign-pss-2048-sha256
```

**Configure IAM Permissions:**
```bash
# Create service account for application
gcloud iam service-accounts create customer-app-sa \
    --display-name="Customer Application Service Account" \
    --description="Service account for customer data encryption"

# Grant KMS permissions to service account
gcloud kms keys add-iam-policy-binding customer-pii-key \
    --location=$LOCATION \
    --keyring=$KEY_RING_NAME \
    --member="serviceAccount:customer-app-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudkms.cryptoKeyEncrypterDecrypter"

gcloud kms keys add-iam-policy-binding payment-data-key \
    --location=$LOCATION \
    --keyring=$KEY_RING_NAME \
    --member="serviceAccount:customer-app-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudkms.cryptoKeyEncrypterDecrypter"

# Create and download service account key
gcloud iam service-accounts keys create ~/customer-app-key.json \
    --iam-account=customer-app-sa@$PROJECT_ID.iam.gserviceaccount.com
```

### Step 2: Application Implementation with KMS Integration

**Go Application with KMS Encryption:**

```go
// main.go - Customer Data Management System
package main

import (
    "context"
    "crypto/rand"
    "crypto/aes"
    "crypto/cipher"
    "encoding/base64"
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "os"
    "time"

    kms "cloud.google.com/go/kms/apiv1"
    "cloud.google.com/go/kms/apiv1/kmspb"
    "github.com/gorilla/mux"
    "google.golang.org/api/option"
)

// Configuration
type Config struct {
    ProjectID       string
    LocationID      string
    KeyRingID       string
    PIIKeyID        string
    PaymentKeyID    string
    ServiceAccount  string
}

// Customer represents customer data with different sensitivity levels
type Customer struct {
    ID              string    `json:"id"`
    Name            string    `json:"name"`            // Level 3: PII - KMS encrypted
    Email           string    `json:"email"`           // Level 3: PII - KMS encrypted
    Phone           string    `json:"phone"`           // Level 3: PII - KMS encrypted
    Address         string    `json:"address"`         // Level 3: PII - KMS encrypted
    PaymentCard     string    `json:"payment_card"`    // Level 4: Payment - KMS encrypted
    CompanyName     string    `json:"company_name"`    // Level 2: Internal - basic encryption
    CreatedAt       time.Time `json:"created_at"`
    LastModified    time.Time `json:"last_modified"`
}

// EncryptedCustomer represents how customer data is stored
type EncryptedCustomer struct {
    ID                   string    `json:"id"`
    EncryptedName        string    `json:"encrypted_name"`
    EncryptedEmail       string    `json:"encrypted_email"`
    EncryptedPhone       string    `json:"encrypted_phone"`
    EncryptedAddress     string    `json:"encrypted_address"`
    EncryptedPaymentCard string    `json:"encrypted_payment_card"`
    CompanyName          string    `json:"company_name"` // Not encrypted for this example
    CreatedAt            time.Time `json:"created_at"`
    LastModified         time.Time `json:"last_modified"`
}

// KMSService handles all KMS operations
type KMSService struct {
    client *kms.KeyManagementClient
    config *Config
}

// CustomerService handles customer operations with encryption
type CustomerService struct {
    kmsService *KMSService
    customers  map[string]*EncryptedCustomer // In-memory store for demo
}

func main() {
    // Load configuration
    config := &Config{
        ProjectID:      getEnv("PROJECT_ID", "your-project-id"),
        LocationID:     getEnv("LOCATION_ID", "us-central1"),
        KeyRingID:      getEnv("KEY_RING_ID", "customer-data-keyring"),
        PIIKeyID:       getEnv("PII_KEY_ID", "customer-pii-key"),
        PaymentKeyID:   getEnv("PAYMENT_KEY_ID", "payment-data-key"),
        ServiceAccount: getEnv("GOOGLE_APPLICATION_CREDENTIALS", ""),
    }

    // Initialize KMS service
    kmsService, err := NewKMSService(config)
    if err != nil {
        log.Fatalf("Failed to initialize KMS service: %v", err)
    }
    defer kmsService.Close()

    // Initialize customer service
    customerService := &CustomerService{
        kmsService: kmsService,
        customers:  make(map[string]*EncryptedCustomer),
    }

    // Setup HTTP routes
    router := mux.NewRouter()
    router.HandleFunc("/customers", customerService.CreateCustomer).Methods("POST")
    router.HandleFunc("/customers/{id}", customerService.GetCustomer).Methods("GET")
    router.HandleFunc("/customers/{id}", customerService.UpdateCustomer).Methods("PUT")
    router.HandleFunc("/customers/{id}", customerService.DeleteCustomer).Methods("DELETE")
    router.HandleFunc("/health", healthCheck).Methods("GET")

    // Start server
    log.Println("Customer Data Management System starting on :8080")
    log.Println("KMS Integration: ENABLED")
    log.Printf("Using KMS Key Ring: %s", config.KeyRingID)
    log.Fatal(http.ListenAndServe(":8080", router))
}

// NewKMSService creates a new KMS service client
func NewKMSService(config *Config) (*KMSService, error) {
    ctx := context.Background()
    
    var client *kms.KeyManagementClient
    var err error
    
    if config.ServiceAccount != "" {
        client, err = kms.NewKeyManagementClient(ctx, option.WithCredentialsFile(config.ServiceAccount))
    } else {
        client, err = kms.NewKeyManagementClient(ctx)
    }
    
    if err != nil {
        return nil, fmt.Errorf("failed to create KMS client: %w", err)
    }

    return &KMSService{
        client: client,
        config: config,
    }, nil
}

// Close closes the KMS client
func (k *KMSService) Close() error {
    return k.client.Close()
}

// EncryptPII encrypts PII data using KMS
func (k *KMSService) EncryptPII(ctx context.Context, plaintext string) (string, error) {
    if plaintext == "" {
        return "", nil
    }

    keyName := fmt.Sprintf("projects/%s/locations/%s/keyRings/%s/cryptoKeys/%s",
        k.config.ProjectID, k.config.LocationID, k.config.KeyRingID, k.config.PIIKeyID)

    req := &kmspb.EncryptRequest{
        Name:      keyName,
        Plaintext: []byte(plaintext),
    }

    resp, err := k.client.Encrypt(ctx, req)
    if err != nil {
        return "", fmt.Errorf("failed to encrypt PII data: %w", err)
    }

    return base64.StdEncoding.EncodeToString(resp.Ciphertext), nil
}

// DecryptPII decrypts PII data using KMS
func (k *KMSService) DecryptPII(ctx context.Context, ciphertext string) (string, error) {
    if ciphertext == "" {
        return "", nil
    }

    keyName := fmt.Sprintf("projects/%s/locations/%s/keyRings/%s/cryptoKeys/%s",
        k.config.ProjectID, k.config.LocationID, k.config.KeyRingID, k.config.PIIKeyID)

    ciphertextBytes, err := base64.StdEncoding.DecodeString(ciphertext)
    if err != nil {
        return "", fmt.Errorf("failed to decode ciphertext: %w", err)
    }

    req := &kmspb.DecryptRequest{
        Name:       keyName,
        Ciphertext: ciphertextBytes,
    }

    resp, err := k.client.Decrypt(ctx, req)
    if err != nil {
        return "", fmt.Errorf("failed to decrypt PII data: %w", err)
    }

    return string(resp.Plaintext), nil
}

// EncryptPaymentData encrypts payment data using KMS with envelope encryption
func (k *KMSService) EncryptPaymentData(ctx context.Context, plaintext string) (string, error) {
    if plaintext == "" {
        return "", nil
    }

    // Generate Data Encryption Key (DEK)
    dek := make([]byte, 32) // 256-bit key
    if _, err := rand.Read(dek); err != nil {
        return "", fmt.Errorf("failed to generate DEK: %w", err)
    }

    // Encrypt data with DEK (envelope encryption)
    block, err := aes.NewCipher(dek)
    if err != nil {
        return "", fmt.Errorf("failed to create cipher: %w", err)
    }

    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return "", fmt.Errorf("failed to create GCM: %w", err)
    }

    nonce := make([]byte, gcm.NonceSize())
    if _, err := rand.Read(nonce); err != nil {
        return "", fmt.Errorf("failed to generate nonce: %w", err)
    }

    encryptedData := gcm.Seal(nonce, nonce, []byte(plaintext), nil)

    // Encrypt DEK with KMS
    keyName := fmt.Sprintf("projects/%s/locations/%s/keyRings/%s/cryptoKeys/%s",
        k.config.ProjectID, k.config.LocationID, k.config.KeyRingID, k.config.PaymentKeyID)

    req := &kmspb.EncryptRequest{
        Name:      keyName,
        Plaintext: dek,
    }

    resp, err := k.client.Encrypt(ctx, req)
    if err != nil {
        return "", fmt.Errorf("failed to encrypt DEK: %w", err)
    }

    // Combine encrypted DEK and encrypted data
    envelope := map[string]string{
        "encrypted_dek":  base64.StdEncoding.EncodeToString(resp.Ciphertext),
        "encrypted_data": base64.StdEncoding.EncodeToString(encryptedData),
    }

    envelopeJSON, err := json.Marshal(envelope)
    if err != nil {
        return "", fmt.Errorf("failed to marshal envelope: %w", err)
    }

    return base64.StdEncoding.EncodeToString(envelopeJSON), nil
}

// DecryptPaymentData decrypts payment data using envelope encryption
func (k *KMSService) DecryptPaymentData(ctx context.Context, envelopeData string) (string, error) {
    if envelopeData == "" {
        return "", nil
    }

    // Decode envelope
    envelopeBytes, err := base64.StdEncoding.DecodeString(envelopeData)
    if err != nil {
        return "", fmt.Errorf("failed to decode envelope: %w", err)
    }

    var envelope map[string]string
    if err := json.Unmarshal(envelopeBytes, &envelope); err != nil {
        return "", fmt.Errorf("failed to unmarshal envelope: %w", err)
    }

    // Decrypt DEK with KMS
    keyName := fmt.Sprintf("projects/%s/locations/%s/keyRings/%s/cryptoKeys/%s",
        k.config.ProjectID, k.config.LocationID, k.config.KeyRingID, k.config.PaymentKeyID)

    encryptedDEK, err := base64.StdEncoding.DecodeString(envelope["encrypted_dek"])
    if err != nil {
        return "", fmt.Errorf("failed to decode encrypted DEK: %w", err)
    }

    req := &kmspb.DecryptRequest{
        Name:       keyName,
        Ciphertext: encryptedDEK,
    }

    resp, err := k.client.Decrypt(ctx, req)
    if err != nil {
        return "", fmt.Errorf("failed to decrypt DEK: %w", err)
    }

    // Decrypt data with DEK
    encryptedData, err := base64.StdEncoding.DecodeString(envelope["encrypted_data"])
    if err != nil {
        return "", fmt.Errorf("failed to decode encrypted data: %w", err)
    }

    block, err := aes.NewCipher(resp.Plaintext)
    if err != nil {
        return "", fmt.Errorf("failed to create cipher: %w", err)
    }

    gcm, err := cipher.NewGCM(block)
    if err != nil {
        return "", fmt.Errorf("failed to create GCM: %w", err)
    }

    nonceSize := gcm.NonceSize()
    if len(encryptedData) < nonceSize {
        return "", fmt.Errorf("ciphertext too short")
    }

    nonce, ciphertext := encryptedData[:nonceSize], encryptedData[nonceSize:]
    plaintext, err := gcm.Open(nil, nonce, ciphertext, nil)
    if err != nil {
        return "", fmt.Errorf("failed to decrypt data: %w", err)
    }

    return string(plaintext), nil
}

// CreateCustomer handles customer creation with encryption
func (cs *CustomerService) CreateCustomer(w http.ResponseWriter, r *http.Request) {
    var customer Customer
    if err := json.NewDecoder(r.Body).Decode(&customer); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }

    ctx := r.Context()
    
    // Generate customer ID
    customer.ID = fmt.Sprintf("cust_%d", time.Now().Unix())
    customer.CreatedAt = time.Now()
    customer.LastModified = time.Now()

    // Encrypt PII data
    encryptedName, err := cs.kmsService.EncryptPII(ctx, customer.Name)
    if err != nil {
        log.Printf("Failed to encrypt name: %v", err)
        http.Error(w, "Encryption failed", http.StatusInternalServerError)
        return
    }

    encryptedEmail, err := cs.kmsService.EncryptPII(ctx, customer.Email)
    if err != nil {
        log.Printf("Failed to encrypt email: %v", err)
        http.Error(w, "Encryption failed", http.StatusInternalServerError)
        return
    }

    encryptedPhone, err := cs.kmsService.EncryptPII(ctx, customer.Phone)
    if err != nil {
        log.Printf("Failed to encrypt phone: %v", err)
        http.Error(w, "Encryption failed", http.StatusInternalServerError)
        return
    }

    encryptedAddress, err := cs.kmsService.EncryptPII(ctx, customer.Address)
    if err != nil {
        log.Printf("Failed to encrypt address: %v", err)
        http.Error(w, "Encryption failed", http.StatusInternalServerError)
        return
    }

    // Encrypt payment data with envelope encryption
    encryptedPaymentCard, err := cs.kmsService.EncryptPaymentData(ctx, customer.PaymentCard)
    if err != nil {
        log.Printf("Failed to encrypt payment card: %v", err)
        http.Error(w, "Encryption failed", http.StatusInternalServerError)
        return
    }

    // Create encrypted customer record
    encryptedCustomer := &EncryptedCustomer{
        ID:                   customer.ID,
        EncryptedName:        encryptedName,
        EncryptedEmail:       encryptedEmail,
        EncryptedPhone:       encryptedPhone,
        EncryptedAddress:     encryptedAddress,
        EncryptedPaymentCard: encryptedPaymentCard,
        CompanyName:          customer.CompanyName, // Not encrypted for demo
        CreatedAt:            customer.CreatedAt,
        LastModified:         customer.LastModified,
    }

    // Store encrypted customer
    cs.customers[customer.ID] = encryptedCustomer

    log.Printf("Customer created with KMS encryption: %s", customer.ID)
    
    // Return customer without sensitive data
    response := map[string]interface{}{
        "id":           customer.ID,
        "company_name": customer.CompanyName,
        "created_at":   customer.CreatedAt,
        "message":      "Customer created successfully with KMS encryption",
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}

// GetCustomer retrieves and decrypts customer data
func (cs *CustomerService) GetCustomer(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    customerID := vars["id"]

    encryptedCustomer, exists := cs.customers[customerID]
    if !exists {
        http.Error(w, "Customer not found", http.StatusNotFound)
        return
    }

    ctx := r.Context()

    // Decrypt PII data
    name, err := cs.kmsService.DecryptPII(ctx, encryptedCustomer.EncryptedName)
    if err != nil {
        log.Printf("Failed to decrypt name: %v", err)
        http.Error(w, "Decryption failed", http.StatusInternalServerError)
        return
    }

    email, err := cs.kmsService.DecryptPII(ctx, encryptedCustomer.EncryptedEmail)
    if err != nil {
        log.Printf("Failed to decrypt email: %v", err)
        http.Error(w, "Decryption failed", http.StatusInternalServerError)
        return
    }

    phone, err := cs.kmsService.DecryptPII(ctx, encryptedCustomer.EncryptedPhone)
    if err != nil {
        log.Printf("Failed to decrypt phone: %v", err)
        http.Error(w, "Decryption failed", http.StatusInternalServerError)
        return
    }

    address, err := cs.kmsService.DecryptPII(ctx, encryptedCustomer.EncryptedAddress)
    if err != nil {
        log.Printf("Failed to decrypt address: %v", err)
        http.Error(w, "Decryption failed", http.StatusInternalServerError)
        return
    }

    // Decrypt payment data (envelope encryption)
    paymentCard, err := cs.kmsService.DecryptPaymentData(ctx, encryptedCustomer.EncryptedPaymentCard)
    if err != nil {
        log.Printf("Failed to decrypt payment card: %v", err)
        http.Error(w, "Decryption failed", http.StatusInternalServerError)
        return
    }

    // Reconstruct customer object
    customer := Customer{
        ID:           encryptedCustomer.ID,
        Name:         name,
        Email:        email,
        Phone:        phone,
        Address:      address,
        PaymentCard:  maskPaymentCard(paymentCard), // Mask for security
        CompanyName:  encryptedCustomer.CompanyName,
        CreatedAt:    encryptedCustomer.CreatedAt,
        LastModified: encryptedCustomer.LastModified,
    }

    log.Printf("Customer data decrypted successfully: %s", customerID)

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(customer)
}

// UpdateCustomer updates customer data with re-encryption
func (cs *CustomerService) UpdateCustomer(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    customerID := vars["id"]

    _, exists := cs.customers[customerID]
    if !exists {
        http.Error(w, "Customer not found", http.StatusNotFound)
        return
    }

    var customer Customer
    if err := json.NewDecoder(r.Body).Decode(&customer); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }

    ctx := r.Context()
    customer.ID = customerID
    customer.LastModified = time.Now()

    // Re-encrypt all PII data (demonstrates key rotation compatibility)
    encryptedName, err := cs.kmsService.EncryptPII(ctx, customer.Name)
    if err != nil {
        log.Printf("Failed to encrypt name: %v", err)
        http.Error(w, "Encryption failed", http.StatusInternalServerError)
        return
    }

    encryptedEmail, err := cs.kmsService.EncryptPII(ctx, customer.Email)
    if err != nil {
        log.Printf("Failed to encrypt email: %v", err)
        http.Error(w, "Encryption failed", http.StatusInternalServerError)
        return
    }

    encryptedPhone, err := cs.kmsService.EncryptPII(ctx, customer.Phone)
    if err != nil {
        log.Printf("Failed to encrypt phone: %v", err)
        http.Error(w, "Encryption failed", http.StatusInternalServerError)
        return
    }

    encryptedAddress, err := cs.kmsService.EncryptPII(ctx, customer.Address)
    if err != nil {
        log.Printf("Failed to encrypt address: %v", err)
        http.Error(w, "Encryption failed", http.StatusInternalServerError)
        return
    }

    encryptedPaymentCard, err := cs.kmsService.EncryptPaymentData(ctx, customer.PaymentCard)
    if err != nil {
        log.Printf("Failed to encrypt payment card: %v", err)
        http.Error(w, "Encryption failed", http.StatusInternalServerError)
        return
    }

    // Update encrypted customer record
    cs.customers[customerID].EncryptedName = encryptedName
    cs.customers[customerID].EncryptedEmail = encryptedEmail
    cs.customers[customerID].EncryptedPhone = encryptedPhone
    cs.customers[customerID].EncryptedAddress = encryptedAddress
    cs.customers[customerID].EncryptedPaymentCard = encryptedPaymentCard
    cs.customers[customerID].CompanyName = customer.CompanyName
    cs.customers[customerID].LastModified = customer.LastModified

    log.Printf("Customer updated with KMS re-encryption: %s", customerID)

    response := map[string]interface{}{
        "id":            customerID,
        "last_modified": customer.LastModified,
        "message":       "Customer updated successfully with KMS re-encryption",
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}

// DeleteCustomer implements GDPR right to be forgotten
func (cs *CustomerService) DeleteCustomer(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    customerID := vars["id"]

    _, exists := cs.customers[customerID]
    if !exists {
        http.Error(w, "Customer not found", http.StatusNotFound)
        return
    }

    // Delete customer data (GDPR compliance)
    delete(cs.customers, customerID)

    log.Printf("Customer deleted (GDPR compliance): %s", customerID)

    response := map[string]interface{}{
        "id":      customerID,
        "message": "Customer data deleted successfully (GDPR compliance)",
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}

// Health check endpoint
func healthCheck(w http.ResponseWriter, r *http.Request) {
    response := map[string]interface{}{
        "status":    "healthy",
        "timestamp": time.Now(),
        "kms":       "enabled",
        "version":   "1.0.0",
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}

// Utility functions
func getEnv(key, defaultValue string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultValue
}

func maskPaymentCard(card string) string {
    if len(card) < 4 {
        return "****"
    }
    return "****-****-****-" + card[len(card)-4:]
}
```

### Step 3: Deployment and Testing

**Docker Configuration:**
```dockerfile
# Dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o customer-app .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /app/customer-app .
COPY --from=builder /app/customer-app-key.json .

EXPOSE 8080
CMD ["./customer-app"]
```

**Environment Configuration:**
```bash
# .env file
PROJECT_ID=your-gcp-project-id
LOCATION_ID=us-central1
KEY_RING_ID=customer-data-keyring
PII_KEY_ID=customer-pii-key
PAYMENT_KEY_ID=payment-data-key
GOOGLE_APPLICATION_CREDENTIALS=./customer-app-key.json
```

**Testing the Application:**
```bash
# Start the application
export GOOGLE_APPLICATION_CREDENTIALS="./customer-app-key.json"
export PROJECT_ID="your-project-id"
go run main.go

# Test customer creation with KMS encryption
curl -X POST http://localhost:8080/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567",
    "address": "123 Main St, Anytown, USA",
    "payment_card": "4532-1234-5678-9012",
    "company_name": "Acme Corp"
  }'

# Response shows data is encrypted
{
  "id": "cust_1703123456",
  "company_name": "Acme Corp",
  "created_at": "2023-12-20T10:30:45Z",
  "message": "Customer created successfully with KMS encryption"
}

# Retrieve customer (data is decrypted on-the-fly)
curl http://localhost:8080/customers/cust_1703123456

# Response shows decrypted data
{
  "id": "cust_1703123456",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1-555-123-4567",
  "address": "123 Main St, Anytown, USA",
  "payment_card": "****-****-****-9012",
  "company_name": "Acme Corp",
  "created_at": "2023-12-20T10:30:45Z",
  "last_modified": "2023-12-20T10:30:45Z"
}
```

### Step 4: Monitoring and Audit

**Cloud Audit Logs Configuration:**
```bash
# Enable audit logs for KMS
gcloud logging sinks create kms-audit-sink \
    bigquery.googleapis.com/projects/$PROJECT_ID/datasets/security_audit \
    --log-filter='protoPayload.serviceName="cloudkms.googleapis.com"'

# Create BigQuery dataset for audit logs
bq mk --dataset $PROJECT_ID:security_audit
```

**Monitoring KMS Usage:**
```bash
# Create alerting policy for unusual KMS activity
gcloud alpha monitoring policies create \
    --policy-from-file=kms-monitoring-policy.yaml
```

**KMS Monitoring Policy:**
```yaml
# kms-monitoring-policy.yaml
displayName: "KMS Unusual Activity Alert"
conditions:
  - displayName: "High KMS API calls"
    conditionThreshold:
      filter: 'resource.type="cloudkms_key"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 1000
      duration: 300s
alertStrategy:
  autoClose: 86400s
notificationChannels:
  - "projects/your-project-id/notificationChannels/your-channel-id"
```

## 🔒 Security Best Practices and Compliance

### Key Management Best Practices

**Key Rotation Strategy:**
```bash
# Automatic rotation (recommended)
gcloud kms keys update customer-pii-key \
    --location=$LOCATION \
    --keyring=$KEY_RING_NAME \
    --rotation-period=90d \
    --next-rotation-time=$(date -d "+90 days" +%Y-%m-%dT%H:%M:%S%z)

# Manual rotation for sensitive keys
gcloud kms keys versions create customer-pii-key \
    --location=$LOCATION \
    --keyring=$KEY_RING_NAME \
    --primary

# Disable old key version
gcloud kms keys versions disable 1 \
    --key=customer-pii-key \
    --location=$LOCATION \
    --keyring=$KEY_RING_NAME
```

**Access Control Best Practices:**
```bash
# Principle of least privilege
gcloud kms keys add-iam-policy-binding customer-pii-key \
    --location=$LOCATION \
    --keyring=$KEY_RING_NAME \
    --member="serviceAccount:app-sa@project.iam.gserviceaccount.com" \
    --role="roles/cloudkms.cryptoKeyEncrypterDecrypter" \
    --condition='expression=request.time < timestamp("2024-12-31T23:59:59Z"),title=Temporary Access,description=Access expires end of year'

# Separate keys for different data types
# PII data: 90-day rotation
# Payment data: 30-day rotation  
# Audit logs: Asymmetric signing keys
```

### Compliance Implementation

**GDPR Compliance:**
```go
// GDPR Right to be Forgotten implementation
func (cs *CustomerService) ForgetCustomer(customerID string) error {
    // 1. Delete encrypted data
    delete(cs.customers, customerID)
    
    // 2. Log deletion for audit
    log.Printf("GDPR: Customer data deleted: %s", customerID)
    
    // 3. Notify downstream systems
    // notifyDownstreamSystems(customerID, "DELETED")
    
    return nil
}

// GDPR Data Portability
func (cs *CustomerService) ExportCustomerData(ctx context.Context, customerID string) (*Customer, error) {
    encryptedCustomer, exists := cs.customers[customerID]
    if !exists {
        return nil, fmt.Errorf("customer not found")
    }
    
    // Decrypt all data for export
    customer, err := cs.decryptCustomer(ctx, encryptedCustomer)
    if err != nil {
        return nil, err
    }
    
    log.Printf("GDPR: Customer data exported: %s", customerID)
    return customer, nil
}
```

**PCI DSS Compliance:**
```go
// PCI DSS compliant payment data handling
func (cs *CustomerService) ProcessPayment(ctx context.Context, customerID string, amount float64) error {
    // 1. Retrieve encrypted payment data
    encryptedCustomer, exists := cs.customers[customerID]
    if !exists {
        return fmt.Errorf("customer not found")
    }
    
    // 2. Decrypt payment card (envelope encryption)
    paymentCard, err := cs.kmsService.DecryptPaymentData(ctx, encryptedCustomer.EncryptedPaymentCard)
    if err != nil {
        return fmt.Errorf("failed to decrypt payment data: %w", err)
    }
    
    // 3. Process payment (never log actual card number)
    log.Printf("PCI DSS: Processing payment for customer %s, amount $%.2f", customerID, amount)
    
    // 4. Clear sensitive data from memory
    paymentCard = ""
    
    return nil
}
```

## 📊 Performance Optimization and Cost Management

### Envelope Encryption Benefits

**Performance Comparison:**
```
Direct KMS Encryption (1MB file):
• KMS API calls: 1 per operation
• Latency: ~100ms per call
• Cost: $0.03 per 10,000 operations
• Network dependency: Required for each operation

Envelope Encryption (1MB file):
• KMS API calls: 1 per DEK (reusable)
• Latency: ~5ms for local encryption + 100ms for DEK
• Cost: $0.03 per 10,000 DEK operations
• Network dependency: Only for DEK operations
```

**Cost Optimization Strategies:**
```go
// DEK caching for performance
type DEKCache struct {
    cache map[string]*CachedDEK
    mutex sync.RWMutex
}

type CachedDEK struct {
    Key       []byte
    ExpiresAt time.Time
}

func (d *DEKCache) GetOrCreateDEK(ctx context.Context, keyName string) ([]byte, error) {
    d.mutex.RLock()
    if cached, exists := d.cache[keyName]; exists && time.Now().Before(cached.ExpiresAt) {
        d.mutex.RUnlock()
        return cached.Key, nil
    }
    d.mutex.RUnlock()
    
    // Generate new DEK and encrypt with KMS
    dek := make([]byte, 32)
    rand.Read(dek)
    
    // Cache DEK for 1 hour
    d.mutex.Lock()
    d.cache[keyName] = &CachedDEK{
        Key:       dek,
        ExpiresAt: time.Now().Add(time.Hour),
    }
    d.mutex.Unlock()
    
    return dek, nil
}
```

### Monitoring and Alerting

**KMS Metrics Dashboard:**
```bash
# Create custom metrics for application
gcloud logging metrics create kms_encryption_operations \
    --description="Count of KMS encryption operations" \
    --log-filter='jsonPayload.message:"KMS encryption"'

gcloud logging metrics create kms_decryption_operations \
    --description="Count of KMS decryption operations" \
    --log-filter='jsonPayload.message:"KMS decryption"'

# Create alerting policies
gcloud alpha monitoring policies create \
    --policy-from-file=kms-alerts.yaml
```

## 💰 Business Impact and ROI Analysis

### Cost-Benefit Analysis

**Traditional Encryption Costs:**
```
Manual Key Management:
• DevOps engineer time: 40 hours/month × $100/hour = $4,000/month
• Security incidents: 3/year × $100,000 = $300,000/year
• Compliance audit failures: 1/year × $50,000 = $50,000/year
• Key rotation downtime: 8 hours/year × $25,000/hour = $200,000/year
• Total annual cost: $598,000
```

**GCP KMS Implementation Costs:**
```
Google Cloud KMS:
• KMS operations: $0.03 per 10,000 operations
• Monthly operations: 1M = $3/month
• HSM operations: $1.00 per 10,000 operations (if needed)
• Implementation time: 80 hours × $100/hour = $8,000 (one-time)
• Ongoing maintenance: 5 hours/month × $100/hour = $6,000/year
• Total first-year cost: $14,036
• Total ongoing annual cost: $6,036

ROI Calculation:
• Traditional approach: $598,000/year
• KMS approach: $6,036/year
• Annual savings: $591,964
• ROI: 9,800% in first year
```

### Compliance Benefits

**Quantified Compliance Value:**
```
GDPR Compliance:
• Potential fines avoided: Up to 4% of annual revenue
• For $100M revenue company: $4M potential fine avoided
• Customer trust value: 15% customer retention improvement
• Brand reputation protection: Immeasurable

PCI DSS Compliance:
• Certification cost savings: $50,000/year
• Reduced audit scope: 60% reduction in audit time
• Lower insurance premiums: 20% reduction
• Faster time-to-market: 3 months faster for payment features
```

This comprehensive guide demonstrates how to implement enterprise-grade encryption using Google Cloud KMS with a real-world application example. The customer management system shows practical patterns for PII encryption, payment data protection, and compliance implementation while maintaining performance and cost efficiency.