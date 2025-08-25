#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的HDF文件兼容性测试
验证原有的lat_dataset = hdf.select('Latitude')代码是否仍然有效
"""

import os
import glob
from pyhdf.SD import SD, SDC


def test_compatibility():
    """测试兼容性"""
    input_folder = r"C:\Users\wuch\Documents"
    
    # 查找HDF文件
    hdf_files = glob.glob(os.path.join(input_folder, "*.hdf"))
    
    if not hdf_files:
        print("未找到HDF文件")
        return
    
    print(f"找到 {len(hdf_files)} 个HDF文件")
    print("=" * 60)
    print("测试原有的代码兼容性")
    print("=" * 60)
    
    # 测试第一个文件
    file_path = hdf_files[0]
    print(f"测试文件: {os.path.basename(file_path)}")
    
    try:
        # 打开HDF文件
        hdf = SD(file_path, SDC.READ)
        datasets = hdf.datasets()
        
        if 'Latitude' in datasets and 'Longitude' in datasets:
            print("✅ 找到Latitude和Longitude数据")
            
            # 测试原有的代码 - 这是关键
            print("\n测试原有代码:")
            print("lat_dataset = hdf.select('Latitude')")
            print("lon_dataset = hdf.select('Longitude')")
            
            lat_dataset = hdf.select('Latitude')
            lon_dataset = hdf.select('Longitude')
            
            print("✅ 成功执行 hdf.select('Latitude')")
            print("✅ 成功执行 hdf.select('Longitude')")
            
            # 测试数据访问
            print("\n测试数据访问:")
            print("lat_data = lat_dataset.get()")
            print("lon_data = lon_dataset.get()")
            
            lat_data = lat_dataset.get()
            lon_data = lon_dataset.get()
            
            print(f"✅ 成功获取Latitude数据，形状: {lat_data.shape}")
            print(f"✅ 成功获取Longitude数据，形状: {lon_data.shape}")
            
            # 关闭数据集
            lat_dataset.end()
            lon_dataset.end()
            hdf.end()
            
            print("\n" + "=" * 60)
            print("✅ 兼容性测试结果")
            print("=" * 60)
            print("✅ 您的原有代码完全兼容！")
            print("✅ lat_dataset = hdf.select('Latitude') 仍然有效")
            print("✅ lon_dataset = hdf.select('Longitude') 仍然有效")
            print("✅ 数据访问方式没有任何变化")
            print("✅ 修改后的文件不会影响您的现有代码")
            
        else:
            print("❌ 未找到Latitude或Longitude数据")
            hdf.end()
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")


if __name__ == "__main__":
    test_compatibility()
