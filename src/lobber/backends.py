from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

from lobber.settings import LOBBER_LOG_FILE
import lobber.log
logger = lobber.log.Logger("web", LOBBER_LOG_FILE)


# The RemoteUserBackend is copied from Django 1.1 django/contrib/auth/backends.py
# with the following modifications done:
# - do not allow externally authenticated privileged users
# - demand that the remote_user contains a "@" character

class RemoteUserBackend(ModelBackend):
    """
    This backend is to be used in conjunction with the ``RemoteUserMiddleware``
    found in the middleware module of this package, and is used when the server
    is handling authentication outside of Django.

    By default, the ``authenticate`` method creates ``User`` objects for
    usernames that don't already exist in the database.  Subclasses can disable
    this behavior by setting the ``create_unknown_user`` attribute to
    ``False``.
    """

    # Create a User object if not already in the database?
    create_unknown_user = True

    def authenticate(self, remote_user, password=None):
        """
        The username passed as ``remote_user`` is considered trusted.  This
        method simply returns the ``User`` object with the given username,
        creating a new ``User`` object if ``create_unknown_user`` is ``True``.

        Returns None if ``create_unknown_user`` is ``False`` and a ``User``
        object with the given username is not found in the database.
        """

        if not remote_user:
            return

        # TCS Change: demand that the remote_user contains a "@" character
        if not "@" in remote_user:
            return

        user = None
        username = self.clean_username(remote_user)

        # Note that this could be accomplished in one try-except clause, but
        # instead we use get_or_create when creating unknown users since it has
        # built-in safeguards for multiple threads.
        if self.create_unknown_user:
            if len(username) > 30:
                logger.warning("%s: username too long (remote_user=%s)"
                               % (username, remote_user))
                return                  # Fail.
            user, created = User.objects.get_or_create(username=username)
            if created:
                user = self.configure_user(user)
        else:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                pass

        # TCS Change: do not allow externally authenticated privileged users
        if user.is_staff or user.is_superuser:
            return None

        return user

    def clean_username(self, username):
        """
        Performs any cleaning on the "username" prior to using it to get or
        create the user object.  Returns the cleaned username.

        By default, returns the username unchanged.
        """
        # Ugly hack for avoiding len(username) > 30.
        return username.replace('@idp.protectnetwork.org', '@PNW.org')

    def configure_user(self, user):
        """
        Configures a user after creation and returns the updated user.

        By default, returns the user unmodified.
        """
        return user
