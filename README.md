# 📁 发票统计工具

简单的发票识别与统计工具，支持 Mac/Windows/Linux。

## 功能

- ✅ 支持 JPG/PNG/PDF 多格式发票
- ✅ OCR 自动识别金额、日期、商家
- ✅ 导出 Excel 统计报表
- ✅ 简洁图形界面

---

## 🍎 Mac 用户 - 两种方式

### 方式一：一键安装（推荐）

```bash
# 1. 下载后打开终端
cd ~/Downloads/invoice_stats

# 2. 运行一键安装脚本
chmod +x install-mac.sh
./install-mac.sh
```

等待完成后，在 `dist/` 文件夹找到 **发票统计.app**，拖到应用程序文件夹即可。

### 方式二：直接运行 Python 脚本

```bash
# 1. 安装 Tesseract
brew install tesseract tesseract-lang

# 2. 安装依赖
pip3 install -r requirements.txt

# 3. 运行
python3 invoice_stats.py
```

---

## 使用说明

1. 点击"选择文件"或"批量选择"添加发票
2. 点击"开始识别"进行 OCR 识别
3. 查看识别结果预览
4. 点击"导出 Excel"保存统计结果

---

## 注意事项

- OCR 识别准确率取决于发票图片质量
- 建议扫描或拍照时保持发票平整、光线充足
- 识别结果可手动在 Excel 中修正
- Mac 首次运行 .app 可能需要右键→打开（安全策略）

---

## 文件结构

```
invoice_stats/
├── invoice_stats.py    # 主程序
├── requirements.txt    # Python 依赖
├── build-mac.sh        # Mac 打包脚本
├── install-mac.sh      # Mac 一键安装脚本
└── README.md          # 说明文档
```

---

## 常见问题

**Q: 提示找不到 tesseract？**
```bash
brew install tesseract tesseract-lang
```

**Q: Mac 无法打开 .app？**
- 右键点击应用 → 打开 → 确认打开
- 或：系统偏好设置 → 安全性 → 允许打开

**Q: 识别不准确？**
- 确保发票图片清晰
- 光线均匀，无阴影
- 尽量使用扫描件而非拍照
