#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
精简版HDF处理函数
只保留经纬度数据，其他数据删除
"""

import os
import glob
import shutil
import tempfile
import logging
import multiprocessing as mp
from datetime import datetime

try:
    from pyhdf.SD import SD, SDC
    HDF4_AVAILABLE = True
except ImportError:
    HDF4_AVAILABLE = False


def get_file_size_mb(file_path):
    """获取文件大小（MB）"""
    return os.path.getsize(file_path) / (1024 * 1024)


def process_single_hdf(hdf_file_path):
    """处理单个HDF文件，只保留经纬度数据"""
    try:
        # 获取原始文件大小
        original_size = get_file_size_mb(hdf_file_path)
        
        # 打开HDF文件
        hdf = SD(hdf_file_path, SDC.READ)
        datasets = hdf.datasets()
        
        # 检查是否存在经纬度数据
        if 'Latitude' not in datasets or 'Longitude' not in datasets:
            hdf.end()
            return {
                'file': os.path.basename(hdf_file_path),
                'success': False,
                'error': '未找到经纬度数据',
                'original_size': original_size,
                'new_size': 0,
                'efficiency': 0
            }
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.hdf')
        temp_file_path = temp_file.name
        temp_file.close()
        
        # 创建新的HDF文件
        new_hdf = SD(temp_file_path, SDC.WRITE | SDC.CREATE)
        
        # 复制经纬度数据
        for dataset_name in ['Latitude', 'Longitude']:
            try:
                # 读取原始数据
                dataset = hdf.select(dataset_name)
                data = dataset.get()
                info = dataset.info()
                
                # 创建新数据集
                new_dataset = new_hdf.create(dataset_name, SDC.FLOAT32, info[1:])
                new_dataset.set(data)
                
                # 复制属性
                attrs = dataset.attributes()
                for attr_name, attr_value in attrs.items():
                    new_dataset.attr(attr_name).set(SDC.FLOAT32, attr_value)
                
                new_dataset.end()
                dataset.end()
                
            except Exception as e:
                continue
        
        # 安全关闭文件
        try:
            hdf.end()
        except:
            pass
        
        try:
            new_hdf.end()
        except:
            pass
        
        # 获取新文件大小
        new_size = get_file_size_mb(temp_file_path)
        
        # 替换原文件
        shutil.move(temp_file_path, hdf_file_path)
        
        # 计算瘦身效率
        efficiency = ((original_size - new_size) / original_size) * 100 if original_size > 0 else 0
        
        return {
            'file': os.path.basename(hdf_file_path),
            'success': True,
            'original_size': original_size,
            'new_size': new_size,
            'efficiency': efficiency
        }
        
    except Exception as e:
        return {
            'file': os.path.basename(hdf_file_path),
            'success': False,
            'error': str(e),
            'original_size': get_file_size_mb(hdf_file_path),
            'new_size': 0,
            'efficiency': 0
        }


def process_hdf_folder(input_folder, output_folder=None, workers=5):
    """
    处理文件夹中的所有HDF文件
    
    参数:
        input_folder (str): 输入文件夹路径
        output_folder (str): 输出文件夹路径，如果为None则直接修改原文件
        workers (int): 并行处理的worker数量
    
    返回:
        dict: 处理结果统计
    """
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)
    
    # 检查输入文件夹
    if not os.path.exists(input_folder):
        logger.error(f"输入文件夹不存在: {input_folder}")
        return None
    
    # 如果指定了输出文件夹，确保它存在
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
    
    # 查找所有HDF文件
    hdf_files = []
    for ext in ['*.hdf', '*.HDF']:
        hdf_files.extend(glob.glob(os.path.join(input_folder, ext)))
    
    if not hdf_files:
        logger.warning(f"在 {input_folder} 中未找到HDF文件")
        return None
    
    logger.info(f"找到 {len(hdf_files)} 个HDF文件")
    logger.info(f"使用 {workers} 个worker进行并行处理")
    
    # 如果需要输出到不同文件夹，先复制文件
    if output_folder:
        new_hdf_files = []
        for hdf_file in hdf_files:
            new_path = os.path.join(output_folder, os.path.basename(hdf_file))
            shutil.copy2(hdf_file, new_path)
            new_hdf_files.append(new_path)
        hdf_files = new_hdf_files
    
    # 并行处理
    with mp.Pool(processes=workers) as pool:
        results = pool.map(process_single_hdf, hdf_files)
    
    # 统计结果
    successful_files = 0
    failed_files = 0
    original_total_size = 0
    new_total_size = 0
    
    for result in results:
        if result['success']:
            successful_files += 1
            original_total_size += result['original_size']
            new_total_size += result['new_size']
            logger.info(f"✅ 成功处理: {result['file']} "
                       f"(原始: {result['original_size']:.2f}MB, "
                       f"新: {result['new_size']:.2f}MB, "
                       f"效率: {result['efficiency']:.1f}%)")
        else:
            failed_files += 1
            logger.error(f"❌ 处理失败: {result['file']} - {result.get('error', '未知错误')}")
    
    # 计算总体效率
    overall_efficiency = ((original_total_size - new_total_size) / original_total_size * 100
                         if original_total_size > 0 else 0)
    
    # 输出总结
    logger.info("\n" + "=" * 50)
    logger.info("处理完成！总结:")
    logger.info(f"总文件数: {len(hdf_files)}")
    logger.info(f"成功: {successful_files}")
    logger.info(f"失败: {failed_files}")
    logger.info(f"原始总大小: {original_total_size:.2f}MB")
    logger.info(f"处理后总大小: {new_total_size:.2f}MB")
    logger.info(f"总体瘦身效率: {overall_efficiency:.1f}%")
    logger.info("=" * 50)
    
    return {
        'total_files': len(hdf_files),
        'successful_files': successful_files,
        'failed_files': failed_files,
        'original_total_size': original_total_size,
        'new_total_size': new_total_size,
        'overall_efficiency': overall_efficiency
    }
