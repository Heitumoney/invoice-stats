# 📁 发票统计工具

发票识别与统计工具，支持 **本地 OCR** 和 **大模型 API** 两种方式。

## 功能

- ✅ 支持 JPG/PNG/PDF 多格式发票
- ✅ 本地 OCR 识别（Tesseract）
- ✅ 大模型 API 识别（Qwen-VL / GPT-4V / GLM-4V）⭐推荐
- ✅ 导出 Excel 统计报表
- ✅ 简洁图形界面

---

## 🚀 快速开始（API 版 - 推荐）

**无需安装 Tesseract，识别更准确！**

### 1. 获取 API Key

**阿里 Qwen-VL（推荐，国内可用）：**
1. 访问 https://dashscope.console.aliyun.com/
2. 注册/登录 → API Key 管理
3. 创建 API Key（新用户有免费额度）

**智谱 GLM-4V：**
1. 访问 https://open.bigmodel.cn/
2. 注册 → API Key

**OpenAI GPT-4V：**
1. 访问 https://platform.openai.com/
2. API Keys → 创建

### 2. 安装依赖

```bash
cd ~/Downloads/invoice-stats-main
pip3 install pandas openpyxl pillow pymupdf requests
```

### 3. 运行

```bash
python3 invoice_stats_api.py
```

### 4. 使用

1. 输入 API Key
2. 选择发票文件
3. 点击"开始识别"
4. 导出 Excel

---

## 🍎 Mac 用户 - 本地 OCR 版

需要安装 Tesseract，适合无网络或大量发票场景。

```bash
# 1. 设置镜像加速
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git"
export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.tuna.tsinghua.edu.cn/homebrew-bottles"

# 2. 安装 Tesseract
brew install tesseract tesseract-lang

# 3. 安装依赖
pip3 install -r requirements.txt

# 4. 打包应用
python3 -m PyInstaller --name="发票统计" --windowed --onefile invoice_stats.py

# 5. 打开
open dist/发票统计.app
```

---

## API 对比

| API | 价格 | 速度 | 准确率 | 推荐 |
|-----|------|------|--------|------|
| Qwen-VL | ¥0.01/张 | 快 | ⭐⭐⭐⭐⭐ | ✅ 国内首选 |
| GLM-4V | ¥0.005/张 | 快 | ⭐⭐⭐⭐ | ✅ 便宜 |
| GPT-4V | $0.01/张 | 中 | ⭐⭐⭐⭐⭐ | 需要代理 |
| Tesseract | 免费 | 快 | ⭐⭐⭐ | 本地离线 |

---

## 文件结构

```
invoice_stats/
├── invoice_stats.py        # 本地 OCR 版
├── invoice_stats_api.py    # API 版（推荐）
├── requirements.txt        # Python 依赖
├── install-mac.sh          # Mac 安装脚本
├── build-mac.sh            # Mac 打包脚本
└── README.md              # 说明文档
```

---

## 常见问题

**Q: API Key 安全吗？**
- API Key 只保存在内存中，关闭程序即清除
- 也可设置环境变量：`export INVOICE_API_KEY=xxx`

**Q: 识别不准确？**
- 确保发票图片清晰、光线均匀
- 优先使用扫描件而非拍照
- API 版准确率远高于本地 OCR

**Q: 费用多少？**
- Qwen-VL：新用户送 ¥20 额度（约 2000 张发票）
- GLM-4V：新用户送 ¥10 额度
- 单张发票约 ¥0.005-0.01
