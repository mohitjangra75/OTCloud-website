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
    list_display = ('title', 'kind', 'category', 'status', 'start_here',
                    'from_therapy_team', 'views', 'published_at')
    list_filter = ('status', 'kind', 'category', 'start_here', 'from_therapy_team', 'published_at')
    search_fields = ('title', 'excerpt', 'body')
    list_editable = ('status', 'start_here', 'from_therapy_team')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    readonly_fields = ('views', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'kind', 'category', 'author', 'status', 'published_at')
        }),
        ('Content', {
            'fields': ('cover_image', 'excerpt', 'body', 'key_takeaways', 'reading_time')
        }),
        ('Where it appears', {
            'fields': ('start_here', 'from_therapy_team'),
            'description': 'Start Here shows the post in the row at the top of the blog. '
                           'Insights shows it under "Insights from OTCloud".'
        }),
        ('Linked pages', {
            'fields': ('related_concern', 'related_concern_note', 'related_service'),
            'description': 'Shown at the end of the post so parents can go from an article '
                           'to the matching concern and service.'
        }),
        ('Record', {'fields': ('views', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(AssessmentRequest)
class AssessmentRequestAdmin(admin.ModelAdmin):
    list_display = ('child_name', 'child_age', 'parent_name', 'phone', 'email', 'area_of_concern', 'status', 'created_at')
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
