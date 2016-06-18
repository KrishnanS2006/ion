# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse

from ..eighth.exceptions import SignupException
from ..eighth.models import EighthActivity, EighthBlock, EighthRoom, EighthScheduledActivity
from ..groups.models import Group
from ..users.models import User
from ...test.ion_test import IonTestCase
"""
Tests for the eighth module.
"""


class EighthTest(IonTestCase):

    def make_admin(self):
        self.login()
        # Make user an eighth admin
        user = User.get_user(username='awilliam')
        group = Group.objects.get_or_create(name="admin_all")[0]
        user.groups.add(group)
        return user

    def add_block(self, **args):
        # Bypass the manual block creation form.
        args.update({'custom_block': True})
        response = self.client.post(reverse('eighth_admin_add_block'), args)
        self.assertEqual(response.status_code, 302)
        return EighthBlock.objects.get(date=args['date'], block_letter=args['block_letter'])

    def add_room(self, **args):
        response = self.client.post(reverse('eighth_admin_add_room'), args)
        self.assertEqual(response.status_code, 302)
        return EighthRoom.objects.get(name=args['name'])

    def add_activity(self, **args):
        response = self.client.post(reverse('eighth_admin_add_activity'), args)
        self.assertEqual(response.status_code, 302)
        return EighthActivity.objects.get(name=args['name'])

    def schedule_activity(self, block_id, activity_id):
        # FIXME: figure out a way to do this that involves less hard-coding.
        args = {'form-TOTAL_FORMS': '1',
                'form-INITIAL_FORMS': '0',
                'form-MAX_NUM_FORMS': '',
                'form-0-block': block_id,
                'form-0-activity': activity_id,
                'form-0-scheduled': True,
                'form-0-capacity': 1}
        response = self.client.post(reverse('eighth_admin_schedule_activity'), args)
        self.assertEqual(response.status_code, 302)
        return EighthScheduledActivity.objects.get(block__id=block_id, activity__id=activity_id)

    def test_add_user(self):
        """Tests adding a user to a EighthScheduledActivity."""
        user = self.make_admin()
        # Ensure we can see the user's signed-up activities.
        response = self.client.get(reverse('eighth_signup'))
        self.assertEqual(response.status_code, 200)

        # Create a block
        block = self.add_block(date='9001-4-20', block_letter='A')
        self.assertEqual(block.formatted_date, 'Mon, April 20, 9001')

        # Create an activity
        activity = self.add_activity(name='Meme Club')

        # Schedule an activity
        schact = self.schedule_activity(block.id, activity.id)

        # Signup for an activity
        response = self.client.post(reverse('eighth_signup'), {'uid': 8889, 'bid': block.id, 'aid': activity.id})
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('eighth_signup'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(user, schact.members.all())

    def verify_signup(self, user, schact):
        old_count = schact.eighthsignup_set.count()
        schact.add_user(user)
        self.assertEqual(schact.eighthsignup_set.count(), old_count + 1)
        self.assertEqual(user.eighthsignup_set.filter(scheduled_activity__block=schact.block).count(), 1)

    def test_signups(self):
        """Do some sample signups."""

        self.make_admin()
        user1 = User.objects.create(username="user1")
        block1 = self.add_block(date='2015-01-01', block_letter='A')
        room1 = self.add_room(name="room1", capacity=1)

        act1 = self.add_activity(name='Test Activity 1')
        act1.rooms.add(room1)
        schact1 = self.schedule_activity(act1.id, block1.id)

        self.verify_signup(user1, schact1)

    def test_blacklist(self):
        """Make sure users cannot sign up for blacklisted activities."""

        self.make_admin()
        user1 = User.objects.create(username="user1")
        block1 = self.add_block(date='2015-01-01', block_letter='A')
        room1 = self.add_room(name="room1", capacity=1)

        act1 = self.add_activity(name='Test Activity 1')
        act1.rooms.add(room1)
        act1.users_blacklisted.add(user1)
        schact1 = self.schedule_activity(act1.id, block1.id)

        with self.assertRaisesMessage(SignupException, "Blacklist"):
            schact1.add_user(user1)

    def test_all_associated_rooms(self):
        """Make sure EighthScheduledActivities can return all associated rooms."""

        self.make_admin()
        block1 = self.add_block(date='2015-01-01', block_letter='A')
        room1 = self.add_room(name="room1", capacity=1)
        room2 = self.add_room(name="room2", capacity=1)

        act1 = self.add_activity(name='Test Activity 1')
        act1.rooms.add(room1)
        schact1 = self.schedule_activity(act1.id, block1.id)
        schact1.rooms.add(room2)

        self.assertIn(room1, schact1.all_associated_rooms)
        self.assertIn(room2, schact1.all_associated_rooms)
        self.assertEqual(2, len(schact1.all_associated_rooms))

    def test_room_use(self):
        """Make sure EighthScheduledActivities return the correct room."""

        self.make_admin()
        block1 = self.add_block(date='2015-01-01', block_letter='A')
        room1 = self.add_room(name="room1", capacity=1)
        room2 = self.add_room(name="room2", capacity=1)

        act1 = self.add_activity(name='Test Activity 1')
        act1.rooms.add(room1)
        schact1 = self.schedule_activity(act1.id, block1.id)

        self.assertIn(room1, schact1.get_scheduled_rooms())
        self.assertEqual(1, len(schact1.get_scheduled_rooms()))

        schact1.rooms.add(room2)
        self.assertIn(room2, schact1.get_scheduled_rooms())
        self.assertEqual(1, len(schact1.get_scheduled_rooms()))

    def test_room_formatting(self):
        """Make sure a room name formatting is correct."""
        self.make_admin()
        room1 = self.add_room(name="999", capacity=1)
        self.assertEqual('Rm. %s' % room1.name, room1.formatted_name)
        room2 = self.add_room(name="Lab 999", capacity=1)
        self.assertEqual(room2.name, room2.formatted_name)
        room3 = self.add_room(name="Weyanoke 999", capacity=1)
        self.assertEqual('Wey. 999', room3.formatted_name)
        room4 = self.add_room(name="Room 999", capacity=1)
        self.assertEqual('Rm. 999', room4.formatted_name)

    def test_both_blocks(self):
        """Make sure that signing up for a both blocks activity works."""
        self.make_admin()
        user1 = User.objects.create(username="user1")
        group1 = Group.objects.create(name="group1")
        user1.groups.add(group1)
        block1 = self.add_block(date='2015-01-01', block_letter='A')
        block2 = self.add_block(date='2015-01-01', block_letter='B')
        room1 = self.add_room(name="room1", capacity=1)

        act1 = self.add_activity(name='Test Activity 1', sticky=True)
        act1.rooms.add(room1)
        schact1 = self.schedule_activity(act1.id, block1.id)

        act2 = self.add_activity(name='Test Activity 2', both_blocks=True)
        act2.rooms.add(room1)
        schact2 = self.schedule_activity(act2.id, block2.id)

        response = self.client.post(reverse('eighth_admin_signup_group_action', args=[group1.id, schact1.id]), {'confirm': True})
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse('eighth_admin_signup_group_action', args=[group1.id, schact2.id]), {'confirm': True})
        self.assertEqual(response.status_code, 302)