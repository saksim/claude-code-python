"""Context notifications for Claude Code Python.

Handles displaying notifications to the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class NotificationType(Enum):
    """Types of notifications."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    PROGRESS = "progress"


@dataclass(frozen=True, slots=True)
class Notification:
    """A notification to display to the user.

    Attributes:
        type: Type of notification.
        title: Notification title.
        message: Notification message.
        timestamp: When the notification was created.
        id: Unique identifier for the notification.
        auto_dismiss: Whether to auto-dismiss the notification.
        dismiss_after: Seconds before auto-dismiss.
        metadata: Additional metadata.
    """

    type: NotificationType
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = ""
    auto_dismiss: bool = True
    dismiss_after: float = 5.0
    metadata: dict[str, Any] = field(default_factory=dict)


class NotificationManager:
    """Manages notifications to display to the user.

    Notifications are queued and can be displayed in various ways.
    """

    def __init__(self) -> None:
        """Initialize NotificationManager."""
        self._notifications: list[Notification] = []
        self._handlers: list[Callable[[Notification], None]] = []

    def add_notification(self, notification: Notification) -> str:
        """Add a notification and return its ID.

        Args:
            notification: The notification to add.

        Returns:
            The notification's ID.
        """
        if not notification.id:
            notification.id = f"notif_{len(self._notifications)}"

        self._notifications.append(notification)

        for handler in self._handlers:
            handler(notification)

        return notification.id

    def info(
        self,
        title: str,
        message: str,
        **kwargs: Any,
    ) -> str:
        """Add an info notification.

        Args:
            title: Notification title.
            message: Notification message.
            **kwargs: Additional notification parameters.

        Returns:
            The notification's ID.
        """
        return self.add_notification(
            Notification(
                type=NotificationType.INFO,
                title=title,
                message=message,
                **kwargs,
            )
        )

    def warning(
        self,
        title: str,
        message: str,
        **kwargs: Any,
    ) -> str:
        """Add a warning notification.

        Args:
            title: Notification title.
            message: Notification message.
            **kwargs: Additional notification parameters.

        Returns:
            The notification's ID.
        """
        return self.add_notification(
            Notification(
                type=NotificationType.WARNING,
                title=title,
                message=message,
                **kwargs,
            )
        )

    def error(
        self,
        title: str,
        message: str,
        **kwargs: Any,
    ) -> str:
        """Add an error notification.

        Args:
            title: Notification title.
            message: Notification message.
            **kwargs: Additional notification parameters.

        Returns:
            The notification's ID.
        """
        return self.add_notification(
            Notification(
                type=NotificationType.ERROR,
                title=title,
                message=message,
                auto_dismiss=False,
                **kwargs,
            )
        )

    def success(
        self,
        title: str,
        message: str,
        **kwargs: Any,
    ) -> str:
        """Add a success notification.

        Args:
            title: Notification title.
            message: Notification message.
            **kwargs: Additional notification parameters.

        Returns:
            The notification's ID.
        """
        return self.add_notification(
            Notification(
                type=NotificationType.SUCCESS,
                title=title,
                message=message,
                **kwargs,
            )
        )

    def progress(
        self,
        title: str,
        message: str,
        **kwargs: Any,
    ) -> str:
        """Add a progress notification.

        Args:
            title: Notification title.
            message: Notification message.
            **kwargs: Additional notification parameters.

        Returns:
            The notification's ID.
        """
        return self.add_notification(
            Notification(
                type=NotificationType.PROGRESS,
                title=title,
                message=message,
                **kwargs,
            )
        )

    def dismiss(self, notification_id: str) -> bool:
        """Dismiss a notification by ID.

        Args:
            notification_id: ID of the notification to dismiss.

        Returns:
            True if dismissed, False if not found.
        """
        for i, notif in enumerate(self._notifications):
            if notif.id == notification_id:
                self._notifications.pop(i)
                return True
        return False

    def clear(self) -> None:
        """Clear all notifications."""
        self._notifications.clear()

    def get_all(self) -> list[Notification]:
        """Get all notifications.

        Returns:
            List of all notifications.
        """
        return self._notifications.copy()

    def register_handler(
        self,
        handler: Callable[[Notification], None],
    ) -> None:
        """Register a handler for notifications.

        Args:
            handler: Callback function to handle notifications.
        """
        self._handlers.append(handler)

    def unregister_handler(
        self,
        handler: Callable[[Notification], None],
    ) -> None:
        """Unregister a notification handler.

        Args:
            handler: Handler to remove.
        """
        if handler in self._handlers:
            self._handlers.remove(handler)


_notification_manager: NotificationManager | None = None


def get_notification_manager() -> NotificationManager:
    """Get the global notification manager.

    Returns:
        Global NotificationManager instance.
    """
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager


def show_notification(
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.INFO,
) -> str:
    """Show a notification.

    Args:
        title: Notification title.
        message: Notification message.
        notification_type: Type of notification.

    Returns:
        The notification's ID.
    """
    manager = get_notification_manager()

    if notification_type == NotificationType.INFO:
        return manager.info(title, message)
    if notification_type == NotificationType.WARNING:
        return manager.warning(title, message)
    if notification_type == NotificationType.ERROR:
        return manager.error(title, message)
    if notification_type == NotificationType.SUCCESS:
        return manager.success(title, message)
    if notification_type == NotificationType.PROGRESS:
        return manager.progress(title, message)

    return manager.add_notification(
        Notification(
            type=notification_type,
            title=title,
            message=message,
        )
    )