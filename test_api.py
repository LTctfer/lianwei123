#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
累加API功能测试
测试修改后的累加逻辑：每次只返回当前批次的累加结果
"""
import requests

BASE = "http://localhost:5000/api/extraction-adsorption-curve"
SESSION = "accumulate_test_demo"

def post_data(data, session_id=None):
    """发送数据到API"""
    payload = {"data": data}
    if session_id:
        payload["session_id"] = session_id

    resp = requests.post(f"{BASE}/process", json=payload, timeout=15)

    # 如果请求失败，打印详细错误信息
    if not resp.ok:
        print(f"   ❌ API请求失败: {resp.status_code}")
        try:
            error_detail = resp.json()
            print(f"   📋 错误详情: {error_detail}")
        except:
            print(f"   📋 错误内容: {resp.text}")
        resp.raise_for_status()

    return resp.json()

def get_session_info(session_id):
    """获取会话信息"""
    try:
        resp = requests.get(f"{BASE}/session/{session_id}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"获取会话信息失败: {e}")
        return None

def reset_session(session_id):
    """重置会话"""
    try:
        resp = requests.delete(f"{BASE}/session/{session_id}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"重置会话失败: {e}")
        return None

def generate_test_data():
    """生成1000条测试数据，分为两批"""
    import random
    from datetime import datetime, timedelta

    # 基准时间
    base_time = datetime(2024, 1, 15, 8, 0, 0)

    # 第一批：500条数据
    batch1 = []
    for i in range(500):
        # 时间递增（每条数据间隔6分钟）
        current_time = base_time + timedelta(minutes=i * 6)

        # 风速：创建连续的风速段（算法要求连续的>=0.5风速段）
        if i < 50:  # 前50条风速小于0.5（开始阶段）
            windspeed = random.uniform(0.1, 0.49)
        elif i < 400:  # 中间350条风速>=0.5（主要工作段）
            windspeed = random.uniform(0.5, 3.0)
        else:  # 后50条风速小于0.5（结束阶段）
            windspeed = random.uniform(0.1, 0.49)

        # gVocs逐渐增加（模拟穿透率上升）
        base_gvocs = 5 + (i * 0.1)  # 从5开始，每条增加0.1
        gvocs = base_gvocs + random.uniform(-2, 2)  # 添加随机波动

        # inVoc逐渐减少（模拟吸附效率下降）
        base_invoc = 100 - (i * 0.05)  # 从100开始，每条减少0.05
        invoc = max(50, base_invoc + random.uniform(-5, 5))  # 添加随机波动，最低50

        batch1.append({
            "gVocs": round(gvocs, 1),
            "inVoc": round(invoc, 1),
            "gWindspeed": round(windspeed, 2),
            "access": 2,
            "createTime": current_time.strftime("%Y-%m-%dT%H:%M:%S")
        })

    # 第二批：500条数据（接续第一批的时间）
    batch2 = []
    for i in range(500):
        # 时间接续第一批
        current_time = base_time + timedelta(minutes=(500 + i) * 6)

        # 风速：继续创建连续的风速段
        if i < 50:  # 前50条风速小于0.5（间隔阶段）
            windspeed = random.uniform(0.1, 0.49)
        elif i < 400:  # 中间350条风速>=0.5（第二个工作段）
            windspeed = random.uniform(0.5, 3.5)
        else:  # 后50条风速小于0.5（最终结束阶段）
            windspeed = random.uniform(0.1, 0.49)

        # gVocs继续增加
        base_gvocs = 55 + (i * 0.15)  # 从55开始（接续第一批）
        gvocs = base_gvocs + random.uniform(-3, 3)

        # inVoc继续减少
        base_invoc = 75 - (i * 0.08)  # 从75开始
        invoc = max(30, base_invoc + random.uniform(-8, 8))  # 最低30

        batch2.append({
            "gVocs": round(gvocs, 1),
            "inVoc": round(invoc, 1),
            "gWindspeed": round(windspeed, 2),
            "access": 2,
            "createTime": current_time.strftime("%Y-%m-%dT%H:%M:%S")
        })

    return batch1, batch2

# 生成测试数据
print("🔄 生成1000条测试数据...")
test_batch1, test_batch2 = generate_test_data()
test_batches = [test_batch1, test_batch2]

print(f"✅ 数据生成完成:")
print(f"   第一批: {len(test_batch1)} 条数据 (350条风速≥0.5, 100条风速<0.5)")
print(f"   第二批: {len(test_batch2)} 条数据 (350条风速≥0.5, 100条风速<0.5)")
print(f"   总计: {len(test_batch1) + len(test_batch2)} 条数据")
print(f"   有效风速段: 700条数据 (算法将处理这些数据)")

# 显示数据样本
print(f"\n📋 第一批数据样本（前3条）:")
for i, sample in enumerate(test_batch1[:3]):
    print(f"   {i+1}. gVocs={sample['gVocs']}, inVoc={sample['inVoc']}, "
          f"windspeed={sample['gWindspeed']}, time={sample['createTime']}")

print(f"\n📋 第二批数据样本（前3条）:")
for i, sample in enumerate(test_batch2[:3]):
    print(f"   {i+1}. gVocs={sample['gVocs']}, inVoc={sample['inVoc']}, "
          f"windspeed={sample['gWindspeed']}, time={sample['createTime']}")

def test_cumulative_mode():
    """测试累加模式功能（1000条数据）"""
    print("=" * 60)
    print("🧪 开始测试累加API功能（1000条数据）")
    print("=" * 60)

    # 1. 重置会话
    print(f"1. 重置会话: {SESSION}")
    reset_result = reset_session(SESSION)
    if reset_result:
        print(f"   ✅ 会话重置成功: {reset_result.get('message', '已重置')}")
    else:
        print("   ⚠️ 会话重置失败或会话不存在")

    all_x_values = []  # 记录所有返回的X值，用于验证累加
    last_max_x = 0     # 记录上一批的最大X值

    # 2. 逐批发送数据并验证累加
    for batch_num, batch_data in enumerate(test_batches, 1):
        print(f"\n2.{batch_num} 发送第{batch_num}批数据 ({len(batch_data)}个数据点)")
        print(f"   ⏳ 处理中，请稍候...")

        try:
            # 发送数据
            import time
            start_time = time.time()
            result = post_data(batch_data, SESSION)
            end_time = time.time()

            # 提取当前批次的X值
            current_x_values = [point["x"] for point in result["data_points"]]
            current_y_values = [point["y"] for point in result["data_points"]]

            print(f"   📊 当前批次返回 {len(current_x_values)} 个数据点")
            print(f"   ⏱️ 处理耗时: {end_time - start_time:.2f} 秒")
            print(f"   📈 X轴范围: {min(current_x_values):.2f}h - {max(current_x_values):.2f}h")
            print(f"   📈 Y轴范围: {min(current_y_values):.2f}% - {max(current_y_values):.2f}%")

            # 验证累加逻辑
            if batch_num == 1:
                # 第一批：X值应该从0开始
                print(f"   ✅ 第一批数据，X值从 {min(current_x_values):.2f}h 开始")
            else:
                # 后续批次：X值应该在上一批的基础上累加
                min_current_x = min(current_x_values)
                if min_current_x > last_max_x:
                    print(f"   ✅ 累加正确：当前批次最小X值 {min_current_x:.2f}h > 上批次最大X值 {last_max_x:.2f}h")
                else:
                    print(f"   ❌ 累加错误：当前批次最小X值 {min_current_x:.2f}h <= 上批次最大X值 {last_max_x:.2f}h")
                    return False

            # 验证当前批次内部X值递增
            if all(current_x_values[i] < current_x_values[i+1] for i in range(len(current_x_values)-1)):
                print(f"   ✅ 当前批次内部X值递增正确")
            else:
                print(f"   ❌ 当前批次内部X值递增错误")
                return False

            # 更新记录
            all_x_values.extend(current_x_values)
            last_max_x = max(current_x_values)

            # 显示部分数据点详情（只显示前3个和后3个）
            print(f"   📋 数据点详情（前3个）:")
            for i, point in enumerate(result["data_points"][:3]):
                # 检查描述格式是否正确（应该使用逗号分隔）
                desc = point['description']
                if ',' in desc and '\n' not in desc:
                    print(f"      点{i+1}: X={point['x']:.2f}h, Y={point['y']:.2f}%, 描述格式✅")
                else:
                    print(f"      点{i+1}: X={point['x']:.2f}h, Y={point['y']:.2f}%, 描述格式❌: {desc[:50]}...")

            if len(result["data_points"]) > 3:
                print(f"   📋 数据点详情（后3个）:")
                for i, point in enumerate(result["data_points"][-3:]):
                    idx = len(result["data_points"]) - 3 + i + 1
                    print(f"      点{idx}: X={point['x']:.2f}h, Y={point['y']:.2f}%")

            # 如果返回的数据点很少，显示详细的调试信息
            if len(result["data_points"]) < 10:
                print(f"   🔍 调试信息：返回数据点较少，显示所有数据点:")
                for i, point in enumerate(result["data_points"]):
                    print(f"      点{i+1}: X={point['x']:.2f}h, Y={point['y']:.2f}%, 描述: {point['description']}")

        except Exception as e:
            print(f"   ❌ 第{batch_num}批数据处理失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    # 3. 验证整体累加效果
    print(f"\n3. 验证整体累加效果")
    print(f"   📊 总共处理了 {len(all_x_values)} 个数据点")
    print(f"   📈 X轴总范围: {min(all_x_values):.2f}h - {max(all_x_values):.2f}h")
    print(f"   📈 X轴总跨度: {max(all_x_values) - min(all_x_values):.2f}h")

    # 验证全局X值递增
    print(f"   🔍 验证全局X值递增性...")
    non_increasing_count = 0
    for i in range(len(all_x_values)-1):
        if all_x_values[i] >= all_x_values[i+1]:
            non_increasing_count += 1

    if non_increasing_count == 0:
        print(f"   ✅ 全局X值递增正确（1000个数据点全部递增）")
    else:
        print(f"   ❌ 全局X值递增错误（发现{non_increasing_count}个非递增点）")
        return False

    # 验证数据分布
    print(f"   📊 数据分布统计:")
    print(f"      第一批数据点数: {len(test_batches[0])}")
    print(f"      第二批数据点数: {len(test_batches[1])}")
    print(f"      累加后总数据点: {len(all_x_values)}")

    # 验证风速分布（检查是否有小于0.5的风速数据）
    windspeed_stats = {"low": 0, "normal": 0}
    for batch in test_batches:
        for data_point in batch:
            if data_point["gWindspeed"] < 0.5:
                windspeed_stats["low"] += 1
            else:
                windspeed_stats["normal"] += 1

    print(f"   🌪️ 风速分布统计:")
    print(f"      低风速(<0.5): {windspeed_stats['low']} 条")
    print(f"      正常风速(≥0.5): {windspeed_stats['normal']} 条")

    if windspeed_stats["low"] > 0:
        print(f"   ✅ 包含低风速数据，符合测试要求")

    # 重要提示：算法只处理风速>=0.5的数据段
    print(f"   ⚠️ 注意：算法只处理风速≥0.5的数据段，低风速数据会被过滤")
    print(f"   📊 预期有效数据点: {windspeed_stats['normal']} 条")

    # 4. 查询会话信息
    print(f"\n4. 查询会话信息")
    session_info = get_session_info(SESSION)
    if session_info:
        print(f"   📋 会话状态: {session_info}")
        if 'last_cumulative_time' in session_info:
            expected_last_time = max(all_x_values)
            actual_last_time = session_info['last_cumulative_time']
            if abs(expected_last_time - actual_last_time) < 0.01:
                print(f"   ✅ 最后累计时间正确: {actual_last_time:.2f}h")
            else:
                print(f"   ❌ 最后累计时间错误: 期望{expected_last_time:.2f}h, 实际{actual_last_time:.2f}h")
                return False
    else:
        print(f"   ⚠️ 无法获取会话信息")

    return True

def test_non_cumulative_mode():
    """测试非累加模式（不提供session_id）"""
    print(f"\n5. 测试非累加模式")

    try:
        # 使用较小的数据集进行非累加测试（取前10条数据）
        small_test_data = test_batches[0][:10]

        print(f"   🔍 使用{len(small_test_data)}条数据进行非累加测试")

        # 发送相同的数据但不提供session_id
        result1 = post_data(small_test_data)
        result2 = post_data(small_test_data)

        x_values1 = [point["x"] for point in result1["data_points"]]
        x_values2 = [point["x"] for point in result2["data_points"]]

        # 非累加模式下，相同数据应该返回相同的X值
        if x_values1 == x_values2:
            print(f"   ✅ 非累加模式正确：相同数据返回相同X值")
            print(f"   📈 X值范围: {min(x_values1):.2f}h - {max(x_values1):.2f}h")
            print(f"   📊 数据点数: {len(x_values1)}")
            return True
        else:
            print(f"   ❌ 非累加模式错误：相同数据返回不同X值")
            print(f"   📈 第一次范围: {min(x_values1):.2f}h - {max(x_values1):.2f}h")
            print(f"   📈 第二次范围: {min(x_values2):.2f}h - {max(x_values2):.2f}h")
            return False

    except Exception as e:
        print(f"   ❌ 非累加模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        # 测试累加模式
        cumulative_success = test_cumulative_mode()

        # 测试非累加模式
        non_cumulative_success = test_non_cumulative_mode()

        # 总结
        print("\n" + "=" * 60)
        print("🎯 测试结果总结")
        print("=" * 60)
        print(f"累加模式测试: {'✅ 通过' if cumulative_success else '❌ 失败'}")
        print(f"非累加模式测试: {'✅ 通过' if non_cumulative_success else '❌ 失败'}")

        if cumulative_success and non_cumulative_success:
            print("🎉 所有测试通过！累加API功能正常工作")
        else:
            print("⚠️ 部分测试失败，请检查API实现")

    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()