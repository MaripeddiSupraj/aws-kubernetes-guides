# SSL/TLS Certificates - Complete DevOps Guide

## Table of Contents
1. [SSL/TLS Fundamentals](#ssltls-fundamentals)
2. [Certificate Components & Structure](#certificate-components--structure)
3. [Types of SSL Certificates](#types-of-ssl-certificates)
4. [Certificate Generation Methods](#certificate-generation-methods)
5. [Real-World Implementation Examples](#real-world-implementation-examples)
6. [Server Configuration & Installation](#server-configuration--installation)
7. [Certificate Management & Renewal](#certificate-management--renewal)
8. [Cloud Provider SSL Solutions](#cloud-provider-ssl-solutions)
9. [Troubleshooting & Best Practices](#troubleshooting--best-practices)
10. [Security Considerations](#security-considerations)

---

## SSL/TLS Fundamentals

### What is SSL/TLS?

#### SSL (Secure Sockets Layer) vs TLS (Transport Layer Security)
- **SSL**: Original protocol (SSL 1.0, 2.0, 3.0) - **DEPRECATED**
- **TLS**: Modern successor (TLS 1.0, 1.1, 1.2, 1.3) - **CURRENT STANDARD**
- **Common Usage**: People still say "SSL" but mean "TLS"

#### Why SSL/TLS Exists
**Problems SSL/TLS Solves**:
1. **Eavesdropping**: Data transmitted in plain text can be intercepted
2. **Man-in-the-Middle Attacks**: Attackers can intercept and modify communications
3. **Identity Verification**: How do you know you're talking to the real server?
4. **Data Integrity**: How do you know data wasn't tampered with?

#### The Three Pillars of SSL/TLS Security

**1. Encryption (Confidentiality)**
```
Plain Text: "Hello World"
Encrypted:  "X7#9$mK@2pL8*4nQ"
```
- Ensures data cannot be read if intercepted
- Uses symmetric encryption for data transfer
- Uses asymmetric encryption for key exchange

**2. Authentication (Identity Verification)**
```
Client asks: "Are you really google.com?"
Server proves: "Yes, here's my certificate signed by a trusted CA"
```
- Verifies the server's identity
- Prevents impersonation attacks
- Uses digital certificates and signatures

**3. Integrity (Data Protection)**
```
Original Message: "Transfer $100"
Tampered Message: "Transfer $1000"
SSL/TLS detects: "Message has been modified!"
```
- Ensures data hasn't been modified in transit
- Uses cryptographic hashes (MAC - Message Authentication Code)

### How SSL/TLS Works (Simplified Handshake)

#### The SSL/TLS Handshake Process:

```
Client                                Server
  |                                     |
  |  1. ClientHello                     |
  |------------------------------------>|
  |     - Supported cipher suites       |
  |     - Random number                 |
  |     - TLS version                   |
  |                                     |
  |  2. ServerHello                     |
  |<------------------------------------|
  |     - Selected cipher suite         |
  |     - Random number                 |
  |     - TLS version                   |
  |                                     |
  |  3. Certificate                     |
  |<------------------------------------|
  |     - Server's SSL certificate      |
  |     - Public key                    |
  |                                     |
  |  4. Certificate Verification        |
  |     - Validate certificate chain    |
  |     - Check expiration              |
  |     - Verify domain name            |
  |                                     |
  |  5. Key Exchange                    |
  |------------------------------------>|
  |     - Pre-master secret (encrypted) |
  |                                     |
  |  6. Generate Session Keys           |
  |     Both sides create symmetric     |
  |     encryption keys from shared     |
  |     secrets                         |
  |                                     |
  |  7. Finished Messages               |
  |<----------------------------------->|
  |     - Encrypted with session keys   |
  |                                     |
  |  8. Secure Communication            |
  |<===================================>|
  |     All data encrypted with         |
  |     session keys                    |
```

#### Step-by-Step Breakdown:

**Step 1: ClientHello**
- Client initiates connection
- Sends supported encryption methods
- Includes random number for key generation

**Step 2: ServerHello**
- Server responds with chosen encryption method
- Sends its own random number
- Confirms TLS version

**Step 3: Certificate Exchange**
- Server sends its SSL certificate
- Certificate contains server's public key
- Certificate is signed by a Certificate Authority (CA)

**Step 4: Certificate Verification**
- Client validates certificate authenticity
- Checks if certificate is expired
- Verifies domain name matches

**Step 5: Key Exchange**
- Client generates pre-master secret
- Encrypts it with server's public key
- Sends encrypted pre-master secret to server

**Step 6: Session Key Generation**
- Both sides use random numbers + pre-master secret
- Generate identical symmetric encryption keys
- These keys encrypt all subsequent communication

**Step 7: Handshake Completion**
- Both sides send "Finished" messages
- Messages are encrypted with new session keys
- Confirms handshake was successful

**Step 8: Secure Communication**
- All data encrypted with session keys
- Much faster than public key encryption
- Keys are unique per session

---

## Certificate Components & Structure

### X.509 Certificate Structure

#### Certificate Fields Explained:

```
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: 12:34:56:78:9a:bc:de:f0
        Signature Algorithm: sha256WithRSAEncryption
        Issuer: C=US, O=Let's Encrypt, CN=R3
        Validity:
            Not Before: Jan  1 00:00:00 2024 GMT
            Not After : Apr  1 23:59:59 2024 GMT
        Subject: CN=example.com
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                RSA Public-Key: (2048 bit)
                Modulus: 00:b4:31:98:...
                Exponent: 65537 (0x10001)
        X509v3 extensions:
            X509v3 Subject Alternative Name:
                DNS:example.com, DNS:www.example.com
            X509v3 Key Usage:
                Digital Signature, Key Encipherment
            X509v3 Extended Key Usage:
                TLS Web Server Authentication
    Signature Algorithm: sha256WithRSAEncryption
         5a:8b:c2:f1:...
```

#### Key Components Breakdown:

**1. Version**
- X.509 version (usually v3)
- Determines available extensions

**2. Serial Number**
- Unique identifier for this certificate
- Used for revocation tracking

**3. Signature Algorithm**
- How the certificate is signed
- Common: SHA-256 with RSA, ECDSA

**4. Issuer**
- Who signed/issued this certificate
- Certificate Authority (CA) information

**5. Validity Period**
- **Not Before**: When certificate becomes valid
- **Not After**: When certificate expires
- **Important**: Always check current time is within this range

**6. Subject**
- Who this certificate belongs to
- Usually the domain name (CN = Common Name)

**7. Public Key**
- The server's public key
- Used for encryption and signature verification
- Key size (1024, 2048, 4096 bits)

**8. Extensions (X509v3)**
- **Subject Alternative Names (SAN)**: Multiple domains covered
- **Key Usage**: What the key can be used for
- **Extended Key Usage**: Specific purposes (web server, email, etc.)

**9. Signature**
- CA's digital signature of the certificate
- Proves certificate authenticity

### Certificate Chain of Trust

#### How Trust Works:

```
Root CA Certificate (Self-Signed)
    ↓ (signs)
Intermediate CA Certificate
    ↓ (signs)
Server Certificate (example.com)
```

#### Real Example - Let's Encrypt Chain:

```
1. ISRG Root X1 (Root CA)
   ↓ Signs
2. R3 (Intermediate CA)
   ↓ Signs  
3. example.com (End Entity Certificate)
```

#### Certificate Chain Validation Process:

```bash
# View certificate chain
openssl s_client -connect example.com:443 -showcerts

# Output shows:
# Certificate chain
#  0 s:CN = example.com
#    i:C = US, O = Let's Encrypt, CN = R3
#  1 s:C = US, O = Let's Encrypt, CN = R3
#    i:C = US, O = Internet Security Research Group, CN = ISRG Root X1
```

**Validation Steps**:
1. Browser receives server certificate (example.com)
2. Checks if it's signed by a trusted CA
3. If not directly trusted, looks for intermediate certificate
4. Validates intermediate certificate against root CA
5. Root CA must be in browser's trust store
6. If chain is valid and not expired → Trust established

---

## Types of SSL Certificates

### 1. By Validation Level

#### Domain Validated (DV) Certificates
**What it validates**: Domain ownership only

**Validation Process**:
- Email verification (admin@domain.com)
- DNS record verification
- HTTP file verification

**Characteristics**:
- **Speed**: Minutes to hours
- **Cost**: Free to $100/year
- **Security**: Basic encryption
- **Trust Indicator**: Padlock icon only

**Use Cases**:
- Personal websites
- Blogs
- Development environments
- Non-commercial sites

**Example Certificate Info**:
```
Subject: CN=blog.example.com
Issuer: CN=Let's Encrypt Authority X3
Validation: Domain Control Validated
```

#### Organization Validated (OV) Certificates
**What it validates**: Domain ownership + Organization identity

**Validation Process**:
- Domain ownership verification
- Organization existence verification
- Business registration checks
- Phone verification

**Characteristics**:
- **Speed**: 1-3 days
- **Cost**: $50-$300/year
- **Security**: Same encryption as DV
- **Trust Indicator**: Padlock + organization name in certificate

**Use Cases**:
- Business websites
- E-commerce sites
- Corporate applications
- Customer-facing services

**Example Certificate Info**:
```
Subject: CN=shop.example.com, O=Example Corp, L=New York, ST=NY, C=US
Issuer: CN=DigiCert SHA2 Secure Server CA
Validation: Organization Validated
```

#### Extended Validation (EV) Certificates
**What it validates**: Domain + Organization + Legal existence

**Validation Process**:
- Comprehensive business verification
- Legal existence confirmation
- Physical address verification
- Authorized representative verification
- Exclusive domain control

**Characteristics**:
- **Speed**: 1-2 weeks
- **Cost**: $150-$1000/year
- **Security**: Same encryption, highest trust
- **Trust Indicator**: Green address bar (older browsers), company name in certificate

**Use Cases**:
- Banking websites
- Payment processors
- High-value e-commerce
- Financial institutions

**Example Certificate Info**:
```
Subject: CN=secure.bank.com, O=Example Bank Inc, 
         STREET=123 Main St, L=New York, ST=NY, C=US,
         serialNumber=12345, businessCategory=Private Organization
Issuer: CN=DigiCert Extended Validation CA
Validation: Extended Validation
```

### 2. By Coverage Scope

#### Single Domain Certificates
**Coverage**: One specific domain

**Examples**:
- `example.com` (covers only example.com)
- `www.example.com` (covers only www.example.com)
- `api.example.com` (covers only api.example.com)

**Certificate Subject**:
```
Subject: CN=api.example.com
```

#### Multi-Domain (SAN) Certificates
**Coverage**: Multiple specific domains

**Examples**:
- One certificate covering:
  - `example.com`
  - `www.example.com`
  - `api.example.com`
  - `shop.example.com`
  - `blog.example.com`

**Certificate Subject**:
```
Subject: CN=example.com
X509v3 Subject Alternative Name:
    DNS:example.com
    DNS:www.example.com
    DNS:api.example.com
    DNS:shop.example.com
    DNS:blog.example.com
```

**Advantages**:
- Single certificate management
- Cost-effective for multiple domains
- Easier renewal process

**Disadvantages**:
- All domains in one certificate (security consideration)
- Limited number of domains (usually 100-250)

#### Wildcard Certificates
**Coverage**: All subdomains of a domain

**Examples**:
- `*.example.com` covers:
  - `www.example.com`
  - `api.example.com`
  - `shop.example.com`
  - `anything.example.com`

**Certificate Subject**:
```
Subject: CN=*.example.com
```

**Advantages**:
- Covers unlimited subdomains
- Easy to add new subdomains
- Single certificate management

**Disadvantages**:
- Higher cost than single domain
- Security risk if private key compromised
- Doesn't cover the root domain (example.com)

**Important Note**: Wildcard certificates only cover one level:
- `*.example.com` covers `api.example.com`
- `*.example.com` does NOT cover `v1.api.example.com`

### 3. By Certificate Authority

#### Commercial CAs
**Examples**: DigiCert, GlobalSign, Sectigo, GoDaddy

**Characteristics**:
- **Cost**: $50-$1000+/year
- **Support**: 24/7 customer support
- **Warranty**: Insurance coverage
- **Validation**: All types (DV, OV, EV)
- **Trust**: Pre-installed in all browsers

#### Free CAs
**Examples**: Let's Encrypt, ZeroSSL

**Let's Encrypt Characteristics**:
- **Cost**: Free
- **Automation**: ACME protocol
- **Validation**: Domain validated only
- **Renewal**: 90-day certificates (auto-renewable)
- **Trust**: Widely trusted

**Use Cases**:
- Development environments
- Personal projects
- Cost-sensitive deployments
- Automated certificate management

#### Internal/Private CAs
**Use Cases**: Internal corporate networks

**Characteristics**:
- **Cost**: Infrastructure cost only
- **Trust**: Must install root CA in all clients
- **Control**: Full control over certificate lifecycle
- **Security**: Not trusted by public browsers

---

## Certificate Generation Methods

### 1. Let's Encrypt (Free, Automated)

#### Using Certbot (Most Common)

**Installation**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx

# macOS
brew install certbot
```

**Generate Certificate**:
```bash
# For Nginx (automatic configuration)
sudo certbot --nginx -d example.com -d www.example.com

# For Apache (automatic configuration)
sudo certbot --apache -d example.com -d www.example.com

# Manual mode (DNS challenge)
sudo certbot certonly --manual --preferred-challenges dns -d example.com

# Webroot mode (existing web server)
sudo certbot certonly --webroot -w /var/www/html -d example.com
```

**Certificate Locations**:
```bash
# Certificate files are stored in:
/etc/letsencrypt/live/example.com/

# Files created:
cert.pem        # Server certificate
chain.pem       # Intermediate certificate
fullchain.pem   # cert.pem + chain.pem
privkey.pem     # Private key
```

#### Using ACME.sh (Alternative Client)

**Installation**:
```bash
curl https://get.acme.sh | sh
source ~/.bashrc
```

**Generate Certificate**:
```bash
# HTTP validation
acme.sh --issue -d example.com -w /var/www/html

# DNS validation (Cloudflare example)
export CF_Key="your-api-key"
export CF_Email="your-email@example.com"
acme.sh --issue --dns dns_cf -d example.com -d www.example.com

# Install certificate
acme.sh --install-cert -d example.com \
  --key-file /etc/nginx/ssl/example.com.key \
  --fullchain-file /etc/nginx/ssl/example.com.crt \
  --reloadcmd "systemctl reload nginx"
```

### 2. Self-Signed Certificates (Development/Testing)

#### Generate Self-Signed Certificate:

**Single Command**:
```bash
# Generate private key and certificate in one command
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/C=US/ST=CA/L=San Francisco/O=MyOrg/CN=example.com"
```

**Step-by-Step Process**:
```bash
# 1. Generate private key
openssl genrsa -out private.key 2048

# 2. Create certificate signing request (CSR)
openssl req -new -key private.key -out certificate.csr \
  -subj "/C=US/ST=CA/L=San Francisco/O=MyOrg/CN=example.com"

# 3. Generate self-signed certificate
openssl x509 -req -in certificate.csr -signkey private.key -out certificate.crt -days 365
```

**With Subject Alternative Names (SAN)**:
```bash
# Create config file for SAN
cat > san.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = CA
L = San Francisco
O = MyOrg
CN = example.com

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = example.com
DNS.2 = www.example.com
DNS.3 = api.example.com
IP.1 = 192.168.1.100
EOF

# Generate certificate with SAN
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -config san.conf -extensions v3_req
```

### 3. Commercial Certificate Authorities

#### Step 1: Generate Certificate Signing Request (CSR)

**Generate Private Key**:
```bash
# RSA 2048-bit (most common)
openssl genrsa -out example.com.key 2048

# RSA 4096-bit (more secure, slower)
openssl genrsa -out example.com.key 4096

# ECDSA P-256 (modern, efficient)
openssl ecparam -genkey -name prime256v1 -out example.com.key
```

**Generate CSR**:
```bash
# Interactive mode
openssl req -new -key example.com.key -out example.com.csr

# Non-interactive mode
openssl req -new -key example.com.key -out example.com.csr \
  -subj "/C=US/ST=California/L=San Francisco/O=Example Corp/CN=example.com"
```

**CSR with Subject Alternative Names**:
```bash
# Create CSR config file
cat > csr.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = Example Corp
OU = IT Department
CN = example.com

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = example.com
DNS.2 = www.example.com
DNS.3 = api.example.com
DNS.4 = shop.example.com
EOF

# Generate CSR with config
openssl req -new -key example.com.key -out example.com.csr -config csr.conf
```

**Verify CSR**:
```bash
# Check CSR details
openssl req -in example.com.csr -text -noout

# Verify CSR signature
openssl req -in example.com.csr -verify -noout
```

#### Step 2: Submit CSR to CA

**DigiCert Process**:
1. Login to DigiCert account
2. Choose certificate type (DV/OV/EV)
3. Upload CSR file
4. Complete domain validation
5. Complete organization validation (OV/EV)
6. Download issued certificate

**Validation Methods**:

**Email Validation**:
- CA sends email to admin@domain.com
- Click validation link in email

**DNS Validation**:
- Add TXT record to DNS
- Record format: `_dv.example.com TXT "validation-token"`

**HTTP Validation**:
- Upload file to `http://example.com/.well-known/pki-validation/`
- File contains validation token

#### Step 3: Download and Install Certificate

**Certificate Bundle Structure**:
```
example.com.crt          # Your domain certificate
intermediate.crt         # Intermediate CA certificate
root.crt                # Root CA certificate (optional)
```

**Create Full Chain**:
```bash
# Combine certificates in correct order
cat example.com.crt intermediate.crt > fullchain.crt

# Or if you have separate files
cat example.com.crt > fullchain.crt
cat intermediate.crt >> fullchain.crt
```

### 4. Internal Certificate Authority (Enterprise)

#### Create Root CA

**Generate Root CA Private Key**:
```bash
# Generate strong private key
openssl genrsa -aes256 -out rootCA.key 4096

# Create root CA certificate
openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 3650 -out rootCA.crt \
  -subj "/C=US/ST=CA/L=San Francisco/O=Example Corp/CN=Example Corp Root CA"
```

**Root CA Configuration**:
```bash
# Create CA config file
cat > rootCA.conf << EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = Example Corp
CN = Example Corp Root CA

[v3_ca]
basicConstraints = critical,CA:TRUE
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
EOF
```

#### Issue Server Certificates

**Generate Server Certificate**:
```bash
# 1. Generate server private key
openssl genrsa -out server.key 2048

# 2. Create server CSR
openssl req -new -key server.key -out server.csr \
  -subj "/C=US/ST=CA/L=San Francisco/O=Example Corp/CN=internal.example.com"

# 3. Sign with Root CA
openssl x509 -req -in server.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial \
  -out server.crt -days 365 -sha256
```

**Server Certificate with Extensions**:
```bash
# Create server config
cat > server.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = Example Corp
CN = internal.example.com

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = internal.example.com
DNS.2 = *.internal.example.com
IP.1 = 10.0.1.100
EOF

# Generate and sign certificate
openssl req -new -key server.key -out server.csr -config server.conf
openssl x509 -req -in server.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial \
  -out server.crt -days 365 -sha256 -extensions v3_req -extfile server.conf
```

---

## Real-World Implementation Examples

### Example 1: E-commerce Website (Multi-Domain Setup)

#### Scenario:
- Main site: `shop.example.com`
- API: `api.example.com`
- Admin panel: `admin.example.com`
- CDN: `cdn.example.com`

#### Solution: Multi-Domain Certificate

**Generate Certificate with Certbot**:
```bash
sudo certbot certonly --nginx \
  -d shop.example.com \
  -d api.example.com \
  -d admin.example.com \
  -d cdn.example.com
```

**Nginx Configuration**:
```nginx
# Main shop site
server {
    listen 443 ssl http2;
    server_name shop.example.com;
    
    ssl_certificate /etc/letsencrypt/live/shop.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shop.example.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# API server
server {
    listen 443 ssl http2;
    server_name api.example.com;
    
    ssl_certificate /etc/letsencrypt/live/shop.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shop.example.com/privkey.pem;
    
    # Same SSL configuration as above
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name shop.example.com api.example.com admin.example.com cdn.example.com;
    return 301 https://$server_name$request_uri;
}
```

### Example 2: Microservices Architecture (Wildcard Certificate)

#### Scenario:
- Multiple microservices: `auth.api.example.com`, `users.api.example.com`, `orders.api.example.com`
- Services are added/removed frequently
- Need flexible certificate management

#### Solution: Wildcard Certificate

**Generate Wildcard Certificate**:
```bash
# Using DNS challenge (required for wildcards)
sudo certbot certonly --manual --preferred-challenges dns \
  -d "*.api.example.com" \
  -d "api.example.com"
```

**DNS Challenge Process**:
```bash
# Certbot will ask you to add TXT record:
# _acme-challenge.api.example.com TXT "random-validation-string"

# Add the record to your DNS provider
# Wait for DNS propagation (check with):
dig TXT _acme-challenge.api.example.com

# Press Enter in certbot to continue
```

**Kubernetes Ingress Configuration**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - "*.api.example.com"
    - api.example.com
    secretName: api-wildcard-tls
  rules:
  - host: auth.api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: auth-service
            port:
              number: 80
  - host: users.api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: users-service
            port:
              number: 80
  - host: orders.api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: orders-service
            port:
              number: 80
```

### Example 3: Development Environment (Self-Signed)

#### Scenario:
- Local development environment
- Multiple developers
- Need HTTPS for testing
- Don't want certificate warnings

#### Solution: Custom CA for Development

**Create Development CA**:
```bash
#!/bin/bash
# create-dev-ca.sh

# Create CA directory structure
mkdir -p dev-ca/{certs,private,csr}
cd dev-ca

# Generate CA private key
openssl genrsa -out private/ca.key 4096

# Create CA certificate
openssl req -x509 -new -nodes -key private/ca.key -sha256 -days 3650 \
  -out certs/ca.crt \
  -subj "/C=US/ST=CA/L=Dev/O=Dev Corp/CN=Dev Corp Root CA"

echo "Development CA created!"
echo "Install certs/ca.crt in your browser/system trust store"
```

**Generate Development Certificates**:
```bash
#!/bin/bash
# generate-dev-cert.sh

DOMAIN=$1
if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <domain>"
    exit 1
fi

# Create certificate config
cat > csr/${DOMAIN}.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = CA
L = Dev
O = Dev Corp
CN = ${DOMAIN}

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${DOMAIN}
DNS.2 = *.${DOMAIN}
DNS.3 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# Generate private key
openssl genrsa -out private/${DOMAIN}.key 2048

# Generate CSR
openssl req -new -key private/${DOMAIN}.key -out csr/${DOMAIN}.csr -config csr/${DOMAIN}.conf

# Sign certificate with CA
openssl x509 -req -in csr/${DOMAIN}.csr -CA certs/ca.crt -CAkey private/ca.key \
  -CAcreateserial -out certs/${DOMAIN}.crt -days 365 -sha256 \
  -extensions v3_req -extfile csr/${DOMAIN}.conf

echo "Certificate generated for ${DOMAIN}"
echo "Certificate: certs/${DOMAIN}.crt"
echo "Private Key: private/${DOMAIN}.key"
```

**Usage**:
```bash
# Generate certificate for local development
./generate-dev-cert.sh local.example.com

# Install CA certificate in system (macOS)
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain certs/ca.crt

# Install CA certificate in system (Ubuntu)
sudo cp certs/ca.crt /usr/local/share/ca-certificates/dev-ca.crt
sudo update-ca-certificates
```

### Example 4: Load Balancer SSL Termination

#### Scenario:
- Application Load Balancer (ALB) in AWS
- Multiple backend servers
- SSL termination at load balancer
- Backend communication over HTTP

#### Solution: ALB with ACM Certificate

**Request Certificate in AWS Certificate Manager**:
```bash
# Request certificate via AWS CLI
aws acm request-certificate \
  --domain-name example.com \
  --subject-alternative-names www.example.com api.example.com \
  --validation-method DNS \
  --region us-west-2

# Get certificate ARN from output
CERT_ARN="arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012"
```

**Terraform Configuration**:
```hcl
# Request ACM certificate
resource "aws_acm_certificate" "main" {
  domain_name               = "example.com"
  subject_alternative_names = ["www.example.com", "api.example.com"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "example.com"
  }
}

# DNS validation records
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.main.zone_id
}

# Certificate validation
resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "main-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.public[*].id

  enable_deletion_protection = false

  tags = {
    Name = "main-alb"
  }
}

# HTTPS Listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate_validation.main.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}

# HTTP to HTTPS redirect
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}
```

---

## Server Configuration & Installation

### 1. Nginx SSL Configuration

#### Basic SSL Configuration:
```nginx
server {
    listen 443 ssl http2;
    server_name example.com www.example.com;
    
    # Certificate files
    ssl_certificate /etc/ssl/certs/example.com.crt;
    ssl_certificate_key /etc/ssl/private/example.com.key;
    
    # SSL protocols and ciphers
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;
    
    # SSL session settings
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/ssl/certs/example.com-chain.crt;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$server_name$request_uri;
}
```

#### Advanced SSL Configuration:
```nginx
# /etc/nginx/conf.d/ssl.conf
# SSL configuration to be included in server blocks

# Modern configuration (2024)
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;

# DH parameters for perfect forward secrecy
ssl_dhparam /etc/ssl/certs/dhparam.pem;

# Session settings
ssl_session_cache shared:SSL:50m;
ssl_session_timeout 1d;
ssl_session_tickets off;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 1.1.1.1 1.0.0.1 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# Security headers
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

**Generate DH Parameters**:
```bash
# Generate strong DH parameters (takes time)
sudo openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048
```

### 2. Apache SSL Configuration

#### Basic SSL Virtual Host:
```apache
<VirtualHost *:443>
    ServerName example.com
    ServerAlias www.example.com
    DocumentRoot /var/www/html
    
    # SSL Engine
    SSLEngine on
    
    # Certificate files
    SSLCertificateFile /etc/ssl/certs/example.com.crt
    SSLCertificateKeyFile /etc/ssl/private/example.com.key
    SSLCertificateChainFile /etc/ssl/certs/example.com-chain.crt
    
    # SSL protocols and ciphers
    SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
    SSLHonorCipherOrder off
    
    # HSTS header
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    
    # Other security headers
    Header always set X-Frame-Options DENY
    Header always set X-Content-Type-Options nosniff
</VirtualHost>

# HTTP to HTTPS redirect
<VirtualHost *:80>
    ServerName example.com
    ServerAlias www.example.com
    Redirect permanent / https://example.com/
</VirtualHost>
```

#### Advanced Apache SSL Configuration:
```apache
# /etc/apache2/conf-available/ssl-params.conf

# Modern SSL configuration
SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305
SSLHonorCipherOrder off

# Session settings
SSLSessionCache shmcb:${APACHE_RUN_DIR}/ssl_scache(512000)
SSLSessionCacheTimeout 300

# OCSP stapling
SSLUseStapling on
SSLStaplingCache shmcb:${APACHE_RUN_DIR}/ssl_stapling(128000)

# Security headers
Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
Header always set X-Frame-Options DENY
Header always set X-Content-Type-Options nosniff
Header always set X-XSS-Protection "1; mode=block"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
```

**Enable Configuration**:
```bash
# Enable SSL module and configuration
sudo a2enmod ssl headers
sudo a2enconf ssl-params
sudo systemctl reload apache2
```

### 3. Node.js/Express SSL Configuration

#### HTTPS Server Setup:
```javascript
// server.js
const express = require('express');
const https = require('https');
const fs = require('fs');
const path = require('path');

const app = express();

// SSL certificate options
const sslOptions = {
  key: fs.readFileSync('/etc/ssl/private/example.com.key'),
  cert: fs.readFileSync('/etc/ssl/certs/example.com.crt'),
  // Include intermediate certificates if needed
  ca: fs.readFileSync('/etc/ssl/certs/intermediate.crt')
};

// Middleware for security headers
app.use((req, res, next) => {
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  next();
});

// Routes
app.get('/', (req, res) => {
  res.send('Hello HTTPS World!');
});

// HTTP to HTTPS redirect server
const httpApp = express();
httpApp.use((req, res) => {
  res.redirect(301, `https://${req.headers.host}${req.url}`);
});

// Start servers
const httpsServer = https.createServer(sslOptions, app);
httpsServer.listen(443, () => {
  console.log('HTTPS Server running on port 443');
});

httpApp.listen(80, () => {
  console.log('HTTP Server running on port 80 (redirecting to HTTPS)');
});
```

#### Production-Ready Configuration:
```javascript
// config/ssl.js
const fs = require('fs');
const path = require('path');

class SSLConfig {
  constructor() {
    this.certPath = process.env.SSL_CERT_PATH || '/etc/ssl/certs';
    this.keyPath = process.env.SSL_KEY_PATH || '/etc/ssl/private';
    this.domain = process.env.DOMAIN || 'example.com';
  }

  getSSLOptions() {
    try {
      const options = {
        key: fs.readFileSync(path.join(this.keyPath, `${this.domain}.key`)),
        cert: fs.readFileSync(path.join(this.certPath, `${this.domain}.crt`))
      };

      // Add intermediate certificate if exists
      const intermediatePath = path.join(this.certPath, `${this.domain}-intermediate.crt`);
      if (fs.existsSync(intermediatePath)) {
        options.ca = fs.readFileSync(intermediatePath);
      }

      return options;
    } catch (error) {
      console.error('SSL certificate loading failed:', error.message);
      throw error;
    }
  }

  // Watch for certificate changes (for auto-renewal)
  watchCertificates(callback) {
    const certFile = path.join(this.certPath, `${this.domain}.crt`);
    const keyFile = path.join(this.keyPath, `${this.domain}.key`);

    fs.watchFile(certFile, () => {
      console.log('SSL certificate changed, reloading...');
      callback();
    });

    fs.watchFile(keyFile, () => {
      console.log('SSL private key changed, reloading...');
      callback();
    });
  }
}

module.exports = SSLConfig;
```

### 4. Docker SSL Configuration

#### Dockerfile with SSL:
```dockerfile
FROM nginx:alpine

# Copy SSL certificates
COPY certs/example.com.crt /etc/ssl/certs/
COPY certs/example.com.key /etc/ssl/private/
COPY certs/example.com-chain.crt /etc/ssl/certs/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Set proper permissions
RUN chmod 644 /etc/ssl/certs/example.com.crt && \
    chmod 600 /etc/ssl/private/example.com.key && \
    chmod 644 /etc/ssl/certs/example.com-chain.crt

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose with SSL:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "80:80"
      - "443:443"
    volumes:
      # Mount Let's Encrypt certificates
      - /etc/letsencrypt/live/example.com:/etc/ssl/certs:ro
      - /etc/letsencrypt/archive/example.com:/etc/ssl/private:ro
    environment:
      - DOMAIN=example.com
    restart: unless-stopped

  certbot:
    image: certbot/certbot
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt
      - /var/www/certbot:/var/www/certbot
    command: certonly --webroot --webroot-path=/var/www/certbot --email admin@example.com --agree-tos --no-eff-email -d example.com
```

#### Kubernetes SSL Configuration:
```yaml
# SSL Certificate Secret
apiVersion: v1
kind: Secret
metadata:
  name: example-com-tls
  namespace: default
type: kubernetes.io/tls
data:
  tls.crt: LS0tLS1CRUdJTi... # base64 encoded certificate
  tls.key: LS0tLS1CRUdJTi... # base64 encoded private key

---
# Ingress with SSL
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - example.com
    - www.example.com
    secretName: example-com-tls
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
  - host: www.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

This comprehensive guide covers SSL/TLS certificates from fundamental concepts to practical implementation. The guide includes real-world examples, security best practices, and detailed configuration instructions for various platforms and use cases.

Would you like me to continue with the remaining sections covering certificate management, renewal, cloud provider solutions, and troubleshooting?