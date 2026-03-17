#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发票统计工具 - API 版
使用视觉大模型识别发票（无需 Tesseract）
支持：Qwen-VL / GPT-4V / Claude / GLM-4V
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import base64
import json
from datetime import datetime
from pathlib import Path

# 第三方库
try:
    import pandas as pd
    from openpyxl import Workbook
    from PIL import Image
    import fitz  # PyMuPDF for PDF
    import requests
    HAS_DEPS = True
except ImportError as e:
    HAS_DEPS = False
    MISSING_DEPS = str(e)


class InvoiceAPIRecognizer:
    """发票识别器 - 使用大模型 API"""
    
    def __init__(self, api_type="qwen", api_key=None):
        self.api_type = api_type
        self.api_key = api_key or os.getenv("INVOICE_API_KEY", "")
        
        # API 配置
        self.endpoints = {
            "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            "gpt": "https://api.openai.com/v1/chat/completions",
            "glm": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        }
        
        self.models = {
            "qwen": "qwen-vl-max-latest",
            "gpt": "gpt-4o",
            "glm": "glm-4v-flash",
        }
    
    def encode_image(self, image_path):
        """将图片编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def pdf_to_image(self, pdf_path, page=0):
        """PDF 转图片"""
        doc = fitz.open(pdf_path)
        page = doc[page]
        pix = page.get_pixmap()
        img_path = pdf_path + f"_page{page}.png"
        pix.save(img_path)
        doc.close()
        return img_path
    
    def recognize(self, file_path):
        """识别发票"""
        ext = os.path.splitext(file_path)[1].lower()
        
        # PDF 转图片
        if ext == ".pdf":
            img_path = self.pdf_to_image(file_path)
            file_path = img_path
        
        # 编码图片
        base64_image = self.encode_image(file_path)
        
        # 构建请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        prompt = """请识别这张发票图片中的关键信息，返回 JSON 格式：
{
    "amount": "发票金额（数字，不含符号）",
    "date": "开票日期（YYYY-MM-DD 格式）",
    "merchant": "商家名称",
    "invoice_code": "发票代码",
    "invoice_number": "发票号码"
}
只返回 JSON，不要其他文字。如果某些字段无法识别，留空字符串。"""
        
        payload = {
            "model": self.models.get(self.api_type, "qwen-vl-max-latest"),
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }],
            "max_tokens": 500
        }
        
        # 发送请求
        endpoint = self.endpoints.get(self.api_type)
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # 解析结果
        content = result["choices"][0]["message"]["content"]
        
        # 提取 JSON
        import re
        json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        
        return {"amount": "", "date": "", "merchant": "", "status": "解析失败"}
    
    def cleanup(self, file_path):
        """清理临时文件"""
        if file_path.endswith("_page.png"):
            try:
                os.remove(file_path)
            except:
                pass


class InvoiceStatsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📁 发票统计工具 - API 版")
        self.root.geometry("650x550")
        self.root.minsize(550, 450)
        
        # 数据
        self.files = []
        self.results = []
        self.is_processing = False
        
        # API 配置
        self.api_type = tk.StringVar(value="qwen")
        self.api_key = tk.StringVar()
        
        # 创建界面
        self._create_widgets()
        
    def _create_widgets(self):
        """创建界面"""
        # 标题
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        ttk.Label(title_frame, text="📁 发票统计工具 - API 版", 
                  font=("Helvetica", 16, "bold")).pack()
        
        # API 配置区
        api_frame = ttk.LabelFrame(self.root, text="API 配置", padding="10")
        api_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # API 类型
        type_frame = ttk.Frame(api_frame)
        type_frame.pack(fill=tk.X)
        
        ttk.Label(type_frame, text="API 类型:").pack(side=tk.LEFT, padx=5)
        api_combo = ttk.Combobox(type_frame, textvariable=self.api_type, 
                                  values=["qwen", "gpt", "glm"], width=15)
        api_combo.pack(side=tk.LEFT, padx=5)
        api_combo.set("qwen")
        
        # API Key
        key_frame = ttk.Frame(api_frame)
        key_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(key_frame, text="API Key:").pack(side=tk.LEFT, padx=5)
        key_entry = ttk.Entry(key_frame, textvariable=self.api_key, width=50, show="*")
        key_entry.pack(side=tk.LEFT, padx=5)
        
        # 提示
        ttk.Label(api_frame, text="💡 也可设置环境变量 INVOICE_API_KEY", 
                  font=("Courier", 8), foreground="gray").pack(anchor=tk.W, pady=(5, 0))
        
        # 文件选择区
        file_frame = ttk.LabelFrame(self.root, text="文件选择", padding="10")
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="📂 选择文件", 
                   command=self._select_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📂 批量选择", 
                   command=self._batch_select).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ 清空", 
                   command=self._clear_files, state=tk.DISABLED).pack(side=tk.RIGHT, padx=5)
        
        # 文件列表
        self.file_count_label = ttk.Label(file_frame, text="已选择：0 个文件")
        self.file_count_label.pack(anchor=tk.W, pady=(5, 0))
        
        self.file_listbox = tk.Listbox(file_frame, height=5, font=("Courier", 9))
        self.file_listbox.pack(fill=tk.X, pady=(5, 0))
        
        # 进度区
        progress_frame = ttk.LabelFrame(self.root, text="处理进度", padding="10")
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_var = tk.StringVar(value="就绪")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=500)
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # 结果预览
        result_frame = ttk.LabelFrame(self.root, text="识别结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("文件名", "金额", "日期", "商家", "状态")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮区
        action_frame = ttk.Frame(self.root, padding="10")
        action_frame.pack(fill=tk.X)
        
        self.btn_process = ttk.Button(action_frame, text="🚀 开始识别", 
                                       command=self._start_processing)
        self.btn_process.pack(side=tk.LEFT, padx=5)
        
        self.btn_export = ttk.Button(action_frame, text="📊 导出 Excel", 
                                      command=self._export_excel, state=tk.DISABLED)
        self.btn_export.pack(side=tk.LEFT, padx=5)
        
        if not HAS_DEPS:
            messagebox.showwarning("依赖缺失", f"缺少依赖：{MISSING_DEPS}\n\n请运行：pip3 install pandas openpyxl pillow pymupdf requests")
    
    def _select_files(self):
        filetypes = [("发票文件", "*.jpg *.jpeg *.png *.pdf"), ("所有文件", "*.*")]
        files = filedialog.askopenfilenames(title="选择发票", filetypes=filetypes)
        if files:
            self._add_files(files)
    
    def _batch_select(self):
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            files = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.pdf']:
                files.extend(Path(folder).glob(ext))
            if files:
                self._add_files([str(f) for f in files])
    
    def _add_files(self, files):
        for f in files:
            if f not in self.files:
                self.files.append(f)
                self.file_listbox.insert(tk.END, f"  {os.path.basename(f)}")
        self._update_file_count()
    
    def _clear_files(self):
        self.files.clear()
        self.results.clear()
        self.file_listbox.delete(0, tk.END)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._update_file_count()
    
    def _update_file_count(self):
        self.file_count_label.config(text=f"已选择：{len(self.files)} 个文件")
    
    def _start_processing(self):
        if not self.files:
            messagebox.showwarning("提示", "请先选择文件")
            return
        if not self.api_key.get():
            messagebox.showwarning("提示", "请填写 API Key")
            return
        
        self.is_processing = True
        self.btn_process.config(state=tk.DISABLED)
        
        self.results.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        thread = threading.Thread(target=self._process_files, daemon=True)
        thread.start()
    
    def _process_files(self):
        recognizer = InvoiceAPIRecognizer(
            api_type=self.api_type.get(),
            api_key=self.api_key.get()
        )
        
        total = len(self.files)
        for i, filepath in enumerate(self.files):
            progress = int((i / total) * 100)
            self.root.after(0, lambda p=progress, f=filepath: 
                self._update_progress(p, f"处理：{os.path.basename(f)}"))
            
            try:
                result = recognizer.recognize(filepath)
                result['filename'] = os.path.basename(filepath)
                result['status'] = '✅' if result.get('amount') else '⚠️'
                self.results.append(result)
                self.root.after(0, lambda r=result: self._add_result(r))
            except Exception as e:
                self.results.append({
                    'filename': os.path.basename(filepath),
                    'amount': '', 'date': '', 'merchant': '', 'status': f'❌ {str(e)}'
                })
        
        self.root.after(0, lambda: self._update_progress(100, "完成！"))
        self.root.after(0, lambda: self.btn_process.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.btn_export.config(state=tk.NORMAL))
    
    def _update_progress(self, value, text):
        self.progress_var.set(text)
        self.progress_bar['value'] = value
    
    def _add_result(self, result):
        self.tree.insert("", tk.END, values=(
            result.get('filename', ''),
            result.get('amount', ''),
            result.get('date', ''),
            result.get('merchant', ''),
            result.get('status', '')
        ))
    
    def _export_excel(self):
        if not self.results:
            messagebox.showwarning("提示", "无数据")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=f"发票_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        if not filepath:
            return
        
        df = pd.DataFrame(self.results)
        df.to_excel(filepath, index=False)
        messagebox.showinfo("成功", f"已导出：\n{filepath}")


def main():
    root = tk.Tk()
    app = InvoiceStatsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
