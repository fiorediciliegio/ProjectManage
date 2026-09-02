from app01.views_modules.common import *


@api_view(['GET'])
def person_collect(request, project_id=None):
    try:
        positions = [
            '项目经理', '生产经理', '技术总工', '安全经理', '商务经理',
            '材料主管', '资料主管', '综合办主任', '工程师', '技术员',
            '质量员', '预算员', '安全员', '资料员', '施工员'
        ]
        count_data = {position: 0 for position in positions}

        if project_id:
            project = Project.objects.get(id=project_id)
            persons = project.ID_Person.filter(POS_Person__in=positions)
        else:
            persons = Person.objects.filter(POS_Person__in=positions)

        for person in persons:
            count_data[person.POS_Person] += 1

        return success_response(
            data={'counts': count_data},
            message='获取人员统计成功',
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

# REST 项目节点模块：按项目获取节点列表

@api_view(['GET', 'POST', 'DELETE'])
def rest_persons(request, person_id=None):
    if request.method == 'GET':
        try:
            if person_id is not None:
                person = Person.objects.get(id=person_id)
                serializer = PersonSerializer(person)
                return success_response(
                    data={'person': serializer.data},
                    message='获取人员详情成功',
                    status_code=status.HTTP_200_OK,
                )

            persons = Person.objects.all().order_by('id')
            if 'page' in request.query_params or 'page_size' in request.query_params:
                page_persons, pagination = paginate_queryset(persons, request)
                serializer = PersonSerializer(page_persons, many=True)
                return success_response(
                    data={
                        'persons': list(serializer.data),
                        'pagination': pagination,
                    },
                    message='获取人员列表成功',
                    status_code=status.HTTP_200_OK,
                )

            serializer = PersonSerializer(persons, many=True)
            return success_response(
                data={'persons': list(serializer.data)},
                message='获取人员列表成功',
                status_code=status.HTTP_200_OK,
            )
        except Person.DoesNotExist:
            return error_response(
                message='人员不存在',
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if request.method == 'POST':
        # 登录校验
        person, auth_error = get_authenticated_person(request)
        if auth_error:
            return auth_error
        if not is_admin(person):
            return permission_denied('只有管理员可以添加人员')
        if person_id is not None:
            return error_response(
                message='创建人员请使用人员集合接口',
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        serializer = PersonSerializer(data=request.data)
        if serializer.is_valid():
            person = serializer.save()
            create_audit_log(
                request=request,
                action='create',
                module='人员管理',
                target_id=person.id,
                target_name=person.NAME_Person,
                description=f'新增人员：{person.NAME_Person}',
            )
            invalidate_project_cache(include_global=True)
            return success_response(
                data={'person': PersonSerializer(person).data},
                message='人员创建成功',
                status_code=status.HTTP_201_CREATED,
            )
        return error_response(
            message='人员创建失败',
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    # 登录校验
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error
    if not is_admin(person):
        return permission_denied('只有管理员可以删除人员')

    if person_id is None:
        return error_response(
            message='缺少人员ID',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        person = Person.objects.get(id=person_id)
        create_audit_log(
            request=request,
            action='delete',
            module='人员管理',
            target_id=person.id,
            target_name=person.NAME_Person,
            description=f'删除人员：{person.NAME_Person}',
        )
        person.delete()
        invalidate_project_cache(include_global=True)
        return success_response(
            data=None,
            message='人员删除成功',
            status_code=status.HTTP_200_OK,
        )
    except Person.DoesNotExist:
        return error_response(
            message='人员不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# REST 项目人员模块：项目人员列表与添加接口
@api_view(['GET', 'POST'])
def rest_project_persons(request, project_id):
    if request.method == 'GET':
        try:
            cache_key = build_project_cache_key(
                request,
                'project-persons',
                project_id,
                *pagination_cache_parts(request),
            )

            def produce_project_persons():
                project = Project.objects.get(id=project_id)
                persons = project.ID_Person.all().order_by('id')
                page_persons, pagination = paginate_queryset(persons, request)
                serializer = PersonSerializer(page_persons, many=True)
                return {
                    'persons': list(serializer.data),
                    'pagination': pagination,
                }

            return cached_success_response(
                request=request,
                cache_key=cache_key,
                producer=produce_project_persons,
                message='获取项目人员列表成功',
                timeout=get_api_cache_timeout('API_CACHE_TTL_PROJECT_PERSONS', 60),
                status_code=status.HTTP_200_OK,
            )
        except Project.DoesNotExist:
            return error_response(message='项目不存在', status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # 登录校验
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error
    # 权限校验
    project = Project.objects.get(id=project_id)
    if not can_manage_project(project, person):
        return permission_denied('只有管理员或当前项目经理可以操作')

    person_ids = request.data.get('person_ids', None)
    if project_id is None or person_ids is None:
        return error_response(
            message='缺少项目ID或人员ID',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    persons = Person.objects.filter(id__in=person_ids)
    project.ID_Person.add(*persons)
    # 日志
    person_names = '、'.join(f'{person.NAME_Person}(编号:{person.NUM_Person})'for person in persons)
    create_audit_log(
        request=request,
        action='create',
        module='人员管理',
        target_id=project.id,
        target_name=project.NAME_Project,
        description=f'向项目内添加人员：{person_names}',
    )
    invalidate_project_cache(project.id)
    return success_response(
        data=None,
        message='项目人员添加成功',
        status_code=status.HTTP_200_OK,
    )

# REST 项目人员模块：移除项目人员接口
@api_view(['DELETE'])
def rest_project_person_detail(request, project_id, person_id):
    # 登录校验
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error
    # 权限校验
    project = Project.objects.get(id=project_id)
    if not can_manage_project(project, person):
        return permission_denied('只有管理员或当前项目经理可以操作')
    try:
        remove_person = Person.objects.get(id=person_id)
    except Person.DoesNotExist:
        return error_response(
            message='项目人员详情不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if not project.ID_Person.filter(id=person_id).exists():
        return error_response(
            message='项目人员关系不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )
    project.ID_Person.remove(remove_person)
    create_audit_log(
        request=request,
        action='delete',
        module='人员管理',
        target_id=project.id,
        target_name=project.NAME_Project,
        description=f'从项目内移除人员：{remove_person.NAME_Person}(编号:{remove_person.NUM_Person})',
    )
    invalidate_project_cache(project.id)
    return success_response(
        data=None,
        message='项目人员移除成功',
        status_code=status.HTTP_200_OK,
    )

# ———————————————————— 成本控制 ————————————————————
# 统计预算与执行成本
