from app01.views_modules.common import *


@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
def rest_projects(request, project_id=None):
    if request.method == 'GET':
        try:
            if project_id is not None:
                cache_key = build_project_cache_key(request, 'project-detail', project_id)

                def produce_project_detail():
                    project = Project.objects.get(id=project_id)
                    serializer = ProjectSerializer(project)
                    return {'project': dict(serializer.data)}

                return cached_success_response(
                    request=request,
                    cache_key=cache_key,
                    producer=produce_project_detail,
                    message='获取项目详情成功',
                    timeout=get_api_cache_timeout('API_CACHE_TTL_PROJECT_DETAIL', 60),
                    status_code=status.HTTP_200_OK,
                )

            cache_key = build_project_cache_key(
                request,
                'project-list',
                None,
                *pagination_cache_parts(request),
            )

            def produce_project_list():
                projects = Project.objects.all().order_by('id')
                page_projects, pagination = paginate_queryset(projects, request)
                serializer = ProjectSerializer(page_projects, many=True)
                return {
                    'projects': list(serializer.data),
                    'pagination': pagination,
                }

            return cached_success_response(
                request=request,
                cache_key=cache_key,
                producer=produce_project_list,
                message='获取项目列表成功',
                timeout=get_api_cache_timeout('API_CACHE_TTL_PROJECT_LIST', 60),
                status_code=status.HTTP_200_OK,
            )
        except Project.DoesNotExist:
            return error_response(
                message='项目不存在',
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
            return permission_denied('只有管理员可以创建项目')

        if project_id is not None:
            return error_response(
                message='创建项目请使用项目集合接口',
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        project_manager_id = request.data.get('pjmanager_id')
        if not project_manager_id:
            return error_response(
                message='请选择项目负责人',
                data={'pjmanager_id': '请选择项目负责人'},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            project_manager = Person.objects.get(id=project_manager_id, POS_Person='项目经理')
        except Person.DoesNotExist:
            return error_response(
                message='项目负责人必须从项目经理中选择',
                data={'pjmanager_id': '项目负责人必须从项目经理中选择'},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        project_data = request.data.copy()
        project_data['pjmanager'] = project_manager.NAME_Person
        project_data.pop('pjmanager_id', None)

        serializer = ProjectSerializer(data=project_data)
        if serializer.is_valid():
            project = serializer.save()
            # 创建日志
            create_audit_log(
                request=request,
                action='create',
                module='项目管理',
                target_id=project.id,
                target_name=project.NAME_Project,
                description=f'创建项目：{project.NAME_Project}',
            )
            project.ID_Person.add(project_manager)
            invalidate_project_cache(project.id, include_global=True)
            return success_response(
                data={'project': ProjectSerializer(project).data},
                message='项目创建成功',
                status_code=status.HTTP_201_CREATED,
            )
        return error_response(
            message='项目创建失败',
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if request.method == 'PATCH':
        if project_id is None:
            return error_response(
                message='缺少项目ID',
                status_code=status.HTTP_400_BAD_REQUEST,
            )
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
        if not can_manage_project(project, person):
            return permission_denied('只有管理员或当前项目经理可以修改项目详情')

        project_data = request.data.copy()
        project_manager_id = project_data.get('pjmanager_id')
        if project_manager_id:
            try:
                project_manager = Person.objects.get(id=project_manager_id, POS_Person='项目经理')
            except Person.DoesNotExist:
                return error_response(
                    message='项目负责人必须从项目经理中选择',
                    data={'pjmanager_id': '项目负责人必须从项目经理中选择'},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            project_data['pjmanager'] = project_manager.NAME_Person
            project_data.pop('pjmanager_id', None)
        else:
            project_manager = None

        serializer = ProjectSerializer(project, data=project_data, partial=True)
        if serializer.is_valid():
            project = serializer.save()
            # 创建日志
            create_audit_log(
                request=request,
                action='update',
                module='项目管理',
                target_id=project.id,
                target_name=project.NAME_Project,
                description=f'修改项目详情：{project.NAME_Project}',
            )
            if project_manager is not None:
                project.ID_Person.add(project_manager)
            invalidate_project_cache(project.id, include_global=True)
            return success_response(
                data={'project': ProjectSerializer(project).data},
                message='项目详情修改成功',
                status_code=status.HTTP_200_OK,
            )
        return error_response(
            message='项目详情修改失败',
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    # 登录校验
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error
    if not is_admin(person):
        return permission_denied('只有管理员可以删除项目')

    if project_id is None:
        return error_response(
            message='缺少项目ID',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        project = Project.objects.get(id=project_id)
        deleted_project_id = project.id
        project_name = project.NAME_Project
        project.delete()
        create_audit_log(
            request=request,
            action='delete',
            module='项目管理',
            target_id=project.id,
            target_name=project_name,
            description=f'删除项目：{project_name}',
        )
        invalidate_project_cache(deleted_project_id, include_global=True)
        return success_response(
            data=None,
            message='项目删除成功',
            status_code=status.HTTP_200_OK,
        )
    except Project.DoesNotExist:
        return error_response(
            message='项目不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 序列化项目节点，统一返回给前端的字段结构
def _serialize_project_node(project_node):
    return {
        'pjn_id': project_node.id,
        'pjn_name': project_node.NAME_Milestone,
        'pjn_ddl': str(project_node.DDL_Milestone),
        'pjn_des': project_node.DES_Milestone,
        'pjn_status': project_node.PHEN_Milestone,
    }

# 统计项目节点状态
@api_view(['GET'])
def projectnode_collect(request, project_id=None):
    try:
        if project_id is None:
            return error_response(
                message='缺少项目ID',
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        summary = {
            'completed_count': ProjectNode.objects.filter(ID_Project=project_id, PHEN_Milestone='已完成').count(),
            'in_progress_count': ProjectNode.objects.filter(ID_Project=project_id, PHEN_Milestone='进行中').count(),
            'pending_count': ProjectNode.objects.filter(ID_Project=project_id, PHEN_Milestone='未处理').count(),
        }
        return success_response(
            data={'summary': summary},
            message='获取项目节点统计成功',
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

# 判断某个项目中是否存在指定职位的人员

@api_view(['GET'])
def rest_project_nodes_by_project(request, project_id):
    try:
        cache_key = build_project_cache_key(
            request,
            'project-nodes',
            project_id,
            *pagination_cache_parts(request),
        )

        def produce_project_nodes():
            projectnodes = ProjectNode.objects.filter(ID_Project=project_id).order_by('id')
            page_projectnodes, pagination = paginate_queryset(projectnodes, request)
            return {
                'project_nodes': [
                    _serialize_project_node(projectnode)
                    for projectnode in page_projectnodes
                ],
                'pagination': pagination,
            }

        return cached_success_response(
            request=request,
            cache_key=cache_key,
            producer=produce_project_nodes,
            message='获取项目节点列表成功',
            timeout=get_api_cache_timeout('API_CACHE_TTL_PROJECT_NODES', 30),
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# REST 项目节点模块：新增、删除和更新节点状态接口
@api_view(['POST', 'DELETE', 'PATCH', 'PUT'])
def rest_project_nodes(request, node_id=None):
    if request.method == 'POST':
        try:
            name_projectnode = request.data.get('pjn_name')
            ddl_projectnode_str = request.data.get('pjn_ddl')
            des_projectnode = request.data.get('pjn_des')
            phen_projectnode = request.data.get('pjn_status')
            id_project = request.data.get('pj_id')
            if not ddl_projectnode_str:
                return error_response(
                    message='节点日期不能为空',
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            ddl_projectnode = datetime.datetime.strptime(ddl_projectnode_str, '%Y-%m-%d').date()
            project_instance = Project.objects.get(id=id_project)
            # 登录校验
            person, auth_error = get_authenticated_person(request)
            if auth_error:
                return auth_error
            # 权限校验
            if not can_manage_project(project_instance, person):
                return permission_denied('只有管理员或当前项目经理可以操作')

            project_node = ProjectNode.objects.create(
                NAME_Milestone=name_projectnode,
                DDL_Milestone=ddl_projectnode,
                DES_Milestone=des_projectnode,
                PHEN_Milestone=phen_projectnode,
                ID_Project=project_instance,
            )
            # 创建日志
            create_audit_log(
                request=request,
                action='create',
                module='项目节点',
                target_id=project_instance.id,
                target_name=project_instance.NAME_Project,
                description=f'创建项目节点：{name_projectnode}',
            )
            invalidate_project_cache(project_instance.id)
            return success_response(
                data={'project_node': _serialize_project_node(project_node)},
                message='项目节点创建成功',
                status_code=status.HTTP_201_CREATED,
            )
        except Project.DoesNotExist:
            return error_response(
                message='项目不存在',
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if node_id is None:
        return error_response(
            message='缺少项目节点ID',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        project_node = ProjectNode.objects.get(id=node_id)
    except ProjectNode.DoesNotExist:
        return error_response(
            message='项目节点不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'DELETE':
        person, auth_error = get_authenticated_person(request)
        if auth_error:
            return auth_error
        # 权限校验
        project = project_node.ID_Project
        if not can_manage_project(project, person):
            return permission_denied('只有管理员或当前项目经理可以操作')
        create_audit_log(
            request=request,
            action='delete',
            module='项目节点',
            target_id=project.id,
            target_name=project.NAME_Project,
            description=f'删除节点：{project_node.NAME_Milestone}',
        )
        project_node.delete()
        invalidate_project_cache(project.id)
        return success_response(
            data=None,
            message='项目节点删除成功',
            status_code=status.HTTP_200_OK,
        )
    # 登录校验
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error
    # 权限校验
    project = project_node.ID_Project
    if not can_manage_project(project, person):
        return permission_denied('只有管理员或当前项目经理可以操作')

    new_status = request.data.get('pjn_status') or request.data.get('new_pjn_status')
    if not new_status:
        return error_response(
            message='节点状态不能为空',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    project_node.PHEN_Milestone = new_status
    project_node.save()
    create_audit_log(
        request=request,
        action='update',
        module='项目节点',
        target_id=project.id,
        target_name=project.NAME_Project,
        description=f'节点状态更新：{project_node.NAME_Milestone}',
    )
    invalidate_project_cache(project.id)
    return success_response(
        data={'project_node': _serialize_project_node(project_node)},
        message='项目节点状态更新成功',
        status_code=status.HTTP_200_OK,
    )

# REST 人员模块：人员列表、详情、新增与删除接口
