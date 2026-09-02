from app01.views_modules.common import *
from app01.views_modules.common import _project_person_exists


# ———————————————————— 质量监测 ————————————————————
# REST 质量模板模块：模板列表与新增接口
@api_view(['GET', 'POST'])
def rest_quality_templates(request, project_id):
    if request.method == 'GET':
        try:
            templates = QualityInspectionTemplate.objects.filter(ID_Project=project_id)
            serializer = QualityInspectionTemplateSerializer(templates, many=True)
            return success_response(
                data={'qitTemplates': serializer.data},
                message='获取质检模板列表成功',
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error
    qit_name = request.data.get('qtname')
    items_data = request.data.get('subitems')
    if not project_id or not qit_name or not items_data:
        return error_response(
            message='缺少项目ID、模板名称或检查项',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        project = Project.objects.get(id=project_id)
        # 权限校验
        if not can_manage_project_cost(project, person):
            return permission_denied('只有管理员、当前项目经理和当前项目质量员能新建模板')
        qit = QualityInspectionTemplate.objects.create(NAME_Qit=qit_name, ID_Project=project)
        for item_data in items_data:
            InspectionItem.objects.create(
                NAME_Item=item_data.get('name'),
                VALUE_Item=item_data.get('requirement'),
                ID_Qit=qit,
            )
        serializer = QualityInspectionTemplateSerializer(qit)
        create_audit_log(
            request=request,
            action='create',
            module='质量监测',
            target_id=qit.pk,
            target_name=project.NAME_Project,
            description=f'新建模板：{qit.NAME_Qit}',
        )
        return success_response(
            data={'template': serializer.data},
            message='质检模板创建成功',
            status_code=status.HTTP_201_CREATED,
        )
    except Project.DoesNotExist:
        return error_response(message='项目不存在', status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# REST 质量模板模块：模板删除接口
@api_view(['DELETE'])
def rest_quality_template_detail(request, template_id):
    try:
        person, auth_error = get_authenticated_person(request)
        if auth_error:
            return auth_error
        template = QualityInspectionTemplate.objects.get(id=template_id)
        if not can_manage_project_quality(template.ID_Project, person):
            return permission_denied('只有管理员、当前项目经理和当前项目质量员能删除模板')
        create_audit_log(
            request=request,
            action='delete',
            module='质量监测',
            target_id=template.pk,
            target_name=template.ID_Project.NAME_Project,
            description=f'删除模板：{template.NAME_Qit}',
        )
        template.delete()
        return success_response(
            data=None,
            message='质检模板删除成功',
            status_code=status.HTTP_200_OK,
        )
    except QualityInspectionTemplate.DoesNotExist:
        return error_response(message='质检模板不存在', status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# REST 质量模板模块：获取模板检查项接口
@api_view(['GET'])
def rest_quality_template_items(request, template_id):
    try:
        items = InspectionItem.objects.filter(ID_Qit=template_id)
        data = [
            {'id': item.pk, 'item_name': item.NAME_Item, 'item_value': item.VALUE_Item}
            for item in items
        ]
        return success_response(
            data={'items': data},
            message='获取质检模板检查项成功',
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# REST 质量报告模块：报告列表与新增接口
@api_view(['GET', 'POST'])
def rest_quality_reports(request, project_id):
    if request.method == 'GET':
        try:
            reports = QualityInspectionReport.objects.filter(ID_Project=project_id)
            serializer = QualityInspectionReportSerializer(reports, many=True)
            return success_response(
                data={'reports': serializer.data},
                message='获取质检报告列表成功',
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    data = request.data
    try:
        project = Project.objects.get(id=project_id)
        person, auth_error = get_authenticated_person(request)
        if auth_error:
            return auth_error
        if not can_manage_project_cost(project, person):
            return permission_denied('只有管理员、当前项目经理和当前项目质量员能新建报告')
    except Project.DoesNotExist:
        return error_response(message='项目不存在', status_code=status.HTTP_404_NOT_FOUND)

    if not _project_person_exists(project_id, data.get('qrperson'), '质量员'):
        return error_response(
            message='质检员必须从当前项目中的质量员中选择',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    serializer = QualityInspectionReportSerializer(data=data)
    if not serializer.is_valid():
        return error_response(
            message='质检报告创建失败',
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        report = serializer.save(ID_Project=project)
        for result_data in data.get('qrsubitems', []):
            InspectionResult.objects.create(
                NAME_Item=result_data.get('name'),
                VALUE_Standard=result_data.get('requirement'),
                RESULT_Inspect=result_data.get('result'),
                ID_Report=report,
            )
        create_audit_log(
            request=request,
            action='create',
            module='质量监测',
            target_id=report.id,
            target_name=project.NAME_Project,
            description=f'新增质量报告：工程名称：{report.NAME_Project}，检验部位及编号：{report.PART_Num}，总体情况：{report.STATUS_Inspect}',
        )
        return success_response(
            data={'report': QualityInspectionReportSerializer(report).data},
            message='质检报告创建成功',
            status_code=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# REST 质量报告模块：报告详情、修改与删除接口
@api_view(['GET', 'PATCH', 'DELETE'])
def rest_quality_report_detail(request, report_id):
    try:
        report = QualityInspectionReport.objects.get(id=report_id)
    except QualityInspectionReport.DoesNotExist:
        return error_response(message='质量报告不存在', status_code=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        report_data = QualityInspectionReportSerializer(report).data
        report_data['qrsubitems'] = [
            {
                'name': result.NAME_Item,
                'requirement': result.VALUE_Standard,
                'result': result.RESULT_Inspect,
            }
            for result in InspectionResult.objects.filter(ID_Report=report)
        ]
        return success_response(
            data={'report': report_data},
            message='获取质量报告详情成功',
            status_code=status.HTTP_200_OK,
        )
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error

    project = report.ID_Project
    if project is None:
        return error_response(
            message='质量报告所属项目不存在',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if not can_manage_project_quality(project, person):
        action_text = '修改' if request.method == 'PATCH' else '删除'
        return permission_denied(f'只有管理员、当前项目经理或当前项目质量员可以{action_text}质量报告')

    if request.method == 'PATCH':
        data = request.data
        if not _project_person_exists(project.id, data.get('qrperson'), '质量员'):
            return error_response(
                message='质检员必须从当前项目中的质量员中选择',
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        serializer = QualityInspectionReportSerializer(report, data=data, partial=True)
        if not serializer.is_valid():
            return error_response(
                message='质量报告修改失败',
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        report = serializer.save()
        if 'qrsubitems' in data:
            InspectionResult.objects.filter(ID_Report=report).delete()
            for result_data in data.get('qrsubitems', []):
                InspectionResult.objects.create(
                    NAME_Item=result_data.get('name'),
                    VALUE_Standard=result_data.get('requirement'),
                    RESULT_Inspect=result_data.get('result'),
                    ID_Report=report,
                )
        create_audit_log(
            request=request,
            action='update',
            module='质量监测',
            target_id=report.id,
            target_name=project.NAME_Project,
            description=f'修改质量报告：工程名称：{report.NAME_Project}，检验部位及编号：{report.PART_Num}，总体情况：{report.STATUS_Inspect}',
        )
        return success_response(
            data={'report': QualityInspectionReportSerializer(report).data},
            message='质量报告修改成功',
            status_code=status.HTTP_200_OK,
        )
    create_audit_log(
        request=request,
        action='delete',
        module='质量监测',
        target_id=report.pk,
        target_name=project.NAME_Project,
        description=f'删除质量报告：工程名称：{report.NAME_Project}，检验部位及编号：{report.PART_Num}，总体情况：{report.STATUS_Inspect}',
    )
    report.delete()
    return success_response(
        data=None,
        message='质量报告删除成功',
        status_code=status.HTTP_200_OK,
    )

# 质量监测统计图
@api_view(['GET'])
def rest_quality_stats(request, project_id):
    try:
        stats = {
            '合格': [0, 0, 0, 0],
            '一般质量问题': [0, 0, 0, 0],
            '重大质量问题': [0, 0, 0, 0],
        }
        report_stats = (
            QualityInspectionReport.objects.filter(ID_Project=project_id)
            .annotate(quarter=ExtractQuarter('TIME_Inspect'))
            .values('STATUS_Inspect', 'quarter')
            .annotate(count=Count('STATUS_Inspect'))
        )
        for stat in report_stats:
            status_value = stat['STATUS_Inspect']
            quarter = stat['quarter']
            count = stat['count']
            if status_value in stats and quarter:
                stats[status_value][quarter - 1] = count
        return success_response(
            data={'stats': stats},
            message='获取质量问题统计成功',
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
