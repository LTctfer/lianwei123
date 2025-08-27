#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modbus PLC连接测试脚本
用于验证AI-BOX与PLC的连接和数据读取功能
"""

from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import struct
import time
import sys
from datetime import datetime

class ModbusConnectionTester:
    """Modbus连接测试器"""

    def __init__(self, ip_address="192.168.1.10", port=502, unit_id=1):
        self.ip_address = ip_address
        self.port = port
        self.unit_id = unit_id
        self.client = ModbusTcpClient(host=ip_address, port=port, timeout=5)

    def print_status(self, message, status="INFO"):
        """打印状态信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if status == "SUCCESS":
            print(f"[{timestamp}] ✅ {message}")
        elif status == "ERROR":
            print(f"[{timestamp}] ❌ {message}")
        elif status == "WARNING":
            print(f"[{timestamp}] ⚠️  {message}")
        else:
            print(f"[{timestamp}] ℹ️  {message}")

    def test_basic_connection(self):
        """测试基本连接"""
        self.print_status("开始测试Modbus连接...")

        try:
            # 尝试连接
            connection = self.client.connect()

            if connection:
                self.print_status(f"成功连接到PLC: {self.ip_address}:{self.port}", "SUCCESS")
                return True
            else:
                self.print_status(f"连接失败: {self.ip_address}:{self.port}", "ERROR")
                return False

        except Exception as e:
            self.print_status(f"连接异常: {e}", "ERROR")
            return False
    
    def get_plc_info(self):
        """获取PLC信息"""
        if not self.client.is_socket_open():
            self.print_status("PLC未连接", "ERROR")
            return False

        try:
            # Modbus没有直接获取设备信息的标准功能
            # 我们通过读取一些基本寄存器来验证连接
            self.print_status("Modbus PLC连接信息:", "INFO")
            print(f"    IP地址: {self.ip_address}")
            print(f"    端口: {self.port}")
            print(f"    从站ID: {self.unit_id}")
            print(f"    协议: Modbus TCP")

            # 尝试读取一个寄存器来验证通信
            try:
                result = self.client.read_holding_registers(40001, 1, unit=self.unit_id)
                if not result.isError():
                    self.print_status("通信验证: 成功", "SUCCESS")
                else:
                    self.print_status(f"通信验证失败: {result}", "WARNING")
            except Exception as e:
                self.print_status(f"通信验证异常: {e}", "WARNING")

            return True

        except Exception as e:
            self.print_status(f"获取PLC信息失败: {e}", "ERROR")
            return False
    
    def test_register_read(self, start_address=40001, count=10):
        """测试寄存器读取"""
        if not self.client.is_socket_open():
            self.print_status("PLC未连接", "ERROR")
            return False

        try:
            self.print_status(f"测试读取保持寄存器，起始地址{start_address}，数量{count}", "INFO")

            # 读取保持寄存器
            result = self.client.read_holding_registers(start_address, count, unit=self.unit_id)

            if not result.isError():
                registers = result.registers
                self.print_status(f"成功读取{len(registers)}个寄存器", "SUCCESS")

                # 显示寄存器数据
                print(f"    寄存器数据: {registers}")

                # 解析一些常见数据类型
                self._parse_sample_registers(registers)

                return True
            else:
                self.print_status(f"读取寄存器失败: {result}", "ERROR")
                return False

        except Exception as e:
            self.print_status(f"读取寄存器异常: {e}", "ERROR")
            return False
    
    def _parse_sample_registers(self, registers):
        """解析示例寄存器数据"""
        self.print_status("解析寄存器示例:", "INFO")

        try:
            # 解析寄存器为不同数据类型
            for i in range(0, min(len(registers), 10), 2):
                if i + 1 < len(registers):
                    # 解析为FLOAT32 (两个寄存器组成)
                    reg1, reg2 = registers[i], registers[i+1]
                    combined = (reg1 << 16) | reg2
                    packed = struct.pack('>I', combined)
                    float_value = struct.unpack('>f', packed)[0]
                    print(f"    寄存器{40001+i}-{40001+i+1}: FLOAT32 = {float_value:10.3f}")

                    # 解析为INT32 (两个寄存器组成)
                    int32_value = combined if combined < 2147483648 else combined - 4294967296
                    print(f"    寄存器{40001+i}-{40001+i+1}: INT32 = {int32_value}")

                    print()

                # 单个寄存器解析
                if i < len(registers):
                    reg_value = registers[i]
                    print(f"    寄存器{40001+i}: INT16 = {reg_value}")

        except Exception as e:
            self.print_status(f"寄存器解析失败: {e}", "WARNING")
    
    def test_continuous_read(self, duration=30, interval=1):
        """测试连续读取"""
        if not self.client.is_socket_open():
            self.print_status("PLC未连接", "ERROR")
            return False

        self.print_status(f"开始连续读取测试，持续{duration}秒，间隔{interval}秒", "INFO")

        start_time = time.time()
        read_count = 0
        error_count = 0

        try:
            while time.time() - start_time < duration:
                try:
                    # 读取保持寄存器40001-40002 (FLOAT32)
                    result = self.client.read_holding_registers(40001, 2, unit=self.unit_id)

                    if not result.isError():
                        read_count += 1
                        registers = result.registers

                        # 解析为FLOAT32值作为示例
                        if len(registers) >= 2:
                            combined = (registers[0] << 16) | registers[1]
                            packed = struct.pack('>I', combined)
                            value = struct.unpack('>f', packed)[0]
                            print(f"读取#{read_count}: 寄存器40001-40002 = {value:.3f}")
                    else:
                        error_count += 1
                        self.print_status(f"读取失败#{error_count}: {result}", "WARNING")

                except Exception as e:
                    error_count += 1
                    self.print_status(f"读取异常#{error_count}: {e}", "ERROR")

                time.sleep(interval)

            # 统计结果
            total_attempts = read_count + error_count
            success_rate = (read_count / total_attempts * 100) if total_attempts > 0 else 0

            self.print_status(f"连续读取测试完成", "SUCCESS")
            print(f"    总尝试次数: {total_attempts}")
            print(f"    成功次数: {read_count}")
            print(f"    失败次数: {error_count}")
            print(f"    成功率: {success_rate:.1f}%")

            return success_rate > 90

        except KeyboardInterrupt:
            self.print_status("用户中断测试", "WARNING")
            return False
    
    def test_coil_read(self):
        """测试线圈读取"""
        if not self.client.is_socket_open():
            self.print_status("PLC未连接", "ERROR")
            return False

        try:
            self.print_status("测试读取线圈，地址1-6", "INFO")

            # 读取线圈
            result = self.client.read_coils(1, 6, unit=self.unit_id)

            if not result.isError():
                coils = result.bits[:6]  # 只取前6个
                self.print_status(f"成功读取{len(coils)}个线圈", "SUCCESS")

                # 显示线圈状态
                for i, coil in enumerate(coils):
                    status = "ON" if coil else "OFF"
                    print(f"    线圈{i+1}: {status}")

                return True
            else:
                self.print_status(f"读取线圈失败: {result}", "ERROR")
                return False

        except Exception as e:
            self.print_status(f"读取线圈异常: {e}", "ERROR")
            return False

    def disconnect(self):
        """断开连接"""
        try:
            if self.client.is_socket_open():
                self.client.close()
                self.print_status("已断开PLC连接", "INFO")
        except Exception as e:
            self.print_status(f"断开连接异常: {e}", "WARNING")
    
    def run_full_test(self):
        """运行完整测试"""
        self.print_status("开始Modbus PLC连接完整测试", "INFO")
        print("=" * 60)

        test_results = []

        # 测试1: 基本连接
        print("\n1. 基本连接测试")
        print("-" * 30)
        result = self.test_basic_connection()
        test_results.append(("基本连接", result))

        if not result:
            self.print_status("基本连接失败，跳过后续测试", "ERROR")
            return False

        # 测试2: PLC信息
        print("\n2. PLC信息获取")
        print("-" * 30)
        result = self.get_plc_info()
        test_results.append(("PLC信息", result))

        # 测试3: 寄存器读取
        print("\n3. 寄存器读取测试")
        print("-" * 30)
        result = self.test_register_read()
        test_results.append(("寄存器读取", result))

        # 测试4: 连续读取
        print("\n4. 连续读取测试")
        print("-" * 30)
        result = self.test_continuous_read(duration=10, interval=0.5)
        test_results.append(("连续读取", result))

        # 测试5: 线圈读取
        print("\n5. 线圈读取测试")
        print("-" * 30)
        result = self.test_coil_read()
        test_results.append(("线圈读取", result))

        # 显示测试结果
        print("\n" + "=" * 60)
        self.print_status("测试结果汇总:", "INFO")

        passed = 0
        total = len(test_results)

        for test_name, result in test_results:
            status = "PASS" if result else "FAIL"
            status_symbol = "✅" if result else "❌"
            print(f"    {status_symbol} {test_name}: {status}")
            if result:
                passed += 1

        print(f"\n总体结果: {passed}/{total} 测试通过")

        if passed == total:
            self.print_status("所有测试通过! PLC连接正常", "SUCCESS")
            return True
        else:
            self.print_status(f"有{total-passed}个测试失败，请检查配置", "ERROR")
            return False

def main():
    """主函数"""
    print("Modbus PLC连接测试工具")
    print("=" * 60)

    # 解析命令行参数
    if len(sys.argv) > 1:
        plc_ip = sys.argv[1]
    else:
        plc_ip = input("请输入PLC IP地址 [192.168.1.10]: ").strip()
        if not plc_ip:
            plc_ip = "192.168.1.10"

    print(f"目标PLC: {plc_ip}")

    # 创建测试器
    tester = ModbusConnectionTester(plc_ip)

    try:
        # 运行测试
        success = tester.run_full_test()

        if success:
            print("\n🎉 测试完成! PLC连接和数据读取功能正常")
            print("您可以继续配置和运行主程序")
        else:
            print("\n⚠️  测试发现问题，请检查:")
            print("1. PLC IP地址是否正确")
            print("2. 网络连接是否正常")
            print("3. PLC是否启用了Modbus TCP通信")
            print("4. 防火墙设置是否正确")
            print("5. Modbus从站ID是否正确")

    except KeyboardInterrupt:
        print("\n\n用户中断测试")
    except Exception as e:
        print(f"\n测试过程中发生异常: {e}")
    finally:
        tester.disconnect()

if __name__ == "__main__":
    main()
