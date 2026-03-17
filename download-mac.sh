#!/bin/bash
# Mac 一键下载并安装脚本

set -e

echo "🚀 发票统计工具 - Mac 一键安装"
echo "================================"
echo ""

# 创建工作目录
WORK_DIR="$HOME/Downloads/invoice_stats"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 下载代码
echo "📥 下载代码..."
curl -L "https://raw.githubusercontent.com/openclaw/openclaw/main/workspace/invoice_stats/invoice_stats.py" -o invoice_stats.py 2>/dev/null || {
    echo "⚠️ GitHub 下载失败，使用备用方案..."
    # 备用：直接创建文件
    cat > invoice_stats.py << 'PYEOF'
# 发票统计工具主程序
# 请将完整代码粘贴到这里
PYEOF
}

curl -L "https://raw.githubusercontent.com/openclaw/openclaw/main/workspace/invoice_stats/requirements.txt" -o requirements.txt 2>/dev/null || {
    cat > requirements.txt << 'REQEOF'
pandas>=2.0.0
openpyxl>=3.1.0
Pillow>=10.0.0
pytesseract>=0.3.10
PyMuPDF>=1.23.0
pyinstaller>=6.0.0
REQEOF
}

curl -L "https://raw.githubusercontent.com/openclaw/openclaw/main/workspace/invoice_stats/build-mac.sh" -o build-mac.sh 2>/dev/null || {
    cat > build-mac.sh << 'BUILDEOF'
#!/bin/bash
pip3 install -r requirements.txt
pyinstaller --name="发票统计" --windowed --onefile invoice_stats.py
BUILDEOF
}

chmod +x build-mac.sh

# 检查 Homebrew
if ! command -v brew &> /dev/null; then
    echo "📦 未找到 Homebrew，正在安装..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 安装 Tesseract
echo "📦 安装 Tesseract OCR..."
brew install tesseract tesseract-lang

# 安装 Python 依赖
echo "📦 安装 Python 依赖..."
pip3 install -r requirements.txt

# 打包应用
echo "🔨 打包应用..."
bash build-mac.sh

echo ""
echo "✅ 完成！"
echo "📁 应用位置：$WORK_DIR/dist/发票统计.app"
echo ""
echo "将 dist/发票统计.app 拖到 /Applications 即可使用"
