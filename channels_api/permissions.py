

class BasePermission(object):
    
    def __init__(self, queryset, lookup_field):
        self.queryset = queryset
        self.lookup_field = lookup_field

    def has_permission(self, user, action, pk):
        pass


class AllowAny(BasePermission):

    def has_permission(self, user, action, pk):
        return True


class IsAuthenticated(BasePermission):

    def has_permission(self, user, action, pk):
        return user.pk and user.is_authenticated
