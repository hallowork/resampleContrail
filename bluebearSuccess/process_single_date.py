"""
单日期处理脚本 - 用于Slurm任务数组
每个任务处理一个日期的所有数据
"""

import os
import sys
import time
import logging
import argparse
import gc
import psutil
from datetime import datetime, timedelta
from contrail_processor import process_contrail_data

# ============= 配置参数 =============
# 从环境变量获取配置，如果没有则使用默认值
MOD03_DIR = os.environ.get('MOD03_DIR', r"C:\researchWorkPlace\pythonProject\dataExample\mod03")
RGB_DIR = os.environ.get('RGB_DIR', r"C:\researchWorkPlace\pythonProject\dataExample\rgb")
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', r"C:\researchWorkPlace\pythonProject\output")

# 处理参数配置
RESOLUTION = int(os.environ.get('RESOLUTION', 1))        # 分辨率(度)
THRESHOLD = float(os.environ.get('THRESHOLD', 0.35))     # 二值化阈值
SAVE_EXCEL = os.environ.get('SAVE_EXCEL', 'false').lower() == 'true'  # 是否保存Excel文件
OUTPUT_RATIO_ONLY = os.environ.get('OUTPUT_RATIO_ONLY', 'false').lower() == 'true'  # 是否只输出比例
WORKERS_PER_TASK = int(os.environ.get('WORKERS_PER_TASK', 4))  # 每个任务的worker数量
# ===================================

def setup_logging(date):
    """设置单个任务的日志记录"""
    # 创建logs目录（在当前工作目录下）
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # 设置日志文件名（按日期）
    log_file = os.path.join(log_dir, f"contrail_{date}.log")
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"日志文件创建: {log_file}")
    return logger

def get_memory_usage():
    """获取当前内存使用情况"""
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        'rss': memory_info.rss / 1024 / 1024,  # MB
        'vms': memory_info.vms / 1024 / 1024,  # MB
        'percent': process.memory_percent()
    }

def parse_slurm_env():
    """解析Slurm环境变量或命令行参数"""
    parser = argparse.ArgumentParser(description='处理单个日期的contrail数据')
    
    # 日期参数
    parser.add_argument('--year', type=int, help='年份')
    parser.add_argument('--doy', type=int, help='一年中的第几天 (1-365/366)')
    parser.add_argument('--date', type=str, help='日期字符串 (YYYYDDD格式)')
    parser.add_argument('--task-id', type=int, help='任务ID (用于模拟SLURM_ARRAY_TASK_ID)')
    
    # 数据处理参数
    parser.add_argument('--resolution', type=int, help='分辨率（度）')
    parser.add_argument('--threshold', type=float, help='二值化阈值')
    parser.add_argument('--save-excel', action='store_true', help='是否保存Excel文件')
    parser.add_argument('--output-ratio-only', action='store_true', help='是否只输出比例')
    parser.add_argument('--workers', type=int, help='并行处理的worker数量')
    
    # 路径参数
    parser.add_argument('--mod03-dir', type=str, help='MOD03数据目录')
    parser.add_argument('--rgb-dir', type=str, help='RGB数据目录')
    parser.add_argument('--output-dir', type=str, help='输出目录')
    
    args = parser.parse_args()
    
    # 优先级：命令行参数 > 环境变量
    if args.date:
        date = args.date
    elif args.year and args.doy:
        date = f"{args.year}{args.doy:03d}"
    else:
        # 尝试从环境变量获取（模拟Slurm）
        task_id = args.task_id or os.environ.get('SLURM_ARRAY_TASK_ID')
        year = args.year or os.environ.get('PROCESS_YEAR', '2013')
        
        if task_id is not None:
            # 将task_id转换为DOY (从0开始计算，所以+1)
            doy = int(task_id) + 1
            date = f"{year}{doy:03d}"
        else:
            print("错误：无法确定要处理的日期")
            print("请使用 --date YYYYDDD 或 --year YYYY --doy DDD")
            sys.exit(1)
    
    # 更新全局配置
    global RESOLUTION, THRESHOLD, SAVE_EXCEL, OUTPUT_RATIO_ONLY, WORKERS_PER_TASK
    global MOD03_DIR, RGB_DIR, OUTPUT_DIR
    
    # 命令行参数优先于环境变量
    if args.resolution is not None:
        RESOLUTION = args.resolution
    if args.threshold is not None:
        THRESHOLD = args.threshold
    if args.save_excel:
        SAVE_EXCEL = True
    if args.output_ratio_only:
        OUTPUT_RATIO_ONLY = True
    if args.workers is not None:
        WORKERS_PER_TASK = args.workers
    
    # 更新路径
    if args.mod03_dir:
        MOD03_DIR = args.mod03_dir
    if args.rgb_dir:
        RGB_DIR = args.rgb_dir
    if args.output_dir:
        OUTPUT_DIR = args.output_dir
    
    # 返回日期和所有配置参数
    return {
        'date': date,
        'resolution': RESOLUTION,
        'threshold': THRESHOLD,
        'save_excel': SAVE_EXCEL,
        'output_ratio_only': OUTPUT_RATIO_ONLY,
        'workers': WORKERS_PER_TASK,
        'mod03_dir': MOD03_DIR,
        'rgb_dir': RGB_DIR,
        'output_dir': OUTPUT_DIR
    }

def main():
    """主函数 - 处理单个日期"""
    # 解析日期和参数
    config = parse_slurm_env()
    date = config['date']  # 提取日期到局部变量
    
    # 设置日志
    logger = setup_logging(date)
    
    print(f"开始处理日期: {config['date']}")
    logger.info("=" * 50)
    logger.info(f"单日期处理任务启动 - 日期: {config['date']}")
    logger.info(f"MOD03目录: {config['mod03_dir']}")
    logger.info(f"RGB目录: {config['rgb_dir']}")
    logger.info(f"输出目录: {config['output_dir']}")
    logger.info(f"分辨率: {config['resolution']}")
    logger.info(f"阈值: {config['threshold']}")
    logger.info(f"保存Excel: {config['save_excel']}")
    logger.info(f"只输出比例: {config['output_ratio_only']}")
    logger.info(f"Worker数量: {config['workers']}")
    
    # 记录初始内存使用
    initial_memory = get_memory_usage()
    logger.info(f"初始内存使用: {initial_memory['rss']:.1f}MB ({initial_memory['percent']:.1f}%)")
    
    start_time = time.time()
    
    try:
        # 处理数据
        result = process_contrail_data(
            mod03_dir=config['mod03_dir'],
            rgb_dir=config['rgb_dir'],
            date=config['date'],
            resolution=config['resolution'],
            output_dir=config['output_dir'],
            threshold=config['threshold'],
            output_ratio_only=config['output_ratio_only'],
            save_excel=config['save_excel'],
            workers=config['workers']
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 记录最终内存使用
        final_memory = get_memory_usage()
        logger.info(f"最终内存使用: {final_memory['rss']:.1f}MB ({final_memory['percent']:.1f}%)")
        logger.info(f"内存增长: {final_memory['rss'] - initial_memory['rss']:.1f}MB")
        
        if result > 0:
            success_msg = f"日期 {date} 处理成功! 处理了 {result} 个文件，耗时 {processing_time:.2f} 秒"
            logger.info(success_msg)
            print(success_msg)
            
            # 输出统计信息
            print(f"内存使用统计:")
            print(f"  初始内存: {initial_memory['rss']:.1f}MB")
            print(f"  最终内存: {final_memory['rss']:.1f}MB")
            print(f"  内存增长: {final_memory['rss'] - initial_memory['rss']:.1f}MB")
            
            sys.exit(0)  # 成功退出
        else:
            warning_msg = f"日期 {date} 没有找到可处理的文件"
            logger.warning(warning_msg)
            print(warning_msg)
            sys.exit(1)  # 失败退出
            
    except Exception as e:
        error_msg = f"处理日期 {date} 时出错: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        
        # 记录错误时的内存使用
        error_memory = get_memory_usage()
        logger.error(f"错误时内存使用: {error_memory['rss']:.1f}MB ({error_memory['percent']:.1f}%)")
        
        sys.exit(1)  # 错误退出
    
    finally:
        # 强制垃圾回收
        gc.collect()
        logger.info("任务完成，进行垃圾回收")

if __name__ == '__main__':
    main()
