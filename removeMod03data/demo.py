#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HDF文件瘦身处理演示程序
使用模拟数据展示功能
"""

import os
import tempfile
import shutil
import numpy as np
import h5py
from datetime import datetime
import logging


def setup_logging(log_file_path):
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def create_demo_hdf_files(demo_folder, num_files=5):
    """创建演示HDF文件"""
    if not os.path.exists(demo_folder):
        os.makedirs(demo_folder)
    
    logger = logging.getLogger(__name__)
    logger.info(f"创建 {num_files} 个演示HDF文件...")
    
    for i in range(num_files):
        # 创建文件名
        filename = f"demo_file_{i+1:03d}.hdf"
        file_path = os.path.join(demo_folder, filename)
        
        # 创建HDF5文件
        with h5py.File(file_path, 'w') as f:
            # 创建经纬度数据
            lat_data = np.random.uniform(-90, 90, (1000, 1000)).astype(np.float32)
            lon_data = np.random.uniform(-180, 180, (1000, 1000)).astype(np.float32)
            
            # 添加经纬度数据
            f.create_dataset('Latitude', data=lat_data)
            f.create_dataset('Longitude', data=lon_data)
            
            # 添加其他模拟数据（这些将被删除）
            f.create_dataset('Temperature', data=np.random.uniform(200, 300, (1000, 1000)))
            f.create_dataset('Pressure', data=np.random.uniform(800, 1200, (1000, 1000)))
            f.create_dataset('Humidity', data=np.random.uniform(0, 100, (1000, 1000)))
            f.create_dataset('CloudCover', data=np.random.uniform(0, 1, (1000, 1000)))
            
            # 添加一些元数据
            f.attrs['Description'] = f'演示文件 {i+1}'
            f.attrs['Created'] = datetime.now().isoformat()
        
        logger.info(f"创建文件: {filename}")
    
    logger.info("演示文件创建完成")


def process_single_hdf_demo(hdf_file_path):
    """处理单个HDF文件（演示版本）"""
    try:
        # 获取原始文件大小
        original_size = os.path.getsize(hdf_file_path) / (1024 * 1024)
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.hdf')
        temp_file_path = temp_file.name
        temp_file.close()
        
        # 读取原始HDF文件
        with h5py.File(hdf_file_path, 'r') as src_file:
            # 创建新的HDF文件
            with h5py.File(temp_file_path, 'w') as dst_file:
                # 复制经纬度数据
                if 'Latitude' in src_file:
                    src_file.copy('Latitude', dst_file)
                if 'Longitude' in src_file:
                    src_file.copy('Longitude', dst_file)
        
        # 获取新文件大小
        new_size = os.path.getsize(temp_file_path) / (1024 * 1024)
        
        # 替换原文件
        shutil.move(temp_file_path, hdf_file_path)
        
        # 计算瘦身效率
        if original_size > 0:
            efficiency = ((original_size - new_size) / original_size) * 100
        else:
            efficiency = 0
            
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
            'original_size': os.path.getsize(hdf_file_path) / (1024 * 1024),
            'new_size': 0,
            'efficiency': 0
        }


def batch_process_demo(demo_folder, workers=5):
    """批量处理演示HDF文件"""
    logger = logging.getLogger(__name__)
    
    # 查找所有HDF文件
    import glob
    hdf_files = glob.glob(os.path.join(demo_folder, "*.hdf"))
    
    if not hdf_files:
        logger.warning(f"在 {demo_folder} 中未找到HDF文件")
        return {
            'total_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'original_total_size': 0,
            'new_total_size': 0,
            'overall_efficiency': 0
        }
    
    logger.info(f"找到 {len(hdf_files)} 个HDF文件")
    logger.info(f"使用 {workers} 个worker进行并行处理")
    
    # 串行处理（演示用）
    results = []
    for hdf_file in hdf_files:
        result = process_single_hdf_demo(hdf_file)
        results.append(result)
    
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
            original_total_size += result['original_size']
            logger.error(f"❌ 处理失败: {result['file']} - {result['error']}")
    
    # 计算总体效率
    if original_total_size > 0:
        overall_efficiency = ((original_total_size - new_total_size) / original_total_size) * 100
    else:
        overall_efficiency = 0
    
    return {
        'total_files': len(hdf_files),
        'successful_files': successful_files,
        'failed_files': failed_files,
        'original_total_size': original_total_size,
        'new_total_size': new_total_size,
        'overall_efficiency': overall_efficiency
    }


def main():
    """主函数"""
    # 配置参数
    DEMO_FOLDER = os.path.join(os.path.dirname(__file__), "demo_files")
    WORKERS = 5
    
    # 设置日志
    log_file = os.path.join(os.path.dirname(__file__), "demo_log.txt")
    logger = setup_logging(log_file)
    
    logger.info("=" * 60)
    logger.info("HDF文件瘦身处理演示程序")
    logger.info("=" * 60)
    logger.info(f"演示文件夹: {DEMO_FOLDER}")
    logger.info(f"Worker数量: {WORKERS}")
    logger.info(f"处理策略: 只保留'Latitude'和'Longitude'数据")
    logger.info("=" * 60)
    
    # 创建演示文件
    create_demo_hdf_files(DEMO_FOLDER, 5)
    
    # 开始处理
    start_time = datetime.now()
    results = batch_process_demo(DEMO_FOLDER, WORKERS)
    end_time = datetime.now()
    
    # 输出最终结果
    logger.info("=" * 60)
    logger.info("处理完成！")
    logger.info("=" * 60)
    logger.info(f"总文件数: {results['total_files']}")
    logger.info(f"成功处理: {results['successful_files']} 个文件")
    logger.info(f"处理失败: {results['failed_files']} 个文件")
    logger.info(f"原始总大小: {results['original_total_size']:.2f} MB")
    logger.info(f"缩减后总大小: {results['new_total_size']:.2f} MB")
    logger.info(f"总体瘦身效率: {results['overall_efficiency']:.1f}%")
    logger.info(f"处理时间: {end_time - start_time}")
    
    # 在控制台输出总结
    print("\n" + "=" * 60)
    print("演示处理完成！")
    print("=" * 60)
    print(f"总文件数: {results['total_files']}")
    print(f"成功处理: {results['successful_files']} 个文件")
    print(f"处理失败: {results['failed_files']} 个文件")
    print(f"原始总大小: {results['original_total_size']:.2f} MB")
    print(f"缩减后总大小: {results['new_total_size']:.2f} MB")
    print(f"总体瘦身效率: {results['overall_efficiency']:.1f}%")
    print(f"处理时间: {end_time - start_time}")
    print(f"演示文件位置: {DEMO_FOLDER}")
    print(f"详细日志: {log_file}")


if __name__ == "__main__":
    main()
