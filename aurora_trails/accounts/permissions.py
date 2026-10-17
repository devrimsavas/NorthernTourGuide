#permission class 
# only logged in customers can make reservations 
# this rule will be used for another apps (apis)

from rest_framework.permissions import BasePermission
from .models import User

# middleware for customer
#base permission DRF class we use this class 
class IsCustomer(BasePermission):
    message="Only Customers can make bookings"
    #true or false 
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role==User.Role.CUSTOMER