from django.contrib import admin
from .models import *
from django.contrib import messages 

class UserAdmin(admin.ModelAdmin): 
    search_fields = ('username', )
    list_display = ('username', 'active','date_joined') 
  
    def active(self, obj): 
        return obj.is_active == 1

    def make_active(modeladmin, request, queryset): 
        queryset.update(is_active = 1) 
        messages.success(request, "Selected Record(s) Marked as Active Successfully !!") 
  
    def make_inactive(modeladmin, request, queryset): 
        queryset.update(is_active = 0) 
        messages.success(request, "Selected Record(s) Marked as Inactive Successfully !!") 
  
    make_active.short_description = "Make user active"
    make_inactive.short_description = "Make user inactive" 
  
    def has_delete_permission(self, request, obj = None): 
        return False    
    def delete_queryset(modeladmin, request, queryset):
        queryset.delete()
        messages.success(request, "Selected Record(s) Deleted Successfully !!")


    active.boolean = True
    delete_queryset.short_description = "Deleted User"
    
    actions = [make_active,make_inactive, delete_queryset ]




admin.site.site_header = 'administration'
admin.site.site_title = 'Admin'
# Register your models here.
admin.site.register(User,UserAdmin) 
admin.site.register(Profile)
