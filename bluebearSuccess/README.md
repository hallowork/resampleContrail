# Contrail数据处理项目

## 项目概述
本项目用于处理MODIS卫星数据，包括MOD03地理定位文件和RGB图像，进行航迹检测和统计分析。

## 文件结构
- `contrail_processor.py` - 核心数据处理模块
- `process_single_date.py` - 单日期处理脚本（用于Slurm任务）
- `submit_contrail_processing.sh` - Slurm提交脚本
- `batch_submit.sh` - 批量提交脚本
- `requirements.txt` - Python依赖包列表

## 参数设置

### Excel保存控制
Excel文件的保存可以通过以下方式控制：

#### 1. 批量提交脚本 (`batch_submit.sh`)
在文件开头设置：
```bash
# 设置Excel保存选项 (true/false)
SAVE_EXCEL=false  # 修改这里来控制是否保存Excel文件
```

#### 2. 单个Slurm任务脚本 (`submit_contrail_processing.sh`)
该脚本会自动从批量提交脚本接收Excel保存参数，无需手动修改。

#### 3. 本地测试 (`process_single_date.py`)
使用命令行参数：
```bash
# 启用Excel保存
python process_single_date.py --year 2013 --doy 1 --save-excel

# 禁用Excel保存（默认）
python process_single_date.py --year 2013 --doy 1
```

### 其他重要参数
在 `submit_contrail_processing.sh` 中可以设置：
- `MOD03_DIR` - MOD03数据目录路径
- `RGB_DIR` - RGB图像目录路径  
- `OUTPUT_DIR` - 输出目录路径
- `--mem-per-cpu=8G` - 每个CPU核心内存分配
- `--time=4:00:00` - 最大运行时间

## 使用方法

### 本地测试
```bash
# 激活conda环境
conda activate wchShap

# 处理单个日期
python process_single_date.py --year 2013 --doy 1 --save-excel
```

### Slurm集群提交
```bash
# 批量提交多年份任务
bash batch_submit.sh

# 或提交单个年份
sbatch --array=0-364 submit_contrail_processing.sh 2013 true
```

## 输出文件
- `output/count_0/` - 背景像素计数GeoTIFF文件
- `output/count_1/` - 航迹像素计数GeoTIFF文件  
- `output/ratio/` - 航迹比例GeoTIFF文件
- `output/excel/` - Excel统计文件（如果启用）
- `output/logs/` - 处理日志文件

## 注意事项
1. 确保数据路径正确设置
2. Excel文件较大，建议仅在需要时启用
3. 处理大量数据时注意内存使用
4. 日志文件会记录详细的处理信息
