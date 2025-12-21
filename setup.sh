#!/bin/bash
#
# Setup script for Duc Tran's GitHub Profile
# Automates common development tasks
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_msg() {
    local color=$1
    local msg=$2
    echo -e "${color}${msg}${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Display banner
show_banner() {
    echo ""
    print_msg "$BLUE" "╔══════════════════════════════════════════╗"
    print_msg "$BLUE" "║     Duc Tran - GitHub Profile Setup      ║"
    print_msg "$BLUE" "║     Hydroinformatics Researcher          ║"
    print_msg "$BLUE" "╚══════════════════════════════════════════╝"
    echo ""
}

# Validate GitHub CLI
check_gh_cli() {
    if command_exists gh; then
        print_msg "$GREEN" "✓ GitHub CLI found"
        return 0
    else
        print_msg "$YELLOW" "⚠ GitHub CLI not found. Install from: https://cli.github.com/"
        return 1
    fi
}

# Validate Git
check_git() {
    if command_exists git; then
        print_msg "$GREEN" "✓ Git found: $(git --version)"
        return 0
    else
        print_msg "$RED" "✗ Git not found. Please install Git first."
        return 1
    fi
}

# Setup Git hooks
setup_hooks() {
    print_msg "$BLUE" "Setting up Git hooks..."

    local hooks_dir=".git/hooks"

    if [ -d "$hooks_dir" ]; then
        # Pre-commit hook
        cat > "$hooks_dir/pre-commit" << 'EOF'
#!/bin/bash
# Pre-commit hook: Validate README.md
if [ -f "README.md" ]; then
    # Check for broken image links
    if grep -q "!\[.*\](.*404.*)" README.md; then
        echo "Warning: Possible broken image links in README.md"
    fi
fi
exit 0
EOF
        chmod +x "$hooks_dir/pre-commit"
        print_msg "$GREEN" "✓ Pre-commit hook installed"
    fi
}

# Update profile stats
update_stats() {
    print_msg "$BLUE" "Fetching latest GitHub stats..."

    if command_exists gh; then
        local username=$(gh api user --jq '.login' 2>/dev/null || echo "ductran27")
        local repos=$(gh api "users/$username/repos" --jq 'length' 2>/dev/null || echo "N/A")
        local followers=$(gh api "users/$username" --jq '.followers' 2>/dev/null || echo "N/A")

        echo ""
        print_msg "$GREEN" "GitHub Stats for $username:"
        echo "  Repositories: $repos"
        echo "  Followers: $followers"
    fi
}

# Main menu
main_menu() {
    echo ""
    print_msg "$YELLOW" "Select an option:"
    echo "  1) Check prerequisites"
    echo "  2) Setup Git hooks"
    echo "  3) Update stats"
    echo "  4) Open portfolio locally"
    echo "  5) Exit"
    echo ""
    read -p "Enter choice [1-5]: " choice

    case $choice in
        1)
            check_git
            check_gh_cli
            ;;
        2)
            setup_hooks
            ;;
        3)
            update_stats
            ;;
        4)
            if [ -f "index.html" ]; then
                print_msg "$BLUE" "Opening portfolio in browser..."
                if command_exists open; then
                    open index.html
                elif command_exists xdg-open; then
                    xdg-open index.html
                else
                    print_msg "$YELLOW" "Please open index.html manually"
                fi
            else
                print_msg "$RED" "index.html not found"
            fi
            ;;
        5)
            print_msg "$GREEN" "Goodbye!"
            exit 0
            ;;
        *)
            print_msg "$RED" "Invalid option"
            ;;
    esac

    main_menu
}

# Entry point
main() {
    show_banner

    if [ "$1" == "--check" ]; then
        check_git
        check_gh_cli
        exit 0
    fi

    main_menu
}

main "$@"
