import unittest

from barnaby.reactions import PerceptionEvent
from barnaby.trigger import OneShot

TARGET = "thumbs_up"


def ev(gesture, expression="neutral"):
    return PerceptionEvent(gesture, expression, 0.9, 0.9, 10.0)


def fires(trigger, events, step=0.2, start=0.0):
    """Feed (gesture[, expression]) events `step` seconds apart; return fire count."""
    count = 0
    for i, item in enumerate(events):
        gesture, *rest = (item,) if isinstance(item, str) else item
        count += trigger.feed(ev(gesture, *rest), start + i * step)
    return count


class OneShotTest(unittest.TestCase):
    def test_held_gesture_with_expression_changes_fires_once(self):
        events = [(TARGET, "neutral"), (TARGET, "happy"), (TARGET, "neutral")]
        self.assertEqual(fires(OneShot(TARGET), events), 1)

    def test_r11_trace_fires_once(self):
        trace = [TARGET, TARGET, "none", TARGET, TARGET, TARGET, TARGET, "none", TARGET]
        self.assertEqual(fires(OneShot(TARGET), trace), 1)

    def test_flicker_inside_cooldown_fires_once(self):
        trace = [TARGET, "none", TARGET, "none", TARGET, "none", TARGET]
        self.assertEqual(fires(OneShot(TARGET), trace, step=1.5), 1)

    def test_fires_again_after_release_and_cooldown(self):
        trigger = OneShot(TARGET, cooldown_s=20.0, rearm_s=1.0)
        self.assertEqual(fires(trigger, [TARGET, "none"], step=1.0), 1)
        self.assertEqual(fires(trigger, [TARGET], start=25.0), 1)

    def test_short_release_after_cooldown_does_not_rearm(self):
        trigger = OneShot(TARGET, cooldown_s=20.0, rearm_s=1.0)
        self.assertTrue(trigger.feed(ev(TARGET), 0.0))
        self.assertFalse(trigger.feed(ev("none"), 29.5))
        self.assertFalse(trigger.feed(ev(TARGET), 30.0))

    def test_release_long_enough_but_inside_cooldown_does_not_fire(self):
        trigger = OneShot(TARGET, cooldown_s=20.0, rearm_s=1.0)
        self.assertTrue(trigger.feed(ev(TARGET), 0.0))
        self.assertFalse(trigger.feed(ev("none"), 1.0))
        self.assertFalse(trigger.feed(ev(TARGET), 10.0))

    def test_other_gestures_never_fire(self):
        trigger = OneShot(TARGET)
        others = ["open_palm", "peace", "pointing", "fist", "unknown", "none"]
        self.assertEqual(fires(trigger, others * 3), 0)

    def test_no_cooldown_or_rearm_fires_on_every_new_show(self):
        trigger = OneShot(TARGET, cooldown_s=0, rearm_s=0)
        self.assertEqual(fires(trigger, [TARGET, "none", TARGET, "none", TARGET]), 3)

    def test_no_cooldown_or_rearm_still_once_per_hold(self):
        trigger = OneShot(TARGET, cooldown_s=0, rearm_s=0)
        self.assertEqual(fires(trigger, [(TARGET, "neutral"), (TARGET, "happy")]), 1)


if __name__ == "__main__":
    unittest.main()
