"""
MOD03和RGB图像处理模块
用于处理卫星数据，进行二值化和经纬度统计
"""

import os
import glob
import numpy as np
from PIL import Image
import h5py
from pyhdf.SD import SD, SDC
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS
from pathlib import Path
import pandas as pd


def process_contrail_data(mod03_dir, rgb_dir, date, resolution, output_dir, threshold=0.35, output_ratio_only=False):
    """
    处理MOD03和RGB数据，进行二值化处理和经纬度统计
    
    参数:
    mod03_dir: MOD03文件目录路径
    rgb_dir: RGB图像目录路径  
    date: 日期，格式如'2013001'
    resolution: 分辨率，1表示1度×1度
    output_dir: 输出目录路径
    threshold: 二值化阈值，默认0.35
    output_ratio_only: 是否只输出比例，True只输出比例，False输出所有三个矩阵
    
    返回:
    成功处理的文件数量
    """
    
    print(f"开始处理日期 {date} 的数据...")
    
    # 1. 查找匹配的RGB文件
    rgb_files = find_rgb_files(rgb_dir, date)
    if not rgb_files:
        print(f"未找到日期 {date} 的RGB文件")
        return 0
    
    print(f"找到 {len(rgb_files)} 个RGB文件")
    
    # 2. 初始化统计数组 (180行×360列，对应纬度×经度)
    count_0 = np.zeros((180, 360), dtype=np.int32)  # 背景计数
    count_1 = np.zeros((180, 360), dtype=np.int32)  # 航迹计数
    
    processed_files = 0
    
    for rgb_file in rgb_files:
        try:
            # 3. 查找对应的MOD03文件
            mod03_file = find_corresponding_mod03(mod03_dir, rgb_file)
            if not mod03_file:
                print(f"未找到 {rgb_file} 对应的MOD03文件")
                continue
                
            print(f"处理文件对: {os.path.basename(rgb_file)} <-> {os.path.basename(mod03_file)}")
            
            # 4. 读取RGB图像并二值化
            rgb_image = Image.open(rgb_file)
            if rgb_image.mode != 'L':
                rgb_image = rgb_image.convert('L')  # 转换为灰度图
            
            rgb_array = np.array(rgb_image) / 255.0  # 归一化到0-1
            binary_image = (rgb_array > threshold).astype(np.int32)
            
            # 5. 读取MOD03经纬度信息
            lat_data, lon_data = read_mod03_coordinates(mod03_file)
            if lat_data is None or lon_data is None:
                print(f"无法读取 {mod03_file} 的经纬度信息")
                continue
            
            # 6. 将像素映射到1度×1度网格并统计
            map_pixels_to_grid(binary_image, lat_data, lon_data, count_0, count_1)
            processed_files += 1
            
        except Exception as e:
            print(f"处理文件 {rgb_file} 时出错: {str(e)}")
            continue
    
    if processed_files == 0:
        print("没有成功处理任何文件")
        return 0
    
    # 7. 计算比例矩阵
    total_count = count_0 + count_1
    ratio_matrix = np.zeros_like(total_count, dtype=np.float32)
    mask = total_count > 0
    ratio_matrix[mask] = count_1[mask] / total_count[mask]
    
    # 8. 保存结果
    save_results(output_dir, count_0, count_1, ratio_matrix, date, output_ratio_only)
    
    print(f"成功处理 {processed_files} 个文件")
    return processed_files


def find_rgb_files(rgb_dir, date):
    """查找指定日期的RGB文件"""
    pattern = os.path.join(rgb_dir, f"*{date}*RGB*.png")
    return glob.glob(pattern)


def find_corresponding_mod03(mod03_dir, rgb_file):
    """根据RGB文件名查找对应的MOD03文件"""
    rgb_basename = os.path.basename(rgb_file)
    
    # 从RGB文件名提取日期和时间信息
    # 例如: MOD021KM.A2013001.0000.061.2017295083828_RGB_denoised.png
    parts = rgb_basename.split('.')
    if len(parts) < 4:
        return None
    
    # 构造MOD03文件名模式
    date_time_part = f"{parts[1]}.{parts[2]}"  # A2013001.0000
    pattern = os.path.join(mod03_dir, f"MOD03.{date_time_part}*.hdf")
    
    mod03_files = glob.glob(pattern)
    return mod03_files[0] if mod03_files else None


def read_mod03_coordinates(mod03_file):
    """读取MOD03文件中的经纬度信息"""
    try:
        # 尝试使用pyhdf读取HDF4文件
        hdf = SD(mod03_file, SDC.READ)
        
        # 读取纬度和经度数据
        lat_dataset = hdf.select('Latitude')
        lon_dataset = hdf.select('Longitude')
        
        lat_data = lat_dataset.get()
        lon_data = lon_dataset.get()
        
        hdf.end()
        
        return lat_data, lon_data
        
    except Exception as e:
        print(f"读取MOD03文件 {mod03_file} 失败: {str(e)}")
        return None, None


def map_pixels_to_grid(binary_image, lat_data, lon_data, count_0, count_1):
    """将像素映射到1度×1度网格并统计"""
    height, width = binary_image.shape
    lat_height, lat_width = lat_data.shape
    
    # 如果尺寸不匹配，进行插值调整
    if (height, width) != (lat_height, lat_width):
        # 简单的最近邻插值调整坐标数据尺寸
        from scipy import ndimage
        zoom_h = height / lat_height
        zoom_w = width / lat_width
        lat_data = ndimage.zoom(lat_data, (zoom_h, zoom_w), order=1)
        lon_data = ndimage.zoom(lon_data, (zoom_h, zoom_w), order=1)
    
    # 遍历每个像素
    for i in range(height):
        for j in range(width):
            lat = lat_data[i, j]
            lon = lon_data[i, j]
            
            # 检查经纬度是否有效
            if np.isnan(lat) or np.isnan(lon) or lat < -90 or lat > 90 or lon < -180 or lon > 180:
                continue
            
            # 将经纬度映射到网格索引
            # 纬度: -90到90映射到179到0 (南到北)
            # 经度: -180到180映射到0到359 (西到东)
            # 处理边界情况
            if lat == 90.0:  # 北极
                lat = 89.999  # 略微调整到最北边的网格内
            elif lat == -90.0:  # 南极
                lat = -89.999  # 略微调整到最南边的网格内
                
            if lon == 180.0:  # 东经180度
                lon = 179.999  # 略微调整到最东边的网格内
            elif lon == -180.0:  # 西经180度
                lon = -179.999  # 略微调整到最西边的网格内
            
            # 将经纬度映射到网格索引
            # 先将坐标映射到对应的网格中心
            lat_grid = np.floor(lat) + 0.5  # 向下取整后加0.5得到网格中心
            lon_grid = np.floor(lon) + 0.5
            
            # 然后计算网格索引
            lat_idx = int(89.5 - lat_grid)  # 纬度索引，北纬90度对应索引0
            lon_idx = int(lon_grid + 179.5)  # 经度索引，西经180度对应索引0
            
            # 确保索引在有效范围内
            if 0 <= lat_idx < 180 and 0 <= lon_idx < 360:
                pixel_value = binary_image[i, j]
                if pixel_value == 0:
                    count_0[lat_idx, lon_idx] += 1
                else:
                    count_1[lat_idx, lon_idx] += 1


def save_results(output_dir, count_0, count_1, ratio_matrix, date, output_ratio_only):
    """保存结果为GeoTIFF文件和Excel文件"""
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 定义地理变换参数 (1度×1度网格)
    # 左上角: (-180, 90), 右下角: (180, -90)
    transform = from_bounds(-180, -90, 180, 90, 360, 180)
    crs = CRS.from_epsg(4326)  # WGS84
    
    if not output_ratio_only:
        # 创建子目录
        count_0_dir = os.path.join(output_dir, 'count_0')
        count_1_dir = os.path.join(output_dir, 'count_1')
        ratio_dir = os.path.join(output_dir, 'ratio')
        excel_dir = os.path.join(output_dir, 'excel')
        
        Path(count_0_dir).mkdir(parents=True, exist_ok=True)
        Path(count_1_dir).mkdir(parents=True, exist_ok=True)
        Path(ratio_dir).mkdir(parents=True, exist_ok=True)
        Path(excel_dir).mkdir(parents=True, exist_ok=True)
        
        # 保存背景计数
        save_geotiff(os.path.join(count_0_dir, f'count_0_{date}.tif'), 
                    count_0, transform, crs)
        
        # 保存航迹计数
        save_geotiff(os.path.join(count_1_dir, f'count_1_{date}.tif'), 
                    count_1, transform, crs)
        
        # 保存比例
        save_geotiff(os.path.join(ratio_dir, f'ratio_{date}.tif'), 
                    ratio_matrix, transform, crs)
        
        # 保存Excel文件
        save_excel_files(count_0, count_1, ratio_matrix, date, excel_dir)
    else:
        # 只保存比例
        ratio_dir = os.path.join(output_dir, 'ratio')
        Path(ratio_dir).mkdir(parents=True, exist_ok=True)
        save_geotiff(os.path.join(ratio_dir, f'ratio_{date}.tif'), 
                    ratio_matrix, transform, crs)


def save_geotiff(filename, data, transform, crs):
    """保存数据为GeoTIFF文件"""
    with rasterio.open(
        filename,
        'w',
        driver='GTiff',
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs=crs,
        transform=transform,
        compress='lzw'
    ) as dst:
        dst.write(data, 1)
    
    print(f"已保存: {filename}")


def save_excel_files(count_0, count_1, ratio_matrix, date, excel_dir):
    """保存数据为Excel文件，包含经纬度信息"""
    print("正在生成Excel文件...")
    
    # 生成经纬度网格
    latitudes = np.arange(89.5, -90.5, -1)  # 89.5, 88.5, ..., -89.5 (180个值)
    longitudes = np.arange(-179.5, 180.5, 1)  # -179.5, -178.5, ..., 179.5 (360个值)
    
    # 准备数据
    df_count_0 = pd.DataFrame(count_0)
    df_count_0.columns = [f'经度{lon}°' for lon in longitudes]
    df_count_0.index = [f'纬度{lat}°' for lat in latitudes]
    
    df_count_1 = pd.DataFrame(count_1)
    df_count_1.columns = [f'经度{lon}°' for lon in longitudes]
    df_count_1.index = [f'纬度{lat}°' for lat in latitudes]
    
    df_ratio = pd.DataFrame(ratio_matrix)
    df_ratio.columns = [f'经度{lon}°' for lon in longitudes]
    df_ratio.index = [f'纬度{lat}°' for lat in latitudes]
    
    # 创建汇总表
    summary_data = {
        '统计项目': [
            '总网格数',
            '有数据的网格数',
            '总背景像素数',
            '总航迹像素数',
            '总像素数',
            '平均航迹比例',
            '最大航迹比例',
            '最小航迹比例'
        ],
        '数值': [
            180 * 360,
            np.sum((count_0 + count_1) > 0),
            int(np.sum(count_0)),
            int(np.sum(count_1)),
            int(np.sum(count_0 + count_1)),
            float(np.mean(ratio_matrix[ratio_matrix > 0])) if np.any(ratio_matrix > 0) else 0,
            float(np.max(ratio_matrix)),
            float(np.min(ratio_matrix))
        ]
    }
    df_summary = pd.DataFrame(summary_data)
    
    # 保存为Excel文件
    excel_filename = os.path.join(excel_dir, f'contrail_statistics_{date}.xlsx')
    
    try:
        with pd.ExcelWriter(excel_filename, engine='openpyxl', mode='w') as writer:
            df_count_0.to_excel(writer, sheet_name='背景像素计数(0)')
            df_count_1.to_excel(writer, sheet_name='航迹像素计数(1)')
            df_ratio.to_excel(writer, sheet_name='航迹比例')
            df_summary.to_excel(writer, sheet_name='汇总统计', index=False)
        
        print(f"已保存Excel文件: {excel_filename}")
        print(f"Excel文件包含 {180 * 360} 个网格的数据")
        print(f"有数据的网格数: {np.sum((count_0 + count_1) > 0)}")
        
    except Exception as e:
        print(f"保存Excel文件时出错: {str(e)}")
        print("尝试分别保存各个表格...")
        
        # 如果合并保存失败，尝试分别保存
        base_name = os.path.splitext(excel_filename)[0]
        df_count_0.to_excel(f"{base_name}_背景像素计数.xlsx")
        df_count_1.to_excel(f"{base_name}_航迹像素计数.xlsx")
        df_ratio.to_excel(f"{base_name}_航迹比例.xlsx")
        df_summary.to_excel(f"{base_name}_汇总统计.xlsx", index=False)
    
    print(f"已保存Excel文件: {excel_filename}")
    print(f"Excel文件包含 {180 * 360} 个网格的数据")
    print(f"有数据的网格数: {np.sum((count_0 + count_1) > 0)}")


def get_processing_statistics(output_dir, date):
    """获取处理结果的统计信息"""
    stats = {}
    
    # 检查输出文件是否存在
    ratio_file = os.path.join(output_dir, 'ratio', f'ratio_{date}.tif')
    count_0_file = os.path.join(output_dir, 'count_0', f'count_0_{date}.tif')
    count_1_file = os.path.join(output_dir, 'count_1', f'count_1_{date}.tif')
    
    try:
        if os.path.exists(ratio_file):
            with rasterio.open(ratio_file) as src:
                ratio_data = src.read(1)
                stats['ratio'] = {
                    'min': float(np.min(ratio_data)),
                    'max': float(np.max(ratio_data)),
                    'mean': float(np.mean(ratio_data[ratio_data > 0])),
                    'non_zero_pixels': int(np.sum(ratio_data > 0))
                }
        
        if os.path.exists(count_0_file):
            with rasterio.open(count_0_file) as src:
                count_0_data = src.read(1)
                stats['count_0'] = {
                    'total': int(np.sum(count_0_data)),
                    'non_zero_pixels': int(np.sum(count_0_data > 0))
                }
        
        if os.path.exists(count_1_file):
            with rasterio.open(count_1_file) as src:
                count_1_data = src.read(1)
                stats['count_1'] = {
                    'total': int(np.sum(count_1_data)),
                    'non_zero_pixels': int(np.sum(count_1_data > 0))
                }
                
    except Exception as e:
        print(f"获取统计信息时出错: {str(e)}")
    
    return stats
