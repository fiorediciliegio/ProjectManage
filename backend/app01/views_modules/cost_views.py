from app01.views_modules.common import *
from app01.views_modules.common import _project_person_exists


@api_view(['GET'])
def project_cost_summary(request, project_id):
    try:
        Project.objects.get(id=project_id)
        cost_items = CostInformation.objects.filter(ID_Project_id=project_id)
        expense_types = ['材料费用', '设备费用', '人工费用', '管理费用', '规费税金', '其他费用']

        result = {
            'TotalBudget': 0,
            'TotalCost': 0,
            'detail': {},
        }
        for expense_type in expense_types:
            result['detail'][expense_type] = {
                'totalbudget': 0,
                'totalcost': 0,
            }

        for expense_type in expense_types:
            budget_summary = cost_items.filter(TYPE_Expense=expense_type).aggregate(
                total_budget_amount=Sum('BUDGET_Amount')
            )
            cost_summary = cost_items.filter(TYPE_Expense=expense_type).aggregate(
                total_cost_amount=Sum('COST_Amount')
            )

            result['detail'][expense_type]['totalbudget'] = budget_summary['total_budget_amount'] or 0
            result['detail'][expense_type]['totalcost'] = cost_summary['total_cost_amount'] or 0
            result['TotalBudget'] += result['detail'][expense_type]['totalbudget']
            result['TotalCost'] += result['detail'][expense_type]['totalcost']

        return success_response(
            data={'summary': result},
            message='获取成本汇总成功',
            status_code=status.HTTP_200_OK,
        )
    except Project.DoesNotExist:
        return error_response(
            message='项目不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

# 按月统计实际成本
@api_view(['GET'])
def project_monthly_cost_summary(request, project_id):
    try:
        Project.objects.get(id=project_id)
        cost_items = CostInformation.objects.filter(ID_Project_id=project_id)
        expense_types = ['材料费用', '设备费用', '人工费用', '管理费用', '规费税金', '其他费用']
        monthly_costs = {}

        for expense_type in expense_types:
            monthly_data = (
                cost_items.filter(TYPE_Expense=expense_type)
                .annotate(month=TruncMonth('DATE_Cost'))
                .values('month')
                .annotate(total_cost_amount=Sum('COST_Amount'))
                .values('month', 'total_cost_amount')
            )

            for item in monthly_data:
                month = item['month'].strftime('%Y-%m')
                if month not in monthly_costs:
                    monthly_costs[month] = {et: 0 for et in expense_types}
                monthly_costs[month][expense_type] = item['total_cost_amount'] or 0

        result = [
            {
                'month': month,
                'material': costs['材料费用'],
                'equipment': costs['设备费用'],
                'labour': costs['人工费用'],
                'manage': costs['管理费用'],
                'tax': costs['规费税金'],
                'other': costs['其他费用'],
            }
            for month, costs in monthly_costs.items()
        ]

        return success_response(
            data={'monthlyCosts': result},
            message='获取月度成本统计成功',
            status_code=status.HTTP_200_OK,
        )
    except Project.DoesNotExist:
        return error_response(
            message='项目不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

# REST 成本模块：项目成本单列表与新增接口
@api_view(['GET', 'POST'])
def rest_project_costs(request, project_id):
    if request.method == 'GET':
        try:
            cache_key = build_project_cache_key(
                request,
                'project-costs',
                project_id,
                *pagination_cache_parts(request),
            )

            def produce_project_costs():
                project = Project.objects.get(id=project_id)
                costs = CostInformation.objects.filter(ID_Project=project).order_by('id')
                page_costs, pagination = paginate_queryset(costs, request)
                serializer = CostInformationSerializer(page_costs, many=True)
                return {
                    'costs': list(serializer.data),
                    'pagination': pagination,
                }

            return cached_success_response(
                request=request,
                cache_key=cache_key,
                producer=produce_project_costs,
                message='获取成本单列表成功',
                timeout=get_api_cache_timeout('API_CACHE_TTL_PROJECT_COSTS', 30),
                status_code=status.HTTP_200_OK,
            )
        except Project.DoesNotExist:
            return error_response(
                message='项目不存在',
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return error_response(
            message='项目不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )
    # 登录校验
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error
    # 权限校验
    if not can_manage_project_cost(project, person):
        return permission_denied('只有管理员、当前项目经理或当前项目财务人员可以操作成本单')

    data = request.data
    expense_type = data.get('expenseType')
    accountant = data.get('accountant')
    description = data.get('description')

    if expense_type == '其他费用' and not str(description or '').strip():
        return error_response(
            message='费用类型为其他费用时，描述为必填项',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if not _project_person_exists(project_id, accountant, '预算员'):
        return error_response(
            message='财务人员必须从当前项目已添加的预算员中选择',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    serializer = CostInformationSerializer(data=data)
    if serializer.is_valid():
        cost = serializer.save(ID_Project=project)
        create_audit_log(
            request=request,
            action='create',
            module='成本控制',
            target_id=cost.id,
            target_name=project.NAME_Project,
            description=f'创建成本单：{cost.NAME_Cost}，费用类型：{cost.TYPE_Expense}，预算金额：{cost.BUDGET_Amount} {cost.UNIT_Currency}，执行金额：{cost.COST_Amount or "0"}{cost.UNIT_Currency}',
        )
        invalidate_project_cache(project.id)
        return success_response(
            data={'cost': CostInformationSerializer(cost).data},
            message='成本单创建成功',
            status_code=status.HTTP_201_CREATED,
        )
    return error_response(
        message='成本单创建失败',
        data=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST,
    )

# REST 成本模块：成本单删除接口
@api_view(['PATCH', 'DELETE'])
def rest_cost_detail(request, cost_id):
    try:
        cost = CostInformation.objects.get(id=cost_id)
    except CostInformation.DoesNotExist:
        return error_response(
            message='成本单不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )
    # 登录校验
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error
    # 权限校验
    project = cost.ID_Project
    if not can_manage_project_cost(project, person):
        return permission_denied('只有管理员、当前项目经理或当前项目财务人员可以操作成本单')
    if request.method == 'PATCH':
        data = request.data
        expense_type = data.get('expenseType', cost.TYPE_Expense)
        accountant = data.get('accountant', cost.NAME_Accountant)
        description = data.get('description', cost.DESC_Cost)

        if expense_type == '其他费用' and not str(description or '').strip():
            return error_response(
                message='费用类型为其他费用时，描述为必填项',
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if accountant and not _project_person_exists(project.id, accountant, '预算员'):
            return error_response(
                message='财务人员必须从当前项目已添加的预算员中选择',
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CostInformationSerializer(cost, data=data, partial=True)
        if serializer.is_valid():
            updated_cost = serializer.save()
            create_audit_log(
                request=request,
                action='update',
                module='成本控制',
                target_id=updated_cost.id,
                target_name=project.NAME_Project,
                description=f'修改成本单：{updated_cost.NAME_Cost}，费用类型：{updated_cost.TYPE_Expense}，预算金额：{updated_cost.BUDGET_Amount} {updated_cost.UNIT_Currency}，执行金额：{updated_cost.COST_Amount or "0"}{updated_cost.UNIT_Currency}',
            )
            invalidate_project_cache(project.id)
            return success_response(
                data={'cost': CostInformationSerializer(updated_cost).data},
                message='成本单修改成功',
                status_code=status.HTTP_200_OK,
            )
        return error_response(
            message='成本单修改失败',
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        create_audit_log(
            request=request,
            action='delete',
            module='成本控制',
            target_id=cost.pk,
            target_name=project.NAME_Project,
            description=f'删除成本单：{cost.NAME_Cost}，费用类型：{cost.TYPE_Expense}，预算金额：{cost.BUDGET_Amount} {cost.UNIT_Currency}，执行金额：{cost.COST_Amount or "0"}{cost.UNIT_Currency}',
        )
        cost.delete()
        invalidate_project_cache(project.id)
        return success_response(
            data=None,
            message='成本单删除成功',
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
