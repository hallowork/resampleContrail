#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HDF文件瘦身处理主程序
只保留经纬度数据，删除其他所有参数
"""

import os
import argparse
from hdf_processor import batch_process_hdf_files, setup_logging
from datetime import datetime


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='HDF文件瘦身处理 - 只保留经纬度数据')
    parser.add_argument('--input-folder', '-i', 
                       default=r"C:\Users\wuch\Documents",
                       help='输入文件夹路径 (默认: C:\\Users\\wuch\\Documents)')
    parser.add_argument('--workers', '-w', 
                       type=int, default=5,
                       help='并行处理的worker数量 (默认: 5)')
    parser.add_argument('--log-file', '-l',
                       default='log.txt',
                       help='日志文件名 (默认: log.txt)')
    
    args = parser.parse_args()
    
    # 设置日志
    log_file = os.path.join(os.path.dirname(__file__), args.log_file)
    logger = setup_logging(log_file)
    
    logger.info("=" * 60)
    logger.info("HDF文件瘦身处理程序")
    logger.info("=" * 60)
    logger.info(f"输入文件夹: {args.input_folder}")
    logger.info(f"Worker数量: {args.workers}")
    logger.info(f"日志文件: {log_file}")
    logger.info(f"处理策略: 只保留'Latitude'和'Longitude'数据")
    logger.info("=" * 60)
    
    # 检查输入文件夹
    if not os.path.exists(args.input_folder):
        logger.error(f"输入文件夹不存在: {args.input_folder}")
        return
    
    # 开始处理
    start_time = datetime.now()
    results = batch_process_hdf_files(args.input_folder, args.workers)
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
    
    # 在控制台输出总结
    print("\n" + "=" * 60)
    print("处理完成！")
    print("=" * 60)
    print(f"总文件数: {results['total_files']}")
    print(f"成功处理: {results['successful_files']} 个文件")
    print(f"处理失败: {results['failed_files']} 个文件")
    print(f"原始总大小: {results['original_total_size']:.2f} MB")
    print(f"缩减后总大小: {results['new_total_size']:.2f} MB")
    print(f"总体瘦身效率: {results['overall_efficiency']:.1f}%")
    print(f"处理时间: {end_time - start_time}")
    print(f"详细日志: {log_file}")


if __name__ == "__main__":
    main()
