#!/bin/bash
# Script to check currently loaded environment variables
# Usage: ./check_env.sh or source check_env.sh

echo "🔍 Checking current environment variables..."
echo ""

# Define variable categories (using simple variables instead of associative arrays for macOS compatibility)
core_vars="OPENAI_API_KEY POSTGRES_URL HUGGINGFACE_TOKEN"
ai_models_vars="OPENAI_MODEL WHISPER_MODEL"
server_vars="CORS_ORIGINS"
vast_config_vars="VAST_API_KEY VAST_API_BASE VAST_INSTANCE_ID VAST_SSH_KEY VAST_CUT_BASE_DIR VAST_REMOTE_BASE_DIR VAST_DETAILS_TTL VAST_DISABLE_AUTO_STOP VAST_STOP_ACTIVITY_WINDOW VAST_SSH_HOST VAST_SSH_PORT VAST_REMOTE_INBOX VAST_REMOTE_OUTBOX VAST_SSH_USER"
gpu_processing_vars="CUT_ON_GPU VAST_UPSCALE_URL VAST_DISABLE_ENSURE GPU_SSH_HOST GPU_SSH_PORT GPU_SSH_USER GPU_CUT_BASE_DIR"
upscale_vars="UPSCALE_CONCURRENCY UPSCALE_UPLOAD_CONCURRENCY UPSCALE_RESULT_DOWNLOAD_CONCURRENCY UPSCALE_MODEL_NAME UPSCALE_DENOISE_STRENGTH UPSCALE_FACE_ENHANCE UPSCALE_OUTSCALE"
model_paths_vars="GFPGAN_MODEL_PATH REALESRGAN_MODEL_PATH XDG_CACHE_HOME"
cut_config_vars="CUT_BASE_DIR CUT_REQUIRE_CUDA CUT_FORCE_DEVICE CUT_ENABLE_UPSCALE"

# Function to check if a variable is set
check_var() {
    local var_name="$1"
    local var_value=$(eval "echo \$${var_name}")
    
    if [ -n "$var_value" ]; then
        case "$var_name" in
            *API_KEY|*PASSWORD|*SECRET|*TOKEN)
                echo "  ✅ $var_name: [SET - ${#var_value} chars]"
                ;;
            *URL|*HOST)
                # Mask sensitive parts of URLs
                masked_value=$(echo "$var_value" | sed -E 's|(://[^:/@]*)[^/@]*|\1***|g')
                echo "  ✅ $var_name: $masked_value"
                ;;
            *)
                echo "  ✅ $var_name: $var_value"
                ;;
        esac
        return 0
    else
        echo "  ❌ $var_name: [NOT SET]"
        return 1
    fi
}

# Function to check a category of variables
check_category() {
    local category_name="$1"
    local vars_list="$2"
    
    echo "📂 ${category_name} VARIABLES:"
    category_set=0
    category_total=0
    
    for var in $vars_list; do
        category_total=$((category_total + 1))
        total_vars=$((total_vars + 1))
        if check_var "$var"; then
            set_vars=$((set_vars + 1))
            category_set=$((category_set + 1))
        fi
    done
    
    echo "   └── ${category_set}/${category_total} variables set in this category"
    echo ""
}

# Check each category
total_vars=0
set_vars=0

check_category "CORE" "$core_vars"
check_category "AI MODELS" "$ai_models_vars"
check_category "SERVER" "$server_vars"
check_category "VAST CONFIG" "$vast_config_vars"
check_category "GPU PROCESSING" "$gpu_processing_vars"
check_category "UPSCALE" "$upscale_vars"
check_category "MODEL PATHS" "$model_paths_vars"
check_category "CUT CONFIG" "$cut_config_vars"

# Summary
echo "📊 SUMMARY:"
echo "   Total variables: $total_vars"
echo "   Set variables: $set_vars"
echo "   Missing variables: $((total_vars - set_vars))"

if [ $set_vars -eq $total_vars ]; then
    echo "   Status: ✅ All variables are configured!"
elif [ $set_vars -gt $((total_vars / 2)) ]; then
    echo "   Status: ⚠️  Most variables are configured"
else
    echo "   Status: ❌ Many variables are missing"
fi

echo ""
echo "💡 Tips:"
echo "   - Use 'source load_env.sh' to load variables from .env file"
echo "   - Use 'cp .env.example .env' to create .env file from template"
echo "   - Edit .env file with your actual values"