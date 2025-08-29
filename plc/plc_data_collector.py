#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLC数据采集器
通过Modbus TCP/IP协议从PLC设备采集监测站数据

使用方法:
python plc_data_collector.py [--config plc_config.json] [--interval 60]
"""

import json
import time
import argparse
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List
import signal
import sys

from modbus_plc_reader import S7DataReader, S7Register

class S7DataCollector:
    """西门子S7-300数据采集器"""

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.s7_reader = None
        self.running = False
        self.data_buffer = []

        # 加载配置
        self.load_config()

        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def load_config(self):
        """加载PLC配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # S7-300连接设置
            plc_settings = config['plc_settings']
            self.s7_reader = S7DataReader(
                host=plc_settings['host'],
                port=plc_settings.get('port', 502),
                unit_id=plc_settings.get('unit_id', 1)
            )
            
            # 添加寄存器配置
            self.s7_reader.add_registers_from_config(config['registers'])
            
            logging.info(f"配置加载成功: {len(config['registers'])} 个寄存器")
            
        except Exception as e:
            logging.error(f"加载配置失败: {e}")
            raise
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        logging.info(f"收到信号 {signum}，正在停止数据采集...")
        self.stop()
    
    def connect_s7(self) -> bool:
        """连接S7-300设备"""
        try:
            if self.s7_reader.connect():
                logging.info("S7-300连接成功")
                return True
            else:
                logging.error("S7-300连接失败")
                return False
        except Exception as e:
            logging.error(f"S7-300连接异常: {e}")
            return False
    
    def collect_single_data(self) -> Dict:
        """采集一次数据"""
        try:
            # 读取所有寄存器数据
            raw_data = self.s7_reader.read_all_registers()
            
            # 转换为监测站数据格式
            monitoring_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'station_id': 'PLC_001',
                'station_name': 'PLC监测站'
            }
            
            # 提取监测参数
            for param_name, param_data in raw_data.items():
                if param_data['value'] is not None:
                    monitoring_data[param_name] = param_data['value']
            
            # 添加必要的坐标信息 (如果PLC中没有，使用默认值)
            if 'x' not in monitoring_data:
                monitoring_data['x'] = 0.0
            if 'y' not in monitoring_data:
                monitoring_data['y'] = 0.0
            if 'z' not in monitoring_data:
                monitoring_data['z'] = 10.0
            if 'longitude' not in monitoring_data:
                monitoring_data['longitude'] = 120.0
            if 'latitude' not in monitoring_data:
                monitoring_data['latitude'] = 30.0
            
            return monitoring_data
            
        except Exception as e:
            logging.error(f"数据采集失败: {e}")
            return None
    
    def start_continuous_collection(self, interval: int = 60):
        """开始连续数据采集"""
        logging.info(f"开始连续数据采集，间隔: {interval} 秒")
        
        if not self.connect_s7():
            return False
        
        self.running = True
        
        try:
            while self.running:
                # 采集数据
                data = self.collect_single_data()
                
                if data:
                    # 添加到缓冲区
                    self.data_buffer.append(data)
                    
                    # 显示数据
                    self.display_data(data)
                    
                    # 定期保存数据
                    if len(self.data_buffer) >= 10:
                        self.save_data_buffer()
                
                # 等待下次采集
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logging.info("用户中断数据采集")
        except Exception as e:
            logging.error(f"数据采集异常: {e}")
        finally:
            self.stop()
    
    def display_data(self, data: Dict):
        """显示采集的数据"""
        print(f"\n📊 数据采集时间: {data['timestamp']}")
        print(f"🏭 监测站: {data['station_name']} ({data['station_id']})")
        
        # 显示主要监测参数
        if 'pm25' in data:
            print(f"PM2.5: {data['pm25']:.1f} μg/m³")
        if 'pm10' in data:
            print(f"PM10: {data['pm10']:.1f} μg/m³")
        if 'wind_speed' in data:
            print(f"风速: {data['wind_speed']:.1f} m/s")
        if 'wind_direction' in data:
            print(f"风向: {data['wind_direction']:.0f}°")
        if 'temperature' in data:
            print(f"温度: {data['temperature']:.1f}°C")
        if 'humidity' in data:
            print(f"湿度: {data['humidity']:.1f}%")
        if 'pressure' in data:
            print(f"气压: {data['pressure']:.1f} hPa")
        if 'device_status' in data:
            status = "正常" if data['device_status'] else "异常"
            print(f"设备状态: {status}")
    
    def save_data_buffer(self):
        """保存数据缓冲区到文件"""
        if not self.data_buffer:
            return
        
        try:
            # 转换为DataFrame
            df = pd.DataFrame(self.data_buffer)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'三色预警/plc_data_{timestamp}.csv'
            
            # 保存为CSV
            df.to_csv(filename, index=False, encoding='utf-8')
            
            logging.info(f"数据已保存: {filename} ({len(self.data_buffer)} 条记录)")
            
            # 清空缓冲区
            self.data_buffer.clear()
            
        except Exception as e:
            logging.error(f"保存数据失败: {e}")
    
    def test_connection(self):
        """测试S7-300连接"""
        print("🔧 测试S7-300连接...")

        if not self.connect_s7():
            print("❌ S7-300连接失败")
            return False

        print("✅ S7-300连接成功")
        
        # 测试读取数据
        print("📊 测试数据读取...")
        data = self.collect_single_data()
        
        if data:
            print("✅ 数据读取成功")
            self.display_data(data)
            return True
        else:
            print("❌ 数据读取失败")
            return False
    
    def stop(self):
        """停止数据采集"""
        self.running = False
        
        # 保存剩余数据
        if self.data_buffer:
            self.save_data_buffer()
        
        # 断开S7-300连接
        if self.s7_reader:
            self.s7_reader.disconnect()
        
        logging.info("数据采集已停止")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PLC数据采集器')
    parser.add_argument('--config', default='三色预警/plc_config.json',
                       help='PLC配置文件路径')
    parser.add_argument('--interval', type=int, default=60,
                       help='数据采集间隔(秒)')
    parser.add_argument('--test', action='store_true',
                       help='测试模式，只测试连接和读取一次数据')
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('三色预警/plc_collector.log'),
            logging.StreamHandler()
        ]
    )
    
    print("🌍 西门子S7-300数据采集器")
    print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⚙️  配置文件: {args.config}")
    print()
    
    try:
        # 创建数据采集器
        collector = S7DataCollector(args.config)
        
        if args.test:
            # 测试模式
            success = collector.test_connection()
            sys.exit(0 if success else 1)
        else:
            # 连续采集模式
            print(f"🚀 开始连续数据采集 (间隔: {args.interval} 秒)")
            print("按 Ctrl+C 停止采集")
            collector.start_continuous_collection(args.interval)
    
    except Exception as e:
        logging.error(f"程序运行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
