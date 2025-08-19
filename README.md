# MOD03和RGB图像处理工具

这个工具用于处理MODIS卫星数据，包括MOD03文件和RGB图像，进行二值化处理和经纬度统计分析。

## 功能特点

- 自动匹配MOD03和RGB文件
- RGB图像二值化处理
- 将像素数据映射到1度×1度经纬度网格
- 统计每个网格中背景(0)和航迹(1)的数量
- 计算航迹比例
- 输出GeoTIFF格式的结果文件

## 安装依赖

```bash
pip install -r requirements.txt
```

## 文件结构

- `contrail_processor.py` - 主处理模块，包含所有核心函数
- `main.py` - 简单的主文件，用于运行默认处理
- `test_contrail_processor.py` - 测试文件，包含多种测试场景
- `requirements.txt` - 依赖包列表

## 使用方法

### 方法1: 直接运行主文件
```bash
python main.py
```
这将使用默认参数运行处理。

### 方法2: 运行测试文件
```bash
python test_contrail_processor.py
```
这将运行完整的测试套件，包括不同参数的测试。

### 方法3: 导入模块使用

```python
from contrail_processor import process_contrail_data

# 设置参数
mod03_dir = r"C:\path\to\mod03"  # MOD03文件目录
rgb_dir = r"C:\path\to\rgb"      # RGB图像目录
date = "2013001"                 # 日期
resolution = 1                   # 分辨率(1度×1度)
output_dir = r"C:\path\to\output" # 输出目录
threshold = 0.35                 # 二值化阈值

# 调用函数
result = process_contrail_data(
    mod03_dir=mod03_dir,
    rgb_dir=rgb_dir,
    date=date,
    resolution=resolution,
    output_dir=output_dir,
    threshold=threshold,
    output_ratio_only=False  # False输出所有矩阵，True只输出比例矩阵
)
```

### 参数说明

- `mod03_dir`: MOD03文件目录路径
- `rgb_dir`: RGB图像目录路径  
- `date`: 日期，格式如'2013001'
- `resolution`: 分辨率，1表示1度×1度
- `output_dir`: 输出目录路径
- `threshold`: 二值化阈值，默认0.35
- `output_ratio_only`: 是否只输出比例，True只输出比例，False输出所有三个矩阵

### 输入文件格式要求

#### MOD03文件
- 格式：`MOD03.A2013001.0000.061.2017341153220.hdf`
- 位置：`mod03_dir`目录下

#### RGB图像文件
- 格式：`MOD021KM.A2013001.0000.061.2017295083828_RGB_denoised.png`
- 位置：`rgb_dir`目录下

### 输出文件

程序会在输出目录下创建以下子目录和文件：

1. `count_0/`: 背景像素计数矩阵
   - 文件名：`count_0_{date}.tif`
   
2. `count_1/`: 航迹像素计数矩阵
   - 文件名：`count_1_{date}.tif`
   
3. `ratio/`: 航迹比例矩阵
   - 文件名：`ratio_{date}.tif`

所有输出文件都是180×360的GeoTIFF格式，包含完整的地理坐标信息。

## 处理流程

1. **文件匹配**：根据日期查找RGB文件，然后匹配对应的MOD03文件
2. **图像二值化**：使用指定阈值对RGB图像进行二值化处理
3. **坐标映射**：读取MOD03中的经纬度信息，将像素映射到1度×1度网格
4. **统计计数**：统计每个网格中背景和航迹像素的数量
5. **结果保存**：将统计结果保存为GeoTIFF文件

## 注意事项

- 确保MOD03和RGB文件的命名格式正确
- 输入的日期格式应为'YYYYDDD'（年份+一年中的第几天）
- 程序会自动创建输出目录
- 如果某些文件处理失败，程序会继续处理其他文件并输出错误信息
