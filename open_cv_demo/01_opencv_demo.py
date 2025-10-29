import cv2
import os
import numpy as np
import math


def read_image_info(image_path):
    """读取图片信息"""
    # 读取图片
    image = cv2.imread(image_path)

    # 检查图像是否成功加载
    if image is None:
        raise FileNotFoundError(f"无法加载图片: {image_path}")

    # 获取图片信息
    height, width, channels = image.shape

    # --- 添加居中水印 ---
    water_mark_text = 'OpenCV Demo 01'
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 2  # 字体大小
    font_thickness = 3  # 字体粗细
    text_color = (62, 62, 187)  # BGR 颜色

    # 获取文本的尺寸 (宽度, 高度), baseline
    (text_width, text_height), baseline = cv2.getTextSize(water_mark_text, font, font_scale, font_thickness)

    # 计算文本的起始坐标 (左下角) 以使其居中
    text_x = (width - text_width) // 2
    text_y = (height + text_height) // 2

    # 在图片上绘制文本
    # cv2.putText(image, water_mark_text, (text_x, text_y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)
    add_rotated_watermark(image, water_mark_text, 45, font_scale, text_color, font_thickness)
    # --- 水印结束 ---

    # 创建一个文件夹存储添加水印之后的文件
    output_dir = 'watermark_output'
    if not os.path.exists(output_dir):
        print(f"文件夹 {output_dir} 不存在，本次进行创建")
        os.makedirs(output_dir, exist_ok=True)

    # 保存图片
    output_path = os.path.join(output_dir, os.path.basename(image_path))
    cv2.imwrite(output_path, image)

    # 显示图像
    cv2.imshow('Image with Watermark', image)
    # 等待按键事件
    cv2.waitKey(0)
    # 在颠倒一下图片展示
    flipped_image = cv2.flip(image, 0)  # 0表示垂直翻转
    cv2.imshow('Flipped Image', flipped_image)
    cv2.waitKey(0)
    # 关闭所有窗口
    cv2.destroyAllWindows()

    return {
        "路径": image_path,
        "高度": height,
        "宽度": width,
        "通道数": channels
    }


def remove_watermark(image_path):
    """
    使用 OpenCV 的图像修复功能去除图片左下角的水印。
    """
    # 读取图片
    image = cv2.imread(image_path)
    if image is None:
        print(f"无法加载图片: {image_path}")
        return

    # --- 1. 定义水印所在的区域 (Region of Interest, ROI) ---
    # !!! 这是你需要根据你的图片手动调整的关键参数 !!!
    # (x, y) 是矩形左上角的坐标
    # w, h 是矩形的宽度和高度
    # 假设水印在左下角，距离左边 10 像素，距离底部 50 像素
    # 并且水印本身的尺寸是 300x40 像素
    x = 10
    h = 40
    y = image.shape[0] - h - 10  # image.shape[0] 是图片总高度
    w = 300

    # --- 2. 创建掩码 (Mask) ---
    # 创建一个和原图一样大小的纯黑图片
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    # 在水印区域画一个纯白色的矩形
    mask[y:y + h, x:x + w] = 255

    # --- 3. 执行图像修复 ---
    # cv2.inpaint(源图片, 掩码, 修复算法的邻域半径, 修复算法)
    # INPAINT_TELEA 是一种效果比较好的算法
    inpainted_image = cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)

    # --- 显示结果 ---
    cv2.imshow("Original Image", image)
    cv2.imshow("Mask", mask)  # 显示掩码，方便调试
    cv2.imshow("Inpainted Result", inpainted_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # 你也可以选择保存修复后的图片
    # cv2.imwrite("result.jpg", inpainted_image)


def add_rotated_watermark(image, text, angle, font_scale, color, thickness):
    """
    在图片中心添加一个旋转指定角度的文字水印（已修复长文本裁切问题）。

    :param image: 原始图片 (OpenCV Mat)
    :param text: 水印文字
    :param angle: 旋转角度
    :param font_scale: 字体大小
    :param color: 字体颜色 (B, G, R)
    :param thickness: 字体粗细
    :return: 添加了水印的图片
    """
    # 1. 获取原始水平文本的尺寸
    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)

    # 2. 计算能容纳旋转后文本的画布尺寸（关键改动）
    # 创建一个边长等于文本对角线长度的正方形画布，确保旋转后内容不会被裁切
    diagonal = math.sqrt(text_w ** 2 + text_h ** 2)
    canvas_size = int(diagonal) + 2  # 加一点余量

    # 创建一个4通道的透明正方形画布 (BGRA)
    watermark_canvas = np.zeros((canvas_size, canvas_size, 4), dtype=np.uint8)

    # 3. 在这个大画布的中心绘制水平文字
    text_x = (canvas_size - text_w) // 2
    text_y = (canvas_size + text_h) // 2
    cv2.putText(watermark_canvas, text, (text_x, text_y), font, font_scale, (*color, 255), thickness, cv2.LINE_AA)

    # 4. 旋转整个画布
    center = (canvas_size // 2, canvas_size // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated_watermark = cv2.warpAffine(watermark_canvas, rotation_matrix, (canvas_size, canvas_size))

    # 5. 将旋转后的水印合并到原始图片中心
    img_h, img_w, _ = image.shape
    center_x, center_y = img_w // 2, img_h // 2

    # 计算水印在原图上的起始位置
    start_x = max(center_x - canvas_size // 2, 0)
    start_y = max(center_y - canvas_size // 2, 0)

    # 确保水印不会超出图片边界
    end_x = min(start_x + canvas_size, img_w)
    end_y = min(start_y + canvas_size, img_h)

    roi = image[start_y:end_y, start_x:end_x]

    # 提取旋转后水印的 BGR 通道和 Alpha 通道
    # 注意：这里的切片尺寸需要和 roi 的尺寸完全对应
    watermark_bgr = rotated_watermark[0:(end_y - start_y), 0:(end_x - start_x), :3]
    alpha = rotated_watermark[0:(end_y - start_y), 0:(end_x - start_x), 3] / 255.0
    alpha = np.expand_dims(alpha, axis=2)

    # Alpha 融合
    blended_roi = (watermark_bgr * alpha + roi * (1 - alpha)).astype(np.uint8)

    # 将融合后的区域放回原图
    image[start_y:end_y, start_x:end_x] = blended_roi

    return image


def main():
    """主函数"""
    # 获取当前脚本的绝对路径
    current_script_path = os.path.abspath(__file__)
    # 获取当前脚本所在的目录
    current_script_dir = os.path.dirname(current_script_path)

    # 构建图片目录的绝对路径
    # 假设图片目录 'image' 和脚本文件 '01_opencv_demo.py' 在同一个父目录下
    image_directory = os.path.join(current_script_dir, 'image')

    print(f"图片目录路径: {image_directory}")

    # 检查目录是否存在
    if os.path.exists(image_directory) and os.path.isdir(image_directory):
        # 列出图片目录中的所有文件
        for filename in os.listdir(image_directory):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                image_path = os.path.join(image_directory, filename)
                print(f"找到图片文件: {image_path}")
                try:
                    # 读取图片信息
                    info = read_image_info(image_path)
                    # 打印图片信息
                    print(info)
                except FileNotFoundError as e:
                    print(e)
    else:
        print(f"错误: 图片目录 '{image_directory}' 不存在或不是一个目录。")


if __name__ == '__main__':
    main()
