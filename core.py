"""Conservative, deterministic customer selection; no external services."""
from collections import defaultdict
from datetime import datetime, date
import re

FIELDS = {'machine': '기계번호', 'model': '모델명', 'customer_id': '고객번호',
          'company': '고객사명', 'name': '이름', 'phone': '전화', 'email': '이메일',
          'region': '지역', 'address': '현재 주소', 'position': '직급', 'updated': '정보수정일',
          'last_name': '성', 'first_name': '이름', 'mobile': '휴대폰'}
OUTPUT_FIELDS = list(FIELDS)[:8]
DEFAULT_KEYWORDS = ['총무', '인사', '경영지원', '구매']
SECONDARY_TITLES = ['대표', '사장', '실장', '팀장']


def clean(value):
    return '' if value is None else str(value).strip()


def combine_name(row):
    parts = [clean(row.get(k)) for k in ('last_name', 'first_name')]
    separator = '' if all(re.fullmatch(r'[가-힣]+', p or '') for p in parts) else ' '
    return separator.join(p for p in parts if p)


def parse_date(value):
    value = clean(value)
    if not value:
        return None
    for pattern in ('%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%Y%m%d',
                    '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y/%m/%d %H:%M:%S'):
        try:
            parsed = datetime.strptime(value, pattern)
            return parsed if parsed.date() <= date.today() else None
        except ValueError:
            pass
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is not None:
            return None
        return parsed if parsed.date() <= date.today() else None
    except ValueError:
        return None


def address_matches(row, keywords):
    address = re.sub(r'\s', '', row.get('address', ''))
    return any(re.sub(r'\s', '', word) in address for word in keywords if word.strip())


def title_rank(row):
    title = re.sub(r'\s', '', row.get('position', ''))
    if title in ('대표', '대표이사'):
        return 0
    if title == '사장':
        return 1
    if title.endswith('실장') and not title.endswith('부실장'):
        return 2
    if title.endswith('팀장') and not title.endswith('부팀장'):
        return 3
    return 4


def buyer_priority(row, keywords):
    if address_matches(row, keywords):
        return 1
    if title_rank(row) < 4 and not contact_errors(row, ('name', 'phone', 'email')):
        return 2
    return 3


def candidate_order(row, keywords):
    priority = buyer_priority(row, keywords)
    return priority, title_rank(row) if priority == 2 else 0


def is_buyer(row, keywords):
    return buyer_priority(row, keywords) < 3


def contact_errors(row, required_fields=OUTPUT_FIELDS):
    errors = [f'{FIELDS[key]} 누락' for key in required_fields if key != 'phone' and not clean(row.get(key))]
    if 'phone' in required_fields and not (clean(row.get('phone')) or clean(row.get('mobile'))):
        errors.append('전화·휴대폰 모두 누락')
    if row.get('last_name') or row.get('first_name'):
        errors.extend(f'{FIELDS[key]} 누락' for key in ('last_name', 'first_name') if not clean(row.get(key)))
    email = clean(row.get('email'))
    if email and not re.fullmatch(r'[^\s@;,]+@[^\s@;,]+\.[^\s@;,]+', email):
        errors.append('이메일 형식 확인')
    for key in ('phone', 'mobile'):
        phone = clean(row.get(key))
        if phone and (not 7 <= len(re.sub(r'\D', '', phone)) <= 20 or not re.fullmatch(r'[\d\s+().\-#/내선extEXT:]+', phone)):
            errors.append(f'{FIELDS[key]} 형식 확인')
    return errors


def latest_value(rows, key, reasons):
    present = [r for r in rows if r.get(key)]
    if not present:
        return ''
    dated = [r for r in present if r['_date']]
    chosen = max(dated, key=lambda r: r['_date']) if dated else present[0]
    peers = [r for r in present if r['_date'] == chosen['_date'] or r['_date'] is None]
    if any(r[key] != chosen[key] for r in peers):
        reasons.append(f'{FIELDS[key]} 충돌: 같은 날짜 또는 날짜 없는 다른 값')
    return chosen[key]


def build_result(records, keywords=None):
    keywords = DEFAULT_KEYWORDS if keywords is None else [clean(k) for k in keywords if clean(k)]
    groups, rejected = defaultdict(list), []
    normalized = []
    for index, original in enumerate(records):
        row = {k: clean(original.get(k)) for k in FIELDS}
        if row['last_name'] or row['first_name']:
            row['name'] = combine_name(row)
        row['source'] = clean(original.get('source'))
        row['warnings'] = list(original.get('warnings', []))
        row['_date'] = parse_date(row['updated'])
        row['record_id'] = index
        normalized.append(row)
        if not row['customer_id']:
            rejected.append(dict(row, reason='고객번호 누락: 자동 연결 불가'))
        else:
            groups[row['customer_id']].append(row)
    customers, machines = [], []
    for customer_id, rows in groups.items():
        reasons = []
        for row in rows:
            reasons.extend(row['warnings'])
            if row['updated'] and row['_date'] is None:
                reasons.append('날짜 형식 오류 또는 미래 날짜')
        customer = {key: '' for key in FIELDS}
        customer.update(customer_id=customer_id, company=latest_value(rows, 'company', reasons),
                        region=latest_value(rows, 'region', reasons))
        by_machine = defaultdict(list)
        for row in rows:
            if row['machine']:
                by_machine[row['machine']].append(row)
        machine_ids, models = [], []
        for machine_id, entries in sorted(by_machine.items()):
            model = latest_value(entries, 'model', reasons)
            machine_ids.append(machine_id)
            models.append(model or '(모델 미확인)')
            if not model:
                reasons.append(f'{machine_id} 모델명 누락')
            machines.append(dict(customer_id=customer_id, company=customer['company'],
                                 machine=machine_id, model=model,
                                 source='\n'.join(dict.fromkeys(r['source'] for r in entries))))
        customer['machine'], customer['model'] = '\n'.join(machine_ids), '\n'.join(models)
        # A newer record revoking a named person's role supersedes the old row.
        by_person = defaultdict(list)
        for row in rows:
            if not any(row[key] for key in ('name', 'phone', 'mobile', 'email', 'position')):
                continue
            by_person[row['name'] or f'unknown-{row["record_id"]}'].append(row)
        current = []
        for entries in by_person.values():
            dates = [r['_date'] for r in entries if r['_date']]
            newest = max(dates) if dates else None
            current.extend(r for r in entries if r['_date'] is None or r['_date'] == newest)
        candidates = [r for r in current if is_buyer(r, keywords)]
        if not candidates:
            reasons.append('1순위 주소 키워드 또는 연락처가 완비된 2순위 직급 후보 없음')
            candidates_for_display = current or rows
        else:
            candidates_for_display = candidates
        best_order = min(candidate_order(r, keywords) for r in candidates_for_display)
        preferred = [r for r in candidates_for_display if candidate_order(r, keywords) == best_order]
        chosen = max(preferred, key=lambda r: r['_date'] or datetime.min)
        priority = buyer_priority(chosen, keywords)
        if any(r['_date'] is None for r in preferred):
            reasons.append('담당자 정보 날짜 없음 또는 확인 불가')
        if candidates:
            newest = chosen['_date']
            tied = [r for r in preferred if r['_date'] == newest]
            signatures = {(r['name'], re.sub(r'\D', '', r['phone']), re.sub(r'\D', '', r['mobile']), r['email'].lower()) for r in tied}
            if len(signatures) > 1:
                reasons.append('같은 최신 날짜에 여러 담당자 또는 연락처 충돌')
            same_person_peers = [r for r in current if r['name'] == chosen['name'] and r['_date'] == newest]
            if any(not is_buyer(r, keywords) for r in same_person_peers):
                reasons.append('같은 날짜의 주소 또는 직급·연락처 선정 조건 충돌')
        for key in ('name', 'last_name', 'first_name', 'phone', 'mobile', 'email', 'address', 'position', 'updated'):
            customer[key] = chosen[key]
        reasons.extend(contact_errors(customer))
        customer.update(status='확인 필요' if reasons else '설문 대상',
                        reasons=list(dict.fromkeys(reasons)), source=chosen['source'],
                        all_sources='\n'.join(dict.fromkeys(r['source'] for r in rows)),
                        priority=priority,
                        selection=('1순위: 현재 주소에 부서 키워드 포함' if priority == 1 else
                                   f'2순위: {SECONDARY_TITLES[title_rank(chosen)]} / 이름·연락처·이메일 완비' if priority == 2 else
                                   '구매 담당자 확인 필요') + ' / 동일 순위 최신 행 선택', manual=False,
                        candidates=[{k: v for k, v in r.items() if k != '_date'} for r in rows])
        customers.append(customer)
    # A machine cannot safely belong to two customers simultaneously.
    ownership = defaultdict(set)
    for machine in machines:
        ownership[machine['machine']].add(machine['customer_id'])
    for customer in customers:
        if any(len(ownership[m]) > 1 for m in customer['machine'].splitlines()):
            customer['reasons'].append('동일 기계번호가 여러 고객번호에 존재')
            customer['status'] = '확인 필요'
    customers.sort(key=lambda c: c['priority'])
    return dict(customers=customers, machines=machines,
                records=[{k: v for k, v in r.items() if k != '_date'} for r in normalized],
                rejected=[{k: v for k, v in r.items() if k != '_date'} for r in rejected], keywords=keywords)


def approve_customer(result, customer_id, values):
    customer = next((c for c in result['customers'] if c['customer_id'] == customer_id), None)
    if customer is None:
        raise ValueError('고객을 찾을 수 없습니다.')
    updated = dict(customer)
    # Machine inventory and customer key stay traceable to the original sources.
    for key in ('company', 'name', 'phone', 'mobile', 'email', 'region', 'address', 'position'):
        updated[key] = clean(values.get(key))
    if 'last_name' in values or 'first_name' in values:
        for key in ('last_name', 'first_name'):
            updated[key] = clean(values.get(key))
        updated['name'] = combine_name(updated)
    errors = contact_errors(updated)
    if '(모델 미확인)' in updated['model']:
        errors.append('모델명 누락: 원본 수정 후 다시 불러오세요.')
    if errors:
        raise ValueError(' / '.join(errors))
    updated.update(status='설문 대상', manual=True, reasons=[],
                   priority=1 if address_matches(updated, result['keywords']) else 2,
                   selection='사용자 확인: 최신 정보 및 구매권한 확인',
                   confirmed_at=datetime.now().isoformat(timespec='seconds'))
    customer.update(updated)
    result['customers'].sort(key=lambda c: c['priority'])
    return customer
