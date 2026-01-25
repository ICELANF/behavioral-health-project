import json
import os

def test_load_experts():
    # 1. 定义绝对路径，确保万无一失
    file_path = r"D:\behavioral-health-project\experts.json"
    
    print(f"--- 正在检测文件是否存在 ---")
    if not os.path.exists(file_path):
        print(f"❌ 错误：在 {file_path} 找不到文件！")
        return

    print(f"✅ 找到文件，尝试读取内容...\n")

    try:
        # 2. 显式指定 utf-8 编码，这是 Windows 环境下最容易报错的地方
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 3. 漂亮打印结果
        print("--- [读取成功] 专家配置如下 ---")
        print(json.dumps(data, indent=4, ensure_ascii=False))
        
        # 4. 逻辑自检
        if "xingjian_coach" in data:
            print(f"\n🚀 自检通过：'行健教练' 已就绪")
        else:
            print(f"\n⚠️ 警告：JSON 格式正确但未发现 'xingjian_coach' 键")

    except UnicodeDecodeError:
        print("❌ 编码错误：请确保 experts.json 是以 UTF-8 编码保存的。")
    except json.JSONDecodeError as e:
        print(f"❌ 格式错误：experts.json 内部 JSON 语法有误: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

if __name__ == "__main__":
    test_load_experts()