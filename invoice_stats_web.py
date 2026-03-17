#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发票统计工具 - 网页版
使用浏览器界面，无需 tkinter
"""

import os
import base64
import json
import re
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template_string
from werkzeug.utils import secure_filename
import pandas as pd
from PIL import Image
import fitz
import requests

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# 配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# API 配置
API_ENDPOINTS = {
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "gpt": "https://api.openai.com/v1/chat/completions",
    "glm": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
}

API_MODELS = {
    "qwen": "qwen-vl-max-latest",
    "gpt": "gpt-4o",
    "glm": "glm-4v-flash",
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def pdf_to_image(pdf_path, page=0):
    doc = fitz.open(pdf_path)
    page = doc[page]
    pix = page.get_pixmap()
    img_path = pdf_path + f"_page{page}.png"
    pix.save(img_path)
    doc.close()
    return img_path


def recognize_invoice(file_path, api_type, api_key):
    """识别发票"""
    ext = os.path.splitext(file_path)[1].lower()
    
    # PDF 转图片
    if ext == ".pdf":
        img_path = pdf_to_image(file_path)
        file_path = img_path
    
    # 编码图片
    base64_image = encode_image(file_path)
    
    # 构建请求
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
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
        "model": API_MODELS.get(api_type, "qwen-vl-max-latest"),
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
    endpoint = API_ENDPOINTS.get(api_type)
    response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    result = response.json()
    
    # 解析结果
    content = result["choices"][0]["message"]["content"]
    
    # 提取 JSON
    json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group())
        # 清理临时文件
        if ext == ".pdf" and os.path.exists(file_path):
            os.remove(file_path)
        return data
    
    if ext == ".pdf" and os.path.exists(file_path):
        os.remove(file_path)
    return {"amount": "", "date": "", "merchant": "", "status": "解析失败"}


# HTML 模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📁 发票统计工具 - 网页版</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .content { padding: 30px; }
        
        .form-group { margin-bottom: 20px; }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e1e5eb;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .upload-area {
            border: 3px dashed #e1e5eb;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 20px;
        }
        .upload-area:hover, .upload-area.dragover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        .upload-area p { color: #666; margin-bottom: 10px; }
        .upload-area .icon { font-size: 48px; margin-bottom: 10px; }
        .upload-area input { display: none; }
        
        .file-list {
            margin: 20px 0;
            max-height: 200px;
            overflow-y: auto;
        }
        .file-item {
            display: flex;
            align-items: center;
            padding: 10px 15px;
            background: #f8f9ff;
            border-radius: 8px;
            margin-bottom: 8px;
        }
        .file-item .name { flex: 1; }
        .file-item .remove {
            color: #ff4757;
            cursor: pointer;
            padding: 5px 10px;
        }
        
        .btn {
            display: inline-block;
            padding: 14px 28px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .btn-secondary {
            background: #6c757d;
        }
        
        .progress {
            margin: 20px 0;
            display: none;
        }
        .progress-bar {
            height: 8px;
            background: #e1e5eb;
            border-radius: 4px;
            overflow: hidden;
        }
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s;
        }
        .progress-text {
            text-align: center;
            margin-top: 10px;
            color: #666;
        }
        
        .results {
            margin-top: 30px;
            display: none;
        }
        .results h3 { margin-bottom: 15px; }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e1e5eb;
        }
        th {
            background: #f8f9ff;
            font-weight: 600;
            color: #333;
        }
        tr:hover { background: #f8f9ff; }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }
        .stat-card .value { font-size: 28px; font-weight: bold; }
        .stat-card .label { opacity: 0.9; margin-top: 5px; }
        
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .alert-info {
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            color: #0d47a1;
        }
        .alert-error {
            background: #ffebee;
            border-left: 4px solid #f44336;
            color: #b71c1c;
        }
        
        .actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📁 发票统计工具 - 网页版</h1>
            <p>使用 AI 大模型自动识别发票，导出 Excel 统计报表</p>
        </div>
        
        <div class="content">
            <div class="alert alert-info">
                💡 <strong>提示：</strong>首次使用需要 API Key。推荐阿里云 Qwen-VL（新用户送 ¥20 额度）
                <br>获取地址：<a href="https://dashscope.console.aliyun.com/" target="_blank">https://dashscope.console.aliyun.com/</a>
            </div>
            
            <div class="form-group">
                <label>API 类型</label>
                <select id="apiType">
                    <option value="qwen">阿里 Qwen-VL（推荐）</option>
                    <option value="gpt">OpenAI GPT-4V</option>
                    <option value="glm">智谱 GLM-4V</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>API Key</label>
                <input type="password" id="apiKey" placeholder="请输入 API Key">
            </div>
            
            <div class="upload-area" id="uploadArea">
                <div class="icon">📤</div>
                <p><strong>点击上传</strong> 或拖拽文件到此处</p>
                <p style="font-size: 12px; color: #999;">支持 JPG、PNG、PDF 格式</p>
                <input type="file" id="fileInput" multiple accept=".jpg,.jpeg,.png,.pdf">
            </div>
            
            <div class="file-list" id="fileList"></div>
            
            <div class="progress" id="progress">
                <div class="progress-bar">
                    <div class="progress-bar-fill" id="progressFill"></div>
                </div>
                <div class="progress-text" id="progressText">准备中...</div>
            </div>
            
            <div class="actions">
                <button class="btn" id="startBtn" onclick="startRecognition()">🚀 开始识别</button>
                <button class="btn btn-secondary" id="exportBtn" onclick="exportExcel()" style="display:none;">📊 导出 Excel</button>
                <button class="btn btn-secondary" onclick="clearAll()">🗑️ 清空</button>
            </div>
            
            <div class="results" id="results">
                <h3>📊 识别结果</h3>
                
                <div class="stats" id="stats"></div>
                
                <table>
                    <thead>
                        <tr>
                            <th>文件名</th>
                            <th>金额</th>
                            <th>日期</th>
                            <th>商家</th>
                            <th>状态</th>
                        </tr>
                    </thead>
                    <tbody id="resultBody"></tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        let files = [];
        let results = [];
        
        // 上传区域
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });
        
        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });
        
        function handleFiles(fileList) {
            for (let file of fileList) {
                if (!files.find(f => f.name === file.name)) {
                    files.push(file);
                }
            }
            renderFileList();
        }
        
        function renderFileList() {
            const list = document.getElementById('fileList');
            list.innerHTML = files.map((f, i) => `
                <div class="file-item">
                    <span class="name">📄 ${f.name}</span>
                    <span class="remove" onclick="removeFile(${i})">✕</span>
                </div>
            `).join('');
        }
        
        function removeFile(index) {
            files.splice(index, 1);
            renderFileList();
        }
        
        function clearAll() {
            files = [];
            results = [];
            renderFileList();
            document.getElementById('results').style.display = 'none';
            document.getElementById('exportBtn').style.display = 'none';
            document.getElementById('progress').style.display = 'none';
        }
        
        async function startRecognition() {
            if (files.length === 0) {
                alert('请先选择文件');
                return;
            }
            
            const apiKey = document.getElementById('apiKey').value;
            if (!apiKey) {
                alert('请填写 API Key');
                return;
            }
            
            const apiType = document.getElementById('apiType').value;
            
            // 显示进度
            document.getElementById('progress').style.display = 'block';
            document.getElementById('startBtn').disabled = true;
            results = [];
            
            // 上传并识别
            const formData = new FormData();
            formData.append('api_type', apiType);
            formData.append('api_key', apiKey);
            
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }
            
            try {
                const response = await fetch('/recognize', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    results = data.results;
                    renderResults();
                } else {
                    alert('识别失败：' + data.error);
                }
            } catch (error) {
                alert('请求失败：' + error.message);
            }
            
            document.getElementById('progress').style.display = 'none';
            document.getElementById('startBtn').disabled = false;
        }
        
        function renderResults() {
            const resultsDiv = document.getElementById('results');
            const tbody = document.getElementById('resultBody');
            const statsDiv = document.getElementById('stats');
            
            // 渲染表格
            tbody.innerHTML = results.map(r => `
                <tr>
                    <td>${r.filename}</td>
                    <td>${r.amount ? '¥' + r.amount : ''}</td>
                    <td>${r.date || ''}</td>
                    <td>${r.merchant || ''}</td>
                    <td>${r.status || '✅'}</td>
                </tr>
            `).join('');
            
            // 统计
            const total = results.length;
            const validAmount = results.filter(r => r.amount).length;
            const totalAmount = results.reduce((sum, r) => {
                const amount = parseFloat(r.amount) || 0;
                return sum + amount;
            }, 0);
            
            statsDiv.innerHTML = `
                <div class="stat-card">
                    <div class="value">${total}</div>
                    <div class="label">总张数</div>
                </div>
                <div class="stat-card">
                    <div class="value">${validAmount}</div>
                    <div class="label">有效金额</div>
                </div>
                <div class="stat-card">
                    <div class="value">¥${totalAmount.toFixed(2)}</div>
                    <div class="label">总金额</div>
                </div>
            `;
            
            resultsDiv.style.display = 'block';
            document.getElementById('exportBtn').style.display = 'inline-block';
        }
        
        async function exportExcel() {
            try {
                const response = await fetch('/export', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({results})
                });
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `发票统计_${new Date().getTime()}.xlsx`;
                a.click();
                window.URL.revokeObjectURL(url);
            } catch (error) {
                alert('导出失败：' + error.message);
            }
        }
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/recognize', methods=['POST'])
def recognize():
    api_type = request.form.get('api_type', 'qwen')
    api_key = request.form.get('api_key', '')
    uploaded_files = request.files.getlist('files')
    
    if not api_key:
        return jsonify({'success': False, 'error': '缺少 API Key'})
    
    results = []
    total = len(uploaded_files)
    
    for i, file in enumerate(uploaded_files):
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                result = recognize_invoice(filepath, api_type, api_key)
                result['filename'] = filename
                result['status'] = '✅' if result.get('amount') else '⚠️'
                results.append(result)
            except Exception as e:
                results.append({
                    'filename': filename,
                    'amount': '',
                    'date': '',
                    'merchant': '',
                    'status': f'❌ {str(e)}'
                })
    
    return jsonify({'success': True, 'results': results})


@app.route('/export', methods=['POST'])
def export():
    data = request.json
    results = data.get('results', [])
    
    df = pd.DataFrame(results)
    
    # 计算统计
    total_amount = 0
    valid_amounts = []
    for r in results:
        if r.get('amount'):
            try:
                amount = float(str(r['amount']).replace('¥', '').replace(',', ''))
                valid_amounts.append(amount)
            except:
                pass
    total_amount = sum(valid_amounts)
    
    # 创建 Excel
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='发票明细', index=False)
        
        # 统计 sheet
        summary_data = {
            '项目': ['总张数', '有效金额张数', '总金额'],
            '值': [len(results), len(valid_amounts), f'¥{total_amount:.2f}']
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='统计汇总', index=False)
    
    return send_file(output_path, as_attachment=True)


if __name__ == '__main__':
    print("=" * 50)
    print("📁 发票统计工具 - 网页版")
    print("=" * 50)
    print()
    print("🌐 访问地址：http://localhost:5000")
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
