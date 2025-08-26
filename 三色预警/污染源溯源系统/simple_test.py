#!/usr/bin/env python3
"""
简化测试脚本 - 不依赖外部包
测试基本Python功能和模块结构
"""

import sys
import os
import traceback
from datetime import datetime

def test_basic_python():
    """测试基本Python功能"""
    print("=" * 50)
    print("测试基本Python功能...")
    
    try:
        # 测试基本数据类型
        test_list = [1, 2, 3, 4, 5]
        test_dict = {'a': 1, 'b': 2}
        test_str = "Hello World"
        
        # 测试基本运算
        result = sum(test_list)
        
        print(f"✓ 基本数据类型测试通过")
        print(f"  列表求和: {result}")
        print(f"  字典访问: {test_dict['a']}")
        print(f"  字符串长度: {len(test_str)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 基本Python功能测试失败: {e}")
        return False

def test_file_structure():
    """测试文件结构"""
    print("=" * 50)
    print("测试项目文件结构...")
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 检查必要的目录
        required_dirs = ['algorithms', 'core', 'web']
        missing_dirs = []
        
        for dir_name in required_dirs:
            dir_path = os.path.join(current_dir, dir_name)
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            print(f"✗ 缺少目录: {missing_dirs}")
            return False
        
        # 检查必要的文件
        required_files = [
            'config.py',
            'requirements.txt',
            'run.py',
            'algorithms/genetic_algorithm.py',
            'algorithms/gaussian_plume.py',
            'core/source_inversion.py',
            'web/app.py'
        ]
        
        missing_files = []
        
        for file_name in required_files:
            file_path = os.path.join(current_dir, file_name)
            if not os.path.exists(file_path):
                missing_files.append(file_name)
        
        if missing_files:
            print(f"✗ 缺少文件: {missing_files}")
            return False
        
        print("✓ 项目文件结构完整")
        print(f"  项目根目录: {current_dir}")
        print(f"  包含目录: {required_dirs}")
        print(f"  核心文件: {len(required_files)} 个")
        
        return True
        
    except Exception as e:
        print(f"✗ 文件结构测试失败: {e}")
        return False

def test_module_syntax():
    """测试模块语法"""
    print("=" * 50)
    print("测试模块语法...")
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 测试Python文件语法
        python_files = [
            'config.py',
            'run.py',
            'algorithms/genetic_algorithm.py',
            'algorithms/pattern_search.py',
            'algorithms/gaussian_plume.py',
            'algorithms/data_fusion.py',
            'core/source_inversion.py'
        ]
        
        syntax_errors = []
        
        for file_name in python_files:
            file_path = os.path.join(current_dir, file_name)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    
                    # 编译检查语法
                    compile(code, file_path, 'exec')
                    
                except SyntaxError as e:
                    syntax_errors.append(f"{file_name}: {e}")
                except Exception as e:
                    # 忽略导入错误，只关注语法错误
                    pass
        
        if syntax_errors:
            print("✗ 发现语法错误:")
            for error in syntax_errors:
                print(f"  {error}")
            return False
        
        print(f"✓ 模块语法检查通过")
        print(f"  检查文件数: {len(python_files)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 模块语法测试失败: {e}")
        return False

def test_config_loading():
    """测试配置加载"""
    print("=" * 50)
    print("测试配置加载...")
    
    try:
        # 添加项目路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # 尝试导入配置
        try:
            import config
            print("✓ 配置模块导入成功")
            
            # 测试配置类
            if hasattr(config, 'Config'):
                config_instance = config.Config()
                print("✓ 配置类实例化成功")
                return True
            else:
                print("✗ 配置类不存在")
                return False
                
        except ImportError as e:
            print(f"✗ 配置模块导入失败: {e}")
            return False
        
    except Exception as e:
        print(f"✗ 配置加载测试失败: {e}")
        return False

def create_sample_data():
    """创建示例数据文件"""
    print("=" * 50)
    print("创建示例数据文件...")
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, 'sample_data')
        
        # 创建数据目录
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 创建监测站数据示例
        monitoring_data = """station_id,x,y,pm25,wind_speed,wind_direction,temperature,humidity,timestamp
S001,100,100,45.2,3.5,45,25.1,60.5,2024-01-01 10:00:00
S002,200,150,52.8,4.2,90,24.8,65.2,2024-01-01 10:00:00
S003,150,200,48.6,3.8,60,25.5,58.9,2024-01-01 10:00:00
S001,100,100,47.1,3.2,50,25.3,61.2,2024-01-01 11:00:00
S002,200,150,54.3,4.5,85,24.6,66.1,2024-01-01 11:00:00
S003,150,200,49.8,3.6,65,25.2,59.5,2024-01-01 11:00:00"""
        
        # 保存监测数据
        monitoring_file = os.path.join(data_dir, 'monitoring_data.csv')
        with open(monitoring_file, 'w', encoding='utf-8') as f:
            f.write(monitoring_data)
        
        # 创建气象数据示例
        meteorological_data = """timestamp,wind_speed,wind_direction,temperature,humidity,pressure,stability_class
2024-01-01 10:00:00,3.5,45,25.1,60.5,1013.2,D
2024-01-01 11:00:00,3.8,50,25.3,61.2,1013.1,D
2024-01-01 12:00:00,4.1,55,25.8,59.8,1012.9,C
2024-01-01 13:00:00,4.5,60,26.2,58.5,1012.7,C"""
        
        # 保存气象数据
        meteorological_file = os.path.join(data_dir, 'meteorological_data.csv')
        with open(meteorological_file, 'w', encoding='utf-8') as f:
            f.write(meteorological_data)
        
        print("✓ 示例数据文件创建成功")
        print(f"  数据目录: {data_dir}")
        print(f"  监测数据: monitoring_data.csv")
        print(f"  气象数据: meteorological_data.csv")
        
        return True
        
    except Exception as e:
        print(f"✗ 示例数据创建失败: {e}")
        return False

def main():
    """主测试函数"""
    print("污染源溯源系统 - 简化测试")
    print(f"Python版本: {sys.version}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行所有测试
    tests = [
        ("基本Python功能", test_basic_python),
        ("项目文件结构", test_file_structure),
        ("模块语法检查", test_module_syntax),
        ("配置加载", test_config_loading),
        ("示例数据创建", create_sample_data)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name}测试过程中发生异常: {e}")
            traceback.print_exc()
            results.append((test_name, False))
    
    # 输出测试结果总结
    print("=" * 50)
    print("测试结果总结:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 基础测试全部通过！")
        print("\n📋 下一步操作:")
        print("1. 安装Python依赖包: pip install -r requirements.txt")
        print("2. 运行完整测试: python test_system.py")
        print("3. 启动Web界面: python run.py")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关问题。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)