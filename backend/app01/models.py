from django.db import models
from django.contrib.auth.models import User

#用户表
class LegacyUser(models.Model):
    id = models.AutoField(primary_key=True)
    NAME_USER = models.CharField(verbose_name='用户名称', max_length=100)
    PASSWORD = models.CharField(verbose_name='用户密码', max_length=100)
    LEVEL = models.CharField(verbose_name='用户级别', max_length=100)

    class Meta:
        verbose_name = '旧用户表'
        verbose_name_plural = '旧用户表'

# 项目表
class Project(models.Model):
    NUM_Project = models.CharField(verbose_name='项目编号', max_length=100)
    NAME_Project = models.CharField(verbose_name='项目名称', max_length=50)
    TYPE_Project = models.CharField(verbose_name='项目类型', max_length=50)
    VALUE_Project = models.CharField(verbose_name='项目价值', max_length=50,default='')
    START_Project = models.CharField(verbose_name='项目开始时间',max_length=20)
    END_Project = models.CharField(verbose_name='项目结束时间', max_length=20)
    ADDRESS_Project = models.CharField(verbose_name='项目地址', max_length=100)
    DESC_Project = models.CharField(verbose_name='项目描述', max_length=1000)
    id = models.AutoField(primary_key=True)
    MANA_Project = models.CharField(verbose_name='项目负责人', max_length=20,default='')
    CUR_Project = models.CharField(verbose_name='货币单位', max_length=50)
    ID_Person = models.ManyToManyField('Person', related_name='projects', blank=True)


# 项目节点表
class ProjectNode(models.Model):
    id = models.AutoField(primary_key=True)
    NAME_Milestone = models.CharField(max_length=100)
    DDL_Milestone = models.DateField()
    DES_Milestone = models.CharField(max_length=1000, null=True, blank=True)
    PHEN_Milestone = models.CharField(max_length=10)
    ID_Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='nodes')

# 人员表
class Person(models.Model):
    SYS_ROLE_CHOICES = [
        ('admin', '系统管理员'),
        ('project_manager', '项目管理员'),
        ('member', '普通成员'),
    ]

    user = models.OneToOneField(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='person_profile',
        verbose_name='关联登录账号'
    )

    sys_role = models.CharField(
        max_length=20,
        choices=SYS_ROLE_CHOICES,
        default='member',
        verbose_name='系统角色'
    )

    id = models.AutoField(primary_key=True)
    NAME_Person = models.CharField(max_length=20)
    NUM_Person = models.CharField(max_length=50)
    MAIL_Person = models.CharField(max_length=50)
    POS_Person = models.CharField(max_length=10)
    DESC_Person = models.CharField(max_length=1000, null=True, blank=True)
    ID_Project = models.ForeignKey(Project, on_delete=models.SET_NULL, related_name='person', null=True, blank=True)

# 日志表
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', '新增'),
        ('update', '修改'),
        ('delete', '删除'),
        ('upload', '上传'),
        ('download', '下载'),
        ('preview', '预览'),
        ('login', '登录'),
        ('logout', '退出登录'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    module = models.CharField(max_length=50)
    target_id = models.IntegerField(null=True, blank=True)
    target_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

#文件表
class File(models.Model):
    FILE = models.FileField(upload_to='uploads/')
    NAME_File = models.CharField(max_length=255)
    SIZE_File = models.IntegerField()
    FORM_File = models.CharField(max_length=20)
    UPTIME_File = models.DateTimeField(auto_now_add=True)
    ID_Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='file',default=1)
    UPLOADER_Person = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_files',
        verbose_name='上传人'
    )

#质检模板表
class QualityInspectionTemplate(models.Model):
    NAME_Qit = models.CharField(max_length=20)
    ID_Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='inspection_templates')

#检验项目表
class InspectionItem(models.Model):
    NAME_Item = models.CharField(max_length=20)
    VALUE_Item = models.CharField(max_length=30)
    ID_Qit = models.ForeignKey(QualityInspectionTemplate, on_delete=models.CASCADE, related_name='inspection_items')

#安检模板表
class SecurityCheckTemplate(models.Model):
    NAME_Sct = models.CharField(max_length=20)
    ID_Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='SCT')

#安检项目表
class SecurityCheckItem(models.Model):
    NAME_Item = models.CharField(max_length=20)
    VALUE_Item = models.CharField(max_length=30)
    ID_Sct = models.ForeignKey(SecurityCheckTemplate, on_delete=models.CASCADE)

# 质量报告表
class QualityInspectionReport(models.Model):
    NAME_Project = models.CharField(verbose_name='工程名称', max_length=200)
    PART_Num = models.CharField(verbose_name='检验部位以及编号', max_length=200)
    INSPECTOR_Person = models.CharField(verbose_name='质检员', max_length=100)
    TIME_Construct = models.DateField(verbose_name='施工时间')
    TIME_Inspect = models.DateField(verbose_name='检验时间')
    NUM_Report = models.CharField(verbose_name='报告编号', max_length=100)
    OPINION_Inspector = models.CharField(verbose_name='质检员意见', max_length=500)
    STATUS_Inspect = models.CharField(verbose_name='质检情况', max_length=500)
    ID_Project = models.ForeignKey(Project, verbose_name='项目', on_delete=models.SET_NULL, related_name='quality_reports', null=True, blank=True)

# 质检结果表
class InspectionResult(models.Model):
    NAME_Item = models.CharField(verbose_name='检验对象名称', max_length=100)
    VALUE_Standard = models.CharField(verbose_name='规定值或允许偏差', max_length=100)
    RESULT_Inspect = models.CharField(verbose_name='检验结果', max_length=50)
    ID_Report = models.ForeignKey(QualityInspectionReport, on_delete=models.CASCADE, related_name='inspection_results')

# 安全检查报告表
class SecurityInspectionReport(models.Model):
    NAME_Project = models.CharField(verbose_name='工程名称', max_length=100)
    NAME_SafetyOfficer = models.CharField(verbose_name='安全员', max_length=50)
    NUM_Report = models.CharField(verbose_name='报告编号', max_length=50)
    PART_Check = models.CharField(verbose_name='检查部位以及编号', max_length=100)
    DATE_Check = models.CharField(verbose_name='检查时间', max_length=20)
    FEEDBACK_SafetyOfficer = models.CharField(verbose_name='安全员意见', max_length=1000)
    STATUS_Overall = models.CharField(verbose_name='总体情况', max_length=1000)
    ID_Project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='inspection_reports', verbose_name='项目')

# 安全检查结果表
class SecurityCheckResult(models.Model):
    NAME_Item = models.CharField(verbose_name='检验项目', max_length=100)
    STANDARD_Item = models.CharField(verbose_name='检验标准', max_length=100)
    RESULT_Item = models.CharField(verbose_name='检验结果', max_length=100)
    ID_Report = models.ForeignKey(SecurityInspectionReport, on_delete=models.CASCADE, related_name='check_results')

# 图片附件表
class SecurityInspectionImage(models.Model):
    image = models.ImageField(upload_to='security_inspection_images/')
    DATE_Upload = models.DateTimeField(auto_now_add=True)
    ID_Report = models.ForeignKey(SecurityInspectionReport, on_delete=models.CASCADE, related_name='images')

#安全问题表
class SafetyIssueSolution(models.Model):
    ID_Report = models.ForeignKey(SecurityInspectionReport, on_delete=models.CASCADE, related_name='solutions')
    DATE_Solution = models.DateField(verbose_name='解决日期')
    DESCRIPTION_Solution = models.CharField(verbose_name='解决方案', max_length=5000)

#成本信息表
class CostInformation(models.Model):
    NAME_Cost = models.CharField(verbose_name='成本名称', max_length=100)
    ID_Project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name='所属项目')
    TYPE_Expense = models.CharField(verbose_name='费用类型', max_length=50)
    BUDGET_Amount = models.CharField(verbose_name='预算金额', max_length=20)
    UNIT_Currency = models.CharField(verbose_name='货币单位', max_length=10)
    DESC_Cost = models.CharField(verbose_name='描述', max_length=500, null=True, blank=True)
    DATE_Cost = models.DateField(verbose_name='日期')
    NAME_Accountant = models.CharField(verbose_name='财务人员', max_length=50)
    COST_Amount = models.CharField(verbose_name='成本金额', max_length=20, null=True, blank=True)
