"""
快乐 8 数据服务
数据源：中国福利彩票官方 cwl.gov.cn

API 接口：
1. GET /api/health          健康检查
2. GET /api/all-data        获取所有数据
3. GET /api/lottery/data    获取开奖数据
4. GET /api/lottery/periods 获取期数列表
5. GET /api/periods/detail  单期详情（含宫格）
6. POST /api/prediction/generate 触发数据刷新
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json
import re
import threading
import time
import os
from datetime import datetime
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# ==================== 配置 ====================

CWL_KJGG_URL = "https://www.cwl.gov.cn/ygkj/kjgg/"
CWL_BASE_URL = "https://www.cwl.gov.cn"

BROWSER_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Host': 'www.cwl.gov.cn',
    'Referer': 'https://www.cwl.gov.cn/ygkj/kjgg/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
}

_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
os.makedirs(_CACHE_DIR, exist_ok=True)

cache_lock = threading.Lock()
_cache = {
    'draws': [],
    'last_update': None,
    'is_updating': False,
}


# ==================== 数据获取 ====================

class LotteryFetcher:
    """从 cwl.gov.cn kjgg 列表页隐藏 div 获取快乐8最新开奖数据"""

    @staticmethod
    def _get_hidden_text(soup, css_class):
        el = soup.find('div', class_=css_class)
        return el.get_text(strip=True) if el else ''

    @staticmethod
    def _parse_numbers(text):
        nums = []
        for part in re.findall(r'\d{1,2}', text):
            n = int(part)
            if 1 <= n <= 80 and n not in nums:
                nums.append(n)
        return sorted(nums)

    @classmethod
    def fetch_latest(cls):
        """获取最新一期开奖数据"""
        try:
            resp = requests.get(CWL_KJGG_URL, headers=BROWSER_HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            numbers_raw = cls._get_hidden_text(soup, 'klRed-dom')
            code = cls._get_hidden_text(soup, 'kl8Qh-dom')
            jc = cls._get_hidden_text(soup, 'kl8Jc-dom')
            gdjc = cls._get_hidden_text(soup, 'kl8GdJc-dom')
            sales = cls._get_hidden_text(soup, 'kl8Sales-dom')
            detail_link = cls._get_hidden_text(soup, 'kl8XqLink-dom')

            # 从详情链接提取日期: /c/2026/04/16/651257.shtml → 04/16
            draw_date = ''
            if detail_link:
                m = re.search(r'/c/\d{4}/(\d{2}/\d{2})/', detail_link)
                if m:
                    draw_date = m.group(1)

            if not code or not numbers_raw:
                print("  列表页未找到KL8数据")
                return None

            numbers = cls._parse_numbers(numbers_raw)

            result = {
                'code': code,
                'date': draw_date,
                'numbers': numbers,
                'pool_float': jc,
                'pool_fixed': gdjc,
                'sales': sales,
                'detail_url': CWL_BASE_URL + detail_link if detail_link else '',
            }
            print(f"  最新期号: {code}, 号码: {len(numbers)}个")
            return result

        except Exception as e:
            print(f"获取最新数据失败: {e}")
            return None


# ==================== 数据更新 ====================

def refresh_data():
    global _cache
    with cache_lock:
        if _cache['is_updating']:
            return
        _cache['is_updating'] = True

    try:
        latest = LotteryFetcher.fetch_latest()

        if latest:
            with cache_lock:
                # 合并去重
                codes = {d['code'] for d in _cache['draws']}
                if latest['code'] in codes:
                    _cache['draws'] = [d for d in _cache['draws'] if d['code'] != latest['code']]
                _cache['draws'].insert(0, latest)
                _cache['last_update'] = datetime.now().isoformat()

            cache_file = os.path.join(_CACHE_DIR, 'api_cache.json')
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(_cache, f, ensure_ascii=False, indent=2)
            print(f"更新完成，最新期号：{latest['code']}")

    except Exception as e:
        print(f"更新失败: {e}")
    finally:
        with cache_lock:
            _cache['is_updating'] = False


def load_cache():
    global _cache
    cache_file = os.path.join(_CACHE_DIR, 'api_cache.json')
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                _cache.update(cached)
                # 兜底提取日期
                for d in _cache.get('draws', []):
                    if not d.get('date') and d.get('detail_url'):
                        m = re.search(r'/c/\d{4}/(\d{2}/\d{2})/', d['detail_url'])
                        if m:
                            d['date'] = m.group(1)
                print(f"已加载缓存，最新期号：{_cache['draws'][0]['code'] if _cache.get('draws') else '?'}")
        except Exception as e:
            print(f"缓存加载失败: {e}")


# ==================== 宫格生成 ====================

def build_grid(lottery_numbers):
    hit_set = set(lottery_numbers or [])
    grid = []
    for row in range(8):
        grid_row = []
        for col in range(10):
            num = row * 10 + col + 1
            grid_row.append({
                'number': num,
                'is_lottery': num in hit_set,
                'is_recommend': False,
                'is_hit': False,
                'type_labels': [],
            })
        grid.append(grid_row)
    return grid


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(_e):
    return jsonify({'success': False, 'message': '接口不存在'}), 404


@app.errorhandler(Exception)
def handle_exception(e):
    print(f"未捕获异常: {e}")
    return jsonify({'success': False, 'message': '服务器内部错误'}), 500


# ==================== API 路由 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    with cache_lock:
        d = _cache['draws'][0] if _cache['draws'] else {}
    return jsonify({
        'status': 'ok' if d else 'no_data',
        'latest_issue': d.get('code', ''),
        'last_update': _cache.get('last_update'),
    })


@app.route('/api/lottery/data', methods=['GET'])
def get_lottery_data():
    limit = request.args.get('limit', 30, type=int)
    draws = _cache['draws'][:limit]
    result = {'current_draw': draws[0]['code'] if draws else '', 'draws': {}, 'total': len(draws)}
    for d in draws:
        result['draws'][d['code']] = {
            'numbers': d.get('numbers', []),
            'date': d.get('date', ''),
            'pool_float': d.get('pool_float', ''),
            'pool_fixed': d.get('pool_fixed', ''),
            'sales': d.get('sales', ''),
        }
    return jsonify({'success': True, 'data': result})


@app.route('/api/lottery/periods', methods=['GET'])
def get_periods_list():
    limit = request.args.get('limit', 15, type=int)
    periods = []
    for d in _cache['draws'][:limit]:
        periods.append({
            'issue': d['code'],
            'date': d.get('date', ''),
            'lottery_numbers': d.get('numbers', []),
            'pool_float': d.get('pool_float', ''),
            'pool_fixed': d.get('pool_fixed', ''),
            'sales': d.get('sales', ''),
        })
    return jsonify({'success': True, 'data': {'periods': periods}})


@app.route('/api/periods/detail', methods=['GET'])
def get_period_detail():
    issue = request.args.get('issue', '')
    if not issue:
        return jsonify({'success': False, 'message': '缺少期号'}), 400

    draw = next((d for d in _cache['draws'] if d['code'] == issue), None)
    if not draw:
        return jsonify({'success': False, 'message': f'未找到期号 {issue}'}), 404

    return jsonify({
        'success': True,
        'data': {
            'period': {
                'issue': issue,
                'date': draw['date'],
                'lottery_numbers': draw['numbers'],
            },
            'grid': build_grid(draw['numbers']),
            'recommend_numbers': [],
            'high_freq_numbers': [],
            'stats': {'total_hits': 0, 'hit_rate': 0.0},
        }
    })


@app.route('/api/prediction/generate', methods=['POST'])
def generate_prediction():
    with cache_lock:
        if _cache['is_updating']:
            return jsonify({'success': False, 'message': '正在更新'}), 409
    threading.Thread(target=refresh_data, daemon=True).start()
    return jsonify({'success': True, 'message': '开始刷新数据'})


@app.route('/api/all-data', methods=['GET'])
def get_all_data():
    with cache_lock:
        latest = _cache['draws'][0] if _cache['draws'] else {}
    return jsonify({
        'success': True,
        'data': {
            'lottery': {
                'latest_issue': latest.get('code', ''),
                'latest_date': latest.get('date', ''),
                'latest_numbers': latest.get('numbers', []),
                'pool_float': latest.get('pool_float', ''),
                'pool_fixed': latest.get('pool_fixed', ''),
                'sales': latest.get('sales', ''),
                'total_periods': len(_cache['draws']),
            },
            'periods': _cache['draws'][:15],
            'last_update': _cache.get('last_update'),
            'is_updating': _cache.get('is_updating', False),
        }
    })


# ==================== 启动 ====================

def start_background_scheduler():
    """每小时自动刷新"""
    def loop():
        while True:
            time.sleep(3600)
            refresh_data()
    threading.Thread(target=loop, daemon=True).start()


if __name__ == '__main__':
    load_cache()
    print("=" * 50)
    print("  快乐 8 数据服务")
    print(f"  缓存期号: {_cache['draws'][0]['code'] if _cache.get('draws') else '?'}")
    print("=" * 50)

    if not _cache.get('draws'):
        print("首次启动，拉取初始数据...")
        refresh_data()

    start_background_scheduler()
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
