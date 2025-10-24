"""
文件压缩和下载功能模块
"""
import os
import zipfile
from datetime import datetime

zips_path = "D:\\pyCharmProject\\AutoViewScript\\zip"


class FileManager:

    def __init__(self, desktop_path=None):
        """
        初始化文件管理器

        Args:
            desktop_path: 桌面路径，如果为None则自动检测
        """
        if desktop_path is None:
            self.desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        else:
            self.desktop_path = desktop_path

        # 文件夹路径
        self.contents_folder = os.path.join(self.desktop_path, "contents")
        self.comments_folder = os.path.join(self.desktop_path, "comments")

        # 确保工作目录是当前脚本所在目录
        self.working_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(self.working_dir)

    def compress_folder(self, folder_name):
        """
        压缩指定文件夹

        Args:
            folder_name: 文件夹名称 ('contents' 或 'comments')

        Returns:
            tuple: (success, message, zip_path)
        """
        if folder_name == "contents":
            folder_path = self.contents_folder
            zip_name = "contents.zip"
        elif folder_name == "comments":
            folder_path = self.comments_folder
            zip_name = "comments.zip"
        else:
            return False, f"不支持的文件夹: {folder_name}", None

        zip_path = os.path.join(zips_path, zip_name)

        try:
            if not os.path.exists(folder_path):
                return False, f"文件夹不存在: {folder_path}", None

            print(f"开始压缩文件夹: {folder_path} -> {zip_path}")

            # 创建zip文件
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                file_count = 0
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 在zip文件中保持相对路径
                        arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                        zipf.write(file_path, arcname)
                        file_count += 1

            file_size = os.path.getsize(zip_path)
            message = f"成功压缩: {zip_name} ({file_count}个文件, {self._format_file_size(file_size)})"
            print(message)
            return True, message, zip_path

        except Exception as e:
            error_msg = f"压缩失败: {str(e)}"
            print(error_msg)
            return False, error_msg, None

    def get_available_files(self):
        """
        获取可下载的文件列表

        Returns:
            list: 文件信息列表
        """
        files = []
        zip_files = ["contents.zip", "comments.zip"]

        for zip_file in zip_files:
            zip_path = os.path.join(zips_path, zip_file)
            if os.path.exists(zip_path):
                file_size = os.path.getsize(zip_path)
                files.append({
                    "name": zip_file,
                    "path": zip_path,
                    "size": file_size,
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "formatted_size": self._format_file_size(file_size),
                    "created_time": datetime.fromtimestamp(os.path.getctime(zip_path)).strftime('%Y-%m-%d %H:%M:%S')
                })

        return files

    def cleanup_old_files(self, days=7):
        """
        清理旧的压缩文件

        Args:
            days: 保留最近多少天的文件

        Returns:
            tuple: (deleted_count, message)
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            deleted_count = 0

            for file_info in self.get_available_files():
                file_path = file_info["path"]
                if os.path.getctime(file_path) < cutoff_time:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"已删除旧文件: {file_info['name']}")

            return deleted_count, f"清理了 {deleted_count} 个旧文件"

        except Exception as e:
            return 0, f"清理文件时出错: {str(e)}"

    def _format_file_size(self, size_bytes):
        """格式化文件大小显示"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


# 全局实例
file_manager = FileManager()


# 便捷函数
def compress_contents():
    """压缩contents文件夹"""
    return file_manager.compress_folder("contents")


def compress_comments():
    """压缩comments文件夹"""
    return file_manager.compress_folder("comments")


def get_downloadable_files():
    """获取可下载文件列表"""
    return file_manager.get_available_files()


def cleanup_files(days=7):
    """清理旧文件"""
    return file_manager.cleanup_old_files(days)
