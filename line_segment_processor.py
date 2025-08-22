"""
线段检测后处理模块
用于对PNG图像进行二值化处理并检测、过滤线段
"""

import cv2
import numpy as np
import os
from PIL import Image


def process_image_for_lines(input_image_path, threshold_value, min_pixel_length=20, output_folder_path="."):
    """
    处理图像中的线段检测和过滤
    
    参数:
    input_image_path: PNG图片文件的输入路径
    threshold_value: 二值化阈值，范围为0到1之间的浮点数（例如0.35）
    min_pixel_length: 要保留的线段的最短像素长度，默认值为20
    output_folder_path: 保存输出图片的文件夹路径
    
    返回:
    output_image_path: 处理后图片（包含检测到的线段）的保存路径
    """
    
    # 1. 加载和预处理图像
    print(f"正在加载图像: {input_image_path}")
    
    # 使用PIL加载图像，避免OpenCV的中文路径问题
    try:
        pil_image = Image.open(input_image_path)
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        image = np.array(pil_image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # 转换为BGR格式供OpenCV使用
    except Exception as e:
        print(f"PIL加载失败，尝试使用OpenCV: {e}")
        image = cv2.imread(input_image_path)
        
    if image is None:
        raise ValueError(f"无法加载图像文件: {input_image_path}")
    
    print(f"图像尺寸: {image.shape[0]}x{image.shape[1]}")

    # 2. 二值化处理
    # 转换为灰度图像
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 将0-1的阈值转换为0-255
    scaled_threshold = int(threshold_value * 255)
    print(f"二值化阈值: {threshold_value} (对应灰度值: {scaled_threshold})")
    
    # 进行二值化处理
    _, binary_image = cv2.threshold(gray_image, scaled_threshold, 255, cv2.THRESH_BINARY)

    # 3. 线段检测
    print("正在进行线段检测...")
    
    # 创建LineSegmentDetector对象
    lsd = cv2.createLineSegmentDetector()
    
    # 检测线段
    lines = lsd.detect(binary_image)[0]  # 获取线段数组
    
    detected_lines = []
    if lines is not None and len(lines) > 0:
        for line in lines:
            # line 的形状是 (1, 4)，需要取 line[0] 来获取 [x1, y1, x2, y2]
            line_coords = line[0]  # 获取实际的坐标数组
            x1, y1, x2, y2 = line_coords[0], line_coords[1], line_coords[2], line_coords[3]
            detected_lines.append(((int(x1), int(y1)), (int(x2), int(y2))))
    
    print(f"检测到 {len(detected_lines)} 条线段")

    # 4. 线段过滤
    print(f"正在过滤长度小于 {min_pixel_length} 像素的线段...")
    filtered_lines = []
    
    for line in detected_lines:
        (x1, y1), (x2, y2) = line
        # 计算线段长度
        length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if length >= min_pixel_length:
            filtered_lines.append(line)
    
    print(f"过滤后保留 {len(filtered_lines)} 条线段")

    # 5. 绘制线段并保存结果
    # 在原始图像上绘制线段
    output_image = image.copy()
    
    for line in filtered_lines:
        (x1, y1), (x2, y2) = line
        # 绘制红色线段，线宽为2
        cv2.line(output_image, (x1, y1), (x2, y2), (0, 0, 255), 2, cv2.LINE_AA)

    # 确保输出目录存在
    os.makedirs(output_folder_path, exist_ok=True)
    
    # 生成输出文件名
    input_filename = os.path.basename(input_image_path)
    output_filename = input_filename.replace(".png", "_lines_detected.png")
    output_image_path = os.path.join(output_folder_path, output_filename)
    
    # 使用PIL保存图像，避免OpenCV的中文路径问题
    try:
        output_image_rgb = cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB)
        pil_output_image = Image.fromarray(output_image_rgb)
        pil_output_image.save(output_image_path)
        print(f"处理完成，结果保存到: {output_image_path}")
        return output_image_path
    except Exception as e:
        raise RuntimeError(f"保存图像失败: {output_image_path}") from e


if __name__ == "__main__":
    # 测试代码
    test_input = "test_image.png"  # 替换为实际的测试图像路径
    test_threshold = 0.35
    test_min_length = 20
    test_output = "output"
    
    if os.path.exists(test_input):
        result = process_image_for_lines(test_input, test_threshold, test_min_length, test_output)
        print(f"测试完成，输出文件: {result}")
    else:
        print(f"测试图像文件不存在: {test_input}")
        print("请修改test_input变量为实际的图像文件路径进行测试")