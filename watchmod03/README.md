# MOD03 HDF文件全球网格统计工具

这个工具用于统计MODIS MOD03 HDF文件中1km栅格在全球1°×1°网格中的分布情况，并生成热图可视化。

## 功能特点

- 读取指定目录下所有MOD03 HDF文件
- 提取经纬度信息并映射到全球1°×1°网格系统
- 统计每个网格中的栅格数量
- 生成线性和对数尺度的热图
- 提供详细的统计信息
- 支持多种输出格式（图像、numpy数组、文本文件）

## 环境要求

### Python版本
- Python 3.7 或更高版本

### 依赖包
```bash
pip install -r requirements.txt
```

主要依赖：
- `numpy`: 数值计算
- `matplotlib`: 绘图
- `pyhdf`: HDF文件读取
- `tqdm`: 进度条显示
- `scipy`: 科学计算（优化版本）

## 安装pyhdf注意事项

`pyhdf`包的安装可能需要额外步骤：

### Windows系统
1. 下载预编译的wheel文件：
   ```bash
   # 从以下网站下载对应版本的wheel文件
   # https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyhdf
   pip install pyhdf-0.10.5-cp39-cp39-win_amd64.whl
   ```

2. 或者使用conda：
   ```bash
   conda install -c conda-forge pyhdf
   ```

### Linux/Mac系统
```bash
# 需要先安装HDF4库
# Ubuntu/Debian:
sudo apt-get install libhdf4-dev

# CentOS/RHEL:
sudo yum install hdf-devel

# 然后安装pyhdf
pip install pyhdf
```

## 使用方法

### 基础版本
```python
python mod03_grid_statistics.py
```

### 优化版本（推荐）
```python
python mod03_grid_statistics_optimized.py
```

## 文件结构

```
contrailmod03Watch/
├── mod03_grid_statistics.py          # 基础版本脚本
├── mod03_grid_statistics_optimized.py # 优化版本脚本
├── requirements.txt                   # 依赖包列表
└── README.md                         # 使用说明
```

## 输出文件

运行后会生成以下文件：

1. **热图图像**
   - `mod03_grid_heatmap.png` (基础版本)
   - `mod03_grid_heatmap_optimized.png` (优化版本)

2. **统计数据**
   - `mod03_grid_statistics.npy` - NumPy数组格式
   - `mod03_grid_statistics_optimized.npy` - 优化版本数组
   - `mod03_grid_statistics_optimized.txt` - 文本格式
   - `mod03_grid_statistics_optimized_metadata.json` - 元数据

## 网格系统说明

- **经度范围**: -180° 到 180° (360列)
- **纬度范围**: -90° 到 90° (180行)
- **网格大小**: 1° × 1°
- **总网格数**: 180 × 360 = 64,800个网格

### 坐标映射规则
- 经度：-180°到180° → 列索引 0到359
- 纬度：90°到-90° → 行索引 0到179 (注意：纬度从北到南)

## 统计信息

程序会输出以下统计信息：
- 总栅格数
- 有数据的网格数量
- 数据覆盖率
- 单个网格的最大栅格数
- 平均栅格数
- 栅格数最多的5个网格位置

## 性能优化

优化版本采用了以下技术：
- 向量化操作替代循环
- 使用`numpy.bincount`进行快速统计
- 稀疏矩阵处理大量零值
- 批量处理减少内存占用

## 常见问题

### 1. 找不到HDF文件
- 检查目录路径是否正确
- 确认文件扩展名为`.hdf`

### 2. 经纬度数据集不存在
- MOD03文件中的经纬度数据集名称可能不同
- 程序会自动尝试常见的名称：`Longitude`, `longitude`, `lon`, `LON`等

### 3. 内存不足
- 使用优化版本，它有更好的内存管理
- 考虑分批处理大量文件

### 4. 显示中文乱码
- 确保系统安装了中文字体（如SimHei、Microsoft YaHei）
- 可以修改代码中的字体设置

## 示例输出

```
在目录 E:\2013007 中找到 24 个HDF文件
处理HDF文件: 100%|██████████| 24/24 [00:15<00:00,  1.52it/s]

处理完成:
成功处理的文件数: 24
总有效像素数: 12,345,678

详细统计结果:
==================================================
总栅格数: 12,345,678
有数据的网格数: 8,456 / 64,800
数据覆盖率: 13.05%
单个网格最大栅格数: 2,345
有数据网格的平均栅格数: 1,460.23
全球网格平均栅格数: 190.52

栅格数最多的5个网格:
排名   纬度     经度     栅格数
-----------------------------------
1     45.5°   120.5°    2,345
2     40.5°   115.5°    2,234
3     35.5°   110.5°    2,123
4     50.5°   125.5°    2,012
5     30.5°   105.5°    1,901

热图已保存为: mod03_grid_heatmap_optimized.png
统计结果已保存:
  - 网格数据: mod03_grid_statistics_optimized.npy
  - 文本格式: mod03_grid_statistics_optimized.txt
  - 元数据: mod03_grid_statistics_optimized_metadata.json
```

## 许可证

此工具仅供学习和研究使用。
