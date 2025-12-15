import os

WORKSPACE_DIR = os.path.join(os.getcwd(), "workspace")


def save_to_workspace(filename: str, content: str):
    """将代码保存到 workspace 目录"""
    os.makedirs(WORKSPACE_DIR, exist_ok=True)

    file_path = os.path.join(WORKSPACE_DIR, filename)
    # 强制使用 UTF-8 和 Linux 换行符，防止 Docker 里的编译器报错
    with open(file_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    return file_path


def read_from_workspace(filename: str) -> str:
    """读取 workspace 中的文件"""
    file_path = os.path.join(WORKSPACE_DIR, filename)
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()