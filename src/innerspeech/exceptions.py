"""Exception types raised by the Inner Speech processing code."""


class InnerSpeechError(Exception):
    """Base class for all errors raised by this package."""


class EventSequenceError(InnerSpeechError):
    """The recorded event sequence is invalid or could not be corrected."""


class InvalidSelectionError(InnerSpeechError, ValueError):
    """An unknown condition, class or channel-group name was requested."""
