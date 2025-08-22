import os
import re
from collections import defaultdict
import numpy as np
import rasterio
from pathlib import Path


def get_year_from_filename(filename):
    """从文件名中提取年份"""
    match = re.search(r'ratio_(\d{4})\d{3}\.tif', filename)
    if match:
        return int(match.group(1))
    return None


def process_geotiffs():
    # 输入和输出路径
    input_dir = r"C:\Users\wuch\Desktop\航迹论文\ratio"
    output_dir = os.path.join(input_dir, "yearavg")
    os.makedirs(output_dir, exist_ok=True)

    # 收集文件信息
    files_by_year = defaultdict(list)
    for file in os.listdir(input_dir):
        if file.endswith('.tif'):
            year = get_year_from_filename(file)
            if year and 2013 <= year <= 2022:
                files_by_year[year].append(os.path.join(input_dir, file))

    # 统计信息
    info_content = []

    # 处理每年的文件
    for year in sorted(files_by_year.keys()):
        files = files_by_year[year]
        if not files:
            continue

        # 读取第一个文件获取元数据
        with rasterio.open(files[0]) as src:
            meta = src.meta.copy()
            shape = src.shape

        # 初始化数组存储累积值
        accumulated = np.zeros(shape)
        valid_count = 0

        # 累加所有文件的值
        for file in files:
            with rasterio.open(file) as src:
                data = src.read(1)
                valid_mask = ~np.isnan(data)
                accumulated[valid_mask] += data[valid_mask]
                valid_count += 1

        # 计算平均值
        if valid_count > 0:
            average = accumulated / valid_count

            # 保存年平均GeoTIFF
            output_file = os.path.join(output_dir, f'ratio_{year}_avg.tif')
            try:
                with rasterio.open(output_file, 'w', **meta) as dst:
                    dst.write(average, 1)
            except Exception as e:
                print(f"保存 {output_file} 时出错: {e}")
                # 尝试使用不同的文件名
                output_file = os.path.join(output_dir, f'ratio_{year}_avg_new.tif')
                with rasterio.open(output_file, 'w', **meta) as dst:
                    dst.write(average, 1)
                print(f"已保存为: {output_file}")

            info_content.append(f"{year}年: 使用了{valid_count}个日期的数据")

    # 保存统计信息
    info_file = os.path.join(output_dir, 'processing_info.txt')
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(info_content))


if __name__ == '__main__':
    process_geotiffs()
