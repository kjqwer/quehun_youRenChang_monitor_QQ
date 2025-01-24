import win32gui
import win32con
import json
import os
import time

def get_window_titles():
    """获取所有可见窗口的标题"""
    titles = []
    def enum_windows_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:  # 只添加有标题的窗口
                titles.append(title)
    win32gui.EnumWindows(enum_windows_callback, None)
    return titles

def update_config(window_title):
    """更新配置文件"""
    config_file = 'config.py'
    
    # 读取现有配置
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新窗口标题
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "'window_title':" in line:
            lines[i] = f"    'window_title': '{window_title}',"
    
    # 写回配置文件
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def main():
    print("正在获取所有可见窗口...")
    titles = get_window_titles()
    
    # 显示所有窗口
    print("\n可用窗口:")
    for i, title in enumerate(titles, 1):
        print(f"{i}. {title}")
    
    while True:
        try:
            choice = input("\n请输入窗口编号（输入q退出）: ")
            if choice.lower() == 'q':
                return
            
            index = int(choice) - 1
            if 0 <= index < len(titles):
                selected_title = titles[index]
                print(f"\n已选择: {selected_title}")
                confirm = input("确认使用这个窗口吗？(y/n): ")
                if confirm.lower() == 'y':
                    update_config(selected_title)
                    print("\n配置已更新！")
                    break
            else:
                print("无效的编号，请重试")
        except ValueError:
            print("请输入有效的数字")

if __name__ == "__main__":
    main() 