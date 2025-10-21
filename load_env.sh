#!/bin/bash
# Script for loading environment variables from .env file into shell environment
# Usage: source load_env.sh

ENV_FILE=".env"

if [ -f "$ENV_FILE" ]; then
    echo "🔧 Loading environment variables from $ENV_FILE..."
    
    # Count non-empty, non-comment lines
    total_vars=$(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$ENV_FILE" | wc -l | tr -d ' ')
    echo "📊 Found $total_vars environment variables to load"
    
    # Load variables with automatic export
    set -a  # Automatically export all variables
    source "$ENV_FILE"
    set +a  # Disable automatic export
    
    # Show loaded variables (without exposing sensitive values)
    echo "✅ Environment variables loaded successfully!"
    echo ""
    echo "📋 Loaded variables:"
    
    # List all variables that were loaded, masking sensitive values
    grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$ENV_FILE" | while IFS='=' read -r var_name var_value; do
        # Get the current value of the variable
        current_value=$(eval "echo \$${var_name}")
        if [ -n "$current_value" ]; then
            case "$var_name" in
                *API_KEY|*PASSWORD|*SECRET|*TOKEN)
                    if [ ${#current_value} -gt 0 ] && [ "$current_value" != "your_openai_api_key_here" ]; then
                        echo "  ✓ $var_name: [SET - ${#current_value} chars]"
                    else
                        echo "  ⚠️  $var_name: [NOT SET]"
                    fi
                    ;;
                *URL|*HOST)
                    if [ ${#current_value} -gt 0 ] && [ "$current_value" != "postgresql://username:password@host:5432/database_name" ]; then
                        # Show only the protocol/host part for URLs
                        masked_value=$(echo "$current_value" | sed -E 's|(://[^:/@]*)[^/@]*|\1***|g')
                        echo "  ✓ $var_name: $masked_value"
                    else
                        echo "  ⚠️  $var_name: [NOT SET]"
                    fi
                    ;;
                *)
                    if [ ${#current_value} -gt 0 ]; then
                        echo "  ✓ $var_name: $current_value"
                    else
                        echo "  ⚠️  $var_name: [EMPTY]"
                    fi
                    ;;
            esac
        fi
    done
    
    echo ""
    echo "💡 Tip: Use 'printenv | grep -E \"(OPENAI|POSTGRES|WHISPER|CORS|VAST|GPU|UPSCALE)\"' to see current values"
    
else
    echo "❌ Warning: $ENV_FILE file not found in current directory"
    echo "📝 Create one by copying from .env.example:"
    echo "   cp .env.example .env"
    echo "   # Then edit .env with your actual values"
    
    if [ -f ".env.example" ]; then
        echo ""
        echo "📋 Available variables in .env.example:"
        grep -E '^[A-Za-z_][A-Za-z0-9_]*=' ".env.example" | cut -d'=' -f1 | sed 's/^/  - /'
    fi
    return 1
fi
