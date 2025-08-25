"""
线段检测后处理模块
用于对PNG图像进行二值化处理并检测、过滤线段
"""

import cv2
import numpy as np
import os
import math
from PIL import Image


def calculate_line_angle(line):
    """计算线段的角度（弧度）"""
    (x1, y1), (x2, y2) = line
    return math.atan2(y2 - y1, x2 - x1)


def calculate_distance_to_line(point, line):
    """计算点到线段的最短距离"""
    (x1, y1), (x2, y2) = line
    px, py = point
    
    # 计算线段长度的平方
    line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
    
    if line_length_sq == 0:
        # 线段退化为点
        return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
    
    # 计算点在线段上的投影参数t
    t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq))
    
    # 计算投影点
    projection_x = x1 + t * (x2 - x1)
    projection_y = y1 + t * (y2 - y1)
    
    # 返回距离
    return math.sqrt((px - projection_x) ** 2 + (py - projection_y) ** 2)


def can_merge_lines(line1, line2, distance_threshold, angle_threshold_rad):
    """判断两条线段是否可以合并"""
    # 计算两条线段的角度
    angle1 = calculate_line_angle(line1)
    angle2 = calculate_line_angle(line2)
    
    # 计算角度差（考虑周期性）
    angle_diff = abs(angle1 - angle2)
    angle_diff = min(angle_diff, 2 * math.pi - angle_diff)
    
    # 如果角度差太大，不能合并
    if angle_diff > angle_threshold_rad:
        return False
    
    # 检查线段端点之间的距离
    (x1_1, y1_1), (x2_1, y2_1) = line1
    (x1_2, y1_2), (x2_2, y2_2) = line2
    
    # 计算所有端点组合之间的距离
    distances = [
        math.sqrt((x1_1 - x1_2) ** 2 + (y1_1 - y1_2) ** 2),  # line1起点到line2起点
        math.sqrt((x1_1 - x2_2) ** 2 + (y1_1 - y2_2) ** 2),  # line1起点到line2终点
        math.sqrt((x2_1 - x1_2) ** 2 + (y2_1 - y1_2) ** 2),  # line1终点到line2起点
        math.sqrt((x2_1 - x2_2) ** 2 + (y2_1 - y2_2) ** 2),  # line1终点到line2终点
    ]
    
    # 如果任何一个端点距离小于阈值，可以合并
    return min(distances) <= distance_threshold


def merge_two_lines(line1, line2):
    """合并两条线段，返回合并后的线段"""
    (x1_1, y1_1), (x2_1, y2_1) = line1
    (x1_2, y1_2), (x2_2, y2_2) = line2
    
    # 找到所有端点
    points = [(x1_1, y1_1), (x2_1, y2_1), (x1_2, y1_2), (x2_2, y2_2)]
    
    # 计算所有点对之间的距离，找到最远的两个点
    max_distance = 0
    best_pair = None
    
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            dist = math.sqrt((points[i][0] - points[j][0]) ** 2 + (points[i][1] - points[j][1]) ** 2)
            if dist > max_distance:
                max_distance = dist
                best_pair = (points[i], points[j])
    
    return best_pair


def merge_lines(detected_lines, distance_threshold, angle_threshold_rad):
    """合并相近的线段"""
    if not detected_lines:
        return detected_lines
    
    print(f"开始线段合并，距离阈值: {distance_threshold}像素, 角度阈值: {math.degrees(angle_threshold_rad):.1f}度")
    
    merged_lines = detected_lines.copy()
    merged = True
    
    while merged:
        merged = False
        new_merged_lines = []
        used = set()
        
        for i in range(len(merged_lines)):
            if i in used:
                continue
                
            current_line = merged_lines[i]
            found_merge = False
            
            for j in range(i + 1, len(merged_lines)):
                if j in used:
                    continue
                    
                if can_merge_lines(current_line, merged_lines[j], distance_threshold, angle_threshold_rad):
                    # 合并线段
                    merged_line = merge_two_lines(current_line, merged_lines[j])
                    new_merged_lines.append(merged_line)
                    used.add(i)
                    used.add(j)
                    found_merge = True
                    merged = True
                    break
            
            if not found_merge:
                new_merged_lines.append(current_line)
                used.add(i)
        
        merged_lines = new_merged_lines
    
    print(f"合并完成，从 {len(detected_lines)} 条线段合并为 {len(merged_lines)} 条线段")
    return merged_lines


def process_image_for_lines(input_image_path, threshold_value, min_pixel_length=20, output_folder_path=".", 
                           enable_merge=False, merge_distance_threshold=5, merge_angle_threshold=10):
    """
    处理图像中的线段检测和过滤
    
    参数:
    input_image_path: PNG图片文件的输入路径
    threshold_value: 二值化阈值，范围为0到1之间的浮点数（例如0.35）
    min_pixel_length: 要保留的线段的最短像素长度，默认值为20
    output_folder_path: 保存输出图片的文件夹路径
    enable_merge: 是否进行线段合并，默认False
    merge_distance_threshold: 线段合并的距离阈值，默认5像素
    merge_angle_threshold: 线段合并的角度阈值，默认10度
    
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

    # 4. 线段合并（如果启用）
    if enable_merge and detected_lines:
        angle_threshold_rad = math.radians(merge_angle_threshold)
        detected_lines = merge_lines(detected_lines, merge_distance_threshold, angle_threshold_rad)

    # 5. 线段过滤
    print(f"正在过滤长度小于 {min_pixel_length} 像素的线段...")
    filtered_lines = []
    
    for line in detected_lines:
        (x1, y1), (x2, y2) = line
        # 计算线段长度
        length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if length >= min_pixel_length:
            filtered_lines.append(line)
    
    print(f"过滤后保留 {len(filtered_lines)} 条线段")

    # 6. 绘制线段并保存结果
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