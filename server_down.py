"""
程序远程运行服务器
"""
import http.server
import json
import os
import socketserver
import subprocess
import threading
import shutil
from datetime import datetime

import down_zip

# 配置
PORT = 8000
SCRIPT_PATHS = {
    "contents": r"D:\AutoViewScript\contents.py",
    "comments": r"D:\AutoViewScript\comments.py"
}


class RemoteControlHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # 返回控制页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.get_control_page().encode('utf-8'))

        elif self.path.startswith('/run/'):
            # 执行脚本
            script_name = self.path.split('/')[-1]
            self.run_script(script_name)

        elif self.path.startswith('/download/'):
            # 下载文件
            file_name = self.path.split('/')[-1]
            self.download_file(file_name)

        elif self.path == '/status':
            # 返回状态信息
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = {
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "files": down_zip.get_downloadable_files()
            }
            self.wfile.write(json.dumps(status).encode('utf-8'))

        elif self.path == '/cleanup':
            # 清理旧文件
            self.cleanup_files()

        else:
            self.send_error(404)

    def download_file(self, file_name):
        """提供文件下载"""
        available_files = down_zip.get_downloadable_files()
        file_info = next((f for f in available_files if f["name"] == file_name), None)

        if not file_info:
            self.send_error(404, "File not found")
            return

        try:
            file_path = file_info["path"]
            file_size = file_info["size"]

            self.send_response(200)
            self.send_header('Content-type', 'application/zip')
            # UTF-8编码文件名
            encoded_filename = file_name.encode('utf-8').decode('latin-1')
            self.send_header('Content-Disposition', f'attachment; filename="{encoded_filename}"')
            self.send_header('Content-Length', str(file_size))
            self.end_headers()

            with open(file_path, 'rb') as f:
                # 分块传输大文件
                shutil.copyfileobj(f, self.wfile)

            print(f"文件 {file_name} 已下载")
        except Exception as e:
            self.send_error(500, f"下载失败: {str(e)}")

    def cleanup_files(self):
        """清理旧文件"""
        deleted_count, message = down_zip.cleanup_files()

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {
            "deleted_count": deleted_count,
            "message": message
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def get_control_page(self):
        available_files = down_zip.get_downloadable_files()
        files_html = ""

        if available_files:
            files_html = """
            <div class="download-section">
                <h2>📥 下载分析结果</h2>
            """
            for file_info in available_files:
                files_html += f"""
                <div class="file-item">
                    <button class="btn btn-download" onclick="downloadFile('{file_info['name']}')">
                        📦 下载 {file_info['name']} ({file_info['formatted_size']})
                    </button>
                    <div class="file-info">创建时间: {file_info['created_time']}</div>
                </div>
                """
            files_html += """
                <button class="btn btn-cleanup" onclick="cleanupFiles()">🗑️ 清理旧文件 (7天前)</button>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>数据分析远程控制</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; text-align: center; }}
                h2 {{ color: #555; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                .btn {{ display: block; width: 100%; padding: 15px; margin: 10px 0; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; transition: all 0.3s; }}
                .btn-run {{ background: #007cba; }}
                .btn-run:hover {{ background: #005a87; transform: translateY(-2px); }}
                .btn-comments {{ background: #28a745; }}
                .btn-comments:hover {{ background: #1e7e34; transform: translateY(-2px); }}
                .btn-download {{ background: #ff6b00; }}
                .btn-download:hover {{ background: #cc5500; transform: translateY(-2px); }}
                .btn-cleanup {{ background: #6c757d; }}
                .btn-cleanup:hover {{ background: #545b62; transform: translateY(-2px); }}
                .status {{ text-align: center; margin: 20px 0; padding: 15px; background: #e9ecef; border-radius: 5px; min-height: 60px; line-height: 1.5; }}
                .download-section {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
                .file-item {{ margin-bottom: 15px; }}
                .file-info {{ font-size: 12px; color: #666; margin-top: 5px; }}
                .success {{ color: #28a745; }}
                .error {{ color: #dc3545; }}
                .loading {{ color: #007cba; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 数据分析远程控制</h1>
                <div class="status" id="status">🟢 服务器运行中</div>
                
                <h2>🚀 运行分析脚本</h2>
                <button class="btn btn-run" onclick="runScript('contents')">📹 运行 Contents 分析</button>
                <button class="btn btn-run btn-comments" onclick="runScript('comments')">💬 运行 Comments 分析</button>

                {files_html}

                <script>
                    function runScript(scriptName) {{
                        const statusEl = document.getElementById('status');
                        statusEl.innerHTML = '⏳ 正在启动 ' + scriptName + ' 分析...<br>请等待分析完成，这可能需要几分钟';
                        statusEl.className = 'status loading';
                        
                        fetch('/run/' + scriptName)
                            .then(response => response.text())
                            .then(data => {{
                                statusEl.innerHTML = '✅ 执行完成: ' + data + '<br>页面将自动刷新显示下载按钮...';
                                statusEl.className = 'status success';
                                // 3秒后刷新页面显示下载按钮
                                setTimeout(() => location.reload(), 3000);
                            }})
                            .catch(error => {{
                                statusEl.innerHTML = '❌ 错误: ' + error;
                                statusEl.className = 'status error';
                            }});
                    }}

                    function downloadFile(fileName) {{
                        const statusEl = document.getElementById('status');
                        statusEl.innerHTML = '📥 正在下载 ' + fileName + '...';
                        statusEl.className = 'status loading';
                        
                        // 创建隐藏的下载链接
                        const link = document.createElement('a');
                        link.href = '/download/' + fileName;
                        link.download = fileName;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        
                        statusEl.innerHTML = '✅ 下载已开始: ' + fileName + '<br>请检查手机下载列表';
                        statusEl.className = 'status success';
                    }}
                    
                    // 清理旧文件（7天前）
                    function cleanupFiles() {{
                        const statusEl = document.getElementById('status');
                        statusEl.innerHTML = '🗑️ 正在清理旧文件...';
                        statusEl.className = 'status loading';
                        
                        fetch('/cleanup')
                            .then(response => response.json())
                            .then(data => {{
                                statusEl.innerHTML = '✅ ' + data.message + '<br>页面将自动刷新...';
                                statusEl.className = 'status success';
                                setTimeout(() => location.reload(), 2000);
                            }})
                            .catch(error => {{
                                statusEl.innerHTML = '❌ 清理失败: ' + error;
                                statusEl.className = 'status error';
                            }});
                    }}

                    // 定期检查服务器状态和文件列表
                    setInterval(() => {{
                        fetch('/status')
                            .then(response => response.json())
                            .then(data => {{
                                const statusEl = document.getElementById('status');
                                if (statusEl.innerHTML.includes('服务器运行正常') || statusEl.innerHTML.includes('服务器运行中')) {{
                                    statusEl.innerHTML = '🟢 服务器运行正常 - ' + new Date(data.timestamp).toLocaleString();
                                }}
                            }});
                    }}, 15000);
                </script>
            </div>
        </body>
        </html>
        """

    def run_script(self, script_name):
        if script_name in SCRIPT_PATHS:
            script_path = SCRIPT_PATHS[script_name]

            # 在新线程中运行脚本，避免阻塞HTTP请求
            def run_in_thread():
                try:
                    # 激活虚拟环境并运行脚本
                    venv_path = r"D:\pyCharmProject\AutoViewScript\.venv\Scripts"
                    python_exe = os.path.join(venv_path, "python.exe")

                    if os.path.exists(python_exe):
                        print(f"开始执行脚本: {script_name}")
                        result = subprocess.run(
                            [python_exe, script_path],
                            capture_output=True,
                            text=True,
                            cwd=os.path.dirname(script_path),
                            timeout=300  # 5分钟超时
                        )
                        print(f"脚本 {script_name} 执行完成")
                        print(f"输出: {result.stdout}")

                        # 脚本执行完成后压缩文件夹
                        if script_name == "contents":
                            success, message, zip_path = down_zip.compress_contents()
                        else:  # comments
                            success, message, zip_path = down_zip.compress_comments()

                        print(f"压缩结果: {message}")

                        if result.stderr:
                            print(f"错误: {result.stderr}")
                    else:
                        # 如果没有虚拟环境，使用系统Python
                        result = subprocess.run(
                            ["python", script_path],
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        print(f"脚本 {script_name} 执行完成")

                except subprocess.TimeoutExpired:
                    print(f"脚本 {script_name} 执行超时")
                except Exception as e:
                    print(f"执行脚本时出错: {e}")

            thread = threading.Thread(target=run_in_thread)
            thread.daemon = True
            thread.start()

            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"已启动 {script_name} 脚本，正在分析数据...".encode('utf-8'))
        else:
            self.send_error(404, "Script not found")


def get_local_ip():
    """获取本机IP地址"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("0.0.0.0", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


if __name__ == "__main__":
    # 确保工作目录正确
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    local_ip = get_local_ip()
    print(f"📡 远程控制服务器已启动!")
    print(f"📱 在手机浏览器中访问: http://{local_ip}:{PORT}")
    print(f"💻 或者访问: http://localhost:{PORT}")
    print("⏹️  按 Ctrl+C 停止服务器")

    # 显示初始文件状态
    files = down_zip.get_downloadable_files()
    print(f"📂 当前可下载文件: {len(files)} 个")
    for file in files:
        print(f"   - {file['name']} ({file['formatted_size']})")

    try:
        with socketserver.TCPServer(("", PORT), RemoteControlHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器错误: {e}")
