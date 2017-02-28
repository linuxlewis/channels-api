class BasePermission(object):
    """
    A base class from which all permission classes should inherit.
    """

    def has_permission(self, user, action, pk):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True


class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, user, action, pk):
        return user.is_authenticated
