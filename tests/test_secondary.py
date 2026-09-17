import unittest
from core import build_result
from test_address import contact


def executive(title, **changes):
    return contact(address='서울 본사', position=title, name=title+'담당', **changes)


class SecondarySelection(unittest.TestCase):
    def test_title_order_precedes_recency(self):
        titles = ['대표', '사장', '실장', '팀장']
        for i, expected in enumerate(titles):
            rows = [executive(t, updated=f'2026-09-{j+1:02d}') for j, t in enumerate(titles[i:])]
            c = build_result(rows)['customers'][0]
            self.assertEqual(c['position'], expected)
            self.assertEqual(c['status'], '설문 대상')
            self.assertEqual(c['priority'], 2)

    def test_address_always_wins_over_executive(self):
        c = build_result([contact(position='사원'), executive('대표', updated='2026-09-10')])['customers'][0]
        self.assertEqual(c['name'], '주소담당')
        self.assertEqual(c['priority'], 1)

    def test_incomplete_or_invalid_higher_title_is_skipped(self):
        for field, value in [('name',''), ('phone',''), ('email',''), ('email','bad@'), ('phone','abc')]:
            higher = executive('대표')
            higher[field] = value
            c = build_result([higher, executive('사장')])['customers'][0]
            self.assertEqual(c['position'], '사장')
            self.assertEqual(c['status'], '설문 대상')

    def test_incomplete_primary_is_reviewed_not_replaced(self):
        c = build_result([contact(email=''), executive('대표')])['customers'][0]
        self.assertEqual(c['priority'], 1)
        self.assertEqual(c['status'], '확인 필요')

    def test_same_title_uses_latest(self):
        c = build_result([executive('팀장'), executive('팀장', updated='2026-09-10', email='new@example.com')])['customers'][0]
        self.assertEqual(c['email'], 'new@example.com')
        self.assertEqual(c['status'], '설문 대상')

    def test_same_title_and_date_conflict_requires_review(self):
        other = executive('실장', email='other@example.com')
        other['name'] = '다른실장'
        c = build_result([executive('실장'), other])['customers'][0]
        self.assertEqual(c['status'], '확인 필요')

    def test_unsupported_titles_do_not_match_substrings(self):
        for title in ['부사장','부팀장','부실장','대표대행','과장']:
            self.assertEqual(build_result([executive(title)])['customers'][0]['status'], '확인 필요')

    def test_ceo_and_department_lead_variants(self):
        for title in ['대표이사','경영지원실장','영업팀장']:
            self.assertEqual(build_result([executive(title)])['customers'][0]['status'], '설문 대상')

    def test_incomplete_newer_person_record_does_not_revive_old_record(self):
        c = build_result([executive('대표'), executive('대표', email='', updated='2026-09-10'), executive('사장')])['customers'][0]
        self.assertEqual(c['position'], '사장')

    def test_lower_title_without_date_does_not_block_ceo(self):
        c = build_result([executive('대표'), executive('팀장', updated='')])['customers'][0]
        self.assertEqual(c['status'], '설문 대상')

if __name__ == '__main__':
    unittest.main()
