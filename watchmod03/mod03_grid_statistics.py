#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MOD03 HDF文件栅格统计脚本
统计E:\2013007目录下所有MOD03 HDF文件中1km栅格在全球1°×1°网格中的分布情况
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from pyhdf.SD import SD, SDC
import glob
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def read_mod03_coordinates(hdf_file):
    """
    读取MOD03 HDF文件中的经纬度数据
    
    Args:
        hdf_file (str): HDF文件路径
        
    Returns:
        tuple: (longitude, latitude) 经纬度数组
    """
    try:
        # 打开HDF文件
        hdf = SD(hdf_file, SDC.READ)
        
        # 读取经纬度数据集
        # MOD03文件中经纬度通常存储在'Longitude'和'Latitude'数据集中
        lon_dataset = hdf.select('Longitude')
        lat_dataset = hdf.select('Latitude')
        
        # 获取数据
        longitude = lon_dataset.get()
        latitude = lat_dataset.get()
        
        # 关闭文件
        hdf.end()
        
        return longitude, latitude
        
    except Exception as e:
        print(f"读取文件 {hdf_file} 时出错: {e}")
        return None, None

def create_global_grid():
    """
    创建全球1°×1°网格系统
    
    Returns:
        numpy.ndarray: 180×360的零矩阵
    """
    # 创建180行（纬度）×360列（经度）的网格
    # 纬度范围：-90°到90° (180个1°格子)
    # 经度范围：-180°到180° (360个1°格子)
    return np.zeros((180, 360), dtype=np.int64)

def lon_lat_to_grid_index(lon, lat):
    """
    将经纬度坐标转换为网格索引
    
    Args:
        lon (float or array): 经度 (-180 to 180)
        lat (float or array): 纬度 (-90 to 90)
        
    Returns:
        tuple: (row_index, col_index) 网格索引
    """
    # 经度：-180°到180° 映射到列索引 0到359
    col_index = np.floor(lon + 180).astype(int)
    
    # 纬度：90°到-90° 映射到行索引 0到179
    # 注意：纬度从北到南递减，所以要用90-lat
    row_index = np.floor(90 - lat).astype(int)
    
    # 确保索引在有效范围内
    col_index = np.clip(col_index, 0, 359)
    row_index = np.clip(row_index, 0, 179)
    
    return row_index, col_index

def process_hdf_files(hdf_directory):
    """
    处理指定目录下的所有HDF文件
    
    Args:
        hdf_directory (str): HDF文件目录路径
        
    Returns:
        numpy.ndarray: 统计结果的180×360网格
    """
    # 创建全球网格
    global_grid = create_global_grid()
    
    # 查找所有HDF文件
    hdf_pattern = os.path.join(hdf_directory, "*.hdf")
    hdf_files = glob.glob(hdf_pattern)
    
    print(f"找到 {len(hdf_files)} 个HDF文件")
    
    if len(hdf_files) == 0:
        print(f"在目录 {hdf_directory} 中未找到HDF文件")
        return global_grid
    
    # 处理每个HDF文件
    for hdf_file in tqdm(hdf_files, desc="处理HDF文件"):
        longitude, latitude = read_mod03_coordinates(hdf_file)
        
        if longitude is not None and latitude is not None:
            # 将经纬度转换为网格索引
            row_indices, col_indices = lon_lat_to_grid_index(longitude, latitude)
            
            # 统计每个网格中的栅格数量
            # 使用numpy的bincount或直接累加
            for i in range(longitude.size):
                row_idx = row_indices.flat[i]
                col_idx = col_indices.flat[i]
                
                # 检查有效的经纬度值（排除填充值）
                if -180 <= longitude.flat[i] <= 180 and -90 <= latitude.flat[i] <= 90:
                    global_grid[row_idx, col_idx] += 1
    
    return global_grid

def plot_heatmap(grid_data, output_file="mod03_grid_heatmap.png"):
    """
    绘制全球网格统计热图
    
    Args:
        grid_data (numpy.ndarray): 180×360的统计数据
        output_file (str): 输出图像文件名
    """
    # 创建图形
    plt.figure(figsize=(16, 8))
    
    # 创建经纬度坐标轴
    lon_ticks = np.arange(-180, 181, 30)  # 经度标记：每30度一个
    lat_ticks = np.arange(-90, 91, 30)    # 纬度标记：每30度一个
    
    # 创建网格坐标用于显示
    lon_edges = np.arange(-180, 181, 1)
    lat_edges = np.arange(90, -91, -1)  # 纬度从90到-90
    
    # 绘制热图
    im = plt.imshow(grid_data, 
                    extent=[-180, 180, -90, 90],
                    cmap='hot', 
                    aspect='auto',
                    interpolation='nearest')
    
    # 添加颜色条
    cbar = plt.colorbar(im, shrink=0.8)
    cbar.set_label('栅格数量', fontsize=12)
    
    # 设置坐标轴
    plt.xlabel('经度 (°)', fontsize=12)
    plt.ylabel('纬度 (°)', fontsize=12)
    plt.title('MOD03 HDF文件全球1°×1°网格栅格分布热图', fontsize=14, pad=20)
    
    # 设置刻度
    plt.xticks(lon_ticks)
    plt.yticks(lat_ticks)
    
    # 添加网格线
    plt.grid(True, alpha=0.3, linestyle='--')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图像
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"热图已保存为: {output_file}")
    
    # 显示图像
    plt.show()
    
    # 打印统计信息
    total_pixels = np.sum(grid_data)
    non_zero_grids = np.count_nonzero(grid_data)
    max_pixels = np.max(grid_data)
    
    print(f"\n统计结果:")
    print(f"总栅格数: {total_pixels}")
    print(f"有数据的网格数: {non_zero_grids}")
    print(f"单个网格最大栅格数: {max_pixels}")
    print(f"平均每个网格栅格数: {total_pixels/64800:.2f}")

def main():
    """
    主函数
    """
    # HDF文件目录
    hdf_directory = r"E:\2013007"
    
    print("开始处理MOD03 HDF文件...")
    print(f"目录: {hdf_directory}")
    
    # 检查目录是否存在
    if not os.path.exists(hdf_directory):
        print(f"错误：目录 {hdf_directory} 不存在！")
        return
    
    # 处理HDF文件并统计
    grid_result = process_hdf_files(hdf_directory)
    
    # 绘制热图
    plot_heatmap(grid_result)
    
    # 保存统计结果
    np.save("mod03_grid_statistics.npy", grid_result)
    print("统计结果已保存为: mod03_grid_statistics.npy")

if __name__ == "__main__":
    main()
