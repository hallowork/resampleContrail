import os
import glob
import logging
from datetime import datetime
from line_segment_processor import process_image_for_lines

# 配置参数
INPUT_FOLDER = r"C:\Users\wuch\Desktop\航迹论文\去除短线\原始数据"
OUTPUT_FOLDER = r"C:\Users\wuch\Desktop\航迹论文\去除短线\输出结果"
THRESHOLD_VALUE = 0.35
MIN_PIXEL_LENGTH = 50

def setup_logging(output_folder):
    """设置日志功能"""
    os.makedirs(output_folder, exist_ok=True)
    log_filename = f"processing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    log_path = os.path.join(output_folder, log_filename)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("线段检测批量处理开始")
    logger.info("=" * 60)
    logger.info(f"输入文件夹: {INPUT_FOLDER}")
    logger.info(f"输出文件夹: {OUTPUT_FOLDER}")
    logger.info(f"二值化阈值: {THRESHOLD_VALUE}")
    logger.info(f"最小线段长度: {MIN_PIXEL_LENGTH} 像素")
    logger.info(f"日志文件: {log_path}")
    logger.info("=" * 60)
    
    return logger

def main():
    # 设置日志
    logger = setup_logging(OUTPUT_FOLDER)
    
    # 获取所有PNG文件
    image_files = glob.glob(os.path.join(INPUT_FOLDER, "*.png"))
    
    if not image_files:
        logger.warning(f"在输入文件夹 '{INPUT_FOLDER}' 中未找到任何PNG图片。")
        return

    logger.info(f"找到 {len(image_files)} 张图片进行处理。")
    
    successful_count = 0
    failed_files = []

    for i, image_path in enumerate(image_files, 1):
        try:
            filename = os.path.basename(image_path)
            logger.info(f"处理文件 {i}/{len(image_files)}: {filename}")
            
            output_path = process_image_for_lines(
                input_image_path=image_path,
                threshold_value=THRESHOLD_VALUE,
                min_pixel_length=MIN_PIXEL_LENGTH,
                output_folder_path=OUTPUT_FOLDER
            )
            successful_count += 1
            logger.info(f"✅ 成功处理: {filename}")
            
        except Exception as e:
            filename = os.path.basename(image_path)
            logger.error(f"处理文件 {filename} 时出错: {e}")
            failed_files.append(filename)
    
    # 记录处理总结
    logger.info("=" * 60)
    logger.info("批量处理完成")
    logger.info("=" * 60)
    logger.info(f"总文件数: {len(image_files)}")
    logger.info(f"成功处理: {successful_count} 个文件")
    logger.info(f"处理失败: {len(failed_files)} 个文件")
    if len(image_files) > 0:
        logger.info(f"成功率: {successful_count/len(image_files)*100:.1f}%")
    
    if failed_files:
        logger.warning("失败的文件:")
        for file in failed_files:
            logger.warning(f"  - {file}")
    
    logger.info("=" * 60)
    print(f"\n✅ 批量处理完成！共处理 {successful_count} 个文件")

if __name__ == '__main__':
    main()