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
    list_display = ('title', 'category', 'status', 'published_at', 'views')
    list_filter = ('status', 'category', 'published_at')
    search_fields = ('title', 'meta_description', 'body')
    list_editable = ('status',)
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    readonly_fields = ('views', 'created_at', 'updated_at')
    fieldsets = (
        ('Post', {
            'fields': ('title', 'slug', 'category', 'cover_image', 'cover_image_alt', 'body'),
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'description': 'How the post appears in Google and when shared. Both are optional.',
        }),
        ('Publishing', {
            'fields': ('status', 'published_at', 'author'),
        }),
        ('Record', {'fields': ('views', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    class Media:
        js = ('admin/blog_seo_counter.js',)


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
