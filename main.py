"""
MOD03和RGB图像处理项目主文件
"""

from contrail_processor import process_contrail_data

def main():
    """主函数 - 运行contrail处理"""
    print("MOD03和RGB图像处理工具")
    print("=" * 50)
    
    # 默认参数
    mod03_dir = r"C:\researchWorkPlace\pythonProject\dataExample\mod03"
    rgb_dir = r"C:\researchWorkPlace\pythonProject\dataExample\rgb"
    date = "2013001"
    resolution = 1
    output_dir = r"C:\researchWorkPlace\pythonProject\output"
    threshold = 0.35
    
    print("使用默认参数运行处理:")
    print(f"  MOD03目录: {mod03_dir}")
    print(f"  RGB目录: {rgb_dir}")
    print(f"  日期: {date}")
    print(f"  分辨率: {resolution}")
    print(f"  输出目录: {output_dir}")
    print(f"  阈值: {threshold}")
    print()
    
    # 调用处理函数
    try:
        result = process_contrail_data(
            mod03_dir=mod03_dir,
            rgb_dir=rgb_dir,
            date=date,
            resolution=resolution,
            output_dir=output_dir,
            threshold=threshold,
            output_ratio_only=False
        )
        
        if result > 0:
            print(f"\n处理成功完成! 共处理了 {result} 个文件")
        else:
            print("\n没有找到可处理的文件")
            
    except Exception as e:
        print(f"\n处理过程中发生错误: {str(e)}")


if __name__ == '__main__':
    main()
