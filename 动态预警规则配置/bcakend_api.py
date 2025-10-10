# backend_api.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import uvicorn
from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List
import os, json, datetime, toml

CONFIG_JSON = "config.json"
CONFIG_TOML = "config.toml"

app = FastAPI(title="Smart Alarm Backend API")
ALARM_STORE: List[Dict[str, Any]] = []

def _load_config_dict() -> Dict[str, Any]:
    if os.path.exists(CONFIG_JSON):
        with open(CONFIG_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    if os.path.exists(CONFIG_TOML):
        with open(CONFIG_TOML, "r", encoding="utf-8") as f:
            return toml.load(f)
    return {}

def _save_config_dict(cfg: Dict[str, Any]):
    with open(CONFIG_JSON, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

class DotPatch(BaseModel):
    updates: Dict[str, Any]
    persist: bool = True

@app.get("/get_config")
def get_config():
    return _load_config_dict()

@app.post("/set_config")
def set_config(cfg: Dict[str, Any] = Body(...)):
    try:
        # 轻量校验：必填字段存在性（详尽校验可按需增强）
        required = [
            "alarmRuleId", "alarmRuleName", "alarmClazz", "alarmType",
            "alarmLevel", "alarmInternal", "dataInternal", "algorithmType",
            "calculateWay", "enabled", "startTime", "endTime", "showProperties", "config"
        ]
        miss = [k for k in required if k not in cfg]
        if miss:
            raise HTTPException(status_code=400, detail=f"missing required: {miss}")
        _save_config_dict(cfg)
        return {"success": True, "message": "config replaced"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/update_config")
def update_config(patch: DotPatch):
    cfg = _load_config_dict()
    for k, v in patch.updates.items():
        cursor = cfg
        parts = k.split(".")
        for p in parts[:-1]:
            if p not in cursor or not isinstance(cursor[p], dict):
                cursor[p] = {}
            cursor = cursor[p]
        cursor[parts[-1]] = v
    if patch.persist:
        _save_config_dict(cfg)
    return {"success": True, "message": "config updated", "config": cfg}

@app.post("/push_alarm")
def push_alarm(alarm: Dict[str, Any] = Body(...)):
    for field in ("alarmId", "alarmTime", "data"):
        if field not in alarm:
            raise HTTPException(status_code=400, detail=f"missing field: {field}")
    alarm["receivedAt"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ALARM_STORE.append(alarm)
    print(f"🚨 [RECV ALARM] {alarm}")
    return {"ok": True}

@app.get("/alarms")
def list_alarms():
    return {"count": len(ALARM_STORE), "items": ALARM_STORE}

if __name__ == "__main__":
    # 启动：uvicorn backend_api:app --reload --host 0.0.0.0 --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)

