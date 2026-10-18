#permission class 
# only logged in customers can make reservations 
# this rule will be used for another apps (apis)

from rest_framework.permissions import BasePermission
from .models import User

# middleware for customer
#base permission DRF class we use this class 
class IsCustomer(BasePermission):
    message = "This action is only available to customers."
    #true or false 
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role==User.Role.CUSTOMER
# guide 
class IsGuide(BasePermission):
    message = "This action is only available to guides."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.GUIDE