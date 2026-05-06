# /Users/tomwang/Codes/Auspicious/backend/app/services/divination/hexagram_table.py
"""8x8 64-hexagram lookup. Attribution:
   moregatest/pi-mono iching_divination.py @ 271c9e3 (MIT License).
"""

# 八卦索引：坤0 艮1 坎2 巽3 震4 離5 兌6 乾7
TRIGRAM_NAMES = ["坤", "艮", "坎", "巽", "震", "離", "兌", "乾"]
TRIGRAM_SYMBOLS = ["☷", "☶", "☵", "☴", "☳", "☲", "☱", "☰"]
TRIGRAM_NATURE = ["地", "山", "水", "風", "雷", "火", "澤", "天"]

# TABLE[下卦][上卦] = 卦號（1-64）
TABLE = [
    [ 2, 23,  8, 20, 16, 35, 45, 12],
    [15, 52, 39, 53, 62, 56, 31, 33],
    [ 7,  4, 29, 59, 40, 64, 47,  6],
    [46, 18, 48, 57, 32, 50, 28, 44],
    [24, 27,  3, 42, 51, 21, 17, 25],
    [36, 22, 63, 37, 55, 30, 49, 13],
    [19, 41, 60, 61, 54, 38, 58, 10],
    [11, 26,  5,  9, 34, 14, 43,  1],
]


def validate_table() -> None:
    nums = [TABLE[r][c] for r in range(8) for c in range(8)]
    if sorted(nums) != list(range(1, 65)):
        raise RuntimeError("TABLE corrupted: not a complete 1..64 set")


validate_table()  # boot-time guard
