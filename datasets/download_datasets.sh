#!/usr/bin/env bash
# =============================================================================
# NutriMind – Dataset Download Script
# Downloads Food-101, UECFood256, Nutrition5K, Recipe1M datasets
# Usage: bash download_datasets.sh [dataset_name]
#   dataset_name: food101 | uecfood256 | nutrition5k | recipe1m | all (default)
# =============================================================================

set -e
DATASETS_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-all}"
BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }

check_tools() {
    for tool in wget curl python3; do
        command -v "$tool" &>/dev/null || { echo "Required tool not found: $tool"; exit 1; }
    done
}

# ── Food-101 (~5GB) ──────────────────────────────────────────────────────────
download_food101() {
    log_info "Downloading Food-101 dataset (~5GB)..."
    mkdir -p "$DATASETS_DIR/food-101"
    cd "$DATASETS_DIR/food-101"

    if [ ! -f "food-101.tar.gz" ]; then
        wget -c "http://data.vision.ee.ethz.ch/cvl/food-101.tar.gz" -O food-101.tar.gz
    fi

    if [ ! -d "images" ]; then
        log_info "Extracting Food-101..."
        tar -xzf food-101.tar.gz --strip-components=1
    fi

    log_ok "Food-101 ready: $(find images -name '*.jpg' | wc -l) images"
    cd "$DATASETS_DIR"
}

# ── UECFood256 (~2GB) ─────────────────────────────────────────────────────────
download_uecfood256() {
    log_info "Downloading UECFood256 dataset (~2GB)..."
    mkdir -p "$DATASETS_DIR/UECFood256"
    cd "$DATASETS_DIR/UECFood256"

    if [ ! -f "UECFOOD256.tar.gz" ]; then
        # Mirror available via Kaggle or direct
        wget -c "http://foodcam.mobi/dataset256.zip" -O UECFOOD256.zip 2>/dev/null || \
        log_warn "UECFood256 direct download unavailable. Download manually from: http://foodcam.mobi/dataset256.zip"
    fi

    if [ -f "UECFOOD256.zip" ]; then
        unzip -q UECFOOD256.zip
        log_ok "UECFood256 extracted"
    fi
    cd "$DATASETS_DIR"
}

# ── Nutrition5K (~8GB, Google Drive) ─────────────────────────────────────────
download_nutrition5k() {
    log_info "Downloading Nutrition5K dataset (~8GB)..."
    mkdir -p "$DATASETS_DIR/nutrition5k"

    log_warn "Nutrition5K requires Google Drive access."
    log_warn "Request access at: https://github.com/google-research-datasets/Nutrition5k"
    log_warn "Then place files in: $DATASETS_DIR/nutrition5k/"
    log_warn "Or use: pip install gdown && gdown <gdrive_id> -O $DATASETS_DIR/nutrition5k/"

    # If gdown is available
    if command -v gdown &>/dev/null; then
        log_info "Attempting gdown download..."
        gdown --folder "https://drive.google.com/drive/folders/1Ykm0gYrv2oWflTKJFzNgjHtMXTolKxH4" \
              -O "$DATASETS_DIR/nutrition5k/" 2>/dev/null || \
        log_warn "gdown failed. Manual download required."
    fi
}

# ── Recipe1M (~30GB) ──────────────────────────────────────────────────────────
download_recipe1m() {
    log_info "Recipe1M requires registration at: http://pic2recipe.csail.mit.edu/"
    mkdir -p "$DATASETS_DIR/recipe1M"

    cat <<EOF
To download Recipe1M:
1. Register at http://pic2recipe.csail.mit.edu/
2. Download layer1.json, layer2.json, and images
3. Place in: $DATASETS_DIR/recipe1M/

Alternative: Use the HuggingFace mirror:
  pip install datasets
  python3 -c "from datasets import load_dataset; ds = load_dataset('huggingface/recipe1m', split='train')"
EOF
}

# ── Indian Food Composition (IFCT 2017) ───────────────────────────────────────
download_indian_fcd() {
    log_info "Setting up Indian Food Composition Tables..."
    mkdir -p "$DATASETS_DIR/indian_fcd"

    # Download if available
    IFCT_URL="https://raw.githubusercontent.com/NutriMind/datasets/main/ifct2017.csv"
    curl -fsSL "$IFCT_URL" -o "$DATASETS_DIR/indian_fcd/ifct2017.csv" 2>/dev/null || \
    log_warn "IFCT 2017 CSV not found online. Place ifct2017.csv in $DATASETS_DIR/indian_fcd/"
}

# ── Preprocess all downloaded datasets ───────────────────────────────────────
preprocess_all() {
    log_info "Running preprocessing scripts..."

    [ -d "$DATASETS_DIR/food-101/images" ] && \
        python3 "$DATASETS_DIR/preprocess_food101.py" && log_ok "Food-101 preprocessed"

    [ -d "$DATASETS_DIR/UECFood256" ] && \
        python3 "$DATASETS_DIR/preprocess_uecfood256.py" && log_ok "UECFood256 preprocessed"

    [ -d "$DATASETS_DIR/nutrition5k" ] && \
        python3 "$DATASETS_DIR/preprocess_nutrition5k.py" && log_ok "Nutrition5K preprocessed"
}

# ── Main ──────────────────────────────────────────────────────────────────────
check_tools

echo "======================================================"
echo "  NutriMind Dataset Downloader"
echo "======================================================"

case "$TARGET" in
    food101)      download_food101 ;;
    uecfood256)   download_uecfood256 ;;
    nutrition5k)  download_nutrition5k ;;
    recipe1m)     download_recipe1m ;;
    indian)       download_indian_fcd ;;
    all)
        download_food101
        download_uecfood256
        download_nutrition5k
        download_recipe1m
        download_indian_fcd
        preprocess_all
        ;;
    *)
        echo "Usage: bash download_datasets.sh [food101|uecfood256|nutrition5k|recipe1m|indian|all]"
        exit 1
        ;;
esac

log_ok "Done! Run preprocessing: python3 preprocess_food101.py"
