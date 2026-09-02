from app01.views_modules.common import *


# ———————————————————— 安全监测 ————————————————————
# 获取安全检查项
@api_view(['GET'])
def sitem_list(request, scr_id):
    try:
        items = SecurityCheckItem.objects.filter(ID_Sct=scr_id)
        items_data = [
            {
                'id': item.pk,
                'item_name': item.NAME_Item,
                'item_value': item.VALUE_Item,
            }
            for item in items
        ]
        return success_response(
            data={'items': items_data},
            message='获取安全检查项成功',
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

# REST 安全模板模块：模板列表与新增接口
@api_view(['GET', 'POST'])
def rest_safety_templates(request, project_id):
    if request.method == 'GET':
        try:
            templates = SecurityCheckTemplate.objects.filter(ID_Project=project_id)
            serializer = SecurityCheckTemplateSerializer(templates, many=True)
            return success_response(
                data={'sctTemplates': serializer.data},
                message='获取安全模板列表成功',
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    template_name = request.data.get('stname')
    items_data = request.data.get('subitems')
    # 登录校验
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error
    # 权限校验
    project = Project.objects.get(id=project_id)
    if not can_manage_project_safety(project, person):
        return permission_denied('只有管理员、当前项目经理或当前项目安全人员可以操作')

    if not project_id or not template_name or not items_data:
        return error_response(
            message='缺少项目ID、模板名称或检查项',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        project = Project.objects.get(id=project_id)
        template = SecurityCheckTemplate.objects.create(NAME_Sct=template_name, ID_Project=project)
        for item_data in items_data:
            SecurityCheckItem.objects.create(
                NAME_Item=item_data.get('name'),
                VALUE_Item=item_data.get('requirement'),
                ID_Sct=template,
            )
        serializer = SecurityCheckTemplateSerializer(template)
        create_audit_log(
            request=request,
            action='create',
            module='安全监测',
            target_id=template.pk,
            target_name=project.NAME_Project,
            description=f'新增安全模板：{template.NAME_Sct}',
        )
        return success_response(
            data={'template': serializer.data},
            message='安全模板创建成功',
            status_code=status.HTTP_201_CREATED,
        )
    except Project.DoesNotExist:
        return error_response(message='项目不存在', status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# REST 安全模板模块：模板删除接口
@api_view(['DELETE'])
def rest_safety_template_detail(request, template_id):
    try:
        template = SecurityCheckTemplate.objects.get(id=template_id)
        # 登录校验
        person, auth_error = get_authenticated_person(request)
        if auth_error:
            return auth_error
        # 权限校验
        project = template.ID_Project
        if not can_manage_project_safety(project, person):
            return permission_denied('只有管理员、当前项目经理或当前项目安全人员可以操作')
        create_audit_log(
            request=request,
            action='delete',
            module='安全监测',
            target_id=template.pk,
            target_name=project.NAME_Project,
            description=f'删除安全模板：{template.NAME_Sct}',
        )
        template.delete()
        return success_response(
            data=None,
            message='安全模板删除成功',
            status_code=status.HTTP_200_OK,
        )
    except SecurityCheckTemplate.DoesNotExist:
        return error_response(message='安全模板不存在', status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# REST 安全模板模块：获取模板检查项接口
@api_view(['GET'])
def rest_safety_template_items(request, template_id):
    try:
        items = SecurityCheckItem.objects.filter(ID_Sct=template_id)
        data = [
            {'id': item.pk, 'item_name': item.NAME_Item, 'item_value': item.VALUE_Item}
            for item in items
        ]
        return success_response(
            data={'items': data},
            message='获取安全模板检查项成功',
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 新建安全检验报告
@api_view(['POST'])
def rest_safety_reports(request, project_id):
    report_data = request.POST.get('report')
    if not report_data:
        return error_response(
            message='缺少报告数据',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        data = json.loads(report_data)
        images = request.FILES.getlist('images')
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return error_response(message='项目不存在', status_code=status.HTTP_404_NOT_FOUND)
    except json.JSONDecodeError:
        return error_response(message='报告数据格式错误', status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # 登录校验
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error
    # 权限校验
    if not can_manage_project_safety(project, person):
        return permission_denied('只有管理员、当前项目经理或当前项目安全人员可以新建安全报告')

    if not _project_person_exists(project_id, data.get('srperson'), '安全员'):
        return error_response(
            message='安全员必须从当前项目中的安全员中选择',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    serializer = SecurityInspectionReportSerializer(data=data)
    if not serializer.is_valid():
        return error_response(
            message='安全报告创建失败',
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        report = serializer.save(ID_Project=project)
        for item in data.get('srsubitems', []):
            SecurityCheckResult.objects.create(
                NAME_Item=item.get('name'),
                STANDARD_Item=item.get('requirement'),
                RESULT_Item=item.get('result'),
                ID_Report=report,
            )
        for image in images:
            SecurityInspectionImage.objects.create(image=image, ID_Report=report)
        create_audit_log(
            request=request,
            action='create',
            module='安全监测',
            target_id=report.pk,
            target_name=project.NAME_Project,
            description=f'新增安全报告：工程名称：{report.NAME_Project}，检查部位及编号：{report.PART_Check}，报告编号：{report.NUM_Report}，总体情况：{report.STATUS_Overall}',
        )
        return success_response(
            data={'report': SecurityInspectionReportSerializer(report).data},
            message='安全报告创建成功',
            status_code=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 现存安全问题列表
@api_view(['GET'])
def rest_safety_issues(request, project_id):
    try:
        reports = SecurityInspectionReport.objects.filter(
            ID_Project=project_id,
            STATUS_Overall__in=['一般安全问题', '重大安全问题'],
            solutions__isnull=True,
        ).distinct().order_by('-id')
        serializer = SecurityInspectionReportSerializer(reports, many=True)
        return success_response(
            data={'filteredReports': serializer.data},
            message='获取现存安全问题成功',
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# REST 安全问题模块：删除现存安全问题接口
@api_view(['DELETE'])
def rest_safety_issue_detail(request, report_id):
    try:
        report = SecurityInspectionReport.objects.get(
            id=report_id,
            STATUS_Overall__in=['一般安全问题', '重大安全问题'],
            solutions__isnull=True,
        )
    except SecurityInspectionReport.DoesNotExist:
        return error_response(message='现存安全问题不存在', status_code=status.HTTP_404_NOT_FOUND)
    # 登录校验
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error
    # 权限校验
    if not can_manage_project_safety(report.ID_Project, person):
        return permission_denied('只有管理员、当前项目经理或当前项目安全人员可以操作')
    try:
        create_audit_log(
            request=request,
            action='delete',
            module='安全监测',
            target_id=report.pk,
            target_name=report.ID_Project.NAME_Project,
            description=f'删除安全问题：工程名称：{report.NAME_Project}，检查部位及编号：{report.PART_Check}，报告编号：{report.NUM_Report}，总体情况：{report.STATUS_Overall}',
        )
        report.delete()
        return success_response(
            data=None,
            message='现存安全问题删除成功',
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# REST 已处理安全问题列表接口
@api_view(['GET'])
def rest_safety_resolved_issues(request, project_id):
    try:
        reports = SecurityInspectionReport.objects.filter(
            ID_Project=project_id,
            solutions__isnull=False,
        ).distinct().order_by('-id')
        report_number = request.query_params.get('reportNumber') or request.query_params.get('srnumber')
        if report_number:
            reports = reports.filter(NUM_Report__icontains=report_number)
        serializer = SecurityInspectionReportSerializer(reports, many=True)
        return success_response(
            data={'resolvedReports': serializer.data},
            message='获取已处理安全问题成功',
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 处理安全问题
@api_view(['GET', 'POST'])
def rest_safety_report_solutions(request, report_id):
    if request.method == 'GET':
        try:
            solutions = SafetyIssueSolution.objects.filter(ID_Report=report_id)
            if not solutions.exists():
                return error_response(
                    message='未找到安全问题处理记录',
                    status_code=status.HTTP_404_NOT_FOUND,
                )
            serializer = SafetyIssueSolutionSerializer(solutions, many=True)
            return success_response(
                data={'solutions': serializer.data},
                message='获取安全问题处理记录成功',
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    solution_date = request.data.get('res_Date') or request.data.get('date')
    solution_description = request.data.get('resolution') or request.data.get('description')
    if not report_id or not solution_date or not solution_description:
        return error_response(
            message='请填写完整的处理信息',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        report = SecurityInspectionReport.objects.get(id=report_id)
        # 登录校验
        person, auth_error = get_authenticated_person(request)
        if auth_error:
            return auth_error
        # 权限校验
        if not can_manage_project_safety(report.ID_Project, person):
            return permission_denied('只有管理员、当前项目经理或当前项目安全人员可以操作')
        SafetyIssueSolution.objects.create(
            ID_Report=report,
            DATE_Solution=solution_date,
            DESCRIPTION_Solution=solution_description,
        )
        report.STATUS_Overall = '已处理'
        report.save()
        create_audit_log(
            request=request,
            action='update',
            module='安全监测',
            target_id=report.pk,
            target_name=report.ID_Project.NAME_Project,
            description=f'处理安全问题：工程名称：{report.NAME_Project}，检查部位及编号：{report.PART_Check}，报告编号：{report.NUM_Report}，总体情况：{report.STATUS_Overall}',
        )
        return success_response(
            data=None,
            message='安全问题处理成功',
            status_code=status.HTTP_201_CREATED,
        )
    except SecurityInspectionReport.DoesNotExist:
        return error_response(message='安全报告不存在', status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
