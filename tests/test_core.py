import unittest
from core import build_result, approve_customer


def row(**changes):
    value = dict(customer_id='0001', company='가상회사', machine='M01', model='모델A',
                 name='김담당', phone='010-1234-5678', email='kim@example.com', region='서울',
                 address='총무팀', position='', updated='2026-09-01', source='A.xlsx / 고객 / 2행')
    value.update(changes)
    return value


class IntegrationRules(unittest.TestCase):
    def test_one_customer_keeps_all_machine_pairs(self):
        result = build_result([row(), row(machine='M02', model='모델B')])
        self.assertEqual(len(result['customers']), 1)
        customer = result['customers'][0]
        self.assertEqual(customer['status'], '설문 대상')
        self.assertEqual(customer['machine'], 'M01\nM02')
        self.assertEqual(customer['model'], '모델A\n모델B')

    def test_latest_buyer_wins_even_when_nonbuyer_is_newer(self):
        result = build_result([row(), row(name='이담당', email='lee@example.com', updated='2026-09-10'),
                               row(name='개발자', address='개발팀', updated='2026-09-11')])
        self.assertEqual(result['customers'][0]['name'], '이담당')
        self.assertEqual(result['customers'][0]['status'], '설문 대상')

    def test_incomplete_newest_contact_does_not_use_old_contact(self):
        customer = build_result([row(), row(name='이담당', email='', updated='2026-09-10')])['customers'][0]
        self.assertEqual(customer['status'], '확인 필요')
        self.assertEqual(customer['email'], '')

    def test_equal_date_different_people_require_review(self):
        customer = build_result([row(), row(name='이담당', email='lee@example.com')])['customers'][0]
        self.assertEqual(customer['status'], '확인 필요')

    def test_undated_candidate_is_never_silently_older(self):
        customer = build_result([row(), row(name='이담당', email='lee@example.com', updated='')])['customers'][0]
        self.assertEqual(customer['status'], '확인 필요')

    def test_position_does_not_override_address(self):
        self.assertEqual(build_result([row(position='사원')])['customers'][0]['status'], '설문 대상')

    def test_no_customer_id_is_separate_rejection(self):
        result = build_result([row(customer_id=''), row()])
        self.assertEqual(len(result['customers']), 1)
        self.assertEqual(len(result['rejected']), 1)

    def test_manual_confirmation_requires_complete_contact(self):
        result = build_result([row(updated='')])
        with self.assertRaises(ValueError):
            approve_customer(result, '0001', dict(row(), email=''))
        approve_customer(result, '0001', row())
        self.assertEqual(result['customers'][0]['status'], '설문 대상')
        self.assertTrue(result['customers'][0]['manual'])

    def test_invalid_date_and_invalid_email_are_blocked(self):
        for changes in [dict(updated='2026-99-99'), dict(updated='2099-01-01'), dict(email='bad@'), dict(phone='abc')]:
            with self.subTest(changes=changes):
                self.assertEqual(build_result([row(**changes)])['customers'][0]['status'], '확인 필요')

    def test_customer_metadata_conflict_requires_review(self):
        self.assertEqual(build_result([row(), row(region='부산')])['customers'][0]['status'], '확인 필요')

    def test_latest_address_does_not_resurrect_older_buyer(self):
        customer = build_result([row(), row(address='서울 개발팀', updated='2026-09-10')])['customers'][0]
        self.assertEqual(customer['status'], '확인 필요')

    def test_machine_only_file_can_join_contact_file(self):
        customer = build_result([row(), row(machine='M02', name='', phone='', email='',
                                           address='', updated='')])['customers'][0]
        self.assertEqual(customer['status'], '설문 대상')
        self.assertEqual(customer['name'], '김담당')

    def test_machine_only_records_require_contact_review(self):
        customer = build_result([row(name='', phone='', email='', address='')])['customers'][0]
        self.assertEqual(customer['status'], '확인 필요')


if __name__ == '__main__':
    unittest.main()
