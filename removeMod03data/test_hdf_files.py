#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试HDF文件的可读性和内容
"""

import os
import glob
import h5py
try:
    from pyhdf.SD import SD, SDC
    HDF4_AVAILABLE = True
except ImportError:
    HDF4_AVAILABLE = False


def test_hdf_file(file_path):
    """测试单个HDF文件"""
    print(f"\n测试文件: {os.path.basename(file_path)}")
    print(f"文件大小: {os.path.getsize(file_path) / (1024*1024):.2f} MB")
    
    # 尝试HDF5
    try:
        with h5py.File(file_path, 'r') as f:
            print("✅ HDF5格式 - 成功打开")
            print(f"数据集: {list(f.keys())}")
            if 'Latitude' in f:
                print(f"Latitude形状: {f['Latitude'].shape}")
            if 'Longitude' in f:
                print(f"Longitude形状: {f['Longitude'].shape}")
    except Exception as e:
        print(f"❌ HDF5格式 - 失败: {str(e)}")
    
    # 尝试HDF4
    if HDF4_AVAILABLE:
        try:
            hdf4_file = SD(file_path, SDC.READ)
            print("✅ HDF4格式 - 成功打开")
            datasets = hdf4_file.datasets()
            print(f"数据集: {list(datasets.keys())}")
            
            if 'Latitude' in datasets:
                lat_data = hdf4_file.select('Latitude')
                lat_info = lat_data.info()
                print(f"Latitude信息: {lat_info}")
                lat_data.end()
            
            if 'Longitude' in datasets:
                lon_data = hdf4_file.select('Longitude')
                lon_info = lon_data.info()
                print(f"Longitude信息: {lon_info}")
                lon_data.end()
            
            hdf4_file.end()
        except Exception as e:
            print(f"❌ HDF4格式 - 失败: {str(e)}")
    else:
        print("❌ HDF4格式 - pyhdf未安装")


def main():
    """主函数"""
    input_folder = r"C:\Users\wuch\Documents"
    
    # 查找HDF文件
    hdf_files = []
    for ext in ['*.hdf', '*.HDF', '*.h5', '*.H5']:
        hdf_files.extend(glob.glob(os.path.join(input_folder, ext)))
    
    print(f"找到 {len(hdf_files)} 个HDF文件")
    
    # 测试前几个文件
    for i, file_path in enumerate(hdf_files[:3]):  # 只测试前3个文件
        test_hdf_file(file_path)
        if i >= 2:  # 只测试前3个
            break


if __name__ == "__main__":
    main()
