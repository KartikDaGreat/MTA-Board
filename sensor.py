import threading

from gpiozero import DistanceSensor
from gpiozero.pins.pigpio import PiGPIOFactory

import config

_sensor = DistanceSensor(
    pin_factory=PiGPIOFactory(),
    echo=config.ULTRASONIC_ECHO_PIN,
    trigger=config.ULTRASONIC_TRIG_PIN,
    max_distance=2,
    threshold_distance=config.ULTRASONIC_THRESHOLD_M,
)

_hold_timer = None
_flip_timer = None
_held = False


def on_gesture(on_wave, on_hold, on_flip):
    """Wire up all three gestures off the same in-range/out-of-range crossing:
    a quick pass -- in range then back out again before HOLD_SECONDS elapses
    -- fires on_wave. Keeping something within threshold_distance
    continuously for HOLD_SECONDS instead fires on_hold, and on_wave is
    suppressed for that gesture. Holding on further, out to FLIP_HOLD_SECONDS,
    additionally fires on_flip -- on_hold has already fired by then, since
    FLIP_HOLD_SECONDS > HOLD_SECONDS."""

    def _enter():
        global _hold_timer, _flip_timer, _held
        _held = False

        def _fire_hold():
            global _held
            _held = True
            on_hold()

        def _fire_flip():
            global _held
            _held = True
            on_flip()

        _hold_timer = threading.Timer(config.HOLD_SECONDS, _fire_hold)
        _hold_timer.daemon = True
        _hold_timer.start()

        _flip_timer = threading.Timer(config.FLIP_HOLD_SECONDS, _fire_flip)
        _flip_timer.daemon = True
        _flip_timer.start()

    def _exit():
        global _hold_timer, _flip_timer, _held
        if _hold_timer is not None:
            _hold_timer.cancel()
            _hold_timer = None
        if _flip_timer is not None:
            _flip_timer.cancel()
            _flip_timer = None
        if not _held:
            on_wave()
        _held = False

    _sensor.when_in_range = _enter
    _sensor.when_out_of_range = _exit
