"""
线段检测测试脚本
演示如何使用line_segment_processor模块
"""

import os
import numpy as np
import cv2
from line_segment_processor import process_line_segments, batch_process_line_segments


def create_test_image(width=800, height=600, filename="test_lines.png"):
    """
    创建一个包含线段的测试图像
    """
    # 创建白色背景
    image = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # 绘制一些测试线段
    # 长线段（应该被保留）
    cv2.line(image, (100, 100), (300, 150), (0, 0, 0), 3)  # 黑色长线段
    cv2.line(image, (200, 200), (500, 250), (0, 0, 0), 2)  # 另一条长线段
    cv2.line(image, (400, 300), (600, 400), (0, 0, 0), 4)  # 粗长线段
    
    # 短线段（应该被过滤掉）
    cv2.line(image, (150, 300), (165, 310), (0, 0, 0), 2)  # 短线段
    cv2.line(image, (250, 400), (260, 405), (0, 0, 0), 2)  # 另一条短线段
    
    # 中等长度线段
    cv2.line(image, (300, 500), (350, 520), (0, 0, 0), 2)  # 中等线段
    
    # 添加一些噪声点
    for i in range(50):
        x, y = np.random.randint(0, width), np.random.randint(0, height)
        cv2.circle(image, (x, y), 1, (128, 128, 128), -1)
    
    # 保存图像
    cv2.imwrite(filename, image)
    print(f"测试图像已创建: {filename}")
    return filename


def test_single_file():
    """测试单文件处理"""
    print("\n" + "="*50)
    print("测试单文件处理")
    print("="*50)
    
    # 创建测试图像
    test_image = create_test_image()
    
    # 测试参数
    threshold = 0.5  # 二值化阈值
    min_length = 30  # 最小线段长度
    output_folder = "test_output"
    
    try:
        result = process_line_segments(
            input_image_path=test_image,
            threshold_value=threshold,
            min_pixel_length=min_length,
            output_folder_path=output_folder
        )
        
        print(f"✅ 单文件处理成功!")
        print(f"输出文件: {result}")
        
        # 清理测试文件
        if os.path.exists(test_image):
            os.remove(test_image)
            
    except Exception as e:
        print(f"❌ 单文件处理失败: {str(e)}")


def test_batch_processing():
    """测试批量处理"""
    print("\n" + "="*50)
    print("测试批量处理")
    print("="*50)
    
    # 创建测试文件夹和多个测试图像
    test_folder = "test_images"
    os.makedirs(test_folder, exist_ok=True)
    
    # 创建3个测试图像
    test_files = []
    for i in range(3):
        filename = os.path.join(test_folder, f"test_image_{i+1}.png")
        create_test_image(filename=filename)
        test_files.append(filename)
    
    # 测试参数
    threshold = 0.4
    min_length = 25
    output_folder = "batch_output"
    
    try:
        results = batch_process_line_segments(
            input_folder=test_folder,
            threshold_value=threshold,
            min_pixel_length=min_length,
            output_folder_path=output_folder
        )
        
        print(f"✅ 批量处理成功!")
        print(f"处理了 {len(results)} 个文件")
        
        # 清理测试文件
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)
        if os.path.exists(test_folder):
            os.rmdir(test_folder)
            
    except Exception as e:
        print(f"❌ 批量处理失败: {str(e)}")


def test_parameter_validation():
    """测试参数验证"""
    print("\n" + "="*50)
    print("测试参数验证")
    print("="*50)
    
    # 创建测试图像
    test_image = create_test_image("param_test.png")
    
    # 测试无效阈值
    print("1. 测试无效阈值...")
    try:
        process_line_segments(test_image, -0.1, 20, "output")
        print("❌ 应该抛出异常但没有")
    except ValueError as e:
        print(f"✅ 正确捕获无效阈值: {e}")
    
    # 测试无效最小长度
    print("2. 测试无效最小长度...")
    try:
        process_line_segments(test_image, 0.5, -5, "output")
        print("❌ 应该抛出异常但没有")
    except ValueError as e:
        print(f"✅ 正确捕获无效最小长度: {e}")
    
    # 测试不存在的文件
    print("3. 测试不存在的文件...")
    try:
        process_line_segments("nonexistent.png", 0.5, 20, "output")
        print("❌ 应该抛出异常但没有")
    except FileNotFoundError as e:
        print(f"✅ 正确捕获文件不存在: {e}")
    
    # 清理测试文件
    if os.path.exists(test_image):
        os.remove(test_image)


def main():
    """运行所有测试"""
    print("线段检测模块测试")
    print("="*50)
    
    # 检查OpenCV是否可用
    try:
        import cv2
        print(f"✅ OpenCV版本: {cv2.__version__}")
    except ImportError:
        print("❌ OpenCV未安装，请先安装: pip install opencv-python")
        return
    
    # 运行测试
    test_single_file()
    test_batch_processing()
    test_parameter_validation()
    
    print("\n" + "="*50)
    print("所有测试完成!")
    print("="*50)
    
    # 提供使用示例
    print("\n使用示例:")
    print("1. 命令行模式:")
    print("   python main_line_processor.py --input image.png --threshold 0.35 --min-length 20 --output results")
    print("   python main_line_processor.py --input image_folder --threshold 0.35 --batch --output results")
    print("\n2. 交互模式:")
    print("   python main_line_processor.py")
    print("\n3. 直接调用函数:")
    print("   from line_segment_processor import process_line_segments")
    print("   result = process_line_segments('image.png', 0.35, 20, 'output')")


if __name__ == "__main__":
    main()
