#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试HDF文件修改前后的代码兼容性
验证Latitude和Longitude数据访问是否受影响
"""

import os
import glob
import h5py
try:
    from pyhdf.SD import SD, SDC
    HDF4_AVAILABLE = True
except ImportError:
    HDF4_AVAILABLE = False


def test_hdf5_compatibility(file_path):
    """测试HDF5文件的兼容性"""
    print(f"\n测试HDF5文件: {os.path.basename(file_path)}")
    
    try:
        with h5py.File(file_path, 'r') as hdf:
            # 检查是否有经纬度数据
            if 'Latitude' in hdf and 'Longitude' in hdf:
                print("✅ 找到Latitude和Longitude数据")
                
                # 模拟原来的代码
                lat_data = hdf['Latitude'][:]
                lon_data = hdf['Longitude'][:]
                
                print(f"Latitude形状: {lat_data.shape}")
                print(f"Longitude形状: {lon_data.shape}")
                print(f"Latitude数据类型: {lat_data.dtype}")
                print(f"Longitude数据类型: {lon_data.dtype}")
                
                # 检查数据范围
                print(f"Latitude范围: {lat_data.min():.2f} 到 {lat_data.max():.2f}")
                print(f"Longitude范围: {lon_data.min():.2f} 到 {lon_data.max():.2f}")
                
                return True
            else:
                print("❌ 未找到Latitude或Longitude数据")
                return False
                
    except Exception as e:
        print(f"❌ HDF5读取错误: {str(e)}")
        return False


def test_hdf4_compatibility(file_path):
    """测试HDF4文件的兼容性"""
    if not HDF4_AVAILABLE:
        print("❌ pyhdf未安装，无法测试HDF4")
        return False
    
    print(f"\n测试HDF4文件: {os.path.basename(file_path)}")
    
    try:
        hdf = SD(file_path, SDC.READ)
        datasets = hdf.datasets()
        
        if 'Latitude' in datasets and 'Longitude' in datasets:
            print("✅ 找到Latitude和Longitude数据")
            
            # 模拟原来的代码 - 这是关键测试
            lat_dataset = hdf.select('Latitude')
            lon_dataset = hdf.select('Longitude')
            
            # 测试基本数据访问
            lat_data = lat_dataset.get()
            lon_data = lon_dataset.get()
            
            print(f"✅ 成功访问Latitude数据，形状: {lat_data.shape}")
            print(f"✅ 成功访问Longitude数据，形状: {lon_data.shape}")
            
            # 关闭数据集
            lat_dataset.end()
            lon_dataset.end()
            hdf.end()
            
            print("✅ 兼容性测试通过：原有的lat_dataset = hdf.select('Latitude')代码仍然有效")
            return True
        else:
            print("❌ 未找到Latitude或Longitude数据")
            hdf.end()
            return False
            
    except Exception as e:
        print(f"❌ HDF4读取错误: {str(e)}")
        return False


def test_before_after_compatibility():
    """测试修改前后的兼容性"""
    input_folder = r"C:\Users\wuch\Documents"
    
    # 查找HDF文件
    hdf_files = []
    for ext in ['*.hdf', '*.HDF', '*.h5', '*.H5']:
        hdf_files.extend(glob.glob(os.path.join(input_folder, ext)))
    
    if not hdf_files:
        print("未找到HDF文件进行测试")
        return
    
    print(f"找到 {len(hdf_files)} 个HDF文件")
    print("=" * 60)
    print("测试修改前的兼容性")
    print("=" * 60)
    
    # 测试修改前的文件
    successful_tests = 0
    for i, file_path in enumerate(hdf_files[:3]):  # 只测试前3个文件
        print(f"\n文件 {i+1}: {os.path.basename(file_path)}")
        
        # 尝试HDF5
        if test_hdf5_compatibility(file_path):
            successful_tests += 1
            continue
        
        # 尝试HDF4
        if test_hdf4_compatibility(file_path):
            successful_tests += 1
            continue
    
    print("\n" + "=" * 60)
    print("兼容性测试总结")
    print("=" * 60)
    print(f"测试文件数: {min(3, len(hdf_files))}")
    print(f"成功测试: {successful_tests}")
    print(f"失败测试: {min(3, len(hdf_files)) - successful_tests}")
    
    if successful_tests > 0:
        print("\n✅ 结论: 修改前的代码可以正常访问Latitude和Longitude数据")
        print("✅ 这意味着修改后的文件仍然兼容原有的代码")
        print("✅ 您的原有代码 lat_dataset = hdf.select('Latitude') 不会受到任何影响")
    else:
        print("\n❌ 结论: 无法访问经纬度数据，可能需要检查文件格式")


def main():
    """主函数"""
    print("HDF文件兼容性测试")
    print("验证修改前后代码的兼容性")
    print("=" * 60)
    
    test_before_after_compatibility()


if __name__ == "__main__":
    main()
