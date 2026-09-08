from django.contrib import admin

from .models import (AppointmentEnquiry, AssessmentRequest, BlogPost,
                     ContactMessage, MilestoneEnquiry)


@admin.register(AppointmentEnquiry)
class AppointmentEnquiryAdmin(admin.ModelAdmin):
    list_display = ('child_name', 'parent_name', 'phone', 'area_of_concern', 'preferred_time', 'status', 'created_at')
    list_filter = ('status', 'area_of_concern', 'preferred_time', 'created_at')
    search_fields = ('child_name', 'parent_name', 'phone')
    list_editable = ('status',)
    readonly_fields = ('created_at',)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'author', 'published_at')
    list_filter = ('status', 'published_at', 'author')
    search_fields = ('title', 'excerpt', 'body')
    list_editable = ('status',)
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    readonly_fields = ('created_at', 'updated_at')
    fields = ('title', 'slug', 'author', 'status', 'published_at',
              'cover_image', 'excerpt', 'body', 'created_at', 'updated_at')


@admin.register(AssessmentRequest)
class AssessmentRequestAdmin(admin.ModelAdmin):
    list_display = ('child_name', 'parent_name', 'email', 'area_of_concern', 'status', 'created_at')
    list_filter = ('status', 'area_of_concern', 'created_at')
    search_fields = ('child_name', 'parent_name', 'email')
    list_editable = ('status',)
    readonly_fields = ('created_at',)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'handled', 'created_at')
    list_filter = ('handled', 'created_at')
    search_fields = ('name', 'email', 'message')
    list_editable = ('handled',)
    readonly_fields = ('created_at',)


@admin.register(MilestoneEnquiry)
class MilestoneEnquiryAdmin(admin.ModelAdmin):
    list_display = ('parent_name', 'phone', 'email', 'child_age', 'score', 'status', 'created_at')
    list_filter = ('status', 'child_age', 'created_at')
    search_fields = ('parent_name', 'phone', 'email')
    list_editable = ('status',)
    readonly_fields = ('created_at',)

    @admin.display(description='Milestones ticked')
    def score(self, obj):
        return f'{obj.milestones_done}/{obj.milestones_total}'
