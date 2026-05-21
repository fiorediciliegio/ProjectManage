from rest_framework import serializers
from .models import (
    Project,
    Person,
    File,
    CostInformation,
    QualityInspectionTemplate,
    InspectionItem,
    QualityInspectionReport,
    InspectionResult,
    SecurityCheckTemplate,
    SecurityCheckItem,
    SecurityInspectionReport,
    SecurityCheckResult,
    SecurityInspectionImage,
    SafetyIssueSolution,
)


class ProjectSerializer(serializers.ModelSerializer):
    pjnumber = serializers.CharField(source='NUM_Project', required=False, allow_blank=True)
    pjname = serializers.CharField(source='NAME_Project', required=False, allow_blank=True)
    pjtype = serializers.CharField(source='TYPE_Project', required=False, allow_blank=True)
    pjmanager = serializers.CharField(source='MANA_Project', required=False, allow_blank=True)
    pjvalue = serializers.CharField(source='VALUE_Project', required=False, allow_blank=True)
    pjcurrency = serializers.CharField(source='CUR_Project', required=False, allow_blank=True)
    pjstart_date = serializers.CharField(source='START_Project', required=False, allow_blank=True)
    pjend_date = serializers.CharField(source='END_Project', required=False, allow_blank=True)
    pjaddress = serializers.CharField(source='ADDRESS_Project', required=False, allow_blank=True)
    pjdescription = serializers.CharField(source='DESC_Project', required=False, allow_blank=True)
    pjid = serializers.IntegerField(source='id', read_only=True)


    def validate_pjnumber(self, value):
        project_id = self.instance.id if self.instance else None
        query = Project.objects.filter(NUM_Project=value)
        if project_id is not None:
            query = query.exclude(id=project_id)
        if value and query.exists():
            raise serializers.ValidationError('该编号已存在')
        return value

    class Meta:
        model = Project
        fields = [
            'pjnumber', 'pjname', 'pjtype', 'pjmanager', 'pjvalue', 'pjcurrency',
            'pjstart_date', 'pjend_date', 'pjaddress', 'pjdescription', 'pjid',
        ]


class PersonSerializer(serializers.ModelSerializer):
    perid = serializers.IntegerField(source='id', read_only=True)
    pername = serializers.CharField(source='NAME_Person', required=False, allow_blank=True)
    pernumber = serializers.CharField(source='NUM_Person', required=False, allow_blank=True)
    permail = serializers.CharField(source='MAIL_Person', required=False, allow_blank=True)
    perrole = serializers.CharField(source='POS_Person', required=False, allow_blank=True)
    perdescription = serializers.CharField(source='DESC_Person', required=False, allow_blank=True, allow_null=True)
    pj_id = serializers.PrimaryKeyRelatedField(
        source='ID_Project',
        queryset=Project.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )


    def validate_pernumber(self, value):
        person_id = self.instance.id if self.instance else None
        query = Person.objects.filter(NUM_Person=value)
        if person_id is not None:
            query = query.exclude(id=person_id)
        if value and query.exists():
            raise serializers.ValidationError('该编号已存在')
        return value
    class Meta:
        model = Person
        fields = ['perid', 'pername', 'pernumber', 'permail', 'perrole', 'perdescription', 'pj_id']


class FileSerializer(serializers.ModelSerializer):
    file_id = serializers.IntegerField(source='id', read_only=True)
    file_name = serializers.CharField(source='NAME_File', read_only=True)
    file_size = serializers.IntegerField(source='SIZE_File', read_only=True)
    file_format = serializers.CharField(source='FORM_File', read_only=True)
    upload_time = serializers.SerializerMethodField()
    uploader_name = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ['file_id', 'file_name', 'file_size', 'file_format', 'upload_time', 'uploader_name']

    def get_upload_time(self, obj):
        return obj.UPTIME_File.strftime('%Y-%m-%d %H:%M:%S')

    def get_uploader_name(self, obj):
        return obj.UPLOADER_Person.NAME_Person if obj.UPLOADER_Person else ''


class CostInformationSerializer(serializers.ModelSerializer):
    costId = serializers.IntegerField(source='id', read_only=True)
    costName = serializers.CharField(source='NAME_Cost', required=False, allow_blank=True)
    projectName = serializers.CharField(source='ID_Project.NAME_Project', read_only=True)
    date = serializers.DateField(source='DATE_Cost', required=False)
    expenseType = serializers.CharField(source='TYPE_Expense', required=False, allow_blank=True)
    accountant = serializers.CharField(source='NAME_Accountant', required=False, allow_blank=True)
    budgetAmount = serializers.CharField(source='BUDGET_Amount', required=False, allow_blank=True)
    currency = serializers.CharField(source='UNIT_Currency', required=False, allow_blank=True)
    costAmount = serializers.CharField(source='COST_Amount', required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(source='DESC_Cost', required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = CostInformation
        fields = [
            'costId', 'costName', 'projectName', 'date', 'expenseType', 'accountant',
            'budgetAmount', 'currency', 'costAmount', 'description',
        ]


class QualityInspectionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionItem
        fields = ['id', 'NAME_Item', 'VALUE_Item']


class QualityInspectionTemplateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source='NAME_Qit', read_only=True)
    items = serializers.SerializerMethodField()

    class Meta:
        model = QualityInspectionTemplate
        fields = ['id', 'name', 'items']

    def get_items(self, obj):
        items = InspectionItem.objects.filter(ID_Qit=obj.id)
        return QualityInspectionItemSerializer(items, many=True).data


class QualityInspectionReportSerializer(serializers.ModelSerializer):
    qrname = serializers.CharField(source='NAME_Project', required=False, allow_blank=True)
    qrnumber = serializers.CharField(source='NUM_Report', required=False, allow_blank=True)
    qrperson = serializers.CharField(source='INSPECTOR_Person', required=False, allow_blank=True)
    qrpart = serializers.CharField(source='PART_Num', required=False, allow_blank=True)
    qrcons_date = serializers.DateField(source='TIME_Construct', required=False)
    qrins_date = serializers.DateField(source='TIME_Inspect', required=False)
    qrfeedback = serializers.CharField(source='OPINION_Inspector', required=False, allow_blank=True)
    qrevaluation = serializers.CharField(source='STATUS_Inspect', required=False, allow_blank=True)
    report_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = QualityInspectionReport
        fields = [
            'qrname', 'qrnumber', 'qrperson', 'qrpart', 'qrcons_date',
            'qrins_date', 'qrfeedback', 'qrevaluation', 'report_id',
        ]


class SecurityCheckItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source='NAME_Item', read_only=True)
    value = serializers.CharField(source='VALUE_Item', read_only=True)

    class Meta:
        model = SecurityCheckItem
        fields = ['id', 'name', 'value']


class SecurityCheckTemplateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source='NAME_Sct', read_only=True)
    items = serializers.SerializerMethodField()

    class Meta:
        model = SecurityCheckTemplate
        fields = ['id', 'name', 'items']

    def get_items(self, obj):
        items = SecurityCheckItem.objects.filter(ID_Sct=obj.id)
        return SecurityCheckItemSerializer(items, many=True).data


class SecurityInspectionImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    upload_date = serializers.SerializerMethodField()

    class Meta:
        model = SecurityInspectionImage
        fields = ['image_url', 'upload_date']

    def get_image_url(self, obj):
        return obj.image.url

    def get_upload_date(self, obj):
        return obj.DATE_Upload.isoformat()


class SecurityCheckResultSerializer(serializers.ModelSerializer):
    item = serializers.CharField(source='NAME_Item', read_only=True)
    requirement = serializers.CharField(source='STANDARD_Item', read_only=True)
    result = serializers.CharField(source='RESULT_Item', read_only=True)

    class Meta:
        model = SecurityCheckResult
        fields = ['item', 'requirement', 'result']


class SecurityInspectionReportSerializer(serializers.ModelSerializer):
    srname = serializers.CharField(source='NAME_Project', required=False, allow_blank=True)
    srperson = serializers.CharField(source='NAME_SafetyOfficer', required=False, allow_blank=True)
    srnumber = serializers.CharField(source='NUM_Report', required=False, allow_blank=True)
    srpart = serializers.CharField(source='PART_Check', required=False, allow_blank=True)
    srins_date = serializers.CharField(source='DATE_Check', required=False, allow_blank=True)
    srfeedback = serializers.CharField(source='FEEDBACK_SafetyOfficer', required=False, allow_blank=True)
    srevaluation = serializers.CharField(source='STATUS_Overall', required=False, allow_blank=True)
    srsubitems = serializers.SerializerMethodField()
    image_attachments = serializers.SerializerMethodField()
    solutions = serializers.SerializerMethodField()
    report_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = SecurityInspectionReport
        fields = [
            'srname', 'srperson', 'srnumber', 'srpart', 'srins_date', 'srfeedback',
            'srevaluation', 'srsubitems', 'image_attachments', 'solutions', 'report_id',
        ]

    def get_srsubitems(self, obj):
        results = SecurityCheckResult.objects.filter(ID_Report=obj.id)
        return SecurityCheckResultSerializer(results, many=True).data

    def get_image_attachments(self, obj):
        images = SecurityInspectionImage.objects.filter(ID_Report=obj.id)
        return SecurityInspectionImageSerializer(images, many=True).data

    def get_solutions(self, obj):
        solutions = SafetyIssueSolution.objects.filter(ID_Report=obj.id).order_by('-DATE_Solution')
        return SafetyIssueSolutionSerializer(solutions, many=True).data


class SafetyIssueSolutionSerializer(serializers.ModelSerializer):
    solution_date = serializers.DateField(source='DATE_Solution', read_only=True)
    solution_description = serializers.CharField(source='DESCRIPTION_Solution', read_only=True)

    class Meta:
        model = SafetyIssueSolution
        fields = ['solution_date', 'solution_description']
