#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API推送模块
提供通过HTTP API接口推送预警消息到后端系统的能力
"""

import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import asdict

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class APIPusher:
    """API推送器类，用于将预警消息推送到后端系统"""
    
    def __init__(self, base_url: str, api_token: Optional[str] = None):
        """
        初始化API推送器
        
        Args:
            base_url: 后端API的基础URL
            api_token: 可选的API令牌用于身份验证
        """
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.session = requests.Session()
        
        # 设置默认请求头
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'RTO/RCO-Warning-System/1.0'
        }
        
        # 如果提供了API令牌，则添加到请求头
        if api_token:
            headers['Authorization'] = f'Bearer {api_token}'
            
        self.session.headers.update(headers)
    
    def push_warning_record(self, record: Any) -> bool:
        """
        推送单条预警记录到后端
        
        Args:
            record: 预警记录对象
            
        Returns:
            bool: 推送是否成功
        """
        try:
            # 将记录对象转换为字典
            if hasattr(record, '__dict__'):
                record_data = record.__dict__
            else:
                record_data = asdict(record)
            
            # 发送POST请求
            response = self.session.post(
                f"{self.base_url}/warnings",
                json=record_data,
                timeout=30
            )
            
            # 检查响应状态
            if response.status_code in [200, 201]:
                logger.info(f"✅ 预警记录推送成功: {record_data.get('rule_name', 'Unknown')}")
                return True
            else:
                logger.error(f"❌ 预警记录推送失败: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 网络请求错误: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 预警记录推送过程中发生错误: {e}")
            return False
    
    def push_violations(self, violations: List[Dict]) -> Dict[str, int]:
        """
        推送违规事件列表到后端
        
        Args:
            violations: 违规事件列表
            
        Returns:
            Dict: 推送结果 {'success': 成功数量, 'failed': 失败数量}
        """
        success_count = 0
        failed_count = 0
        
        for violation in violations:
            try:
                # 发送POST请求
                response = self.session.post(
                    f"{self.base_url}/violations",
                    json=violation,
                    timeout=30
                )
                
                # 检查响应状态
                if response.status_code in [200, 201]:
                    logger.info(f"✅ 违规事件推送成功: {violation.get('rule_name', 'Unknown')}")
                    success_count += 1
                else:
                    logger.error(f"❌ 违规事件推送失败: {response.status_code} - {response.text}")
                    failed_count += 1
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ 网络请求错误: {e}")
                failed_count += 1
            except Exception as e:
                logger.error(f"❌ 违规事件推送过程中发生错误: {e}")
                failed_count += 1
        
        return {'success': success_count, 'failed': failed_count}
    
    def push_summary(self, summary: Dict[str, Any]) -> bool:
        """
        推送汇总信息到后端
        
        Args:
            summary: 汇总信息字典
            
        Returns:
            bool: 推送是否成功
        """
        try:
            # 添加时间戳
            summary_data = summary.copy()
            summary_data['timestamp'] = datetime.now().isoformat()
            
            # 发送POST请求
            response = self.session.post(
                f"{self.base_url}/summary",
                json=summary_data,
                timeout=30
            )
            
            # 检查响应状态
            if response.status_code in [200, 201]:
                logger.info("✅ 汇总信息推送成功")
                return True
            else:
                logger.error(f"❌ 汇总信息推送失败: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 网络请求错误: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 汇总信息推送过程中发生错误: {e}")
            return False

def extend_warning_system_with_api(warning_system: Any, api_url: str, token: Optional[str] = None) -> Any:
    """
    扩展预警系统，增加API推送功能
    
    Args:
        warning_system: 原始预警系统实例
        api_url: API地址
        token: API令牌（可选）
        
    Returns:
        扩展后的预警系统实例
    """
    # 创建API推送器
    api_pusher = APIPusher(api_url, token)
    
    # 保存原始方法
    original_process_data_file = warning_system.process_data_file
    
    def process_data_file_with_api_push(self, file_path: str) -> tuple:
        """
        带有API推送功能的数据处理方法
        """
        # 调用原始方法处理数据
        violations, summary = original_process_data_file(file_path)
        
        # 如果有违规事件，推送数据到API
        if violations:
            print("\n🚀 正在推送数据到后端API...")
            
            # 推送违规事件
            result = api_pusher.push_violations(violations)
            print(f"  违规事件推送: 成功 {result['success']} 条, 失败 {result['failed']} 条")
            
            # 推送汇总信息
            if api_pusher.push_summary(summary):
                print("  汇总信息推送成功")
            else:
                print("  汇总信息推送失败")
            
            # 推送活跃预警记录
            active_warnings = list(self.rule_engine.active_warnings.values())
            if active_warnings:
                print(f"\n正在推送 {len(active_warnings)} 条活跃预警...")
                success_count = 0
                failed_count = 0
                for record in active_warnings:
                    if api_pusher.push_warning_record(record):
                        success_count += 1
                    else:
                        failed_count += 1
                print(f"  活跃预警推送: 成功 {success_count} 条, 失败 {failed_count} 条")
            
            # 推送已解决的预警记录
            resolved_warnings = self.rule_engine.warning_records
            if resolved_warnings:
                print(f"\n正在推送 {len(resolved_warnings)} 条已解决预警...")
                success_count = 0
                failed_count = 0
                for record in resolved_warnings:
                    if api_pusher.push_warning_record(record):
                        success_count += 1
                    else:
                        failed_count += 1
                print(f"  已解决预警推送: 成功 {success_count} 条, 失败 {failed_count} 条")
        
        return violations, summary
    
    # 替换原始方法
    import types
    warning_system.process_data_file = types.MethodType(process_data_file_with_api_push, warning_system)
    
    return warning_system

# 使用示例
def example_usage():
    """使用示例"""
    print("🚀 API推送模块使用示例")
    print("=" * 50)
    
    try:
        # 导入核心预警系统
        from warning_system_core import WarningSystem
        print("✅ 成功导入预警系统核心模块")
        
        # 获取API配置
        api_url = input("请输入后端API地址 (例如: http://localhost:8000/api): ").strip()
        if not api_url:
            api_url = "http://localhost:8000/api"
        
        api_token = input("请输入API令牌 (可选，直接回车跳过): ").strip()
        if not api_token:
            api_token = None
        
        # 创建预警系统实例
        warning_system = WarningSystem()
        
        # 扩展预警系统增加API推送功能
        warning_system = extend_warning_system_with_api(warning_system, api_url, api_token)
        print("\n🎉 预警系统已扩展API推送功能")
        
        # 查找并分析数据文件
        from pathlib import Path
        test_files = [
            "data/equipment_data.xlsx",
            "data/equipment_data.csv", 
            "PLCTags.csv",
            "sample_data.xlsx"
        ]
        
        for file_path in test_files:
            if Path(file_path).exists():
                print(f"\n🔍 分析文件: {file_path}")
                warning_system.process_data_file(file_path)
                break
        else:
            print("⚠️ 未找到数据文件")
            
    except ImportError:
        print("❌ 无法导入预警系统核心模块")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    example_usage()