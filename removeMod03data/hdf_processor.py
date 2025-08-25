import os
import glob
import h5py
import numpy as np
import multiprocessing as mp
from datetime import datetime
import logging
import shutil
import tempfile
try:
    from pyhdf.SD import SD, SDC
    HDF4_AVAILABLE = True
except ImportError:
    HDF4_AVAILABLE = False


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


def get_file_size_mb(file_path):
    """获取文件大小（MB）"""
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except:
        return 0


def process_single_hdf(hdf_file_path):
    """处理单个HDF文件，只保留经纬度数据"""
    try:
        # 获取原始文件大小
        original_size = get_file_size_mb(hdf_file_path)
        
        # 尝试HDF5格式
        try:
            with h5py.File(hdf_file_path, 'r') as src_file:
                # 检查是否有经纬度数据
                has_lat = 'Latitude' in src_file
                has_lon = 'Longitude' in src_file
                
                if not has_lat and not has_lon:
                    return {
                        'file': os.path.basename(hdf_file_path),
                        'success': False,
                        'error': '未找到Latitude或Longitude数据',
                        'original_size': original_size,
                        'new_size': 0,
                        'efficiency': 0
                    }
                
                # 创建临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.hdf')
                temp_file_path = temp_file.name
                temp_file.close()
                
                # 创建新的HDF文件
                with h5py.File(temp_file_path, 'w') as dst_file:
                    # 复制经纬度数据
                    if has_lat:
                        src_file.copy('Latitude', dst_file)
                    if has_lon:
                        src_file.copy('Longitude', dst_file)
                
                # 获取新文件大小
                new_size = get_file_size_mb(temp_file_path)
                
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
                
        except Exception as h5_error:
            # 如果HDF5失败，尝试HDF4格式
            if not HDF4_AVAILABLE:
                return {
                    'file': os.path.basename(hdf_file_path),
                    'success': False,
                    'error': f'HDF5格式错误: {str(h5_error)}，且未安装pyhdf支持HDF4',
                    'original_size': original_size,
                    'new_size': 0,
                    'efficiency': 0
                }
            
            try:
                # 读取HDF4文件
                hdf4_file = SD(hdf_file_path, SDC.READ)
                
                # 检查是否有经纬度数据
                datasets = hdf4_file.datasets()
                has_lat = 'Latitude' in datasets
                has_lon = 'Longitude' in datasets
                
                if not has_lat and not has_lon:
                    hdf4_file.end()
                    return {
                        'file': os.path.basename(hdf_file_path),
                        'success': False,
                        'error': '未找到Latitude或Longitude数据',
                        'original_size': original_size,
                        'new_size': 0,
                        'efficiency': 0
                    }
                
                # 只处理能找到的数据
                processed_datasets = []
                
                # 创建临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.hdf')
                temp_file_path = temp_file.name
                temp_file.close()
                
                # 创建新的HDF4文件
                new_hdf4_file = SD(temp_file_path, SDC.WRITE | SDC.CREATE)
                
                # 复制经纬度数据
                if has_lat:
                    try:
                        lat_data = hdf4_file.select('Latitude')
                        lat_array = lat_data.get()
                        lat_info = lat_data.info()
                        
                        # 创建新的数据集
                        new_lat = new_hdf4_file.create('Latitude', SDC.FLOAT32, lat_info[1:])
                        new_lat.set(lat_array)
                        new_lat.end()
                        lat_data.end()
                        processed_datasets.append('Latitude')
                    except Exception as lat_error:
                        print(f"处理Latitude数据时出错: {lat_error}")
                
                if has_lon:
                    try:
                        lon_data = hdf4_file.select('Longitude')
                        lon_array = lon_data.get()
                        lon_info = lon_data.info()
                        
                        # 创建新的数据集
                        new_lon = new_hdf4_file.create('Longitude', SDC.FLOAT32, lon_info[1:])
                        new_lon.set(lon_array)
                        new_lon.end()
                        lon_data.end()
                        processed_datasets.append('Longitude')
                    except Exception as lon_error:
                        print(f"处理Longitude数据时出错: {lon_error}")
                
                # 检查是否成功处理了至少一个数据集
                if not processed_datasets:
                    try:
                        hdf4_file.end()
                    except:
                        pass
                    try:
                        new_hdf4_file.end()
                    except:
                        pass
                    os.unlink(temp_file_path)
                    return {
                        'file': os.path.basename(hdf_file_path),
                        'success': False,
                        'error': '无法处理任何经纬度数据',
                        'original_size': original_size,
                        'new_size': 0,
                        'efficiency': 0
                    }
                
                # 安全关闭文件
                try:
                    hdf4_file.end()
                except:
                    pass  # 忽略关闭错误
                
                try:
                    new_hdf4_file.end()
                except:
                    pass  # 忽略关闭错误
                
                # 获取新文件大小
                new_size = get_file_size_mb(temp_file_path)
                
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
                
            except Exception as h4_error:
                return {
                    'file': os.path.basename(hdf_file_path),
                    'success': False,
                    'error': f'HDF4格式错误: {str(h4_error)}',
                    'original_size': original_size,
                    'new_size': 0,
                    'efficiency': 0
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


def batch_process_hdf_files(input_folder, workers=5):
    """批量处理HDF文件"""
    logger = logging.getLogger(__name__)
    
    # 查找所有HDF文件
    hdf_files = []
    for ext in ['*.hdf', '*.HDF', '*.h5', '*.H5']:
        hdf_files.extend(glob.glob(os.path.join(input_folder, ext)))
    
    if not hdf_files:
        logger.warning(f"在 {input_folder} 中未找到HDF文件")
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
    INPUT_FOLDER = r"C:\Users\wuch\Documents"
    WORKERS = 5  # 默认5个worker
    
    # 设置日志
    log_file = os.path.join(os.path.dirname(__file__), "log.txt")
    logger = setup_logging(log_file)
    
    logger.info("=" * 60)
    logger.info("开始HDF文件瘦身处理")
    logger.info("=" * 60)
    logger.info(f"输入文件夹: {INPUT_FOLDER}")
    logger.info(f"Worker数量: {WORKERS}")
    logger.info(f"处理策略: 只保留'Latitude'和'Longitude'数据")
    
    # 检查输入文件夹
    if not os.path.exists(INPUT_FOLDER):
        logger.error(f"输入文件夹不存在: {INPUT_FOLDER}")
        return
    
    # 开始处理
    start_time = datetime.now()
    results = batch_process_hdf_files(INPUT_FOLDER, WORKERS)
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
    
    if results['failed_files'] > 0:
        logger.warning(f"有 {results['failed_files']} 个文件处理失败，请检查日志")
    
    logger.info(f"详细日志已保存到: {log_file}")


if __name__ == "__main__":
    main()
