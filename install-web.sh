#!/bin/bash
# 发票统计工具 - Mac 一键安装脚本
# 运行：curl -fsSL https://raw.githubusercontent.com/Heitumoney/invoice-stats/main/install-web.sh | bash

set -e

echo ""
echo "=========================================="
echo "  📁 发票统计工具 - 一键安装"
echo "=========================================="
echo ""

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 工作目录
WORK_DIR="$HOME/Applications/invoice-stats"

echo "📂 安装目录：$WORK_DIR"
echo ""

# 创建目录
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 检查 Python
echo "🔍 检查 Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 Python3${NC}"
    echo "请先安装 Python: https://www.python.org/downloads/"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"
echo ""

# 创建虚拟环境
echo "📦 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
echo -e "${GREEN}✅ 虚拟环境已创建${NC}"
echo ""

# 安装依赖
echo "📦 安装依赖 (约 1-2 分钟)..."
pip install --upgrade pip -q
pip install pandas openpyxl pillow pymupdf requests flask werkzeug -q
echo -e "${GREEN}✅ 依赖安装完成${NC}"
echo ""

# 下载代码
echo "📥 下载代码..."
curl -sL "https://raw.githubusercontent.com/Heitumoney/invoice-stats/main/invoice_stats_web.py" -o invoice_stats_web.py
if [ ! -f "invoice_stats_web.py" ]; then
    echo -e "${RED}❌ 代码下载失败${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 代码下载完成${NC}"
echo ""

# 创建启动脚本
cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo ""
echo "=========================================="
echo "  📁 发票统计工具"
echo "=========================================="
echo ""
echo "🌐 访问地址：http://localhost:5000"
echo "📱 或：http://$(hostname).local:5000"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="
echo ""
python3 invoice_stats_web.py
EOF
chmod +x start.sh

# 创建停止脚本
cat > stop.sh << 'EOF'
#!/bin/bash
pkill -f "invoice_stats_web.py"
echo "✅ 服务已停止"
EOF
chmod +x stop.sh

# 创建 README
cat > README.md << 'EOF'
# 发票统计工具

## 启动
```bash
./start.sh
```

## 访问
浏览器打开：http://localhost:5000

## 停止
```bash
./stop.sh
```
或按 Ctrl+C

## 获取 API Key
推荐阿里云 Qwen-VL：https://dashscope.console.aliyun.com/
新用户送 ¥20 额度（约 2000 张发票）
EOF

echo ""
echo "=========================================="
echo -e "${GREEN}✅ 安装完成！${NC}"
echo "=========================================="
echo ""
echo "📁 安装位置：$WORK_DIR"
echo ""
echo "🚀 启动命令："
echo "   cd $WORK_DIR"
echo "   ./start.sh"
echo ""
echo "📱 或创建快捷方式："
echo "   打开 Automator → 应用程序 → 运行 Shell 脚本"
echo "   输入：cd $WORK_DIR && ./start.sh"
echo ""

# 询问是否立即启动
read -p "是否现在启动？(y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./start.sh
else
    echo ""
    echo "稍后运行以下命令启动："
    echo "  cd $WORK_DIR && ./start.sh"
fi
