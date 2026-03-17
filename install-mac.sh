#!/bin/bash
# 一键安装脚本 - 在 Mac 上运行

set -e

echo "🚀 发票统计工具 - Mac 一键安装"
echo "================================"
echo ""

# 检查 Homebrew
if ! command -v brew &> /dev/null; then
    echo "📦 安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 安装 Tesseract
echo "📦 安装 Tesseract OCR..."
brew install tesseract tesseract-lang

# 安装 Python 依赖
echo "📦 安装 Python 依赖..."
pip3 install pandas openpyxl pytesseract pillow pymupdf pyinstaller

# 打包应用
echo "🔨 打包应用..."
bash build-mac.sh

echo ""
echo "✅ 安装完成！"
echo ""
