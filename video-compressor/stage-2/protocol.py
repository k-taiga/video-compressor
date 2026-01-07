# バイトオーダー
BYTE_ORDER = 'big'

# ヘッダーの各サイズ（バイト数）
JSON_SIZE_LENGTH = 2
MEDIA_TYPE_SIZE_LENGTH = 1
PAYLOAD_SIZE_LENGTH = 5
HEADER_SIZE = JSON_SIZE_LENGTH + MEDIA_TYPE_SIZE_LENGTH + PAYLOAD_SIZE_LENGTH  # 合計 8バイト

# スライス用の開始位置
JSON_SIZE_START = 0
MEDIA_TYPE_SIZE_START = JSON_SIZE_START + JSON_SIZE_LENGTH  # 2
PAYLOAD_SIZE_START = MEDIA_TYPE_SIZE_START + MEDIA_TYPE_SIZE_LENGTH  # 3

# スライス用の終了位置
JSON_SIZE_END = JSON_SIZE_START + JSON_SIZE_LENGTH  # 2
MEDIA_TYPE_SIZE_END = MEDIA_TYPE_SIZE_START + MEDIA_TYPE_SIZE_LENGTH  # 3
PAYLOAD_SIZE_END = PAYLOAD_SIZE_START + PAYLOAD_SIZE_LENGTH  # 8


def create_header(json_size_int: int, media_type_size_int: int, payload_size_int: int) -> bytes:
    """
    3つの数値(JSON Size, メディアタイプサイズ, ペイロードサイズ) をあわせた8バイトのヘッダーを作る
    """
    json_size = json_size_int.to_bytes(JSON_SIZE_LENGTH, BYTE_ORDER)
    media_type_size = media_type_size_int.to_bytes(MEDIA_TYPE_SIZE_LENGTH, BYTE_ORDER)
    payload_size = payload_size_int.to_bytes(PAYLOAD_SIZE_LENGTH, BYTE_ORDER)

    return json_size + media_type_size + payload_size


def parse_header(header_bytes: bytes) -> tuple[int, int, int]:
    """
    8バイトのヘッダー → 3つの数値を取り出す
    """
    json_size = int.from_bytes(
        header_bytes[JSON_SIZE_START:JSON_SIZE_END], BYTE_ORDER
    )
    media_type_size = int.from_bytes(
        header_bytes[MEDIA_TYPE_SIZE_START:MEDIA_TYPE_SIZE_END], BYTE_ORDER
    )
    payload_size = int.from_bytes(
        header_bytes[PAYLOAD_SIZE_START:PAYLOAD_SIZE_END], BYTE_ORDER
    )

    return json_size, media_type_size, payload_size
