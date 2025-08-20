#!/bin/bash

# 检查必要的环境变量是否存在
if [ -z "$WORKERS_PER_TASK" ] || [ -z "$MEM_PER_CPU" ] || [ -z "$TIME_LIMIT" ]; then
    echo "错误: 缺少必要的环境变量设置"
    echo "请先运行 batch_submit.sh 或手动设置以下环境变量:"
    echo "  WORKERS_PER_TASK: 每个任务的worker数量"
    echo "  MEM_PER_CPU: 每个CPU的内存（GB）"
    echo "  TIME_LIMIT: 最大运行时间"
    exit 1
fi

# SBATCH参数通过batch_submit.sh在提交时指定

# 设置参数
YEAR=$1  # 从命令行参数获取年份
SAVE_EXCEL_PARAM=$2  # 从命令行参数获取Excel保存选项

if [ -z "$YEAR" ]; then
    echo "错误: 请提供年份参数"
    echo "用法: sbatch submit_contrail_processing.sh 2013 [true|false]"
    exit 1
fi

# 如果没有提供Excel参数，使用默认值
if [ -z "$SAVE_EXCEL_PARAM" ]; then
    SAVE_EXCEL_PARAM=false
fi

# 检查年份是否为闰年
if [ $((YEAR % 4)) -eq 0 ] && { [ $((YEAR % 100)) -ne 0 ] || [ $((YEAR % 400)) -eq 0 ]; }; then
    MAX_DOY=366  # 闰年
else
    MAX_DOY=365  # 平年
fi

# 检查任务ID是否超出范围
if [ $SLURM_ARRAY_TASK_ID -ge $MAX_DOY ]; then
    echo "任务ID $SLURM_ARRAY_TASK_ID 超出年份 $YEAR 的范围 (最大: $((MAX_DOY-1)))"
    exit 0  # 正常退出，不算作失败
fi

# 计算当前任务的DOY (Day of Year)
DOY=$((SLURM_ARRAY_TASK_ID + 1))  # SLURM_ARRAY_TASK_ID从0开始，DOY从1开始

# 生成日期字符串
DATE=$(printf "%04d%03d" $YEAR $DOY)

echo "=========================================="
echo "Slurm任务信息:"
echo "  任务ID: $SLURM_ARRAY_TASK_ID"
echo "  作业ID: $SLURM_ARRAY_JOB_ID"
echo "  年份: $YEAR"
echo "  DOY: $DOY"
echo "  日期: $DATE"
echo "  节点: $SLURMD_NODENAME"
echo "  CPU核心数: $SLURM_CPUS_PER_TASK"
echo "  内存: ${SLURM_MEM_PER_CPU}MB per CPU"
echo "=========================================="

# 创建必要的目录
mkdir -p logs
mkdir -p output/logs
mkdir -p output/count_0
mkdir -p output/count_1
mkdir -p output/ratio
mkdir -p output/excel

# 加载Python环境 (根据集群环境调整)
# module load python/3.8

# 激活conda环境
source ~/.bashrc
conda activate wchsShap

# 检查Python环境
echo "检查Python环境..."
python --version
echo "检查已安装的包..."
pip list | grep -E "(numpy|Pillow|h5py|pyhdf|rasterio|scipy)"

# 检查数据处理参数是否存在
if [ -z "$RESOLUTION" ] || [ -z "$THRESHOLD" ] || [ -z "$OUTPUT_RATIO_ONLY" ]; then
    echo "错误: 缺少数据处理参数"
    echo "请先运行 batch_submit.sh 或手动设置以下环境变量:"
    echo "  RESOLUTION: 分辨率（度）"
    echo "  THRESHOLD: 二值化阈值"
    echo "  OUTPUT_RATIO_ONLY: 是否只输出比例"
    exit 1
fi

# 检查路径设置是否存在
if [ -z "$MOD03_DIR" ] || [ -z "$RGB_DIR" ] || [ -z "$OUTPUT_DIR" ]; then
    echo "错误: 缺少路径设置"
    echo "请先运行 batch_submit.sh 或手动设置以下环境变量:"
    echo "  MOD03_DIR: MOD03数据目录"
    echo "  RGB_DIR: RGB数据目录"
    echo "  OUTPUT_DIR: 输出目录"
    exit 1
fi

# 设置Python路径 (根据实际情况调整)
PYTHON_EXE="python"

# 执行Python脚本
echo "开始处理日期: $DATE"
echo "参数设置:"
echo "  分辨率: $RESOLUTION"
echo "  阈值: $THRESHOLD"
echo "  Excel保存: $SAVE_EXCEL_PARAM"
echo "  只输出比例: $OUTPUT_RATIO_ONLY"
echo "  Worker数量: $WORKERS_PER_TASK"

$PYTHON_EXE process_single_date.py \
    --date $DATE \
    --resolution $RESOLUTION \
    --threshold $THRESHOLD \
    --workers $WORKERS_PER_TASK \
    $([ "$SAVE_EXCEL_PARAM" = "true" ] && echo "--save-excel") \
    $([ "$OUTPUT_RATIO_ONLY" = "true" ] && echo "--output-ratio-only")

# 检查执行结果
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "任务 $SLURM_ARRAY_TASK_ID (日期 $DATE) 成功完成"
else
    echo "任务 $SLURM_ARRAY_TASK_ID (日期 $DATE) 执行失败，退出代码: $EXIT_CODE"
fi

exit $EXIT_CODE
