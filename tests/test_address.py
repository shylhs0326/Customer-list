import unittest
from core import build_result
from excel_io import export_result
from io import BytesIO
from openpyxl import load_workbook


def contact(**changes):
    row = dict(customer_id='001', company='고객사', machine='M1', model='A',
               name='주소담당', phone='01012345678', email='a@example.com', region='서울',
               address='서울시 강남구 10층 총무팀', updated='2026-09-01', position='과장')
    row.update(changes)
    return row


class AddressPriority(unittest.TestCase):
    def test_address_keywords_are_primary(self):
        for word in ['총무', '인사', '경영지원', '구매']:
            customer = build_result([contact(address=f'서울 3층 {word}팀')])['customers'][0]
            self.assertEqual(customer['status'], '설문 대상')
            self.assertEqual(customer['priority'], 1)

    def test_primary_address_beats_newer_nonmatching_contact(self):
        result = build_result([contact(), contact(name='다른담당', email='b@example.com',
                               address='서울 2층 영업팀', position='부장', updated='2026-09-10')])
        self.assertEqual(result['customers'][0]['name'], '주소담당')

    def test_department_is_no_longer_the_keyword_source(self):
        customer = build_result([contact(address='서울시', department='총무팀')])['customers'][0]
        self.assertEqual(customer['status'], '확인 필요')

    def test_primary_customer_is_listed_first(self):
        result = build_result([contact(customer_id='002', machine='M2', address='서울', position='부장'), contact()])
        self.assertEqual([r['customer_id'] for r in result['customers']], ['001', '002'])

    def test_priority_does_not_bypass_missing_email(self):
        customer = build_result([contact(email='')])['customers'][0]
        self.assertEqual(customer['status'], '확인 필요')

    def test_newer_address_for_same_person_replaces_old_address(self):
        customer = build_result([contact(), contact(address='서울 개발팀', updated='2026-09-10')])['customers'][0]
        self.assertEqual(customer['status'], '확인 필요')

    def test_equal_date_different_priorities_are_not_a_contact_tie(self):
        customer = build_result([contact(), contact(name='다른담당', address='서울', position='부장', email='b@example.com')])['customers'][0]
        self.assertEqual(customer['status'], '설문 대상')

    def test_export_preserves_address_and_priority_order(self):
        result = build_result([contact(customer_id='002', machine='M2', address='서울', position='부장'), contact()])
        book = load_workbook(BytesIO(export_result(result)))
        sheet = book['설문 대상']
        self.assertEqual(sheet['C2'].value, '001')
        self.assertEqual(sheet['I1'].value, '현재 주소')
        self.assertEqual(sheet['I2'].value, '서울시 강남구 10층 총무팀')
        self.assertEqual(sheet['J2'].value, '1')

if __name__ == '__main__':
    unittest.main()
