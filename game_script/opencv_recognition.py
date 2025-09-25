"""
OpenCV + PyAutoGUI 图像识别示例
功能：模板匹配、颜色检测、形状识别、OCR文字识别
"""
import cv2
import numpy as np
import pyautogui
import time
import os
from pathlib import Path

# 创建必要的文件夹
def create_directories():
    """创建必要的文件夹"""
    directories = ['game_script/screenshots', 'game_script/templates', 'game_script/results']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def take_screenshot(region=None, save_path=None):
    """截取屏幕截图"""
    if region:
        screenshot = pyautogui.screenshot(region=region)
    else:
        screenshot = pyautogui.screenshot()

    if save_path:
        screenshot.save(save_path)

    # 转换为OpenCV格式 (BGR)
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    return screenshot_cv


def color_detection(target_color_bgr, tolerance=30):
    """颜色检测 - 查找指定颜色的区域"""
    print("=== 颜色检测示例 ===")

    # 截取屏幕
    screenshot = take_screenshot()

    # 定义颜色范围
    lower_bound = np.array([max(0, c - tolerance) for c in target_color_bgr])
    upper_bound = np.array([min(255, c + tolerance) for c in target_color_bgr])

    # 创建掩码
    mask = cv2.inRange(screenshot, lower_bound, upper_bound)

    # 查找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    color_regions = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 100:  # 过滤太小的区域
            x, y, w, h = cv2.boundingRect(contour)
            color_regions.append({
                'x': x, 'y': y, 'width': w, 'height': h,
                'area': area, 'center': (x + w//2, y + h//2)
            })

            # 在原图上标记
            cv2.rectangle(screenshot, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(screenshot, f"Area: {int(area)}",
                      (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

    print(f"找到 {len(color_regions)} 个颜色区域")

    # 保存结果
    cv2.imwrite('game_script/results/color_detection_result.png', screenshot)
    cv2.imwrite('game_script/results/color_mask.png', mask)

    return color_regions


def monitor_screen_changes(region=None, threshold=0.1, duration=10):
    """监控屏幕变化"""
    print(f"=== 监控屏幕变化 (持续{duration}秒) ===")

    # 获取初始截图
    prev_screenshot = take_screenshot(region)
    prev_gray = cv2.cvtColor(prev_screenshot, cv2.COLOR_BGR2GRAY)

    start_time = time.time()
    change_count = 0

    while time.time() - start_time < duration:
        # 获取当前截图
        current_screenshot = take_screenshot(region)
        current_gray = cv2.cvtColor(current_screenshot, cv2.COLOR_BGR2GRAY)

        # 计算差异
        diff = cv2.absdiff(prev_gray, current_gray)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

        # 计算变化百分比
        change_pixels = np.sum(thresh == 255)
        total_pixels = thresh.shape[0] * thresh.shape[1]
        change_percentage = change_pixels / total_pixels

        if change_percentage > threshold:
            change_count += 1
            print(f"检测到屏幕变化: {change_percentage:.2%}")

            # 保存变化的截图
            cv2.imwrite(f'game_script/results/change_{change_count}.png', current_screenshot)
            cv2.imwrite(f'game_script/results/diff_{change_count}.png', diff)

        prev_gray = current_gray
        time.sleep(0.5)  # 检查间隔

    print(f"监控完成，共检测到 {change_count} 次变化")


def game_ui_detection():
    """游戏UI元素检测示例"""
    print("=== 游戏UI检测示例 ===")

    # 截取屏幕
    screenshot = take_screenshot()

    # 转换为HSV颜色空间，更容易检测特定颜色
    hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)

    # 检测红色UI元素（如血条）
    red_lower1 = np.array([0, 50, 50])
    red_upper1 = np.array([10, 255, 255])
    red_lower2 = np.array([170, 50, 50])
    red_upper2 = np.array([180, 255, 255])

    red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
    red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)

    # 检测蓝色UI元素（如魔法条）
    blue_lower = np.array([100, 50, 50])
    blue_upper = np.array([130, 255, 255])
    blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)

    # 检测绿色UI元素（如经验条）
    green_lower = np.array([40, 50, 50])
    green_upper = np.array([80, 255, 255])
    green_mask = cv2.inRange(hsv, green_lower, green_upper)

    # 分析每种颜色的区域
    ui_elements = {}

    for color_name, mask in [('red', red_mask), ('blue', blue_mask), ('green', green_mask)]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        elements = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 200:  # 过滤小区域
                x, y, w, h = cv2.boundingRect(contour)
                elements.append({
                    'x': x, 'y': y, 'width': w, 'height': h,
                    'area': area, 'aspect_ratio': w/h
                })

        ui_elements[color_name] = elements
        print(f"检测到 {len(elements)} 个{color_name}色UI元素")

    # 在原图上标记检测到的UI元素
    colors = {'red': (0, 0, 255), 'blue': (255, 0, 0), 'green': (0, 255, 0)}
    for color_name, elements in ui_elements.items():
        for element in elements:
            cv2.rectangle(screenshot,
                        (element['x'], element['y']),
                        (element['x'] + element['width'], element['y'] + element['height']),
                        colors[color_name], 2)
            cv2.putText(screenshot, color_name,
                      (element['x'], element['y'] - 10),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[color_name], 1)

    # 保存结果
    cv2.imwrite('game_script/results/ui_detection_result.png', screenshot)

    return ui_elements


def template_matching(template_path, threshold=0.8):
    """模板匹配 - 在屏幕上查找指定图像"""
    print(f"=== 模板匹配示例 ===")

    # 读取模板图像
    if not os.path.exists(template_path):
        print(f"模板文件不存在: {template_path}")
        return None

    template = cv2.imread(template_path)
    if template is None:
        print("无法加载模板图像")
        return None

    # 截取当前屏幕
    screenshot = take_screenshot()

    # 进行模板匹配
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)

    matches = []
    for pt in zip(*locations[::-1]):  # 转换坐标
        matches.append({
            'x': pt[0],
            'y': pt[1],
            'width': template.shape[1],
            'height': template.shape[0],
            'confidence': result[pt[1], pt[0]]
        })

    print(f"找到 {len(matches)} 个匹配项")

    # 在截图上标记找到的位置
    if matches:
        for match in matches:
            cv2.rectangle(screenshot,
                        (match['x'], match['y']),
                        (match['x'] + match['width'], match['y'] + match['height']),
                        (0, 255, 0), 2)

            # 添加置信度文本
            cv2.putText(screenshot, f"{match['confidence']:.2f}",
                      (match['x'], match['y'] - 10),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # 保存结果
        cv2.imwrite('game_script/results/template_match_result.png', screenshot)
        print("匹配结果已保存到 game_script/results/template_match_result.png")

    return matches


def find_and_click(template_path, threshold=0.8, click_offset=(0, 0)):
    """查找图像并点击"""
    print("=== 查找并点击示例 ===")

    matches = template_matching(template_path, threshold)
    if matches:
        # 点击第一个匹配项的中心
        best_match = max(matches, key=lambda x: x['confidence'])
        click_x = best_match['x'] + best_match['width'] // 2 + click_offset[0]
        click_y = best_match['y'] + best_match['height'] // 2 + click_offset[1]

        print(f"点击位置: ({click_x}, {click_y}), 置信度: {best_match['confidence']:.2f}")
        pyautogui.click(click_x, click_y)
        return True
    else:
        print("未找到目标图像")
        return False


class ImageRecognition:
    def __init__(self):
        create_directories()
        # 禁用PyAutoGUI的暂停，提高性能
        pyautogui.PAUSE = 0


def create_sample_template():
    """创建一个示例模板图像用于测试"""
    # 创建一个简单的按钮模板
    template = np.zeros((50, 100, 3), dtype=np.uint8)
    cv2.rectangle(template, (5, 5), (95, 45), (100, 100, 100), -1)  # 灰色背景
    cv2.rectangle(template, (5, 5), (95, 45), (255, 255, 255), 2)   # 白色边框
    cv2.putText(template, "Button", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    
    cv2.imwrite('game_script/templates/sample_button.png', template)
    print("已创建示例模板: game_script/templates/sample_button.png")

if __name__ == "__main__":
    print("OpenCV 图像识别示例")
    
    # 创建示例模板
    create_sample_template()
    
    # 初始化图像识别器
    recognizer = ImageRecognition()
    
    try:
        print("\n选择要执行的功能:")
        print("1. 模板匹配")
        print("2. 颜色检测")
        print("3. 查找并点击")
        print("4. 监控屏幕变化")
        print("5. 游戏UI检测")
        print("6. 执行所有示例")
        
        choice = input("请选择 (1-6): ")
        
        if choice == '1':
            template_matching('game_script/templates/sample_button.png')
            
        elif choice == '2':
            # 检测红色区域 (BGR格式)
            red_color = [0, 0, 255]
            color_detection(red_color)
            
        elif choice == '3':
            find_and_click('game_script/templates/sample_button.png')
            
        elif choice == '4':
            print("开始监控屏幕变化...")
            monitor_screen_changes(duration=10)
            
        elif choice == '5':
            game_ui_detection()
            
        elif choice == '6':
            print("执行所有示例...")
            template_matching('game_script/templates/sample_button.png')
            color_detection([0, 0, 255])  # 红色
            game_ui_detection()
            
        print("\n所有结果已保存到 game_script/results/ 文件夹")
        
    except KeyboardInterrupt:
        print("用户中断程序")
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
