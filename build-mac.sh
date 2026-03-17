#!/bin/bash
# Mac 打包脚本 - 在 Mac 上运行此脚本创建 .app 应用

set -e

echo "🔧 开始打包发票统计工具..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python"
    exit 1
fi

# 安装依赖
echo "📦 安装 Python 依赖..."
pip3 install -r requirements.txt

# 安装 PyInstaller
echo "📦 安装 PyInstaller..."
pip3 install pyinstaller

# 检查 Tesseract
if ! command -v tesseract &> /dev/null; then
    echo "⚠️ 未找到 Tesseract OCR"
    echo "请运行：brew install tesseract tesseract-lang"
    read -p "是否继续打包？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 创建 PyInstaller 配置
echo "🔨 创建应用包..."

pyinstaller --name="发票统计" \
    --windowed \
    --onefile \
    --icon=icon.icns \
    --add-data="README.md:." \
    --osx-bundle-identifier="com.invoice.stats" \
    --hidden-import=pandas \
    --hidden-import=openpyxl \
    --hidden-import=pytesseract \
    --hidden-import=PIL \
    --hidden-import=fitz \
    invoice_stats.py

# 清理
echo "🧹 清理临时文件..."
rm -rf build
rm -rf invoice_stats.spec

echo ""
echo "✅ 打包完成！"
echo ""
echo "📁 应用位置：dist/发票统计.app"
echo ""
echo "使用方法："
echo "  1. 将 dist/发票统计.app 拖到 /Applications 文件夹"
echo "  2. 首次运行可能需要右键→打开（Mac 安全策略）"
echo ""
