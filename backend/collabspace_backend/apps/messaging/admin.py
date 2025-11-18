from django.contrib import admin
from .models import Channel, Message, ChannelMember, MessageReaction, DirectMessage

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'workspace', 'channel_type', 'created_by', 'is_archived', 'created_at']
    list_filter = ['channel_type', 'is_archived', 'workspace', 'created_at']
    search_fields = ['name', 'description']
    raw_id_fields = ['workspace', 'created_by']


class ChannelMemberInline(admin.TabularInline):
    model = ChannelMember
    extra = 0
    raw_id_fields = ['user']
    readonly_fields = ['last_read_at', 'created_at']

@admin.register(ChannelMember)
class ChannelMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'channel', 'role', 'last_read_at', 'notifications_enabled']
    list_filter = ['role', 'notifications_enabled', 'channel__channel_type']
    search_fields = ['user__username', 'channel__name']
    raw_id_fields = ['user', 'channel']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['channel', 'sender', 'content_preview', 'created_at', 'is_edited', 'is_deleted']
    list_filter = ['message_type', 'is_edited', 'is_pinned', 'is_deleted', 'created_at']
    search_fields = ['content', 'sender__username']
    raw_id_fields = ['channel', 'sender', 'parent_message']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'emoji', 'created_at']
    list_filter = ['emoji', 'created_at']
    search_fields = ['message__content', 'user__username']
    raw_id_fields = ['message', 'user']


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'content_preview', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['content', 'sender__username', 'recipient__username']
    raw_id_fields = ['sender', 'recipient']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'