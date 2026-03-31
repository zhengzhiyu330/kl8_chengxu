"""
API 测试脚本
用于测试快乐 8 智能预测 API 的各个接口
"""

import requests
import time
import json

BASE_URL = 'http://localhost:5000'


def test_health():
    """测试健康检查接口"""
    print("\n【测试健康检查】")
    try:
        response = requests.get(f'{BASE_URL}/api/health')
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_latest_prediction():
    """测试获取最新预测接口"""
    print("\n【测试获取最新预测】")
    try:
        response = requests.get(f'{BASE_URL}/api/prediction/latest')
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"期号: {data['data']['period']}")
            print(f"预测号码: {data['data']['predicted_numbers']}")
            print(f"胆码: {data['data']['dan_codes']}")
            print(f"生成时间: {data['data']['generated_at']}")
            return True
        else:
            print(f"响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_prediction_history():
    """测试获取历史预测接口"""
    print("\n【测试获取历史预测】")
    try:
        response = requests.get(f'{BASE_URL}/api/prediction/history?limit=5')
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"总数: {data['data']['total']}")
            print(f"预测记录数: {len(data['data']['predictions'])}")
            return True
        else:
            print(f"响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_lottery_data():
    """测试获取开奖数据接口"""
    print("\n【测试获取开奖数据】")
    try:
        response = requests.get(f'{BASE_URL}/api/lottery/data?limit=10')
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"当前期号: {data['data']['current_draw']}")
            print(f"期数: {data['data']['total']}")
            return True
        else:
            print(f"响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_periods_data():
    """测试获取推荐数据接口"""
    print("\n【测试获取推荐数据】")
    try:
        response = requests.get(f'{BASE_URL}/api/lottery/periods?limit=5')
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"期数: {data['data']['total']}")
            if data['data']['periods']:
                first_period = data['data']['periods'][0]
                print(f"最新期号: {first_period['issue']}")
                print(f"开奖号码: {first_period['lottery_numbers'][:10]}...")
            return True
        else:
            print(f"响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_backtest_stats():
    """测试获取回测统计接口"""
    print("\n【测试获取回测统计】")
    try:
        response = requests.get(f'{BASE_URL}/api/analysis/backtest')
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            stats = data['data']
            print(f"回测期数: {stats['total_periods']}")
            print(f"最优命中率: {stats['max_hit_rate']:.1f}%")
            print(f"高频推荐命中率: {stats['high_freq_hit_rate']:.1f}%")
            return True
        else:
            print(f"响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_periodicity_analysis():
    """测试获取周期性分析接口"""
    print("\n【测试获取周期性分析】")
    try:
        response = requests.get(f'{BASE_URL}/api/analysis/periodicity')
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            result = data['data']
            print(f"最优回测期数: {result['optimal_periods']}")
            return True
        else:
            print(f"响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_generate_prediction():
    """测试生成预测接口"""
    print("\n【测试生成预测】")
    try:
        response = requests.post(f'{BASE_URL}/api/prediction/generate')
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_period_detail(issue=None):
    """测试获取单期详情接口"""
    print("\n【测试获取单期详情】")
    
    # 如果没有提供期号，先获取最新期号
    if not issue:
        try:
            response = requests.get(f'{BASE_URL}/api/lottery/periods?limit=1')
            if response.status_code == 200:
                periods = response.json()['data']['periods']
                if periods:
                    issue = periods[0]['issue']
                    print(f"使用期号: {issue}")
        except:
            pass
    
    if not issue:
        print("❌ 无法获取期号")
        return False
    
    try:
        response = requests.get(f'{BASE_URL}/api/periods/detail?issue={issue}')
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            period_data = data['data']
            print(f"期号: {period_data['period']['issue']}")
            print(f"9 宫格行数: {len(period_data['grid'])}")
            print(f"高频推荐号数: {len(period_data['high_freq_numbers'])}")
            print(f"总命中数: {period_data['stats']['total_hits']}")
            print(f"命中率: {period_data['stats']['hit_rate']:.1f}%")
            return True
        else:
            print(f"响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_all_data():
    """测试获取所有数据接口"""
    print("\n【测试获取所有数据】")
    try:
        response = requests.get(f'{BASE_URL}/api/all-data')
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"最后更新: {data['data']['last_update']}")
            print(f"是否正在更新: {data['data']['is_updating']}")
            print(f"预测数据: {'✓' if data['data']['prediction'] else '✗'}")
            print(f"回测数据: {'✓' if data['data']['backtest'] else '✗'}")
            print(f"周期性数据: {'✓' if data['data']['periodicity'] else '✗'}")
            return True
        else:
            print(f"响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 80)
    print("快乐 8 智能预测 API 测试")
    print("=" * 80)
    
    results = []
    
    # 测试健康检查
    results.append(("健康检查", test_health()))
    
    # 测试获取所有数据
    results.append(("获取所有数据", test_all_data()))
    
    # 测试获取最新预测
    results.append(("获取最新预测", test_latest_prediction()))
    
    # 测试获取历史预测
    results.append(("获取历史预测", test_prediction_history()))
    
    # 测试获取开奖数据
    results.append(("获取开奖数据", test_lottery_data()))
    
    # 测试获取推荐数据
    results.append(("获取推荐数据", test_periods_data()))
    
    # 测试获取回测统计
    results.append(("获取回测统计", test_backtest_stats()))
    
    # 测试获取周期性分析
    results.append(("获取周期性分析", test_periodicity_analysis()))
    
    # 测试获取单期详情
    results.append(("获取单期详情", test_period_detail()))
    
    # 测试生成预测（可选）
    print("\n" + "=" * 80)
    print("是否要测试生成预测接口？这可能需要较长时间...")
    print("输入 'y' 继续测试，其他键跳过")
    choice = input("> ")
    if choice.lower() == 'y':
        results.append(("生成预测", test_generate_prediction()))
        
        # 等待一段时间让预测生成
        print("\n等待 10 秒让预测生成...")
        time.sleep(10)
        
        # 再次测试最新预测
        results.append(("获取最新预测（更新后）", test_latest_prediction()))
    
    # 打印测试结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:30s} {status}")
    
    print("\n" + "=" * 80)
    print(f"总计: {passed}/{total} 通过")
    print("=" * 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试已中断")
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback
        traceback.print_exc()
