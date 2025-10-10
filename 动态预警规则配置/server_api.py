#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预警规则配置服务端
提供规则配置和预警数据管理的 RESTful API
"""

from fastapi import FastAPI, HTTPException, Body
from typing import Dict, List, Any
import json
import os
from datetime import datetime

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
# 预警记录存储
ALARM_STORE: List[Dict[str, Any]] = []

# 创建 FastAPI 应用
app = FastAPI(
    title="预警规则配置服务",
    description="提供预警规则配置和预警数据管理的 RESTful API",
    version="1.0.0"
)

def load_config() -> Dict[str, Any]:
    """从文件加载配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"配置文件格式错误: {e}")
    return {"rules": []}

def save_config(config: Dict[str, Any]):
    """保存配置到文件"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {e}")

@app.get("/get_config")
def get_config():
    """
    获取当前规则配置
    
    返回:
        Dict: 包含所有预警规则的配置
    """
    try:
        return load_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync_rules")
def sync_rules(config: Dict[str, Any] = Body(...)):
    """
    完全覆盖现有的规则配置
    
    参数:
        config: Dict[str, Any] - 新的规则配置，将完全覆盖现有配置
        
    返回:
        Dict: 更新结果，包含新旧规则数量
    """
    if "rules" not in config:
        raise HTTPException(status_code=400, detail="Missing 'rules' field")
    
    try:
        # 获取当前配置（用于记录变更）
        old_config = load_config()
        old_rules_count = len(old_config.get("rules", []))
        
        # 验证新规则格式
        rules = config["rules"]
        for rule in rules:
            if not all(k in rule for k in ["alarmRuleId", "alarmRuleName", "config"]):
                raise HTTPException(
                    status_code=400,
                    detail="每条规则必须包含 alarmRuleId, alarmRuleName 和 config"
                )
        
        # 验证规则 ID 唯一性
        rule_ids = [r["alarmRuleId"] for r in rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise HTTPException(status_code=400, detail="规则 ID 必须唯一")
        
        # 完全覆盖保存配置
        save_config(config)
        print(f"✅ 规则更新成功：原有 {old_rules_count} 条规则被 {len(rules)} 条新规则覆盖")
        
        return {
            "success": True,
            "old_count": old_rules_count,
            "new_count": len(rules),
            "message": f"原有 {old_rules_count} 条规则已被 {len(rules)} 条新规则完全覆盖"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/push_alarm")
def push_alarm(alarm: Dict[str, Any] = Body(...)):
    """
    接收预警数据
    
    参数:
        alarm: Dict[str, Any] - 预警数据
        
    返回:
        Dict: 处理结果
    """
    required_fields = ["alarmId", "alarmTime", "data"]
    for field in required_fields:
        if field not in alarm:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")
    
    try:
        # 添加接收时间
        alarm["receivedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ALARM_STORE.append(alarm)
        print(f"🚨 收到预警: {alarm}")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alarms")
def list_alarms():
    """
    获取预警记录列表
    
    返回:
        Dict: 包含所有预警记录
    """
    return {
        "count": len(ALARM_STORE),
        "items": ALARM_STORE
    }

# 健康检查接口
@app.get("/health")
def health_check():
    """
    服务健康检查
    
    返回:
        Dict: 服务状态信息
    """
    return {
        "status": "healthy",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "alarm_count": len(ALARM_STORE)
    }

if __name__ == "__main__":
    import uvicorn
    
    # 启动服务
    print("🚀 启动预警规则配置服务...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
