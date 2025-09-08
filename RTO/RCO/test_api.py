#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API功能测试脚本
用于测试预警规则管理API的各项功能
"""

import requests
import json
import time

class APITester:
    def __init__(self, base_url="http://localhost:8090"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_get_rules(self):
        """测试获取所有规则"""
        print("🔍 测试获取所有规则...")
        try:
            response = self.session.get(f"{self.base_url}/api/rules")
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    print(f"✅ 成功获取 {data['total']} 条规则")
                    return data['data']
                else:
                    print(f"❌ 获取规则失败: {data['error']}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
        return []
    
    def test_get_rule_detail(self, rule_id):
        """测试获取单个规则详情"""
        print(f"🔍 测试获取规则详情: {rule_id}")
        try:
            response = self.session.get(f"{self.base_url}/api/rules/{rule_id}")
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    rule = data['data']
                    print(f"✅ 成功获取规则: {rule['rule_name']}")
                    print(f"   阈值: {rule['threshold_value']}{rule['threshold_unit']}")
                    print(f"   状态: {'启用' if rule['is_active'] else '禁用'}")
                    return rule
                else:
                    print(f"❌ 获取规则失败: {data['error']}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
        return None
    
    def test_update_threshold(self, rule_id, new_threshold):
        """测试更新规则阈值"""
        print(f"🔧 测试更新规则阈值: {rule_id} -> {new_threshold}")
        try:
            data = {
                "rule_id": rule_id,
                "threshold": new_threshold
            }
            response = self.session.post(
                f"{self.base_url}/api/rules/update-threshold",
                json=data
            )
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print(f"✅ {result['message']}")
                    return True
                else:
                    print(f"❌ 更新失败: {result['error']}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
        return False
    
    def test_toggle_status(self, rule_id):
        """测试切换规则状态"""
        print(f"🔄 测试切换规则状态: {rule_id}")
        try:
            data = {"rule_id": rule_id}
            response = self.session.post(
                f"{self.base_url}/api/rules/toggle-status",
                json=data
            )
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print(f"✅ {result['message']}")
                    return result.get('is_active', False)
                else:
                    print(f"❌ 操作失败: {result['error']}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
        return None
    
    def test_update_rule(self, rule_id, update_data):
        """测试更新规则详情"""
        print(f"📝 测试更新规则详情: {rule_id}")
        try:
            response = self.session.put(
                f"{self.base_url}/api/rules/{rule_id}",
                json=update_data
            )
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print(f"✅ {result['message']}")
                    return True
                else:
                    print(f"❌ 更新失败: {result['error']}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
        return False
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 开始API综合测试")
        print("=" * 50)
        
        # 1. 获取所有规则
        rules = self.test_get_rules()
        if not rules:
            print("❌ 无法获取规则列表，测试终止")
            return
        
        # 选择第一个规则进行测试
        test_rule = rules[0]
        rule_id = test_rule['rule_id']
        original_threshold = test_rule['threshold_value']
        original_status = test_rule['is_active']
        
        print(f"\n📋 测试规则: {test_rule['rule_name']} ({rule_id})")
        print(f"   原始阈值: {original_threshold}{test_rule['threshold_unit']}")
        print(f"   原始状态: {'启用' if original_status else '禁用'}")
        
        # 2. 获取规则详情
        self.test_get_rule_detail(rule_id)
        
        # 3. 更新阈值
        new_threshold = original_threshold + 10
        self.test_update_threshold(rule_id, new_threshold)
        time.sleep(1)
        
        # 4. 验证阈值更新
        updated_rule = self.test_get_rule_detail(rule_id)
        if updated_rule and updated_rule['threshold_value'] == new_threshold:
            print("✅ 阈值更新验证成功")
        else:
            print("❌ 阈值更新验证失败")
        
        # 5. 切换状态
        new_status = self.test_toggle_status(rule_id)
        time.sleep(1)
        
        # 6. 验证状态切换
        if new_status is not None and new_status != original_status:
            print("✅ 状态切换验证成功")
        else:
            print("❌ 状态切换验证失败")
        
        # 7. 恢复原始状态
        print(f"\n🔄 恢复原始配置...")
        self.test_update_threshold(rule_id, original_threshold)
        if new_status != original_status:
            self.test_toggle_status(rule_id)
        
        print("\n🎉 API测试完成!")
        print("=" * 50)

def main():
    """主函数"""
    print("🧪 RTO/RCO预警系统API测试工具")
    print("请确保服务器已启动 (python warning_system.py 选择模式2)")
    print()
    
    tester = APITester()
    
    try:
        # 检查服务器是否运行
        response = requests.get("http://localhost:8090/api/rules", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器连接正常，开始测试...")
            tester.run_comprehensive_test()
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器已启动")
        print("   启动命令: python warning_system.py")
        print("   然后选择模式 2 (启动实时监控大屏)")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()
