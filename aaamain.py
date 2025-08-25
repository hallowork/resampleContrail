#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主程序：调用HDF处理函数
"""

import os
import argparse
from aaaremovemod03data import process_hdf_folder


def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='HDF文件瘦身处理 - 只保留经纬度数据')
    
    # 添加命令行参数
    parser.add_argument('--input', '-i', 
                      default=r"C:\Users\wuch\Documents",
                      help='输入文件夹路径')
    
    parser.add_argument('--output', '-o',
                      default=None,
                      help='输出文件夹路径（可选，默认直接修改原文件）')
    
    parser.add_argument('--workers', '-w',
                      type=int,
                      default=5,
                      help='并行处理的worker数量')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 处理HDF文件
    result = process_hdf_folder(
        input_folder=args.input,
        output_folder=args.output,
        workers=args.workers
    )
    
    if result is None:
        print("处理失败，请检查输入路径是否正确。")
        return
    
    # 打印最终结果
    print("\n最终处理结果：")
    print(f"总文件数: {result['total_files']}")
    print(f"成功处理: {result['successful_files']}")
    print(f"处理失败: {result['failed_files']}")
    print(f"原始总大小: {result['original_total_size']:.2f}MB")
    print(f"处理后总大小: {result['new_total_size']:.2f}MB")
    print(f"总体瘦身效率: {result['overall_efficiency']:.1f}%")


if __name__ == "__main__":
    main()
