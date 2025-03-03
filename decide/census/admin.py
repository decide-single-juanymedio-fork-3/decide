from django.contrib import admin

from .models import Census, CensusGroup

class CensusAdmin(admin.ModelAdmin):
    list_display = ('voting_id', 'voter_id')
    list_filter = ('voting_id', )
    search_fields = ('voter_id', )

class CensusGroupAdmin(admin.ModelAdmin):
    list_display = ('groupName', 'voting_id')
    def apply_census_action(self, request, queryset):
        for group in queryset:
            group.applyCensus() 
    apply_census_action.short_description = "Apply Census"
    actions = [apply_census_action]

admin.site.register(Census, CensusAdmin)
admin.site.register(CensusGroup, CensusGroupAdmin)
