#!/bin/bash

# ============================================================================
# Generate Secure Android JKS Keystore Files for All Apps
# ============================================================================
# This script generates JKS keystores for each Android app with secure passwords
# Generated files should be stored securely (GitHub Secrets, local secure storage)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEYS_DIR="${SCRIPT_DIR}/../android-keys"
LOG_FILE="${SCRIPT_DIR}/../ANDROID_KEYS_MANIFEST.md"

# Apps to generate keys for
APPS=("doudou" "docan" "finar" "klit" "repstore" "opentorrent")

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to generate secure password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to generate markdown documentation
generate_markdown() {
    local markdown_file="$1"
    
    cat > "${markdown_file}" << 'EOF'
# Android JKS Keystore Configuration for GitHub Actions

> **⚠️ SECURITY WARNING**: Keep all credentials confidential. Store them only in GitHub Secrets.

## Generated Keys Summary

This document contains the GitHub Secrets that need to be configured for Android app signing.

### Setup Instructions

1. Go to your GitHub Repository
2. Navigate to **Settings → Secrets and variables → Actions**
3. Create each secret below with the exact **Name** and **Value**

---

EOF

    # Append secrets for each app
    for app in "${APPS[@]}"; do
        local keystore_path="${KEYS_DIR}/${app}.jks"
        
        if [ -f "${keystore_path}" ]; then
            local keystore_base64=$(base64 -w 0 < "${keystore_path}")
            
            # Extract passwords from temp file if exists
            local temp_creds="${KEYS_DIR}/.${app}_creds"
            if [ -f "${temp_creds}" ]; then
                source "${temp_creds}"
                
                cat >> "${markdown_file}" << EOF
## ${app^^} Application

### Keystore File (Base64 Encoded)
**Name:** \`${app^^}_KEYSTORE_BASE64\`  
**Value:**
\`\`\`
${keystore_base64}
\`\`\`

### Keystore Password
**Name:** \`${app^^}_KEYSTORE_PASSWORD\`  
**Value:** 
\`\`\`
${KEYSTORE_PASS}
\`\`\`

### Key Password
**Name:** \`${app^^}_KEY_PASSWORD\`  
**Value:**
\`\`\`
${KEY_PASS}
\`\`\`

### Key Alias
**Name:** \`${app^^}_KEY_ALIAS\`  
**Value:** \`${KEY_ALIAS}\`

---

EOF
            fi
        fi
    done
    
    cat >> "${markdown_file}" << 'EOF'

## GitHub Actions Usage

In your workflow, decode and use the keystore:

```yaml
- name: Setup Android Signing
  env:
    KEYSTORE_BASE64: ${{ secrets.DOUDOU_KEYSTORE_BASE64 }}
    KEYSTORE_PASSWORD: ${{ secrets.DOUDOU_KEYSTORE_PASSWORD }}
    KEY_PASSWORD: ${{ secrets.DOUDOU_KEY_PASSWORD }}
    KEY_ALIAS: ${{ secrets.DOUDOU_KEY_ALIAS }}
  run: |
    echo "$KEYSTORE_BASE64" | base64 -d > build.keystore
    flutter build apk --release \
      --android-signing-keystore-path=build.keystore \
      --android-signing-keystore-password="$KEYSTORE_PASSWORD" \
      --android-signing-key-password="$KEY_PASSWORD" \
      --android-signing-key-alias="$KEY_ALIAS"
```

## Security Best Practices

✅ **DO:**
- Store all passwords in GitHub Secrets only
- Use unique passwords for each app
- Rotate keys annually
- Keep local .jks files in secure location
- Add `android-keys/` to `.gitignore`

❌ **DON'T:**
- Commit .jks files to repository
- Share passwords via email or Slack
- Use weak passwords
- Commit base64 encoded keystores
- Reuse passwords across apps

## Reference

- **Keystore Type:** JKS (Java KeyStore)
- **Key Algorithm:** RSA 2048-bit
- **Validity Period:** 10 years (3650 days)
- **Signing Certificate CN:** {app}.openlyst.com

---

**Generated:** $(date)  
**Last Updated:** $(date)

EOF

    echo -e "${GREEN}[✓] Markdown documentation generated: ${markdown_file}${NC}"
}

# Main execution
main() {
    echo -e "${GREEN}============================================================================${NC}"
    echo -e "${GREEN}Android JKS Keystore Generator (Secure)${NC}"
    echo -e "${GREEN}============================================================================${NC}\n"
    
    # Create keys directory
    mkdir -p "${KEYS_DIR}"
    echo -e "${YELLOW}[*] Keys will be stored in: ${KEYS_DIR}${NC}\n"
    
    # Generate keys for all apps
    for app in "${APPS[@]}"; do
        local keystore_path="${KEYS_DIR}/${app}.jks"
        local alias="${app}_key"
        local keystore_pass=$(generate_password)
        local key_pass=$(generate_password)
        
        echo -e "${YELLOW}[*] Generating JKS key for ${app}...${NC}"
        
        # Create keystore with RSA 2048-bit key, 10-year validity
        keytool -genkeypair \
            -v \
            -keystore "${keystore_path}" \
            -keyalg RSA \
            -keysize 2048 \
            -validity 36500 \
            -alias "${alias}" \
            -keypass "${key_pass}" \
            -storepass "${keystore_pass}" \
            -dname "CN=${app}.openlyst.com, OU=Openlyst, O=Openlyst, L=Internet, ST=Web, C=US" \
            2>/dev/null
        
        if [ -f "${keystore_path}" ]; then
            echo -e "${GREEN}[✓] Generated ${keystore_path}${NC}"
            
            # Store credentials in temporary file for markdown generation
            cat > "${KEYS_DIR}/.${app}_creds" << CREDS
KEYSTORE_PASS="${keystore_pass}"
KEY_PASS="${key_pass}"
KEY_ALIAS="${alias}"
CREDS
            chmod 600 "${KEYS_DIR}/.${app}_creds"
        else
            echo -e "${RED}[✗] Failed to generate keystore for ${app}${NC}"
            return 1
        fi
    done
    
    # Generate markdown documentation
    generate_markdown "${LOG_FILE}"
    
    echo -e "\n${GREEN}============================================================================${NC}"
    echo -e "${GREEN}IMPORTANT SECURITY NOTES${NC}"
    echo -e "${GREEN}============================================================================${NC}"
    echo -e "1. ✓ JKS files generated and stored in: ${YELLOW}${KEYS_DIR}${NC}"
    echo -e "2. ✓ Markdown guide created: ${YELLOW}${LOG_FILE}${NC}"
    echo -e "3. Store JKS files in secure location (NOT in version control)"
    echo -e "4. Add '${KEYS_DIR}' to .gitignore to prevent accidental commit"
    echo -e "\n${YELLOW}Review ${LOG_FILE} for GitHub Secrets setup instructions${NC}\n"
    
    # Add to .gitignore
    if [ ! -f "${SCRIPT_DIR}/../.gitignore" ]; then
        touch "${SCRIPT_DIR}/../.gitignore"
    fi
    
    if ! grep -q "android-keys" "${SCRIPT_DIR}/../.gitignore"; then
        echo "android-keys/" >> "${SCRIPT_DIR}/../.gitignore"
        echo -e "${GREEN}[✓] Added android-keys/ to .gitignore${NC}"
    fi
    
    echo -e "${GREEN}[✓] Setup complete!${NC}\n"
}

main "$@"
