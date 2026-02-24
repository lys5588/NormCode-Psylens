"""
加载参考内容.py

从文件路径加载内容参考或样式参考的实际内容。
使用 body.file_system 进行文件操作（当可用时）。

输入：
- input_1: 元数据对象 {name, path, type, [for]}
- input_2: 输入目录（基础目录）

输出：
- 包含实际内容的对象 {name, path, type, [for], content, loaded}
"""

import os
import json


def load_with_body(full_path, body):
    """
    使用 body.file_system 加载文件内容
    
    Args:
        full_path: 完整的相对路径（base_dir/relative_path）
        body: Agent body with file_system
    
    Returns:
        (content, error) tuple
    """
    try:
        read_result = body.file_system.read(full_path)
        
        if read_result.get('status') == 'success':
            content = read_result.get('content', '')
            
            # 如果内容已经是 dict/list，转为 JSON 字符串或直接返回
            if isinstance(content, (dict, list)):
                return content, None
            
            # 如果是字符串，检查是否是 JSON
            if isinstance(content, str):
                if full_path.endswith('.json'):
                    try:
                        return json.loads(content), None
                    except json.JSONDecodeError:
                        pass
                return content, None
            
            return content, None
        else:
            error_msg = read_result.get('message', '读取失败')
            return None, f"文件读取失败: {error_msg} (路径: {full_path})"
    except Exception as e:
        return None, f"加载异常: {str(e)} (路径: {full_path})"


def load_direct(full_path):
    """
    直接从文件系统加载（fallback 方法）
    
    Args:
        full_path: 完整文件路径
    
    Returns:
        (content, error) tuple
    """
    try:
        if os.path.exists(full_path):
            if full_path.endswith('.json'):
                with open(full_path, 'r', encoding='utf-8') as f:
                    return json.load(f), None
            else:
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read(), None
        else:
            return None, f"文件不存在: {full_path}"
    except Exception as e:
        return None, f"读取失败: {str(e)}"


def main(input_1, input_2, body=None, **kwargs):
    """
    加载参考内容
    
    Args:
        input_1: 元数据对象，包含 name, path, type 等字段
        input_2: 输入目录（基础目录）
        body: Agent body with file_system（用于路径解析）
    
    Returns:
        dict: 包含实际内容的对象
    """
    metadata = input_1
    base_dir = input_2
    
    # 构造完整路径
    relative_path = metadata.get('path', '')
    full_path = os.path.join(base_dir, relative_path)
    
    # 使用 body.file_system 或直接加载
    if body and hasattr(body, 'file_system'):
        content, error = load_with_body(full_path, body)
    else:
        content, error = load_direct(full_path)
    
    # 构造输出对象
    result = {
        'name': metadata.get('name', ''),
        'path': relative_path,
        'type': metadata.get('type', ''),
        'content': content if error is None else f"[错误: {error}]"
    }
    
    # 保留原有的额外字段（如 'for'）
    if 'for' in metadata:
        result['for'] = metadata['for']
    
    # 添加加载状态
    result['loaded'] = error is None
    if error:
        result['error'] = error
    
    return result


if __name__ == "__main__":
    # 测试用例
    test_metadata = {
        "name": "测试内容",
        "path": "内容/公司介绍.md",
        "type": "company_info"
    }
    test_base_dir = "provisions/inputs"
    
    result = main(test_metadata, test_base_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
