#!/bin/bash
# 批量提交多年份的contrail处理任务

#=====================================================
# 全局参数设置
#=====================================================

# 1. 时间范围设置
START_YEAR=2013                    # 开始年份
END_YEAR=2015                     # 结束年份

# 2. 数据处理参数
RESOLUTION=1                      # 分辨率（度）
THRESHOLD=0.35                    # 二值化阈值
SAVE_EXCEL=false                  # 是否保存Excel文件
OUTPUT_RATIO_ONLY=false           # 是否只输出比例（true则不输出count_0和count_1）

# 3. 计算资源设置
WORKERS_PER_TASK=4               # 每个任务的worker数量（与CPU核心数保持一致）
MEM_PER_CPU=8                    # 每个CPU的内存（GB）
TIME_LIMIT="4:00:00"             # 最大运行时间

# 4. 路径设置
MOD03_DIR="/path/to/mod03/data"  # MOD03数据目录
RGB_DIR="/path/to/rgb/data"      # RGB数据目录
OUTPUT_DIR="/path/to/output"     # 输出目录

# 5. 导出所有参数为环境变量（这样子任务可以继承）
export RESOLUTION THRESHOLD SAVE_EXCEL OUTPUT_RATIO_ONLY
export WORKERS_PER_TASK MEM_PER_CPU TIME_LIMIT
export MOD03_DIR RGB_DIR OUTPUT_DIR

echo "=========================================="
echo "批量提交Contrail处理任务"
echo "----------------------------------------"
echo "1. 时间范围设置:"
echo "   开始年份: $START_YEAR"
echo "   结束年份: $END_YEAR"
echo ""
echo "2. 数据处理参数:"
echo "   分辨率: ${RESOLUTION}度"
echo "   阈值: $THRESHOLD"
echo "   Excel保存: $SAVE_EXCEL"
echo "   只输出比例: $OUTPUT_RATIO_ONLY"
echo ""
echo "3. 计算资源设置:"
echo "   Worker数量: $WORKERS_PER_TASK"
echo "   每CPU内存: ${MEM_PER_CPU}GB"
echo "   最大运行时间: $TIME_LIMIT"
echo ""
echo "4. 数据路径:"
echo "   MOD03目录: $MOD03_DIR"
echo "   RGB目录: $RGB_DIR"
echo "   输出目录: $OUTPUT_DIR"
echo "=========================================="

# 为每个年份提交任务
for YEAR in $(seq $START_YEAR $END_YEAR); do
    echo "提交年份 $YEAR 的处理任务..."
    
    # 检查是否为闰年，确定任务数组大小
    if [ $((YEAR % 4)) -eq 0 ] && { [ $((YEAR % 100)) -ne 0 ] || [ $((YEAR % 400)) -eq 0 ]; }; then
        ARRAY_SIZE="0-365"  # 闰年366天
        DAYS=366
    else
        ARRAY_SIZE="0-364"  # 平年365天
        DAYS=365
    fi
    
    # 提交任务
    JOB_ID=$(sbatch --array=$ARRAY_SIZE submit_contrail_processing.sh $YEAR $SAVE_EXCEL | grep -o '[0-9]*')
    
    if [ $? -eq 0 ]; then
        echo "  年份 $YEAR: 任务已提交，作业ID: $JOB_ID，任务数: $DAYS"
    else
        echo "  年份 $YEAR: 任务提交失败"
    fi
    
    # 短暂延迟，避免过快提交
    sleep 2
done

echo "=========================================="
echo "所有任务已提交完成"
echo "使用以下命令监控任务状态:"
echo "  squeue -u \$USER"
echo "  sacct -u \$USER --starttime=today"
echo "=========================================="
