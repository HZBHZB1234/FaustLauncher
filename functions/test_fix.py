import sys
import os
sys.path.append(os.path.dirname(__file__))

from handle_colorful import process_dlg_text

# 测试用户提到的具体条目
test_text = '<color=#af612c>啊啊……难道……你是……\n我的辛克莱……？！</color>'
print("原始文本:")
print(test_text)
print("\n处理后文本:")
result = process_dlg_text(test_text)
print(result)

# 检查是否发生了变化
if test_text != result:
    print("\n✅ 处理成功 - 文本已被渐变处理")
else:
    print("\n❌ 处理失败 - 文本未被处理")

# 测试其他包含换行符的条目
print("\n" + "="*50)
print("测试其他包含换行符的条目:")
test_cases = [
    '<color=#6e44a6>呼，洗盘子的家伙们\n也会捅刀过来。</color>',
    '<color=#6e44a6>凯瑟琳……？！是我，希斯克利夫……！\n求求你再一次接受我吧！！！</color>',
    '<color=#6e44a6>你是什么希斯克利夫都无所谓！\n我会拥所有的凯瑟琳入怀！！！</color>'
]

for i, test_case in enumerate(test_cases, 1):
    print(f"\n测试用例 {i}:")
    print(f"输入: {test_case}")
    result = process_dlg_text(test_case)
    print(f"输出: {result}")
    if test_case != result:
        print("✅ 处理成功")
    else:
        print("❌ 处理失败")