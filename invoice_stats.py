#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发票统计工具 - Invoice Stats
支持图片/PDF 发票识别，导出 Excel 统计
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from datetime import datetime
from pathlib import Path

# 第三方库（需要安装）
try:
    import pandas as pd
    from openpyxl import Workbook
    import pytesseract
    from PIL import Image
    import fitz  # PyMuPDF for PDF
    HAS_DEPS = True
except ImportError as e:
    HAS_DEPS = False
    MISSING_DEPS = str(e)


class InvoiceStatsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📁 发票统计工具")
        self.root.geometry("600x500")
        self.root.minsize(500, 400)
        
        # 数据存储
        self.files = []
        self.results = []
        self.is_processing = False
        
        # 创建界面
        self._create_widgets()
        
    def _create_widgets(self):
        """创建界面组件"""
        # 标题
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame, 
            text="📁 发票统计工具", 
            font=("Helvetica", 16, "bold")
        )
        title_label.pack()
        
        # 文件选择区
        file_frame = ttk.LabelFrame(self.root, text="文件选择", padding="10")
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X)
        
        self.btn_select = ttk.Button(
            btn_frame, text="📂 选择文件", command=self._select_files
        )
        self.btn_select.pack(side=tk.LEFT, padx=5)
        
        self.btn_batch = ttk.Button(
            btn_frame, text="📂 批量选择", command=self._batch_select
        )
        self.btn_batch.pack(side=tk.LEFT, padx=5)
        
        self.btn_clear = ttk.Button(
            btn_frame, text="🗑️ 清空", command=self._clear_files, state=tk.DISABLED
        )
        self.btn_clear.pack(side=tk.RIGHT, padx=5)
        
        # 文件列表
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.file_count_label = ttk.Label(list_frame, text="已选择：0 个文件")
        self.file_count_label.pack(anchor=tk.W)
        
        # 文件列表框
        self.file_listbox = tk.Listbox(file_frame, height=6, font=("Courier", 9))
        self.file_listbox.pack(fill=tk.X, pady=(5, 0))
        
        # 进度区
        progress_frame = ttk.LabelFrame(self.root, text="处理进度", padding="10")
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_var = tk.StringVar(value="就绪")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame, mode='determinate', length=500
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # 结果预览区
        result_frame = ttk.LabelFrame(self.root, text="识别结果预览", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 表格
        columns = ("文件名", "金额", "日期", "商家", "状态")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=6)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮区
        action_frame = ttk.Frame(self.root, padding="10")
        action_frame.pack(fill=tk.X)
        
        self.btn_process = ttk.Button(
            action_frame, text="🚀 开始识别", command=self._start_processing
        )
        self.btn_process.pack(side=tk.LEFT, padx=5)
        
        self.btn_export = ttk.Button(
            action_frame, text="📊 导出 Excel", command=self._export_excel, state=tk.DISABLED
        )
        self.btn_export.pack(side=tk.LEFT, padx=5)
        
        # 依赖检查提示
        if not HAS_DEPS:
            self._show_dep_warning()
    
    def _show_dep_warning(self):
        """显示依赖缺失警告"""
        warning = f"""⚠️ 缺少必要的依赖库

请运行以下命令安装：

pip install pandas openpyxl pytesseract pillow pymupdf

或者使用 requirements.txt:
pip install -r requirements.txt

注意：还需要安装 Tesseract OCR：
- Mac: brew install tesseract
- 详见 README.md"""
        
        messagebox.showwarning("依赖缺失", warning)
    
    def _select_files(self):
        """选择单个文件"""
        filetypes = [
            ("发票文件", "*.jpg *.jpeg *.png *.pdf"),
            ("图片文件", "*.jpg *.jpeg *.png"),
            ("PDF 文件", "*.pdf"),
            ("所有文件", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="选择发票文件",
            filetypes=filetypes
        )
        
        if files:
            self._add_files(files)
    
    def _batch_select(self):
        """批量选择（文件夹）"""
        folder = filedialog.askdirectory(title="选择发票文件夹")
        if folder:
            files = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.pdf']:
                files.extend(Path(folder).glob(ext))
            if files:
                self._add_files([str(f) for f in files])
    
    def _add_files(self, files):
        """添加文件到列表"""
        for f in files:
            if f not in self.files:
                self.files.append(f)
                self.file_listbox.insert(tk.END, f"  {os.path.basename(f)}")
        
        self._update_file_count()
        self.btn_clear.config(state=tk.NORMAL if self.files else tk.DISABLED)
    
    def _clear_files(self):
        """清空文件列表"""
        self.files.clear()
        self.results.clear()
        self.file_listbox.delete(0, tk.END)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._update_file_count()
        self.btn_clear.config(state=tk.DISABLED)
        self.btn_export.config(state=tk.DISABLED)
        self.progress_var.set("已清空")
        self.progress_bar['value'] = 0
    
    def _update_file_count(self):
        """更新文件计数"""
        self.file_count_label.config(text=f"已选择：{len(self.files)} 个文件")
    
    def _start_processing(self):
        """开始处理（线程）"""
        if not self.files:
            messagebox.showwarning("提示", "请先选择发票文件")
            return
        
        if self.is_processing:
            return
        
        self.is_processing = True
        self.btn_process.config(state=tk.DISABLED)
        self.btn_select.config(state=tk.DISABLED)
        self.btn_batch.config(state=tk.DISABLED)
        
        # 清空旧结果
        self.results.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 启动处理线程
        thread = threading.Thread(target=self._process_files, daemon=True)
        thread.start()
    
    def _process_files(self):
        """处理所有文件"""
        if not HAS_DEPS:
            self.root.after(0, lambda: messagebox.showerror(
                "错误", "缺少依赖库，请先安装依赖"
            ))
            self._reset_ui()
            return
        
        total = len(self.files)
        
        for i, filepath in enumerate(self.files):
            # 更新进度
            progress = int((i / total) * 100)
            self.root.after(0, lambda p=progress, f=filepath: self._update_progress(p, f"处理中：{os.path.basename(f)}"))
            
            try:
                result = self._extract_invoice_info(filepath)
                self.results.append(result)
                
                # 添加到表格
                self.root.after(0, lambda r=result: self._add_result_to_table(r))
                
            except Exception as e:
                self.results.append({
                    'filename': os.path.basename(filepath),
                    'amount': '',
                    'date': '',
                    'merchant': '',
                    'status': f'❌ 错误：{str(e)}'
                })
                self.root.after(0, lambda f=filepath, err=str(e): 
                    self._add_result_to_table({
                        'filename': os.path.basename(f),
                        'amount': '',
                        'date': '',
                        'merchant': '',
                        'status': f'❌ {err}'
                    })
                )
        
        # 完成
        self.root.after(0, lambda: self._update_progress(100, "处理完成！"))
        self.root.after(0, self._reset_ui)
        self.root.after(0, lambda: self.btn_export.config(state=tk.NORMAL))
    
    def _extract_invoice_info(self, filepath):
        """提取发票信息（简化版 OCR）"""
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()
        
        text = ""
        
        if ext in ['.jpg', '.jpeg', '.png']:
            # 图片 OCR
            image = Image.open(filepath)
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            
        elif ext == '.pdf':
            # PDF 处理
            doc = fitz.open(filepath)
            for page in doc:
                text += page.get_text()
            doc.close()
            
            # 如果 PDF 是扫描版，尝试 OCR
            if len(text.strip()) < 50:
                # 简单处理第一页
                page = doc[0]
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img, lang='chi_sim+eng')
        
        # 解析文本（简化版，实际需要更复杂的正则）
        amount = self._extract_amount(text)
        date = self._extract_date(text)
        merchant = self._extract_merchant(text)
        
        return {
            'filename': filename,
            'amount': amount or '',
            'date': date or '',
            'merchant': merchant or '未识别',
            'status': '✅ 成功' if amount else '⚠️ 金额未识别'
        }
    
    def _extract_amount(self, text):
        """提取金额（简化版）"""
        import re
        # 匹配 ¥ 123.45 或 123.45 元
        patterns = [
            r'¥\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*元',
            r'金额 [:：]?\s*([\d,]+\.?\d*)',
            r'小计 [:：]?\s*([\d,]+\.?\d*)',
            r'总计 [:：]?\s*([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                amount = match.group(1).replace(',', '')
                return f"¥{amount}"
        
        return None
    
    def _extract_date(self, text):
        """提取日期"""
        import re
        patterns = [
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?)',
            r'(\d{2}[-/]\d{2}[-/]\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_merchant(self, text):
        """提取商家名称（简化版）"""
        import re
        # 查找可能的公司名
        patterns = [
            r'([^\n]{0,30}公司 [^\n]{0,10})',
            r'([^\n]{0,30}店 [^\n]{0,10})',
            r'销售方 [:：]?\s*([^\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()[:20]
        
        return None
    
    def _update_progress(self, value, text):
        """更新进度"""
        self.progress_var.set(text)
        self.progress_bar['value'] = value
    
    def _add_result_to_table(self, result):
        """添加结果到表格"""
        self.tree.insert("", tk.END, values=(
            result['filename'],
            result['amount'],
            result['date'],
            result['merchant'],
            result['status']
        ))
    
    def _reset_ui(self):
        """重置 UI 状态"""
        self.is_processing = False
        self.btn_process.config(state=tk.NORMAL)
        self.btn_select.config(state=tk.NORMAL)
        self.btn_batch.config(state=tk.NORMAL)
    
    def _export_excel(self):
        """导出 Excel"""
        if not self.results:
            messagebox.showwarning("提示", "没有可导出的数据")
            return
        
        filetypes = [("Excel 文件", "*.xlsx")]
        filepath = filedialog.asksaveasfilename(
            title="导出 Excel",
            defaultextension=".xlsx",
            filetypes=filetypes,
            initialfile=f"发票统计_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        
        if not filepath:
            return
        
        try:
            # 创建 DataFrame
            df = pd.DataFrame(self.results)
            
            # 添加统计行
            total_amount = 0
            valid_amounts = []
            for r in self.results:
                if r['amount']:
                    try:
                        amount = float(r['amount'].replace('¥', '').replace(',', ''))
                        valid_amounts.append(amount)
                    except:
                        pass
            total_amount = sum(valid_amounts)
            
            # 写入 Excel
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='发票明细', index=False)
                
                # 统计 sheet
                summary_data = {
                    '项目': ['总张数', '有效金额张数', '总金额'],
                    '值': [len(self.results), len(valid_amounts), f'¥{total_amount:.2f}']
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='统计汇总', index=False)
            
            messagebox.showinfo("成功", f"已导出到:\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出失败:\n{str(e)}")


def main():
    root = tk.Tk()
    app = InvoiceStatsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
