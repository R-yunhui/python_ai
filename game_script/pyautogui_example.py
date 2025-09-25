"""
PyAutoGUI 示例 - 最推荐的鼠标键盘操作库
功能：鼠标控制、键盘输入、屏幕截图、图像识别
"""
import pyautogui
import time
import uuid

# 安全设置：移动鼠标到屏幕左上角可以中断程序
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1  # 每个操作之间的暂停时间

def mouse_operations():
    """鼠标操作示例"""
    print("=== 鼠标操作示例 ===")
    
    # 获取屏幕尺寸
    screen_width, screen_height = pyautogui.size()
    print(f"屏幕尺寸: {screen_width} x {screen_height}")
    
    # 获取当前鼠标位置
    current_x, current_y = pyautogui.position()
    print(f"当前鼠标位置: ({current_x}, {current_y})")
    
    # 移动鼠标
    print("移动鼠标到屏幕中央...")
    pyautogui.moveTo(screen_width // 2, screen_height // 2, duration=1)
    
    # 相对移动
    print("相对移动鼠标...")
    pyautogui.move(100, 50, duration=0.5)
    
    # 点击操作
    print("执行点击操作...")
    pyautogui.click()  # 左键单击
    time.sleep(0.5)
    pyautogui.rightClick()  # 右键单击
    time.sleep(0.5)
    pyautogui.doubleClick()  # 双击
    
    # 拖拽操作
    print("执行拖拽操作...")
    pyautogui.drag(100, 100, duration=1)  # 拖拽到相对位置
    
    # 滚轮操作
    print("滚轮操作...")
    pyautogui.scroll(3)  # 向上滚动
    time.sleep(0.5)
    pyautogui.scroll(-3)  # 向下滚动

def keyboard_operations():
    """键盘操作示例"""
    print("\n=== 键盘操作示例 ===")
    
    # 等待用户准备
    print("5秒后开始键盘操作，请打开一个文本编辑器...")
    time.sleep(5)
    
    # 输入文本
    pyautogui.typewrite("Hello, 这是PyAutoGUI键盘测试!", interval=0.1)
    
    # 按键操作
    pyautogui.press('enter')  # 回车
    pyautogui.typewrite("新的一行")
    
    # 组合键
    pyautogui.hotkey('ctrl', 'a')  # 全选
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'c')  # 复制
    
    # 特殊按键
    pyautogui.press('end')  # End键
    pyautogui.press('enter')
    pyautogui.hotkey('ctrl', 'v')  # 粘贴

def screenshot_and_image_recognition():
    """截图和图像识别示例"""
    print("\n=== 截图和图像识别示例 ===")
    
    # 截取全屏
    screenshot = pyautogui.screenshot()
    # 使用 UUID 生成随机文件名
    random_filename = f"{uuid.uuid4()}.png"
    path = f"D:\\ryh\\personal\\python\\large-model\\game_script\\snapshot\\{random_filename}"
    screenshot.save(path)
    print("已保存全屏截图")
    
    # 截取指定区域
    region_screenshot = pyautogui.screenshot(region=(0, 0, 400, 300))
    region_screenshot.save(path)
    print("已保存区域截图")
    
    # 获取指定位置的像素颜色
    x, y = pyautogui.position()
    pixel_color = pyautogui.pixel(x, y)
    print(f"鼠标位置 ({x}, {y}) 的像素颜色: {pixel_color}")

def game_script_example():
    """游戏脚本示例"""
    print("\n=== 游戏脚本示例 ===")
    print("模拟游戏中的连续点击操作...")
    
    # 模拟连续点击（可用于游戏中的自动攻击等）
    click_positions = [
        (500, 300),
        (600, 300),
        (700, 300)
    ]
    
    for i in range(3):  # 执行3轮
        print(f"第 {i+1} 轮点击")
        for pos in click_positions:
            pyautogui.click(pos[0], pos[1])
            time.sleep(0.2)
        time.sleep(1)

if __name__ == "__main__":
    try:
        print("PyAutoGUI 鼠标键盘操作示例")
        print("注意: 移动鼠标到屏幕左上角可以紧急停止程序")
        
        # 执行各种示例
        # mouse_operations()
        
        # 键盘操作需要用户确认
        choice = input("\n是否执行键盘操作示例? (y/n): ")
        if choice.lower() == 'y':
            keyboard_operations()
        
        screenshot_and_image_recognition()
        
        # 游戏脚本示例需要用户确认
        choice = input("\n是否执行游戏脚本示例? (y/n): ")
        if choice.lower() == 'y':
            game_script_example()
            
    except pyautogui.FailSafeException:
        print("检测到鼠标移动到屏幕左上角，程序安全退出")
    except KeyboardInterrupt:
        print("用户中断程序")
    except Exception as e:
        print(f"发生错误: {e}")
