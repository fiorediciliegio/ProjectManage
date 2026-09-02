from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from celery import current_app
from rest_framework.decorators import api_view
from rest_framework import status
from django.http import JsonResponse
from django.http import HttpResponse
from django.http import StreamingHttpResponse
from django.utils.encoding import smart_str
from django.utils import timezone
from app01.models import AuditLog
from app01.models import Project
from app01.models import ProjectNode
from app01.models import Person
from app01.models import File
from app01.models import QualityInspectionTemplate
from app01.models import QualityInspectionReport
from app01.models import InspectionItem
from app01.models import InspectionResult
from app01.models import SecurityCheckTemplate
from app01.models import SecurityCheckItem
from app01.models import SecurityInspectionReport
from app01.models import SecurityCheckResult
from app01.models import SecurityInspectionImage
from app01.models import SafetyIssueSolution
from app01.models import CostInformation
from app01.models import RagChatSession
from app01.models import RagChatMessage
from app01.serializers import (
    ProjectSerializer,
    PersonSerializer,
    FileSerializer,
    RagChatSessionSerializer,
    RagChatMessageSerializer,
    CostInformationSerializer,
    QualityInspectionTemplateSerializer,
    QualityInspectionReportSerializer,
    SecurityCheckTemplateSerializer,
    SecurityInspectionReportSerializer,
    SafetyIssueSolutionSerializer,
)
from app01.response import success_response, error_response
from django.db import transaction
from django.db.models.functions import ExtractQuarter
import os
import json
import datetime
from django.db.models import Count
import mimetypes
from docx import Document
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from html import escape
from openpyxl import load_workbook
from app01.services.elasticsearch_service import search_audit_logs, delete_file_chunks_from_elasticsearch
from app01.services.langchain_rag_service import (
    answer_question_with_rag,
    delete_langchain_file_vectors,
    summarize_chat_history_for_memory,
)
from app01.tasks import (
    rag_delete_file_vectors_task,
    rag_finalize_file_index_cancel_task,
    rag_index_file_task,
)
from app01.services.cache_service import (
    build_project_cache_key,
    cached_success_response,
    get_api_cache_timeout,
    invalidate_project_cache,
)
from app01.services.pagination import paginate_queryset, pagination_cache_parts
from app01.services.rag_resilience_service import (
    check_rag_chat_admission,
    release_rag_chat_admission,
)


ACTIVE_RAG_TASK_STATUSES = {'queued', 'running', 'retrying', 'cancelling', 'deleting'}
CANCELLABLE_RAG_TASK_STATUSES = {'queued', 'running', 'retrying'}

# ———————————————————— 登录 ————————————————————
# 登录
@api_view(['POST'])
def login_view(request):
    try:
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return error_response(
                message='用户名和密码不能为空',
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        user = authenticate(request, username=username, password=password)
        if user is None:
            return error_response(
                message='用户名或密码错误',
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if not user.is_active:
            return error_response(
                message='账号已被禁用',
                status_code=status.HTTP_403_FORBIDDEN,
            )
        login(request, user)
        create_audit_log(
            request=request,
            action='login',
            module='用户',
            target_id=user.pk,
            target_name=username,
            description='登录'
        )
        try:
            person = user.person_profile
            person_data = {
                'person_id': person.id,
                'person_name': person.NAME_Person,
                'person_role': person.POS_Person,
                'sys_role': person.sys_role,
            }
        except Person.DoesNotExist:
            person_data = {
                'person_id': None,
                'person_name': None,
                'person_role': None,
                'sys_role': None,
            }
        return success_response(
            data={
                'username': user.username,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                **person_data,
            },
            message='登录成功',
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

# 获取当前登录用户信息
@api_view(['GET'])
def current_user_view(request):
    if not request.user.is_authenticated:
        return error_response(
            message='当前未登录',
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    user = request.user
    try:
        person = user.person_profile
        person_data = {
            'person_id': person.id,
            'person_name': person.NAME_Person,
            'person_role': person.POS_Person,
            'sys_role': person.sys_role,
        }
    except Person.DoesNotExist:
        person_data = {
            'person_id': None,
            'person_name': None,
            'person_role': None,
            'sys_role': None,
        }
    return success_response(
        data={
            'username': user.username,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            **person_data,
        },
        message='获取当前用户信息成功',
        status_code=status.HTTP_200_OK,
    )

# 退出登录
@api_view(['POST'])
def logout_view(request):
    user = request.user
    create_audit_log(
        request=request,
        action='logout',
        module='用户',
        target_id=user.id,
        target_name=user.username,
        description='退出登录',
    )
    logout(request)
    return success_response(
        data=None,
        message='退出登录成功',
        status_code=status.HTTP_200_OK,
    )

# 检验登录状态
def get_authenticated_person(request):
    if not request.user.is_authenticated:
        return None, error_response(
            message='请先登录',
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        person = request.user.person_profile
        return person, None
    except Person.DoesNotExist:
        return None, error_response(
            message='当前账号未绑定人员信息',
            status_code=status.HTTP_403_FORBIDDEN,
        )

# 检验账号权限
def is_admin(person):
    return person.sys_role == 'admin'

def is_project_manager(person):
    return person.sys_role == 'project_manager'

def is_admin_or_project_manager(person):
    return person.sys_role in ['admin', 'project_manager']

def permission_denied(message='无权限操作'):
    return error_response(
        message=message,
        status_code=status.HTTP_403_FORBIDDEN,
    )

def is_project_member(project, person):
    return project.ID_Person.filter(id=person.id).exists()

def is_project_manager_of(project, person):
    return (
        person.sys_role == 'project_manager'
        and person.POS_Person == '项目经理'
        and is_project_member(project, person)
    )

def is_project_budgeter_of(project, person):
    return (
        person.POS_Person in ['预算员', '商务经理']
        and is_project_member(project, person)
    )

def is_project_quality_officer_of(project, person):
    return (
        person.POS_Person == '质量员'
        and is_project_member(project, person)
    )

def is_project_safety_officer_of(project, person):
    return (
        person.POS_Person in ['安全员', '安全经理']
        and is_project_member(project, person)
    )

def is_project_file_manager_of(project, person):
    return (
        person.POS_Person in ['资料员', '资料主管']
        and is_project_member(project, person)
    )

def can_manage_project(project, person):
    return is_admin(person) or is_project_manager_of(project, person)

def can_manage_project_cost(project, person):
    return (
        is_admin(person)
        or is_project_manager_of(project, person)
        or is_project_budgeter_of(project, person)
    )

def can_manage_project_quality(project, person):
    return (
        is_admin(person)
        or is_project_manager_of(project, person)
        or is_project_quality_officer_of(project, person)
    )

def can_manage_project_safety(project, person):
    return (
        is_admin(person)
        or is_project_manager_of(project, person)
        or is_project_safety_officer_of(project, person)
    )

def can_manage_project_file(project, person):
    return (
        is_admin(person)
        or is_project_manager_of(project, person)
        or is_project_file_manager_of(project, person)
    )

@ensure_csrf_cookie
@api_view(['GET'])
def csrf_token_view(request):
    return success_response(
        data=None,
        message='CSRF cookie 设置成功',
        status_code=status.HTTP_200_OK,
    )

# ———————————————————— 日志 ————————————————————
# 创建日志
def create_audit_log(request, action, module, target_id=None, target_name='', description=''):
    user = request.user if request.user.is_authenticated else None
    person = getattr(user, 'person_profile', None) if user else None
    log = AuditLog.objects.create(
        user=user,
        person=person,
        action=action,
        module=module,
        target_id=target_id,
        target_name=target_name,
        description=description,
    )
    try:
        from app01.services.elasticsearch_service import index_audit_log
        index_audit_log(log)
    except Exception as e:
        print(f'操作日志写入 Elasticsearch 失败：{e}')
    return log

# ES 查看并操作日志
@api_view(['GET'])
def rest_audit_logs_search(request):
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error

    if not is_admin(person):
        return permission_denied('只有管理员可以查看操作日志')

    keyword = request.GET.get('keyword', '').strip()
    module = request.GET.get('module', '').strip()
    action = request.GET.get('action', '').strip()
    date = request.GET.get('date', '').strip()

    try:
        logs = search_audit_logs(
            keyword=keyword,
            module=module,
            action=action,
            date=date,
            size=100,
        )
        return success_response(
            data={'logs': logs},
            message='获取操作日志成功',
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

# ———————————————————— 项目与人员 ————————————————————
# REST 项目模块：项目列表、详情、新增与删除接口

def _project_person_exists(project_id, person_name, role):
    if not person_name:
        return False
    return Project.objects.filter(
        id=project_id,
        ID_Person__NAME_Person=person_name,
        ID_Person__POS_Person=role,
    ).exists()

# 统计各职位人员数量
