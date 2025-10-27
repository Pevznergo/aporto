#!/bin/bash
# Fix for distutils-installed packages that prevent pip upgrades
# Common packages: blinker, PyYAML, etc.

set -e

echo "🔧 Fixing distutils-installed packages..."

# List of common problematic packages
PROBLEMATIC_PACKAGES=(
    "blinker"
    "PyYAML"
    "MarkupSafe"
    "Jinja2"
)

# Function to safely remove a distutils package
remove_distutils_package() {
    local package=$1
    
    # Check if package is installed
    if python3 -c "import $package" 2>/dev/null; then
        echo "  Found distutils package: $package"
        
        # Try to get package location
        PACKAGE_PATH=$(python3 -c "import $package; print($package.__file__)" 2>/dev/null | xargs dirname 2>/dev/null || echo "")
        
        if [ -n "$PACKAGE_PATH" ] && [ -d "$PACKAGE_PATH" ]; then
            # Check if it's in system directories
            if [[ "$PACKAGE_PATH" == /usr/lib/* ]] || [[ "$PACKAGE_PATH" == /usr/local/lib/* ]]; then
                echo "    System package detected, using --ignore-installed"
                return 0
            fi
        fi
    fi
    return 1
}

# Check for problematic packages
NEEDS_IGNORE=false
for pkg in "${PROBLEMATIC_PACKAGES[@]}"; do
    # Convert package name to module name (e.g., PyYAML -> yaml)
    MODULE_NAME=$pkg
    case $pkg in
        "PyYAML") MODULE_NAME="yaml" ;;
        "MarkupSafe") MODULE_NAME="markupsafe" ;;
        "Jinja2") MODULE_NAME="jinja2" ;;
    esac
    
    if remove_distutils_package "$MODULE_NAME"; then
        NEEDS_IGNORE=true
    fi
done

# Create a flag file to indicate pip should use --ignore-installed
if [ "$NEEDS_IGNORE" = true ]; then
    echo "  ⚠️  Distutils packages detected"
    echo "  Will use --ignore-installed for pip install"
    touch /tmp/.pip_ignore_installed
    echo "true"
else
    echo "  ✅ No problematic distutils packages found"
    rm -f /tmp/.pip_ignore_installed
    echo "false"
fi
