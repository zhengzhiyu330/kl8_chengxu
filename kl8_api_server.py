"""
================================================================================
快乐 8 智能预测系统 - API 服务器
适配小程序前端接口
================================================================================

提供以下 API 接口：
1. GET /api/prediction/latest - 获取最新一期预测
2. GET /api/prediction/history - 获取历史预测记录
3. GET /api/lottery/data - 获取开奖数据
4. GET /api/lottery/periods - 获取推荐数据
5. GET /api/analysis/backtest - 获取回测统计
6. POST /api/prediction/generate - 生成新的预测
7. GET /api/analysis/periodicity - 获取周期性分析

作者：基于 kl8_intelligent_prediction.py 的 API 适配版
日期：2026-03-30
"""

from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import json
from collections import Counter, defaultdict
from datetime import datetime
from itertools import islice
from typing import Dict, List, Set, Tuple
import threading
import time
import os

# 线程锁，用于保护共享数据
cache_lock = threading.Lock()

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# ==================== 配置部分 ====================

KL8_HTML_URL = 'https://www.17500.cn/tool/kl8-allm.html'
KL8_API_URL = 'https://m.17500.cn/tgj/api/kl8/getTbList?action=zhfb&page=1&limit=100&orderby=asc&start_issue=0&end_issue=0&week=all'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': 'https://m.17500.cn/tgj/kl8-kjfb.html'
}

BASE_DIMENSIONS = {
    'hot_number': 30,
    'cold_number': 12,
    'omission': 18,
    'diagonal': 10,
    'consecutive': 8,
    'repeat': 10,
    'sum_trend': 5,
    'odd_even': 5,
    'big_small': 3,
    'zone_hot': 8,
    'tail_pattern': 6,
    'head_focus': 5,
    'modulo_3': 5,
}

# 缓存目录（与脚本同目录下的 cache/，便于部署在 /opt/kl8-api 时权限与路径一致）
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(_BASE_DIR, 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# 全局缓存
cache_data = {
    'lottery_data': None,
    'periods_data': None,
    'prediction_result': None,
    'backtest_stats': None,
    'periodicity_result': None,
    'all_predictions': None,
    'last_update': None,
    'is_updating': False
}


# ==================== 第一部分：数据获取 ====================

class DataFetcher:
    """数据获取器"""
    
    def __init__(self):
        pass
    
    def fetch_lottery_api_data(self, limit=100):
        """从 API 获取开奖数据"""
        try:
            response = requests.get(KL8_API_URL, headers=API_HEADERS, timeout=10)
            response.raise_for_status()
            data = json.loads(response.text)
            
            if 'data' not in data or 'data' not in data['data']:
                raise ValueError("API 返回数据格式不正确")
            
            return data
        except Exception as e:
            print(f"✗ API 数据获取失败：{e}")
            return None
    
    def fetch_html_recommend_data(self, limit=30):
        """从 HTML 页面获取推荐数据"""
        try:
            response = requests.get(KL8_HTML_URL, headers=HEADERS, timeout=15)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            periods_data = {}
            
            dd_tags = soup.find_all('dd', class_='flex lineb')
            
            for dd in dd_tags:
                issue_elem = dd.find('p')
                if not issue_elem:
                    continue
                
                issue = issue_elem.get_text(strip=True)
                
                if issue not in periods_data:
                    periods_data[issue] = {
                        'issue': issue,
                        'lottery_numbers': [],
                        'kaiji': [],
                        'shiji': [],
                        'jin': [],
                        'guanzhu': [],
                        'duiying': [],
                        'date': ''
                    }
                
                date_elem = dd.find('p', class_='fcol9')
                if date_elem:
                    periods_data[issue]['date'] = date_elem.get_text(strip=True)
                
                winnum_elem = dd.find('p', class_='ball', attrs={'data-name': re.compile(r'winnum_')})
                if winnum_elem:
                    numbers = []
                    b_tags = winnum_elem.find_all('b')
                    for b in b_tags:
                        num_text = b.get_text(strip=True)
                        if num_text.isdigit():
                            numbers.append(int(num_text))
                    periods_data[issue]['lottery_numbers'] = sorted(numbers)
                
                data_elements = dd.find_all(attrs={'data-name': True, 'data-v': True})
                for elem in data_elements:
                    data_name = elem.get('data-name', '')
                    data_value = elem.get('data-v', '')
                    
                    numbers = [int(n) for n in data_value.split() if n.isdigit()]
                    
                    i_tag = elem.find('i')
                    i_text = i_tag.get_text(strip=True) if i_tag else ''
                    
                    if 'kjh_' in data_name or i_text == '开':
                        periods_data[issue]['kaiji'] = numbers
                    elif 'sjh_' in data_name or i_text == '试':
                        periods_data[issue]['shiji'] = numbers
                    elif 'jinma_' in data_name or i_text == '金':
                        periods_data[issue]['jin'] = numbers
                    elif 'threema_' in data_name or i_text == '关':
                        periods_data[issue]['guanzhu'] = numbers
                    elif 'duiyingma_' in data_name or i_text == '对':
                        periods_data[issue]['duiying'] = numbers
            
            sorted_periods = sorted(periods_data.values(), key=lambda x: x['issue'], reverse=True)
            return sorted_periods[:limit]
        
        except Exception as e:
            print(f"✗ HTML 推荐数据获取失败：{e}")
            return []
    
    def parse_api_data(self, api_data):
        """解析 API 数据"""
        lottery_data = {
            'current_draw': '',
            'historical_draws': {},
            'sorted_issues': []
        }
        
        pattern = r"<span class='fred'>(\d+)</span>"
        
        for item in api_data['data']['data']:
            issue = str(item['issue'])
            numbers_html = item['winnum']
            numbers = [int(m) for m in re.findall(pattern, numbers_html)]
            
            if not numbers or len(numbers) != 20:
                continue
            
            zhfb = item.get('zhfb', {})
            
            lottery_data['historical_draws'][issue] = {
                'numbers': sorted(numbers),
                'date': item['kjdate'],
                'sum': zhfb.get('hz', sum(numbers)),
                'span': zhfb.get('kd', max(numbers) - min(numbers)),
                'odd_even_ratio': zhfb.get('jo', ''),
                'big_small_ratio': zhfb.get('dx', ''),
                'zone_ratio': zhfb.get('zh', ''),
                'lye_ratio': zhfb.get('lye', ''),
                'ac_value': zhfb.get('hw', 0),
                'avg': zhfb.get('avg', 0)
            }
            
            if not lottery_data['current_draw'] or int(issue) > int(lottery_data['current_draw']):
                lottery_data['current_draw'] = issue
        
        lottery_data['sorted_issues'] = sorted(lottery_data['historical_draws'].keys())
        
        return lottery_data


# ==================== 第二部分：周期性分析器 ====================

class PeriodicityAnalyzer:
    """周期性分析器"""
    
    def __init__(self, lottery_data: Dict):
        self.lottery_data = lottery_data
        self.sorted_issues = lottery_data['sorted_issues'] if lottery_data else []
    
    def analyze_optimal_backtest_periods(self) -> Dict:
        """分析最优回测期数"""
        test_ranges = [5, 7, 10, 12, 15, 20, 25, 30]
        results = {}
        
        for period_count in test_ranges:
            if len(self.sorted_issues) < period_count:
                continue
            
            hit_rates = []
            
            for start_idx in range(len(self.sorted_issues) - period_count):
                end_idx = start_idx + period_count
                test_issues = self.sorted_issues[start_idx:end_idx]
                
                repeat_counts = []
                for i in range(1, len(test_issues)):
                    prev_nums = set(self.lottery_data['historical_draws'][test_issues[i-1]]['numbers'])
                    curr_nums = set(self.lottery_data['historical_draws'][test_issues[i]]['numbers'])
                    repeat_counts.append(len(prev_nums & curr_nums))
                
                if repeat_counts:
                    avg_repeat = sum(repeat_counts) / len(repeat_counts)
                    hit_rates.append(avg_repeat)
            
            if hit_rates:
                avg_hit_rate = sum(hit_rates) / len(hit_rates)
                std_dev = (sum((x - avg_hit_rate) ** 2 for x in hit_rates) / len(hit_rates)) ** 0.5
                stability = 1 - (std_dev / avg_hit_rate if avg_hit_rate > 0 else 1)
                results[period_count] = {
                    'avg_hit_rate': avg_hit_rate,
                    'std_dev': std_dev,
                    'stability': stability
                }
        
        if not results:
            return {'optimal_periods': 15, 'all_results': {}}
        
        best_period = max(results.items(), key=lambda x: x[1]['stability'])
        
        return {
            'optimal_periods': best_period[0],
            'all_results': results
        }


# ==================== 第三部分：多维度分析引擎 ====================

class MultiDimensionAnalyzer:
    """多维度分析器"""
    
    def __init__(self, lottery_data: Dict, dimension_weights: Dict):
        self.lottery_data = lottery_data
        self.weights = dimension_weights
        self.sorted_issues = lottery_data['sorted_issues'] if lottery_data else []
        self.number_stats = {}
        self.pattern_cache = {}
        
        if lottery_data:
            self._precompute_statistics()
            self._discover_patterns()
    
    def _precompute_statistics(self):
        """预计算统计数据"""
        if not self.lottery_data:
            return
        
        total_periods = len(self.sorted_issues)
        
        occurrence_count = [0] * 80
        current_absence = [0] * 80
        absence_history = [[] for _ in range(80)]
        
        for draw in self.lottery_data['historical_draws'].values():
            for num in draw['numbers']:
                if 1 <= num <= 80:
                    occurrence_count[num - 1] += 1
        
        for j in range(80):
            num = j + 1
            current_absence[j] = total_periods
            
            for idx in range(total_periods - 1, -1, -1):
                issue = self.sorted_issues[idx]
                numbers = self.lottery_data['historical_draws'][issue]['numbers']
                if num in numbers:
                    current_absence[j] = (total_periods - 1) - idx
                    break
        
        average_absence = []
        max_absence = []
        
        for j in range(80):
            num = j + 1
            last_idx = None
            
            for idx in range(total_periods):
                issue = self.sorted_issues[idx]
                numbers = self.lottery_data['historical_draws'][issue]['numbers']
                if num in numbers:
                    if last_idx is not None:
                        gap = idx - last_idx - 1
                        absence_history[j].append(gap)
                    last_idx = idx
            
            if last_idx is not None and last_idx < total_periods - 1:
                current_gap = (total_periods - 1) - last_idx
                absence_history[j].append(current_gap)
            
            avg_val = sum(absence_history[j]) / len(absence_history[j]) if absence_history[j] else float(total_periods)
            max_val = max(absence_history[j]) if absence_history[j] else total_periods
            
            average_absence.append(avg_val)
            max_absence.append(max_val)
        
        for num in range(1, 81):
            idx = num - 1
            self.number_stats[num] = {
                'total_count': occurrence_count[idx],
                'current_absence': current_absence[idx],
                'average_absence': average_absence[idx],
                'max_absence': max_absence[idx]
            }
        
        recent_10_issues = self.sorted_issues[-10:]
        recent_counts = Counter()
        for issue in recent_10_issues:
            draw = self.lottery_data['historical_draws'][issue]
            for num in draw['numbers']:
                recent_counts[num] += 1
        
        for num in range(1, 81):
            self.number_stats[num]['recent_10_count'] = recent_counts.get(num, 0)
    
    def _discover_patterns(self):
        """自动发现出号规律"""
        self.pattern_cache = {
            'hot_zones': self._find_hot_zones(),
            'hot_tails': self._find_hot_tails(),
            'hot_heads': self._find_hot_heads(),
            'modulo_trend': self._find_modulo_trend(),
            'diagonal_sequences': self._find_diagonal_sequences()
        }
    
    def _find_hot_zones(self) -> List[int]:
        zones = [(1, 20), (21, 40), (41, 60), (61, 80)]
        zone_counts = [0, 0, 0, 0]
        
        recent_issues = self.sorted_issues[-10:]
        for issue in recent_issues:
            draw = self.lottery_data['historical_draws'][issue]
            for num in draw['numbers']:
                for idx, (start, end) in enumerate(zones):
                    if start <= num <= end:
                        zone_counts[idx] += 1
        
        hot_zone_idx = zone_counts.index(max(zone_counts))
        return [hot_zone_idx + 1]
    
    def _find_hot_tails(self) -> List[int]:
        tail_counts = Counter()
        
        recent_issues = self.sorted_issues[-10:]
        for issue in recent_issues:
            draw = self.lottery_data['historical_draws'][issue]
            for num in draw['numbers']:
                tail = num % 10
                tail_counts[tail] += 1
        
        return [tail for tail, count in tail_counts.most_common(3)]
    
    def _find_hot_heads(self) -> List[int]:
        head_counts = Counter()
        
        recent_issues = self.sorted_issues[-10:]
        for issue in recent_issues:
            draw = self.lottery_data['historical_draws'][issue]
            for num in draw['numbers']:
                head = num // 10
                head_counts[head] += 1
        
        return [head for head, count in head_counts.most_common(2)]
    
    def _find_modulo_trend(self) -> int:
        modulo_counts = {0: 0, 1: 0, 2: 0}
        
        recent_issues = self.sorted_issues[-10:]
        for issue in recent_issues:
            draw = self.lottery_data['historical_draws'][issue]
            for num in draw['numbers']:
                mod = num % 3
                modulo_counts[mod] += 1
        
        return max(modulo_counts.items(), key=lambda x: x[1])[0]
    
    def _find_diagonal_sequences(self) -> Set[int]:
        diagonals = set()
        
        if len(self.sorted_issues) < 3:
            return diagonals
        
        for i in range(len(self.sorted_issues) - 2):
            curr_nums = set(self.lottery_data['historical_draws'][self.sorted_issues[i]]['numbers'])
            next_nums = set(self.lottery_data['historical_draws'][self.sorted_issues[i + 1]]['numbers'])
            next_next_nums = set(self.lottery_data['historical_draws'][self.sorted_issues[i + 2]]['numbers'])
            
            for num in curr_nums:
                if (num + 1) in next_nums and (num + 2) in next_next_nums:
                    diagonals.add(num + 2)
                if (num - 1) in next_nums and (num - 2) in next_next_nums:
                    diagonals.add(num - 2)
        
        return diagonals
    
    def get_latest_numbers(self, n=1):
        if not self.lottery_data or n > len(self.sorted_issues):
            return []
        
        issue = self.sorted_issues[-n]
        return self.lottery_data['historical_draws'][issue]['numbers']
    
    def analyze_number(self, num: int) -> float:
        """分析单个号码的综合评分"""
        if num not in self.number_stats:
            return 0.0
        
        stats = self.number_stats[num]
        score = 0.0
        
        # 热号
        recent_count = stats['recent_10_count']
        if recent_count >= 5:
            score += self.weights['hot_number'] * (recent_count / 10) * 1.5
        elif recent_count >= 3:
            score += self.weights['hot_number'] * (recent_count / 10)
        
        # 重号
        if num in self.get_latest_numbers(1):
            repeat_prob = self._calculate_repeat_probability()
            score += self.weights['repeat'] * (repeat_prob / 2) * 5
            if recent_count >= 4:
                score *= 1.3
        
        # 遗漏值
        current_miss = stats['current_absence']
        avg_miss = stats['average_absence']

        if current_miss > avg_miss * 1.5 and avg_miss > 0:
            ratio = current_miss / avg_miss
            score += self.weights['omission'] * (ratio * 5)
        elif current_miss > 5 and current_miss <= 15:
            score += self.weights['omission'] * (current_miss / 2)

        # 冷号
        if current_miss > 15:
            score += self.weights['cold_number'] * min(current_miss / 5, 12)
        
        # 斜连
        if num in self.pattern_cache.get('diagonal_sequences', set()):
            score += self.weights['diagonal'] * 2
        
        # 连号
        consecutive_bonus = self._check_consecutive_pattern(num)
        score += self.weights['consecutive'] * consecutive_bonus
        
        # 和值
        sum_trend = self._analyze_sum_trend()
        avg_sum = sum_trend.get('average', 810)
        
        if num <= 40 and avg_sum < 800:
            score += self.weights['sum_trend'] * 3
        elif num > 40 and avg_sum > 800:
            score += self.weights['sum_trend'] * 3
        
        # 奇偶
        odd_even_trend = self._analyze_odd_even_trend()
        target_odd = odd_even_trend.get('target_odd', 10)
        
        if num % 2 == 1:
            if target_odd >= 10:
                score += self.weights['odd_even'] * 3
        else:
            if target_odd <= 10:
                score += self.weights['odd_even'] * 3
        
        # 大小
        big_small_trend = self._analyze_big_small_trend()
        
        if num <= 40:
            if big_small_trend == '小数多':
                score += self.weights['big_small'] * 4
        else:
            if big_small_trend == '大数多':
                score += self.weights['big_small'] * 4
        
        # 区域
        zone_num = ((num - 1) // 20) + 1
        if zone_num in self.pattern_cache.get('hot_zones', []):
            score += self.weights['zone_hot'] * 3
        
        # 尾数
        tail = num % 10
        if tail in self.pattern_cache.get('hot_tails', []):
            score += self.weights['tail_pattern'] * 3
        
        # 头数
        head = num // 10
        if head in self.pattern_cache.get('hot_heads', []):
            score += self.weights['head_focus'] * 4
        
        # 012 路
        mod = num % 3
        if mod == self.pattern_cache.get('modulo_trend', -1):
            score += self.weights['modulo_3'] * 3
        
        return score
    
    def _check_consecutive_pattern(self, num: int) -> float:
        bonus = 0.0
        
        latest_nums = set(self.get_latest_numbers(1))
        
        if (num - 1) in latest_nums or (num + 1) in latest_nums:
            bonus += 1.0
        
        if (num - 1) in latest_nums and (num + 1) in latest_nums:
            bonus += 1.5
        
        return min(bonus, 2.0)
    
    def _calculate_repeat_probability(self) -> float:
        if len(self.sorted_issues) < 2:
            return 5.0
        
        repeat_counts = []
        for i in range(1, min(10, len(self.sorted_issues))):
            prev_nums = set(self.get_latest_numbers(i + 1))
            curr_nums = set(self.get_latest_numbers(i))
            repeat_counts.append(len(prev_nums & curr_nums))
        
        return sum(repeat_counts) / len(repeat_counts) if repeat_counts else 5.0
    
    def _analyze_sum_trend(self) -> Dict:
        recent_sums = []
        for issue in self.sorted_issues[-10:]:
            draw = self.lottery_data['historical_draws'][issue]
            recent_sums.append(draw['sum'])
        
        return {
            'average': sum(recent_sums) / len(recent_sums) if recent_sums else 810,
            'trend': 'up' if recent_sums[-1] > recent_sums[0] else 'down' if recent_sums else 'stable'
        }
    
    def _analyze_odd_even_trend(self) -> Dict:
        odd_counts = []
        for issue in self.sorted_issues[-10:]:
            draw = self.lottery_data['historical_draws'][issue]
            odd_count = sum(1 for n in draw['numbers'] if n % 2 == 1)
            odd_counts.append(odd_count)
        
        avg_odd = sum(odd_counts) / len(odd_counts) if odd_counts else 10
        
        return {
            'average': avg_odd,
            'target_odd': 12 if avg_odd > 10 else 8 if avg_odd < 10 else 10
        }
    
    def _analyze_big_small_trend(self) -> str:
        big_counts = []
        for issue in self.sorted_issues[-10:]:
            draw = self.lottery_data['historical_draws'][issue]
            big_count = sum(1 for n in draw['numbers'] if n > 40)
            big_counts.append(big_count)
        
        avg_big = sum(big_counts) / len(big_counts) if big_counts else 10
        
        return '大数多' if avg_big > 10 else '小数多' if avg_big < 10 else '平衡'


# ==================== 第四部分：智能预测器 ====================

class IntelligentPredictor:
    """智能预测器"""
    
    def __init__(self, dimension_weights: Dict):
        self.weights = dimension_weights
        self.analyzer = None
    
    def set_lottery_data(self, lottery_data: Dict):
        self.analyzer = MultiDimensionAnalyzer(lottery_data, self.weights)
    
    def predict_for_period(self, period_data: Dict, count=10) -> List[int]:
        """预测单期号码"""
        # 构建推荐号池
        recommend_pool = set()
        recommend_pool.update(period_data.get('kaiji', []))
        recommend_pool.update(period_data.get('shiji', []))
        recommend_pool.update(period_data.get('jin', []))
        recommend_pool.update(period_data.get('guanzhu', []))
        recommend_pool.update(period_data.get('duiying', []))
        
        if not recommend_pool:
            return []
        
        # 为每个推荐号评分
        scores = {}
        for num in recommend_pool:
            score = self.analyzer.analyze_number(num)
            scores[num] = score
        
        # 按评分排序，选择前 count 个
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        predicted = [item[0] for item in sorted_scores[:count]]
        
        return predicted


# ==================== 第五部分：回测优化器 ====================

class BacktestOptimizer:
    """回测优化器"""
    
    def __init__(self):
        self.base_weights = BASE_DIMENSIONS.copy()
    
    def optimize_weights_by_reverse_engineering(self, all_periods_data: List[Dict], 
                                                   lottery_data: Dict, 
                                                   optimal_periods: int) -> Tuple[Dict, Dict]:
        """反推优化法"""
        # 测试不同权重组合
        best_config = self._test_weight_configs(all_periods_data, lottery_data, optimal_periods)
        
        # 分析高频推荐号命中率
        feature_data = []
        
        for period_data in all_periods_data:
            if not period_data.get('lottery_numbers'):
                continue
            
            actual = set(period_data['lottery_numbers'])
            
            # 构建推荐号池
            recommend_pool = set()
            recommend_pool.update(period_data.get('kaiji', []))
            recommend_pool.update(period_data.get('shiji', []))
            recommend_pool.update(period_data.get('jin', []))
            recommend_pool.update(period_data.get('guanzhu', []))
            recommend_pool.update(period_data.get('duiying', []))
            
            # 统计每个号码在 5 个推荐源中的出现次数
            recommend_counter = Counter()
            for num in period_data.get('kaiji', []):
                recommend_counter[num] += 1
            for num in period_data.get('shiji', []):
                recommend_counter[num] += 1
            for num in period_data.get('jin', []):
                recommend_counter[num] += 1
            for num in period_data.get('guanzhu', []):
                recommend_counter[num] += 1
            for num in period_data.get('duiying', []):
                recommend_counter[num] += 1
            
            # 为每个推荐号记录特征
            for num in recommend_pool:
                is_hit = num in actual
                recommend_count = recommend_counter[num]
                
                feature_data.append({
                    'is_hit': is_hit,
                    'num': num,
                    'recommend_count': recommend_count
                })
        
        # 分析高频推荐号的命中率
        high_freq_hits = 0
        high_freq_total = 0
        low_freq_hits = 0
        low_freq_total = 0
        
        for feature in feature_data:
            if feature['recommend_count'] >= 2:
                high_freq_total += 1
                if feature['is_hit']:
                    high_freq_hits += 1
            else:
                low_freq_total += 1
                if feature['is_hit']:
                    low_freq_hits += 1
        
        high_freq_rate = (high_freq_hits / high_freq_total * 100) if high_freq_total > 0 else 0
        low_freq_rate = (low_freq_hits / low_freq_total * 100) if low_freq_total > 0 else 0
        
        return best_config['weights'], {
            'hit_rate': best_config['hit_rate'],
            'high_freq_hit_rate': high_freq_rate,
            'low_freq_hit_rate': low_freq_rate
        }
    
    def _test_weight_configs(self, all_periods_data: List[Dict], lottery_data: Dict, 
                            optimal_periods: int) -> Dict:
        """测试多种权重配置"""
        configs = []
        
        configs.append({'name': '基础配置', 'weights': self.base_weights.copy()})
        
        for hot_w in [35, 40]:
            config = self.base_weights.copy()
            config['hot_number'] = hot_w
            config['repeat'] = 12
            configs.append({'name': f'热号强化 (hot={hot_w})', 'weights': config})
        
        for repeat_w in [12, 15]:
            config = self.base_weights.copy()
            config['repeat'] = repeat_w
            config['hot_number'] = 35
            configs.append({'name': f'重号强化 (repeat={repeat_w})', 'weights': config})
        
        for omission_w in [20, 25]:
            config = self.base_weights.copy()
            config['omission'] = omission_w
            configs.append({'name': f'遗漏优化 (omission={omission_w})', 'weights': config})
        
        config = self.base_weights.copy()
        config['hot_number'] = 35
        config['repeat'] = 12
        config['omission'] = 20
        config['diagonal'] = 12
        configs.append({'name': '综合优化', 'weights': config})
        
        best_config = None
        best_hit_rate = 0
        
        for config in configs:
            predictor = IntelligentPredictor(config['weights'])
            predictor.set_lottery_data(lottery_data)
            
            total_hits = 0
            total_predictions = 0
            
            reversed_periods = list(reversed(all_periods_data[:optimal_periods]))
            
            for period_data in reversed_periods:
                if not period_data.get('lottery_numbers'):
                    continue
                
                predicted = predictor.predict_for_period(period_data, count=10)
                
                if not predicted:
                    continue
                
                actual = set(period_data['lottery_numbers'])
                hits = len(set(predicted) & actual)
                total_hits += hits
                total_predictions += len(predicted)
            
            hit_rate = (total_hits / total_predictions * 100) if total_predictions > 0 else 0
            
            if hit_rate > best_hit_rate:
                best_hit_rate = hit_rate
                best_config = config
        
        return {'weights': best_config['weights'] if best_config else self.base_weights, 'hit_rate': best_hit_rate}


# ==================== 数据更新线程 ====================

def update_data():
    """后台数据更新线程"""
    global cache_data
    
    with cache_lock:
        if cache_data['is_updating']:
            return
        cache_data['is_updating'] = True
    
    try:
        print("【开始更新数据】")
        fetcher = DataFetcher()
        
        print("  正在获取推荐数据...")
        all_periods_data = fetcher.fetch_html_recommend_data(limit=30)
        if not all_periods_data:
            print("  ✗ 推荐数据获取失败")
            with cache_lock:
                cache_data['is_updating'] = False
            return
        
        print(f"  ✓ 成功获取 {len(all_periods_data)} 期推荐数据")
        
        print("  正在获取开奖数据...")
        api_data = fetcher.fetch_lottery_api_data(limit=100)
        if not api_data:
            print("  ✗ 开奖数据获取失败")
            with cache_lock:
                cache_data['is_updating'] = False
            return
        
        lottery_data = fetcher.parse_api_data(api_data)
        print(f"  ✓ 成功获取 {len(lottery_data['sorted_issues'])} 期开奖数据")
        
        print("  正在分析周期性...")
        periodicity_analyzer = PeriodicityAnalyzer(lottery_data)
        periodicity_result = periodicity_analyzer.analyze_optimal_backtest_periods()
        optimal_periods = periodicity_result['optimal_periods']
        
        print("  正在反推优化权重...")
        optimizer = BacktestOptimizer()
        backtest_periods = [p for p in all_periods_data if p.get('lottery_numbers')][:optimal_periods]
        
        if len(backtest_periods) < optimal_periods:
            print(f"  ⚠️ 已开奖期数不足{optimal_periods}期，使用{len(backtest_periods)}期回测")
        
        optimal_weights, backtest_result = optimizer.optimize_weights_by_reverse_engineering(
            backtest_periods, lottery_data, optimal_periods
        )
        
        print("  正在生成预测结果...")
        all_predictions = {}
        predictor = IntelligentPredictor(optimal_weights)
        predictor.set_lottery_data(lottery_data)
        
        for period_data in all_periods_data[:15]:
            period_issue = period_data.get('issue', '')
            predicted = predictor.predict_for_period(period_data, count=10)
            all_predictions[period_issue] = predicted
        
        latest_period = all_periods_data[0]
        predicted_numbers = predictor.predict_for_period(latest_period, count=10)
        dan_codes = predicted_numbers[:2] if len(predicted_numbers) >= 2 else predicted_numbers
        
        backtest_stats = {
            'total_periods': len(backtest_periods),
            'max_hit_rate': backtest_result.get('hit_rate', 0.0),
            'high_freq_hit_rate': backtest_result.get('high_freq_hit_rate', 0.0),
            'low_freq_hit_rate': backtest_result.get('low_freq_hit_rate', 0.0)
        }
        
        # 更新缓存（使用锁保护）
        with cache_lock:
            cache_data['lottery_data'] = lottery_data
            cache_data['periods_data'] = all_periods_data
            cache_data['prediction_result'] = {
                'predicted_numbers': predicted_numbers,
                'dan_codes': dan_codes,
                'period': latest_period.get('issue', '')
            }
            cache_data['backtest_stats'] = backtest_stats
            cache_data['periodicity_result'] = periodicity_result
            cache_data['all_predictions'] = all_predictions
            cache_data['last_update'] = datetime.now().isoformat()
            # 必须在写入缓存文件前清除，否则会长期把 is_updating=true 存进磁盘，
            # 下次启动 load_cache 后 /api/prediction/generate 会一直 409。
            cache_data['is_updating'] = False
        
        # 保存到文件
        cache_file = os.path.join(CACHE_DIR, 'api_cache.json')
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✓ 数据更新完成，时间：{cache_data['last_update']}")
        
    except Exception as e:
        print(f"✗ 数据更新失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        with cache_lock:
            cache_data['is_updating'] = False


def load_cache():
    """加载缓存数据"""
    global cache_data
    
    cache_file = os.path.join(CACHE_DIR, 'api_cache.json')
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                cache_data.update(cached)
                # 持久化文件里可能带有上次更新中途写入的 is_updating；进程刚启动时没有后台任务在跑。
                cache_data['is_updating'] = False
                print(f"✓ 已加载缓存数据，上次更新：{cache_data['last_update']}")
        except Exception as e:
            print(f"⚠️ 加载缓存失败：{e}")


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    """处理 404 错误"""
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """处理 500 错误"""
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500


@app.errorhandler(Exception)
def handle_exception(e):
    """处理所有未捕获的异常"""
    print(f"未捕获的异常: {e}")
    import traceback
    traceback.print_exc()
    return jsonify({
        'success': False,
        'message': '服务器错误，请稍后重试'
    }), 500


# ==================== API 路由 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    with cache_lock:
        data = {
            'status': 'ok',
            'message': '快乐 8 智能预测 API 运行正常',
            'last_update': cache_data.get('last_update'),
            'is_updating': cache_data.get('is_updating', False)
        }
    
    response = make_response(jsonify(data))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/api/prediction/latest', methods=['GET'])
def get_latest_prediction():
    """获取最新一期预测"""
    with cache_lock:
        prediction = cache_data.get('prediction_result')
        last_update = cache_data.get('last_update')
    
    if not prediction:
        return jsonify({
            'success': False,
            'message': '暂无预测数据，请先生成预测'
        }), 404
    
    return jsonify({
        'success': True,
        'data': {
            'period': prediction.get('period'),
            'predicted_numbers': prediction.get('predicted_numbers', []),
            'dan_codes': prediction.get('dan_codes', []),
            'generated_at': last_update
        }
    })


@app.route('/api/prediction/history', methods=['GET'])
def get_prediction_history():
    """获取历史预测记录（最近 15 期）"""
    with cache_lock:
        all_predictions = cache_data.get('all_predictions')
    
    if not all_predictions:
        return jsonify({
            'success': False,
            'message': '暂无历史预测数据'
        }), 404
    
    limit = request.args.get('limit', 15, type=int)
    limit = min(max(limit, 1), 15)

    # all_predictions 在缓存里为 {期号: [预测号码...]}，不能对 dict 做 [:limit] 切片。
    if isinstance(all_predictions, dict):
        predictions_payload = dict(islice(all_predictions.items(), limit))
        total = len(all_predictions)
    else:
        seq = list(all_predictions)
        predictions_payload = seq[:limit]
        total = len(seq)

    return jsonify({
        'success': True,
        'data': {
            'predictions': predictions_payload,
            'total': total
        }
    })


@app.route('/api/lottery/data', methods=['GET'])
def get_lottery_data():
    """获取开奖数据"""
    with cache_lock:
        lottery_data = cache_data.get('lottery_data')
    
    if not lottery_data:
        return jsonify({
            'success': False,
            'message': '暂无开奖数据'
        }), 404
    
    limit = request.args.get('limit', 30, type=int)
    
    sorted_issues = lottery_data.get('sorted_issues', [])[-limit:]
    historical_draws = lottery_data.get('historical_draws', {})
    draws = {
        issue: historical_draws[issue]
        for issue in sorted_issues if issue in historical_draws
    }
    
    return jsonify({
        'success': True,
        'data': {
            'current_draw': lottery_data.get('current_draw'),
            'draws': draws,
            'total': len(draws)
        }
    })


@app.route('/api/lottery/periods', methods=['GET'])
def get_periods_data():
    """获取推荐数据"""
    with cache_lock:
        periods_data = cache_data.get('periods_data')
    
    if not periods_data:
        return jsonify({
            'success': False,
            'message': '暂无推荐数据'
        }), 404
    
    limit = request.args.get('limit', 15, type=int)
    limit = min(limit, len(periods_data))
    
    # 简化数据结构，添加命中率计算
    simplified_periods = []
    for period in periods_data[:limit]:
        # 计算推荐号池和命中率
        recommend_pool = set()
        recommend_pool.update(period.get('kaiji', []))
        recommend_pool.update(period.get('shiji', []))
        recommend_pool.update(period.get('jin', []))
        recommend_pool.update(period.get('guanzhu', []))
        recommend_pool.update(period.get('duiying', []))
        
        lottery_numbers = set(period.get('lottery_numbers', []))
        
        # 计算推荐号命中数和命中率
        hits = len(recommend_pool & lottery_numbers)
        total_recommends = len(recommend_pool)
        hit_rate = (hits / total_recommends * 100) if total_recommends > 0 else 0
        
        simplified_periods.append({
            'issue': period.get('issue', ''),
            'date': period.get('date', ''),
            'kaiji': period.get('kaiji', []),
            'shiji': period.get('shiji', []),
            'jin': period.get('jin', []),
            'guanzhu': period.get('guanzhu', []),
            'duiying': period.get('duiying', []),
            'lottery_numbers': period.get('lottery_numbers', []),
            'recommend_count': total_recommends,
            'hit_count': hits,
            'hit_rate': hit_rate
        })
    
    return jsonify({
        'success': True,
        'data': {
            'periods': simplified_periods,
            'total': len(simplified_periods)
        }
    })


@app.route('/api/analysis/backtest', methods=['GET'])
def get_backtest_stats():
    """获取回测统计"""
    with cache_lock:
        backtest_stats = cache_data.get('backtest_stats')
    
    if not backtest_stats:
        return jsonify({
            'success': False,
            'message': '暂无回测数据'
        }), 404
    
    return jsonify({
        'success': True,
        'data': backtest_stats
    })


@app.route('/api/analysis/periodicity', methods=['GET'])
def get_periodicity_analysis():
    """获取周期性分析"""
    with cache_lock:
        periodicity_result = cache_data.get('periodicity_result')
    
    if not periodicity_result:
        return jsonify({
            'success': False,
            'message': '暂无周期性分析数据'
        }), 404
    
    return jsonify({
        'success': True,
        'data': periodicity_result
    })


@app.route('/api/prediction/generate', methods=['POST'])
def generate_prediction():
    """生成新的预测"""
    with cache_lock:
        is_updating = cache_data.get('is_updating', False)
    
    if is_updating:
        return jsonify({
            'success': False,
            'message': '正在更新数据，请稍后重试'
        }), 409
    
    # 异步更新数据
    thread = threading.Thread(target=update_data)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': '开始生成预测，请稍后查询结果'
    })


@app.route('/api/periods/detail', methods=['GET'])
def get_period_detail():
    """获取单期详细数据（含 9 宫格）"""
    period_issue = request.args.get('issue')
    
    if not period_issue:
        return jsonify({
            'success': False,
            'message': '缺少期号参数'
        }), 400
    
    with cache_lock:
        periods_data = cache_data.get('periods_data')
    
    if not periods_data:
        return jsonify({
            'success': False,
            'message': '暂无数据'
        }), 404
    
    # 查找对应期数
    period_data = None
    for period in periods_data:
        if period.get('issue') == period_issue:
            period_data = period
            break
    
    if not period_data:
        return jsonify({
            'success': False,
            'message': f'未找到期号 {period_issue} 的数据'
        }), 404
    
    # 生成 9 宫格数据
    lottery_numbers = set(period_data.get('lottery_numbers', []))
    kaiji = set(period_data.get('kaiji', []))
    shiji = set(period_data.get('shiji', []))
    jin = set(period_data.get('jin', []))
    guanzhu = set(period_data.get('guanzhu', []))
    duiying = set(period_data.get('duiying', []))
    
    grid = []
    for row in range(8):
        grid_row = []
        for col in range(10):
            num = row * 10 + col + 1
            
            is_lottery = num in lottery_numbers
            is_kaiji = num in kaiji
            is_shiji = num in shiji
            is_jin = num in jin
            is_guanzhu = num in guanzhu
            is_duiying = num in duiying
            
            is_recommend = is_kaiji or is_shiji or is_jin or is_guanzhu or is_duiying
            is_hit = is_lottery and is_recommend
            
            type_labels = []
            if is_kaiji:
                type_labels.append('开')
            if is_shiji:
                type_labels.append('试')
            if is_jin:
                type_labels.append('金')
            if is_guanzhu:
                type_labels.append('关')
            if is_duiying:
                type_labels.append('对')
            
            grid_row.append({
                'number': num,
                'is_lottery': is_lottery,
                'is_recommend': is_recommend,
                'is_hit': is_hit,
                'type_labels': type_labels
            })
        grid.append(grid_row)
    
    # 计算高频推荐号
    recommend_counter = Counter()
    for num in period_data.get('kaiji', []):
        recommend_counter[num] += 1
    for num in period_data.get('shiji', []):
        recommend_counter[num] += 1
    for num in period_data.get('jin', []):
        recommend_counter[num] += 1
    for num in period_data.get('guanzhu', []):
        recommend_counter[num] += 1
    for num in period_data.get('duiying', []):
        recommend_counter[num] += 1
    
    high_freq_numbers = [
        {'number': num, 'count': count, 'is_hit': num in lottery_numbers}
        for num, count in recommend_counter.items() if count >= 2
    ]
    high_freq_numbers.sort(key=lambda x: (x['count'], x['number']), reverse=True)
    
    # 计算命中统计
    all_recommends = set(kaiji | shiji | jin | guanzhu | duiying)
    total_hits = len(all_recommends & lottery_numbers)
    hit_rate = (total_hits / 20 * 100) if len(lottery_numbers) > 0 else 0
    
    # 计算推荐号（10个）- 基于高频推荐号
    top_10_recommend_numbers = []
    for num_info in high_freq_numbers[:10]:
        top_10_recommend_numbers.append(num_info['number'])
    
    # 安全获取预测数据
    all_predictions = cache_data.get('all_predictions')
    prediction = all_predictions.get(period_issue, []) if all_predictions else []
    
    return jsonify({
        'success': True,
        'data': {
            'period': period_data,
            'recommend_numbers': top_10_recommend_numbers,  # 10个推荐号
            'grid': grid,
            'high_freq_numbers': high_freq_numbers,
            'stats': {
                'total_hits': total_hits,
                'hit_rate': hit_rate,
                'kaiji_hits': len(kaiji & lottery_numbers),
                'shiji_hits': len(shiji & lottery_numbers),
                'jin_hits': len(jin & lottery_numbers),
                'guanzhu_hits': len(guanzhu & lottery_numbers),
                'duiying_hits': len(duiying & lottery_numbers),
                'total_recommends': len(all_recommends)
            },
            'prediction': prediction
        }
    })


@app.route('/api/all-data', methods=['GET'])
def get_all_data():
    """获取所有数据（一次性返回）"""
    with cache_lock:
        return jsonify({
            'success': True,
            'data': {
                'prediction': cache_data.get('prediction_result'),
                'backtest': cache_data.get('backtest_stats'),
                'periodicity': cache_data.get('periodicity_result'),
                'all_predictions': cache_data.get('all_predictions'),
                'last_update': cache_data.get('last_update'),
                'is_updating': cache_data.get('is_updating', False)
            }
        })


# ==================== 启动服务 ====================

_scheduler_started = False
_scheduler_lock = threading.Lock()


def start_background_scheduler():
    """
    每小时自动更新数据（每个 worker 进程最多启动一条后台线程）。
    生产环境使用 Gunicorn 时也必须调用，否则不会定时更新。
    """
    global _scheduler_started

    def scheduled_update():
        while True:
            time.sleep(3600)
            update_data()

    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True
    threading.Thread(target=scheduled_update, daemon=True).start()


def bootstrap_worker():
    """供 Gunicorn worker 与本地 python 直连模式共用：加载缓存、冷启动拉数、启动定时任务。"""
    load_cache()
    print("\n" + "=" * 80)
    print("快乐 8 智能预测 API 服务器")
    print("=" * 80)
    if not cache_data.get('lottery_data') or not cache_data.get('periods_data'):
        print("\n首次启动，正在获取初始数据...")
        update_data()
    else:
        print(f"\n使用缓存数据，上次更新：{cache_data.get('last_update')}")
    start_background_scheduler()


if __name__ == '__main__':
    bootstrap_worker()

    # 启动 Flask 服务器
    print("\n" + "=" * 80)
    print("API 服务器启动成功")
    print("=" * 80)
    print("访问地址：http://localhost:8000")
    print("API 文档：")
    print("  - GET  /api/health              健康检查")
    print("  - GET  /api/prediction/latest   最新预测")
    print("  - GET  /api/prediction/history  历史预测")
    print("  - GET  /api/lottery/data        开奖数据")
    print("  - GET  /api/lottery/periods     推荐数据")
    print("  - GET  /api/analysis/backtest   回测统计")
    print("  - GET  /api/analysis/periodicity 周期性分析")
    print("  - POST /api/prediction/generate 生成预测")
    print("  - GET  /api/periods/detail      单期详情（含 9 宫格）")
    print("  - GET  /api/all-data            获取所有数据")
    print("=" * 80)
    print()
    
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
