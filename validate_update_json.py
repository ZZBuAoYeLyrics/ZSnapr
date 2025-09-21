# Validate the migrated update.json file
import json
from pathlib import Path

def validate_update_json():
    try:
        with open('assets/update/update.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ JSON格式验证通过!")
        print(f"📱 应用名称: {data['app']['name']}")
        print(f"🔢 当前版本: {data['app']['currentVersion']}")
        print(f"🆕 最新版本: {data['app']['latestVersion']}")
        print(f"📋 版本记录数: {len(data['releases'])}")
        
        print("\n📋 版本历史:")
        for release in data['releases']:
            version = release['version']
            date = release['releaseDate']
            added_count = len(release['changelog']['added'])
            fixed_count = len(release['changelog']['fixed'])
            print(f"  {version} ({date}) - {added_count}个新功能, {fixed_count}个修复")
        
        print("\n🎯 最新版本详情:")
        latest = data['releases'][0]
        print(f"版本: {latest['version']}")
        print(f"发布日期: {latest['releaseDate']}")
        print(f"类型: {latest['type']}")
        print(f"状态: {latest['status']}")
        
        print("\n✨ 新增功能:")
        for feature in latest['changelog']['added']:
            print(f"  + {feature}")
        
        print("\n🔧 修复问题:")
        for fix in latest['changelog']['fixed']:
            print(f"  - {fix}")
            
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

if __name__ == "__main__":
    validate_update_json()