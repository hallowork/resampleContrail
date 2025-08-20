"""
MOD03和RGB图像处理测试文件
用于测试contrail_processor模块的功能
"""

import os
import sys
from datetime import datetime
from contrail_processor import process_contrail_data, get_processing_statistics


def test_basic_processing():
    """基本处理功能测试"""
    print("=" * 60)
    print("开始基本处理功能测试")
    print("=" * 60)
    
    # 测试参数
    mod03_dir = r"C:\researchWorkPlace\pythonProject\dataExample\mod03"
    rgb_dir = r"C:\researchWorkPlace\pythonProject\dataExample\rgb"
    date = "2013001"
    resolution = 1
    output_dir = r"C:\researchWorkPlace\pythonProject\output"
    threshold = 0.35
    
    print(f"测试参数:")
    print(f"  MOD03目录: {mod03_dir}")
    print(f"  RGB目录: {rgb_dir}")
    print(f"  日期: {date}")
    print(f"  分辨率: {resolution}")
    print(f"  输出目录: {output_dir}")
    print(f"  阈值: {threshold}")
    print()
    
    # 检查输入目录是否存在
    if not os.path.exists(mod03_dir):
        print(f"警告: MOD03目录不存在: {mod03_dir}")
        return False
    
    if not os.path.exists(rgb_dir):
        print(f"警告: RGB目录不存在: {rgb_dir}")
        return False
    
    try:
        # 执行处理
        start_time = datetime.now()
        result = process_contrail_data(
            mod03_dir=mod03_dir,
            rgb_dir=rgb_dir,
            date=date,
            resolution=resolution,
            output_dir=output_dir,
            threshold=threshold,
            output_ratio_only=False
        )
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"\n处理完成!")
        print(f"处理文件数量: {result}")
        print(f"处理时间: {processing_time:.2f} 秒")
        
        # 获取处理统计信息
        stats = get_processing_statistics(output_dir, date)
        if stats:
            print(f"\n处理结果统计:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        return result > 0
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False


def test_only_ratio_output():
    """测试只输出比例矩阵"""
    print("=" * 60)
    print("开始只输出比例矩阵测试")
    print("=" * 60)
    
    # 测试参数
    mod03_dir = r"C:\researchWorkPlace\pythonProject\dataExample\mod03"
    rgb_dir = r"C:\researchWorkPlace\pythonProject\dataExample\rgb"
    date = "2013001"
    resolution = 1
    output_dir = r"C:\researchWorkPlace\pythonProject\output_ratio_only"
    threshold = 0.35
    
    print(f"测试参数:")
    print(f"  输出目录: {output_dir}")
    print(f"  只输出比例: True")
    print()
    
    try:
        # 执行处理
        result = process_contrail_data(
            mod03_dir=mod03_dir,
            rgb_dir=rgb_dir,
            date=date,
            resolution=resolution,
            output_dir=output_dir,
            threshold=threshold,
            output_ratio_only=True  # 只输出比例
        )
        
        print(f"处理完成! 处理文件数量: {result}")
        
        # 检查输出文件
        ratio_file = os.path.join(output_dir, 'ratio', f'ratio_{date}.tif')
        count_0_file = os.path.join(output_dir, 'count_0', f'count_0_{date}.tif')
        count_1_file = os.path.join(output_dir, 'count_1', f'count_1_{date}.tif')
        
        print(f"\n输出文件检查:")
        print(f"  比例文件存在: {os.path.exists(ratio_file)}")
        print(f"  背景计数文件存在: {os.path.exists(count_0_file)} (应该为False)")
        print(f"  航迹计数文件存在: {os.path.exists(count_1_file)} (应该为False)")
        
        return result > 0
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False


def test_different_threshold():
    """测试不同阈值"""
    print("=" * 60)
    print("开始不同阈值测试")
    print("=" * 60)
    
    # 测试参数
    mod03_dir = r"C:\researchWorkPlace\pythonProject\dataExample\mod03"
    rgb_dir = r"C:\researchWorkPlace\pythonProject\dataExample\rgb"
    date = "2013001"
    resolution = 1
    thresholds = [0.2, 0.5, 0.7]
    
    results = {}
    
    for threshold in thresholds:
        print(f"\n测试阈值: {threshold}")
        output_dir = rf"C:\researchWorkPlace\pythonProject\output_threshold_{threshold}"
        
        try:
            result = process_contrail_data(
                mod03_dir=mod03_dir,
                rgb_dir=rgb_dir,
                date=date,
                resolution=resolution,
                output_dir=output_dir,
                threshold=threshold,
                output_ratio_only=True
            )
            
            results[threshold] = result
            print(f"阈值 {threshold} 处理完成，处理文件数: {result}")
            
            # 获取统计信息
            stats = get_processing_statistics(output_dir, date)
            if 'ratio' in stats:
                print(f"  平均比例: {stats['ratio']['mean']:.4f}")
                print(f"  非零像素数: {stats['ratio']['non_zero_pixels']}")
            
        except Exception as e:
            print(f"阈值 {threshold} 测试失败: {str(e)}")
            results[threshold] = 0
    
    print(f"\n不同阈值测试结果汇总:")
    for threshold, result in results.items():
        print(f"  阈值 {threshold}: {result} 个文件")
    
    return all(result > 0 for result in results.values())


def check_input_files():
    """检查输入文件是否存在"""
    print("=" * 60)
    print("检查输入文件")
    print("=" * 60)
    
    mod03_dir = r"C:\researchWorkPlace\pythonProject\dataExample\mod03"
    rgb_dir = r"C:\researchWorkPlace\pythonProject\dataExample\rgb"
    
    print(f"MOD03目录: {mod03_dir}")
    if os.path.exists(mod03_dir):
        mod03_files = [f for f in os.listdir(mod03_dir) if f.endswith('.hdf')]
        print(f"  找到 {len(mod03_files)} 个HDF文件")
        for i, f in enumerate(mod03_files[:3]):  # 显示前3个文件
            print(f"    {i+1}. {f}")
        if len(mod03_files) > 3:
            print(f"    ... 还有 {len(mod03_files)-3} 个文件")
    else:
        print(f"  目录不存在!")
    
    print(f"\nRGB目录: {rgb_dir}")
    if os.path.exists(rgb_dir):
        rgb_files = [f for f in os.listdir(rgb_dir) if f.endswith('.png')]
        print(f"  找到 {len(rgb_files)} 个PNG文件")
        for i, f in enumerate(rgb_files[:3]):  # 显示前3个文件
            print(f"    {i+1}. {f}")
        if len(rgb_files) > 3:
            print(f"    ... 还有 {len(rgb_files)-3} 个文件")
    else:
        print(f"  目录不存在!")


def run_all_tests():
    """运行所有测试"""
    print("开始运行所有测试...")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 检查输入文件
    check_input_files()
    print()
    
    test_results = []
    
    # 基本功能测试
    try:
        result1 = test_basic_processing()
        test_results.append(("基本处理功能", result1))
        print()
    except Exception as e:
        print(f"基本处理功能测试出错: {str(e)}")
        test_results.append(("基本处理功能", False))
    
    # 只输出比例测试
    try:
        result2 = test_only_ratio_output()
        test_results.append(("只输出比例", result2))
        print()
    except Exception as e:
        print(f"只输出比例测试出错: {str(e)}")
        test_results.append(("只输出比例", False))
    
    # 不同阈值测试
    try:
        result3 = test_different_threshold()
        test_results.append(("不同阈值", result3))
        print()
    except Exception as e:
        print(f"不同阈值测试出错: {str(e)}")
        test_results.append(("不同阈值", False))
    
    # 输出测试结果汇总
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "通过" if result else "失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("所有测试通过! ✓")
    else:
        print(f"有 {total - passed} 个测试失败! ✗")
    
    return passed == total


if __name__ == "__main__":
    # 运行所有测试
    success = run_all_tests()
    
    # 退出程序时返回适当的退出码
    sys.exit(0 if success else 1)
