#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MOD03 HDF文件栅格统计脚本（优化版）
统计E:\2013007目录下所有MOD03 HDF文件中1km栅格在全球1°×1°网格中的分布情况
使用向量化操作提高性能
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from pyhdf.SD import SD, SDC
import glob
from tqdm import tqdm
import warnings
from scipy.sparse import coo_matrix
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class MOD03GridStatistics:
    """MOD03网格统计类"""
    
    def __init__(self, hdf_directory):
        self.hdf_directory = hdf_directory
        self.global_grid = np.zeros((180, 360), dtype=np.int64)
        self.processed_files = 0
        self.total_pixels = 0
        
    def read_mod03_coordinates(self, hdf_file):
        """
        读取MOD03 HDF文件中的经纬度数据
        
        Args:
            hdf_file (str): HDF文件路径
            
        Returns:
            tuple: (longitude, latitude) 经纬度数组，如果失败返回(None, None)
        """
        try:
            # 打开HDF文件
            hdf = SD(hdf_file, SDC.READ)
            
            # 尝试不同的经纬度数据集名称
            possible_lon_names = ['Longitude', 'longitude', 'lon', 'LON']
            possible_lat_names = ['Latitude', 'latitude', 'lat', 'LAT']
            
            longitude = None
            latitude = None
            
            # 获取所有数据集名称
            datasets = hdf.datasets()
            dataset_names = [name for name, info in datasets.items()]
            
            # 查找经度数据集
            for lon_name in possible_lon_names:
                if lon_name in dataset_names:
                    longitude = hdf.select(lon_name).get()
                    break
                    
            # 查找纬度数据集
            for lat_name in possible_lat_names:
                if lat_name in dataset_names:
                    latitude = hdf.select(lat_name).get()
                    break
            
            # 关闭文件
            hdf.end()
            
            if longitude is None or latitude is None:
                print(f"警告：在文件 {os.path.basename(hdf_file)} 中未找到经纬度数据集")
                print(f"可用数据集: {dataset_names}")
                return None, None
                
            return longitude, latitude
            
        except Exception as e:
            print(f"读取文件 {os.path.basename(hdf_file)} 时出错: {e}")
            return None, None
    
    def lon_lat_to_grid_index_vectorized(self, lon, lat):
        """
        将经纬度坐标转换为网格索引（向量化版本）
        
        Args:
            lon (numpy.ndarray): 经度数组 (-180 to 180)
            lat (numpy.ndarray): 纬度数组 (-90 to 90)
            
        Returns:
            tuple: (valid_mask, row_indices, col_indices)
        """
        # 创建有效数据掩码（排除填充值和无效值）
        valid_mask = ((lon >= -180) & (lon <= 180) & 
                     (lat >= -90) & (lat <= 90) & 
                     (~np.isnan(lon)) & (~np.isnan(lat)))
        
        # 只处理有效的经纬度值
        valid_lon = lon[valid_mask]
        valid_lat = lat[valid_mask]
        
        if len(valid_lon) == 0:
            return valid_mask, np.array([]), np.array([])
        
        # 经度：-180°到180° 映射到列索引 0到359
        col_indices = np.floor(valid_lon + 180).astype(int)
        
        # 纬度：90°到-90° 映射到行索引 0到179
        row_indices = np.floor(90 - valid_lat).astype(int)
        
        # 确保索引在有效范围内
        col_indices = np.clip(col_indices, 0, 359)
        row_indices = np.clip(row_indices, 0, 179)
        
        return valid_mask, row_indices, col_indices
    
    def update_grid_vectorized(self, row_indices, col_indices):
        """
        使用向量化操作更新网格统计
        
        Args:
            row_indices (numpy.ndarray): 行索引数组
            col_indices (numpy.ndarray): 列索引数组
        """
        if len(row_indices) == 0:
            return
            
        # 使用numpy的bincount进行快速统计
        # 将二维索引转换为一维索引
        linear_indices = row_indices * 360 + col_indices
        
        # 统计每个网格的像素数量
        counts = np.bincount(linear_indices, minlength=180*360)
        
        # 将一维计数结果重新整形为二维网格并累加
        self.global_grid += counts.reshape(180, 360)
    
    def process_all_files(self):
        """
        处理目录下的所有HDF文件
        
        Returns:
            numpy.ndarray: 统计结果的180×360网格
        """
        # 查找所有HDF文件
        hdf_pattern = os.path.join(self.hdf_directory, "*.hdf")
        hdf_files = glob.glob(hdf_pattern)
        
        print(f"在目录 {self.hdf_directory} 中找到 {len(hdf_files)} 个HDF文件")
        
        if len(hdf_files) == 0:
            print(f"警告：在目录中未找到HDF文件")
            return self.global_grid
        
        # 处理每个HDF文件
        for hdf_file in tqdm(hdf_files, desc="处理HDF文件"):
            longitude, latitude = self.read_mod03_coordinates(hdf_file)
            
            if longitude is not None and latitude is not None:
                # 展平数组以便向量化处理
                lon_flat = longitude.flatten()
                lat_flat = latitude.flatten()
                
                # 获取网格索引
                valid_mask, row_indices, col_indices = self.lon_lat_to_grid_index_vectorized(
                    lon_flat, lat_flat)
                
                # 更新网格统计
                self.update_grid_vectorized(row_indices, col_indices)
                
                # 更新统计信息
                self.processed_files += 1
                self.total_pixels += np.sum(valid_mask)
        
        print(f"\n处理完成:")
        print(f"成功处理的文件数: {self.processed_files}")
        print(f"总有效像素数: {self.total_pixels}")
        
        return self.global_grid
    
    def plot_heatmap(self, output_file="mod03_grid_heatmap_optimized.png"):
        """
        绘制全球网格统计热图
        
        Args:
            output_file (str): 输出图像文件名
        """
        # 创建图形
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
        
        # 第一个子图：原始数据热图
        im1 = ax1.imshow(self.global_grid, 
                        extent=[-180, 180, -90, 90],
                        cmap='hot', 
                        aspect='auto',
                        interpolation='nearest')
        
        ax1.set_xlabel('经度 (°)', fontsize=12)
        ax1.set_ylabel('纬度 (°)', fontsize=12)
        ax1.set_title('MOD03 HDF文件全球1°×1°网格栅格分布热图（线性尺度）', fontsize=14)
        
        # 添加颜色条
        cbar1 = plt.colorbar(im1, ax=ax1, shrink=0.8)
        cbar1.set_label('栅格数量', fontsize=12)
        
        # 设置刻度
        lon_ticks = np.arange(-180, 181, 30)
        lat_ticks = np.arange(-90, 91, 30)
        ax1.set_xticks(lon_ticks)
        ax1.set_yticks(lat_ticks)
        ax1.grid(True, alpha=0.3, linestyle='--')
        
        # 第二个子图：对数尺度热图（用于更好地显示数据分布）
        # 避免log(0)的问题
        log_data = np.log10(self.global_grid + 1)
        
        im2 = ax2.imshow(log_data, 
                        extent=[-180, 180, -90, 90],
                        cmap='hot', 
                        aspect='auto',
                        interpolation='nearest')
        
        ax2.set_xlabel('经度 (°)', fontsize=12)
        ax2.set_ylabel('纬度 (°)', fontsize=12)
        ax2.set_title('MOD03 HDF文件全球1°×1°网格栅格分布热图（对数尺度）', fontsize=14)
        
        # 添加颜色条
        cbar2 = plt.colorbar(im2, ax=ax2, shrink=0.8)
        cbar2.set_label('栅格数量 (log10(count+1))', fontsize=12)
        
        ax2.set_xticks(lon_ticks)
        ax2.set_yticks(lat_ticks)
        ax2.grid(True, alpha=0.3, linestyle='--')
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图像
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"热图已保存为: {output_file}")
        
        # 显示图像
        plt.show()
        
        # 打印详细统计信息
        self.print_statistics()
    
    def print_statistics(self):
        """打印详细统计信息"""
        total_pixels = np.sum(self.global_grid)
        non_zero_grids = np.count_nonzero(self.global_grid)
        max_pixels = np.max(self.global_grid)
        mean_pixels = np.mean(self.global_grid[self.global_grid > 0]) if non_zero_grids > 0 else 0
        
        print(f"\n详细统计结果:")
        print(f"=" * 50)
        print(f"总栅格数: {total_pixels:,}")
        print(f"有数据的网格数: {non_zero_grids:,} / {180*360:,}")
        print(f"数据覆盖率: {non_zero_grids/(180*360)*100:.2f}%")
        print(f"单个网格最大栅格数: {max_pixels:,}")
        print(f"有数据网格的平均栅格数: {mean_pixels:.2f}")
        print(f"全球网格平均栅格数: {total_pixels/(180*360):.2f}")
        
        # 找出栅格数最多的几个网格
        top_indices = np.unravel_index(np.argsort(self.global_grid.ravel())[-5:], 
                                      self.global_grid.shape)
        
        print(f"\n栅格数最多的5个网格:")
        print(f"{'排名':<4} {'纬度':<8} {'经度':<8} {'栅格数':<10}")
        print("-" * 35)
        
        for i, (row, col) in enumerate(zip(top_indices[0][::-1], top_indices[1][::-1])):
            lat = 90 - row - 0.5  # 网格中心纬度
            lon = col - 180 + 0.5  # 网格中心经度
            count = self.global_grid[row, col]
            print(f"{i+1:<4} {lat:>7.1f}° {lon:>7.1f}° {count:>9,}")
    
    def save_results(self, filename="mod03_grid_statistics_optimized"):
        """
        保存统计结果
        
        Args:
            filename (str): 文件名前缀
        """
        # 保存numpy数组
        np.save(f"{filename}.npy", self.global_grid)
        
        # 保存为文本文件（便于其他软件读取）
        np.savetxt(f"{filename}.txt", self.global_grid, fmt='%d', delimiter='\t')
        
        # 保存元数据
        metadata = {
            'processed_files': self.processed_files,
            'total_pixels': self.total_pixels,
            'grid_shape': self.global_grid.shape,
            'non_zero_grids': np.count_nonzero(self.global_grid),
            'max_pixels': np.max(self.global_grid),
            'description': 'MOD03 HDF文件全球1°×1°网格栅格统计结果'
        }
        
        import json
        with open(f"{filename}_metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"统计结果已保存:")
        print(f"  - 网格数据: {filename}.npy")
        print(f"  - 文本格式: {filename}.txt")
        print(f"  - 元数据: {filename}_metadata.json")

def main():
    """主函数"""
    # HDF文件目录
    hdf_directory = r"E:\2013007"
    
    print("开始处理MOD03 HDF文件（优化版）...")
    print(f"目录: {hdf_directory}")
    
    # 检查目录是否存在
    if not os.path.exists(hdf_directory):
        print(f"错误：目录 {hdf_directory} 不存在！")
        print("请检查路径是否正确")
        return
    
    # 创建统计对象并处理
    statistics = MOD03GridStatistics(hdf_directory)
    
    # 处理所有文件
    grid_result = statistics.process_all_files()
    
    # 绘制热图
    statistics.plot_heatmap()
    
    # 保存结果
    statistics.save_results()

if __name__ == "__main__":
    main()
