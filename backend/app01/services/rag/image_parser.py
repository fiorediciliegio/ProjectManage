from app01.services.rag.blocks import make_block
from app01.services.rag.pdf_parser import get_ocr_engine


# 图片解析
def load_image_blocks(file_path, base_metadata):
    ocr_engine = get_ocr_engine()

    if ocr_engine is None:
        raise ValueError('当前环境未安装 PaddleOCR，无法识别图片文字')

    result = ocr_engine.ocr(file_path)
    text = extract_text_from_ocr_result(result)

    if not text.strip():
        raise ValueError('图片中未识别到可入库文字')

    return [
        make_block(
            text=text,
            block_type='image_ocr_text',
            base_metadata=base_metadata,
            order=0,
            caption='图片 OCR 识别文本',
        )
    ]
