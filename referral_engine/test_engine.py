import unittest
from referral_engine.engine import ReferralEngine

class TestReferralEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ReferralEngine(reward_amount=10)

    def test_add_user_and_referral(self):
        self.engine.add_user("user1")
        self.engine.add_user("user2")
        self.engine.add_referral("user1", "user2")
        self.assertIn("user2", self.engine.get_referrals("user1"))
        self.assertEqual(self.engine.get_rewards("user1"), 0)

    def test_conversion_rewards(self):
        self.engine.add_referral("user1", "user2")
        self.engine.record_conversion("user2")
        self.assertEqual(self.engine.get_rewards("user1"), 10)
        # Converting again does not add more rewards
        self.engine.record_conversion("user2")
        self.assertEqual(self.engine.get_rewards("user1"), 10)

    def test_no_referrer_no_reward(self):
        self.engine.add_user("user3")
        self.engine.record_conversion("user3")
        self.assertEqual(self.engine.get_rewards("user3"), 0)

    def test_multiple_referrals(self):
        self.engine.add_referral("user1", "user2")
        self.engine.add_referral("user1", "user3")
        self.engine.record_conversion("user2")
        self.engine.record_conversion("user3")
        self.assertEqual(self.engine.get_rewards("user1"), 20)

    def test_get_converted_users(self):
        self.engine.add_referral("user1", "user2")
        self.engine.record_conversion("user2")
        self.engine.record_conversion("user3")  # user3 not referred
        converted = self.engine.get_converted_users()
        self.assertIn("user2", converted)
        self.assertIn("user3", converted)
        self.assertNotIn("user1", converted)

if __name__ == "__main__":
    unittest.main()
