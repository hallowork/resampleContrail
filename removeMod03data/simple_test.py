#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的HDF文件测试
"""

import os
import glob
import tempfile
import shutil
from pyhdf.SD import SD, SDC


def test_single_file():
    """测试单个文件"""
    input_folder = r"C:\Users\wuch\Documents"
    
    # 找到第一个HDF文件
    hdf_files = glob.glob(os.path.join(input_folder, "*.hdf"))
    if not hdf_files:
        print("未找到HDF文件")
        return
    
    file_path = hdf_files[0]
    print(f"测试文件: {os.path.basename(file_path)}")
    print(f"文件大小: {os.path.getsize(file_path) / (1024*1024):.2f} MB")
    
    try:
        # 读取原始文件
        hdf4_file = SD(file_path, SDC.READ)
        datasets = hdf4_file.datasets()
        print(f"数据集: {list(datasets.keys())}")
        
        # 检查经纬度数据
        has_lat = 'Latitude' in datasets
        has_lon = 'Longitude' in datasets
        print(f"有Latitude: {has_lat}")
        print(f"有Longitude: {has_lon}")
        
        if has_lat:
            lat_data = hdf4_file.select('Latitude')
            lat_array = lat_data.get()
            print(f"Latitude形状: {lat_array.shape}")
            lat_data.end()
        
        if has_lon:
            lon_data = hdf4_file.select('Longitude')
            lon_array = lon_data.get()
            print(f"Longitude形状: {lon_array.shape}")
            lon_data.end()
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.hdf')
        temp_file_path = temp_file.name
        temp_file.close()
        
        # 创建新的HDF文件
        new_hdf4_file = SD(temp_file_path, SDC.WRITE | SDC.CREATE)
        
        # 复制经纬度数据
        if has_lat:
            lat_data = hdf4_file.select('Latitude')
            lat_array = lat_data.get()
            lat_info = lat_data.info()
            print(f"Latitude信息: {lat_info}")
            
            # 创建新的数据集
            new_lat = new_hdf4_file.create('Latitude', SDC.FLOAT32, lat_info[1:])
            new_lat.set(lat_array)
            new_lat.end()
            lat_data.end()
            print("✅ Latitude数据复制成功")
        
        if has_lon:
            lon_data = hdf4_file.select('Longitude')
            lon_array = lon_data.get()
            lon_info = lon_data.info()
            print(f"Longitude信息: {lon_info}")
            
            # 创建新的数据集
            new_lon = new_hdf4_file.create('Longitude', SDC.FLOAT32, lon_info[1:])
            new_lon.set(lon_array)
            new_lon.end()
            lon_data.end()
            print("✅ Longitude数据复制成功")
        
        # 关闭文件
        hdf4_file.end()
        new_hdf4_file.end()
        
        # 检查新文件大小
        original_size = os.path.getsize(file_path) / (1024*1024)
        new_size = os.path.getsize(temp_file_path) / (1024*1024)
        efficiency = ((original_size - new_size) / original_size) * 100
        
        print(f"原始大小: {original_size:.2f} MB")
        print(f"新大小: {new_size:.2f} MB")
        print(f"瘦身效率: {efficiency:.1f}%")
        
        # 清理临时文件
        os.unlink(temp_file_path)
        print("✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")


if __name__ == "__main__":
    test_single_file()
