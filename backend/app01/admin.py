from django.contrib import admin

from .models import (
    CostInformation,
    File,
    InspectionItem,
    InspectionResult,
    Person,
    Project,
    ProjectNode,
    QualityInspectionReport,
    QualityInspectionTemplate,
    SafetyIssueSolution,
    SecurityCheckItem,
    SecurityCheckResult,
    SecurityCheckTemplate,
    SecurityInspectionImage,
    SecurityInspectionReport,
    LegacyUser,
)


@admin.register(LegacyUser)
class LegacyUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'NAME_USER', 'LEVEL')
    search_fields = ('NAME_USER', 'LEVEL')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'NUM_Project', 'NAME_Project', 'TYPE_Project', 'MANA_Project', 'START_Project', 'END_Project')
    search_fields = ('NUM_Project', 'NAME_Project', 'MANA_Project', 'ADDRESS_Project')
    list_filter = ('TYPE_Project', 'CUR_Project')


@admin.register(ProjectNode)
class ProjectNodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'NAME_Milestone', 'ID_Project', 'DDL_Milestone', 'PHEN_Milestone')
    search_fields = ('NAME_Milestone', 'DES_Milestone', 'ID_Project__NAME_Project', 'ID_Project__NUM_Project')
    list_filter = ('PHEN_Milestone', 'DDL_Milestone')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'NUM_Person', 'NAME_Person', 'POS_Person', 'MAIL_Person', 'ID_Project')
    search_fields = ('NUM_Person', 'NAME_Person', 'MAIL_Person', 'POS_Person', 'ID_Project__NAME_Project')
    list_filter = ('POS_Person',)


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('id', 'NAME_File', 'FORM_File', 'SIZE_File', 'ID_Project', 'UPTIME_File')
    search_fields = ('NAME_File', 'FORM_File', 'ID_Project__NAME_Project', 'ID_Project__NUM_Project')
    list_filter = ('FORM_File', 'UPTIME_File')


@admin.register(CostInformation)
class CostInformationAdmin(admin.ModelAdmin):
    list_display = ('id', 'NAME_Cost', 'ID_Project', 'TYPE_Expense', 'NAME_Accountant', 'DATE_Cost')
    search_fields = ('NAME_Cost', 'TYPE_Expense', 'NAME_Accountant', 'ID_Project__NAME_Project', 'ID_Project__NUM_Project')
    list_filter = ('TYPE_Expense', 'DATE_Cost', 'UNIT_Currency')


@admin.register(QualityInspectionTemplate)
class QualityInspectionTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'NAME_Qit', 'ID_Project')
    search_fields = ('NAME_Qit', 'ID_Project__NAME_Project', 'ID_Project__NUM_Project')


@admin.register(InspectionItem)
class InspectionItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'NAME_Item', 'VALUE_Item', 'ID_Qit')
    search_fields = ('NAME_Item', 'VALUE_Item', 'ID_Qit__NAME_Qit')


@admin.register(QualityInspectionReport)
class QualityInspectionReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'NUM_Report', 'NAME_Project', 'INSPECTOR_Person', 'STATUS_Inspect', 'TIME_Inspect')
    search_fields = ('NUM_Report', 'NAME_Project', 'PART_Num', 'INSPECTOR_Person')
    list_filter = ('STATUS_Inspect', 'TIME_Inspect')


@admin.register(InspectionResult)
class InspectionResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'NAME_Item', 'VALUE_Standard', 'RESULT_Inspect', 'ID_Report')
    search_fields = ('NAME_Item', 'VALUE_Standard', 'RESULT_Inspect', 'ID_Report__NUM_Report')


@admin.register(SecurityCheckTemplate)
class SecurityCheckTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'NAME_Sct', 'ID_Project')
    search_fields = ('NAME_Sct', 'ID_Project__NAME_Project', 'ID_Project__NUM_Project')


@admin.register(SecurityCheckItem)
class SecurityCheckItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'NAME_Item', 'VALUE_Item', 'ID_Sct')
    search_fields = ('NAME_Item', 'VALUE_Item', 'ID_Sct__NAME_Sct')


@admin.register(SecurityInspectionReport)
class SecurityInspectionReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'NUM_Report', 'NAME_Project', 'NAME_SafetyOfficer', 'STATUS_Overall', 'DATE_Check')
    search_fields = ('NUM_Report', 'NAME_Project', 'PART_Check', 'NAME_SafetyOfficer')
    list_filter = ('STATUS_Overall',)


@admin.register(SecurityCheckResult)
class SecurityCheckResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'NAME_Item', 'STANDARD_Item', 'RESULT_Item', 'ID_Report')
    search_fields = ('NAME_Item', 'STANDARD_Item', 'RESULT_Item', 'ID_Report__NUM_Report')


@admin.register(SecurityInspectionImage)
class SecurityInspectionImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'ID_Report', 'DATE_Upload')
    search_fields = ('ID_Report__NUM_Report',)
    list_filter = ('DATE_Upload',)


@admin.register(SafetyIssueSolution)
class SafetyIssueSolutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'ID_Report', 'DATE_Solution')
    search_fields = ('ID_Report__NUM_Report', 'DESCRIPTION_Solution')
    list_filter = ('DATE_Solution',)
