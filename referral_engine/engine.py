"""
Automated Referral Engine Module

This module implements a simple referral engine that tracks users,
their referrals, and rewards referrers when referees convert.

Components:
- Identity Layer: User IDs
- Reward Logic: $10 credit after referee's first paid month
- Trigger System: Event-driven reward on conversion

Usage:
- add_user(user_id)
- add_referral(referrer_id, referee_id)
- record_conversion(user_id)
- get_rewards(user_id)
"""

from collections import defaultdict

class ReferralEngine:
    def __init__(self, reward_amount=10):
        # Maps user_id to set of referred user_ids
        self.referrals = defaultdict(set)
        # Tracks which users have converted (paid)
        self.converted = set()
        # Tracks rewards earned by each user
        self.rewards = defaultdict(int)
        # Reward amount per successful referral
        self.reward_amount = reward_amount
        # Maps referee to referrer for quick lookup
        self.referee_to_referrer = {}

    def add_user(self, user_id):
        # Ensure user exists in data structures
        self.referrals[user_id]  # initializes empty set if new
        self.rewards[user_id]    # initializes to 0 if new

    def add_referral(self, referrer_id, referee_id):
        # Add users if not present
        self.add_user(referrer_id)
        self.add_user(referee_id)
        # Record referral relationship
        self.referrals[referrer_id].add(referee_id)
        self.referee_to_referrer[referee_id] = referrer_id

    def record_conversion(self, user_id):
        # Mark user as converted
        if user_id in self.converted:
            # Already converted, no new reward
            return
        self.converted.add(user_id)
        # If user was referred, reward the referrer
        referrer = self.referee_to_referrer.get(user_id)
        if referrer:
            self.rewards[referrer] += self.reward_amount

    def get_rewards(self, user_id):
        return self.rewards.get(user_id, 0)

    def get_referrals(self, user_id):
        return self.referrals.get(user_id, set())

    def get_converted_users(self):
        return set(self.converted)
