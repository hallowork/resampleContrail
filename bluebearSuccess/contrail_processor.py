"""
MOD03和RGB图像处理模块
用于处理卫星数据，进行二值化和经纬度统计
"""

import os
import glob
import gc
import numpy as np
from PIL import Image
import h5py
from pyhdf.SD import SD, SDC
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS
from pathlib import Path
import pandas as pd
import logging
import psutil
import multiprocessing as mp
from functools import partial
import time


def process_single_file_pair(args):
    """
    处理单个RGB和MOD03文件对
    这个函数将被多个worker并行调用
    """
    rgb_file, mod03_dir, threshold, resolution = args
    
    try:
        # 1. 找到对应的MOD03文件
        rgb_basename = os.path.basename(rgb_file)
        mod03_file = find_corresponding_mod03(mod03_dir, rgb_file)
        
        if not mod03_file:
            return {
                'count_0': None,
                'count_1': None,
                'file': rgb_basename,
                'success': False,
                'error': f'未找到对应的MOD03文件'
            }
        
        # 2. 处理RGB图像
        rgb_image = Image.open(rgb_file)
        if rgb_image.mode != 'L':
            rgb_image = rgb_image.convert('L')
        
        rgb_array = np.array(rgb_image) / 255.0  # 归一化到0-1
        binary_image = (rgb_array > threshold).astype(np.int32)
        
        # 3. 读取MOD03坐标
        lat_data, lon_data = read_mod03_coordinates(mod03_file)
        if lat_data is None or lon_data is None:
            return {
                'count_0': None,
                'count_1': None,
                'file': rgb_basename,
                'success': False,
                'error': f'无法读取MOD03坐标: {mod03_file}'
            }
            
        # 4. 映射像素到网格
        count_0_local = np.zeros((180, 360), dtype=np.int32)
        count_1_local = np.zeros((180, 360), dtype=np.int32)
        map_pixels_to_grid(binary_image, lat_data, lon_data, count_0_local, count_1_local)
        
        # 清理内存
        del rgb_image, rgb_array, binary_image, lat_data, lon_data
        gc.collect()
        
        return {
            'count_0': count_0_local,
            'count_1': count_1_local,
            'file': rgb_basename,
            'success': True
        }
        
    except Exception as e:
        return {
            'count_0': None,
            'count_1': None,
            'file': os.path.basename(rgb_file),
            'success': False,
            'error': str(e)
        }

def process_contrail_data(mod03_dir, rgb_dir, date, resolution, output_dir, threshold=0.35, output_ratio_only=False, save_excel=False, workers=1):
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
    save_excel: 是否保存Excel文件，默认False
    
    返回:
    成功处理的文件数量
    """
    
    logger = logging.getLogger(f"Worker-{date}")
    logger.info(f"开始处理日期 {date} 的数据")
    print(f"开始处理日期 {date} 的数据...")
    
    # 1. 查找匹配的RGB文件
    try:
        rgb_files = find_rgb_files(rgb_dir, date)
        if not rgb_files:
            warning_msg = f"未找到日期 {date} 的RGB文件"
            logger.warning(warning_msg)
            print(warning_msg)
            return 0
        
        logger.info(f"找到 {len(rgb_files)} 个RGB文件")
        print(f"找到 {len(rgb_files)} 个RGB文件")
        
    except Exception as e:
        error_msg = f"搜索RGB文件时出错: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        return 0
    
    # 2. 初始化统计数组 (180行×360列，对应纬度×经度)
    count_0 = np.zeros((180, 360), dtype=np.int32)  # 背景计数
    count_1 = np.zeros((180, 360), dtype=np.int32)  # 航迹计数
    
    processed_files = 0
    failed_files = []
    
    # 内存监控函数
    def log_memory_usage(stage, logger):
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            logger.debug(f"{stage} - 内存使用: {memory_mb:.1f}MB")
            return memory_mb
        except:
            return 0
    
    logger.info(f"开始处理 {len(rgb_files)} 个文件，使用 {workers} 个worker")
    print(f"开始处理 {len(rgb_files)} 个文件，使用 {workers} 个worker")
    
    # 记录开始时间
    start_time = time.time()
    successful_files = 0
    
    if workers > 1:
        # 多进程并行处理
        logger.info(f"启动 {workers} 个并行worker进行处理")
        print(f"启动 {workers} 个并行worker进行处理")
        
        # 准备并行处理的参数
        process_args = [(rgb_file, mod03_dir, threshold, resolution) for rgb_file in rgb_files]
        
        with mp.Pool(processes=workers) as pool:
            # 提交所有任务并获取结果
            results = pool.map(process_single_file_pair, process_args)
            
        # 汇总所有worker的结果
        for result in results:
            if result is None:
                continue
                
            if result['success']:
                # 累加统计结果到主矩阵
                count_0 += result['count_0']
                count_1 += result['count_1']
                successful_files += 1
                logger.info(f"成功处理文件: {result['file']}")
            else:
                failed_files.append(result['file'])
                logger.error(f"处理失败: {result['file']} - {result.get('error', '未知错误')}")
                
    else:
        # 单进程顺序处理
        logger.info("使用单进程顺序处理")
        print("使用单进程顺序处理")
        
        for i, rgb_file in enumerate(rgb_files, 1):
            try:
                # 处理单个文件对
                args = (rgb_file, mod03_dir, threshold, resolution)
                result = process_single_file_pair(args)
                
                logger.info(f"处理文件 {i}/{len(rgb_files)}: {os.path.basename(rgb_file)}")
                print(f"处理文件 {i}/{len(rgb_files)}: {os.path.basename(rgb_file)}")
                
                if result['success']:
                    count_0 += result['count_0']
                    count_1 += result['count_1']
                    successful_files += 1
                    logger.info(f"成功处理文件: {result['file']}")
                else:
                    failed_files.append(result['file'])
                    logger.error(f"处理失败: {result['file']} - {result.get('error', '未知错误')}")
            except Exception as e:
                error_msg = f"处理文件 {rgb_file} 时发生未预期错误: {str(e)}"
                logger.error(error_msg)
                print(error_msg)
                failed_files.append(os.path.basename(rgb_file))
                continue
    
    # 记录处理统计
    end_time = time.time()
    processing_time = end_time - start_time
    logger.info(f"并行处理完成，耗时 {processing_time:.2f} 秒")
    print(f"并行处理完成，耗时 {processing_time:.2f} 秒")
    
    processed_files = successful_files
    
    # 记录处理结果统计
    if failed_files:
        logger.warning(f"处理失败的文件 ({len(failed_files)}个): {', '.join(failed_files)}")
    
    if processed_files == 0:
        warning_msg = "没有成功处理任何文件"
        logger.warning(warning_msg)
        print(warning_msg)
        return 0
    
    logger.info(f"成功处理 {processed_files} 个文件，失败 {len(failed_files)} 个文件")
    
    try:
        # 7. 计算比例矩阵
        total_count = count_0 + count_1
        ratio_matrix = np.zeros_like(total_count, dtype=np.float32)
        mask = total_count > 0
        ratio_matrix[mask] = count_1[mask] / total_count[mask]
        logger.info("成功计算比例矩阵")
        
        # 8. 保存结果
        save_results(output_dir, count_0, count_1, ratio_matrix, date, output_ratio_only, save_excel)
        logger.info(f"成功保存处理结果到: {output_dir}")
        
    except Exception as e:
        error_msg = f"保存结果时出错: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        return 0
    
    print(f"成功处理 {processed_files} 个文件")
    return processed_files


def find_rgb_files(rgb_dir, date):
    """查找指定日期的RGB文件
    
    参数:
        rgb_dir: RGB文件目录
        date: 日期字符串，格式为YYYYDDD，例如2013001
        
    文件名格式：MOD021KM.AYYYYDDD.HHMM.VVV.YYYYDDDHHMMSS_RGB_denoised.png
    """
    # 使用严格的位置匹配
    pattern = os.path.join(rgb_dir, f"MOD021KM.A{date}.[0-9][0-9][0-9][0-9].[0-9][0-9][0-9].*_RGB*.png")
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
    logger = logging.getLogger("read_mod03")
    
    try:
        # 检查文件是否存在
        if not os.path.exists(mod03_file):
            error_msg = f"MOD03文件不存在: {mod03_file}"
            logger.error(error_msg)
            print(error_msg)
            return None, None
        
        # 尝试使用pyhdf读取HDF4文件
        try:
            hdf = SD(mod03_file, SDC.READ)
        except Exception as e:
            error_msg = f"读取MOD03文件 {mod03_file}  失败: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            return None, None
        
        try:
            # 读取纬度和经度数据
            lat_dataset = hdf.select('Latitude')
            lon_dataset = hdf.select('Longitude')
            
            lat_data = lat_dataset.get()
            lon_data = lon_dataset.get()
            
            # 检查数据有效性
            if lat_data is None or lon_data is None:
                error_msg = f"MOD03文件 {mod03_file} 中的经纬度数据为空"
                logger.error(error_msg)
                print(error_msg)
                hdf.end()
                return None, None
            
            # 检查数据形状
            if lat_data.shape != lon_data.shape:
                error_msg = f"MOD03文件 {mod03_file} 中经纬度数据形状不匹配: lat{lat_data.shape} vs lon{lon_data.shape}"
                logger.error(error_msg)
                print(error_msg)
                hdf.end()
                return None, None
            
            logger.debug(f"成功读取MOD03经纬度数据，形状: {lat_data.shape}")
            hdf.end()
            return lat_data, lon_data
            
        except Exception as e:
            error_msg = f"读取MOD03文件 {mod03_file} 的经纬度数据时出错: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            try:
                hdf.end()
            except:
                pass
            return None, None
        
    except Exception as e:
        error_msg = f"读取MOD03文件 {mod03_file} 时发生未预期错误: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
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


def save_results(output_dir, count_0, count_1, ratio_matrix, date, output_ratio_only, save_excel=False):
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
        
        # 保存Excel文件（如果启用）
        if save_excel:
            save_excel_files(count_0, count_1, ratio_matrix, date, excel_dir)
        else:
            print("Excel文件保存已禁用")
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
