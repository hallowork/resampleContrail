"""
MOD03和RGB图像处理项目主文件
支持多进程并行处理和时间表生成
"""

import os
import time
import calendar
import logging
from datetime import datetime, timedelta
from multiprocessing import Pool, cpu_count
from contrail_processor import process_contrail_data

# ============= 配置参数 =============
# 时间范围配置
START_YEAR = 2013
START_DOY = 1    # Day of Year
END_YEAR = 2013
END_DOY = 4

# 并行处理配置
N_WORKERS = 4    # 并行进程数

# 数据路径配置
MOD03_DIR = r"C:\researchWorkPlace\pythonProject\dataExample\mod03"
RGB_DIR = r"C:\researchWorkPlace\pythonProject\dataExample\rgb"
OUTPUT_DIR = r"C:\researchWorkPlace\pythonProject\output"

# 处理参数配置
RESOLUTION = 1   # 分辨率(度)
THRESHOLD = 0.35 # 二值化阈值
# ===================================

def setup_logging():
    """设置日志记录"""
    # 创建logs目录
    log_dir = os.path.join(OUTPUT_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # 设置日志文件名（包含时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"contrail_processing_{timestamp}.log")
    
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

def generate_date_list(start_year, start_doy, end_year, end_doy):
    """生成时间表"""
    print(f"\n第一步: 生成时间表")
    print(f"时间范围: {start_year}{start_doy:03d} - {end_year}{end_doy:03d}")
    
    date_list = []
    current_date = datetime(start_year, 1, 1) + timedelta(days=start_doy-1)
    end_date = datetime(end_year, 1, 1) + timedelta(days=end_doy-1)
    
    while current_date <= end_date:
        # 获取当年的总天数
        year_days = 366 if calendar.isleap(current_date.year) else 365
        print(f"  处理年份 {current_date.year} (共{year_days}天)")
        
        # 生成日期字符串 (YYYYDDD格式)
        doy = current_date.timetuple().tm_yday
        date_str = f"{current_date.year}{doy:03d}"
        date_list.append(date_str)
        
        # 移动到下一天
        current_date += timedelta(days=1)
    
    print(f"时间表生成完成，共 {len(date_list)} 个日期")
    return date_list

def process_single_date(args):
    """处理单个日期的数据"""
    date, mod03_dir, rgb_dir, output_dir, resolution, threshold = args
    
    # 为每个进程设置单独的logger
    logger = logging.getLogger(f"Worker-{date}")
    
    try:
        logger.info(f"开始处理日期: {date}")
        print(f"开始处理日期: {date}")
        start_time = time.time()
        
        result = process_contrail_data(
            mod03_dir=mod03_dir,
            rgb_dir=rgb_dir,
            date=date,
            resolution=resolution,
            output_dir=output_dir,
            threshold=threshold,
            output_ratio_only=False
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if result > 0:
            success_msg = f"日期 {date} 处理完成! 处理了 {result} 个文件，耗时 {processing_time:.2f} 秒"
            logger.info(success_msg)
            print(success_msg)
        else:
            warning_msg = f"日期 {date} 没有找到可处理的文件"
            logger.warning(warning_msg)
            print(warning_msg)
            
        return date, result, processing_time
        
    except Exception as e:
        error_msg = f"处理日期 {date} 时出错: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        return date, 0, 0

def main():
    """主函数 - 运行contrail处理"""
    print("MOD03和RGB图像处理工具")
    print("=" * 50)
    
    # 设置日志记录
    logger = setup_logging()
    
    print(f"配置信息:")
    print(f"  时间范围: {START_YEAR}{START_DOY:03d} - {END_YEAR}{END_DOY:03d}")
    print(f"  并行进程数: {N_WORKERS}")
    print(f"  MOD03目录: {MOD03_DIR}")
    print(f"  RGB目录: {RGB_DIR}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"  分辨率: {RESOLUTION}")
    print(f"  阈值: {THRESHOLD}")
    
    # 记录配置信息到日志
    logger.info("=" * 50)
    logger.info("MOD03和RGB图像处理工具启动")
    logger.info(f"时间范围: {START_YEAR}{START_DOY:03d} - {END_YEAR}{END_DOY:03d}")
    logger.info(f"并行进程数: {N_WORKERS}")
    logger.info(f"MOD03目录: {MOD03_DIR}")
    logger.info(f"RGB目录: {RGB_DIR}")
    logger.info(f"输出目录: {OUTPUT_DIR}")
    logger.info(f"分辨率: {RESOLUTION}")
    logger.info(f"阈值: {THRESHOLD}")
    
    # 第一步：生成时间表
    logger.info("开始生成时间表")
    date_list = generate_date_list(START_YEAR, START_DOY, END_YEAR, END_DOY)
    logger.info(f"时间表生成完成，共 {len(date_list)} 个日期")
    
    # 第二步：并行处理
    print(f"\n第二步: 并行处理数据")
    print(f"配置启动 {N_WORKERS} 个worker进行并行处理...")
    logger.info("开始并行处理数据")
    logger.info(f"配置启动 {N_WORKERS} 个worker进行并行处理")
    
    # 准备处理参数
    process_args = [
        (date, MOD03_DIR, RGB_DIR, OUTPUT_DIR, RESOLUTION, THRESHOLD)
        for date in date_list
    ]
    
    # 创建进程池并执行处理
    start_time = time.time()
    print(f"正在创建进程池，目标进程数: {N_WORKERS}")
    logger.info(f"正在创建进程池，目标进程数: {N_WORKERS}")
    
    try:
        with Pool(N_WORKERS) as pool:
            print(f"进程池创建成功，实际启动 {pool._processes} 个worker进程")
            print(f"开始并行处理 {len(date_list)} 个日期的数据...")
            logger.info(f"进程池创建成功，实际启动 {pool._processes} 个worker进程")
            logger.info(f"开始并行处理 {len(date_list)} 个日期的数据")
            
            results = pool.map(process_single_date, process_args)
            
            print(f"所有worker进程已完成，正在收集结果...")
            logger.info("所有worker进程已完成，正在收集结果")
        
        end_time = time.time()
        
        # 统计处理结果
        total_files = sum(result[1] for result in results)
        total_time = end_time - start_time
        successful_dates = sum(1 for result in results if result[1] > 0)
        failed_dates = len(date_list) - successful_dates
        
        # 统计失败的日期
        failed_date_list = [result[0] for result in results if result[1] == 0]
        
        print("\n处理完成!")
        print(f"总统计:")
        print(f"  处理日期数: {len(date_list)}")
        print(f"  成功处理日期数: {successful_dates}")
        print(f"  失败处理日期数: {failed_dates}")
        print(f"  处理文件总数: {total_files}")
        print(f"  总耗时: {total_time:.2f} 秒")
        print(f"  平均每个日期耗时: {total_time/len(date_list):.2f} 秒")
        
        # 记录统计结果到日志
        logger.info("=" * 30 + " 处理完成统计 " + "=" * 30)
        logger.info(f"处理日期数: {len(date_list)}")
        logger.info(f"成功处理日期数: {successful_dates}")
        logger.info(f"失败处理日期数: {failed_dates}")
        logger.info(f"处理文件总数: {total_files}")
        logger.info(f"总耗时: {total_time:.2f} 秒")
        logger.info(f"平均每个日期耗时: {total_time/len(date_list):.2f} 秒")
        
        if failed_date_list:
            logger.warning(f"失败的日期列表: {', '.join(failed_date_list)}")
            print(f"  失败的日期: {', '.join(failed_date_list)}")
        
        logger.info("程序执行完成")
        
    except KeyboardInterrupt:
        logger.warning("程序被用户中断 (Ctrl+C)")
        print("\n程序被用户中断")
    except Exception as e:
        logger.error(f"并行处理过程中发生错误: {str(e)}")
        print(f"\n并行处理过程中发生错误: {str(e)}")

if __name__ == '__main__':
    main()
