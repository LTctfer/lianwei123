#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Alarm Backend API (JSON Version)
--------------------------------------
支持多规则配置同步与预警数据上报
配置文件格式：config.json
"""

import uvicorn
from fastapi import FastAPI, Body, HTTPException
from typing import Any, Dict, List
import json
import os
import datetime

# ==============================
# 配置文件路径
# ==============================
CONFIG_PATH = "config.json"

# ==============================
# FastAPI 初始化
# ==============================
app = FastAPI(title="Smart Alarm Backend (JSON Version)")
ALARM_STORE: List[Dict[str, Any]] = []


# ==============================
# 工具函数
# ==============================
def _load_config() -> Dict[str, Any]:
    """从 config.json 加载规则配置"""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON 解析错误: {e}")
                return {"rules": []}
    return {"rules": []}


def _save_config(cfg: Dict[str, Any]):
    """保存规则配置到 config.json"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ==============================
# 接口定义
# ==============================

@app.get("/get_config")
def get_config():
    """
    算法引擎拉取配置：返回所有规则
    GET /get_config
    """
    return _load_config()


@app.post("/sync_rules")
def sync_rules(body: Dict[str, Any] = Body(...)):
    """
    批量同步规则（一次可下发多条）
    请求格式:
    {
      "rules": [ {rule1}, {rule2}, ... ]
    }
    """
    if "rules" not in body or not isinstance(body["rules"], list):
        raise HTTPException(status_code=400, detail="Missing 'rules' list")
    try:
        _save_config(body)
        print(f"✅ 同步规则 {len(body['rules'])} 条成功")
        return {"success": True, "count": len(body["rules"])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/push_alarm")
def push_alarm(alarm: Dict[str, Any] = Body(...)):
    """
    算法引擎上报预警
    POST /push_alarm
    {
      "alarmId": "R001",
      "alarmTime": "2025-10-10 14:32:55",
      "data": {"temperature": 95.3}
    }
    """
    for field in ("alarmId", "alarmTime", "data"):
        if field not in alarm:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    alarm["receivedAt"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ALARM_STORE.append(alarm)
    print(f"🚨 [RECV ALARM] {alarm}")
    return {"ok": True}


@app.get("/alarms")
def list_alarms():
    """
    查看已接收预警
    GET /alarms
    """
    return {"count": len(ALARM_STORE), "items": ALARM_STORE}


# ==============================
# 主入口
# ==============================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
