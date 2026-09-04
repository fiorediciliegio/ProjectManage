from app01.views_modules.common import *


def serialize_file_index_status(file_obj):
    return {
        'file_id': file_obj.pk,
        'index_status': file_obj.INDEX_STATUS_File,
        'index_task_id': file_obj.INDEX_TASK_ID_File,
        'index_stage': file_obj.INDEX_STAGE_File,
        'index_stage_label': file_obj.get_INDEX_STAGE_File_display(),
        'index_error': file_obj.INDEX_ERROR_File,
        'index_error_type': file_obj.INDEX_ERROR_TYPE_File,
        'index_error_detail': file_obj.INDEX_ERROR_DETAIL_File,
        'index_retry_count': file_obj.INDEX_RETRY_COUNT_File,
        'index_max_retries': file_obj.INDEX_MAX_RETRIES_File,
        'index_next_retry_at': file_obj.INDEX_NEXT_RETRY_AT_File.strftime('%Y-%m-%d %H:%M:%S') if file_obj.INDEX_NEXT_RETRY_AT_File else None,
        'index_retryable': file_obj.INDEX_RETRYABLE_File,
        'index_cancel_requested': file_obj.INDEX_CANCEL_REQUESTED_File,
        'index_cancelled_at': file_obj.INDEX_CANCELLED_AT_File.strftime('%Y-%m-%d %H:%M:%S') if file_obj.INDEX_CANCELLED_AT_File else None,
        'indexed_at': file_obj.INDEXED_AT_File.strftime('%Y-%m-%d %H:%M:%S') if file_obj.INDEXED_AT_File else None,
    }


def request_rag_index_cancel(file_obj):
    with transaction.atomic():
        locked_file = File.objects.select_for_update().get(pk=file_obj.pk)
        if locked_file.INDEX_STATUS_File not in CANCELLABLE_RAG_TASK_STATUSES:
            return False, locked_file

        locked_file.INDEX_STATUS_File = 'cancelling'
        locked_file.INDEX_STAGE_File = 'cancel_requested'
        locked_file.INDEX_CANCEL_REQUESTED_File = True
        locked_file.INDEX_CANCELLED_AT_File = None
        locked_file.INDEX_NEXT_RETRY_AT_File = None
        locked_file.INDEX_RETRYABLE_File = False
        locked_file.INDEX_ERROR_File = '用户请求取消入库任务'
        locked_file.INDEX_ERROR_TYPE_File = ''
        locked_file.INDEX_ERROR_DETAIL_File = ''
        locked_file.save(update_fields=[
            'INDEX_STATUS_File',
            'INDEX_STAGE_File',
            'INDEX_CANCEL_REQUESTED_File',
            'INDEX_CANCELLED_AT_File',
            'INDEX_NEXT_RETRY_AT_File',
            'INDEX_RETRYABLE_File',
            'INDEX_ERROR_File',
            'INDEX_ERROR_TYPE_File',
            'INDEX_ERROR_DETAIL_File',
        ])

        task_id = locked_file.INDEX_TASK_ID_File

    if task_id:
        current_app.control.revoke(task_id, terminate=False)

    rag_finalize_file_index_cancel_task.apply_async(
        args=[file_obj.pk],
        countdown=5,
        queue=getattr(settings, 'CELERY_RAG_MAINTENANCE_QUEUE', 'rag_maintenance'),
    )
    return True, File.objects.get(pk=file_obj.pk)


def enqueue_rag_index_task(file_id, rebuild=False):
    with transaction.atomic():
        file_obj = File.objects.select_for_update().get(pk=file_id)
        if file_obj.INDEX_STATUS_File in ACTIVE_RAG_TASK_STATUSES:
            return None, file_obj
        file_obj.INDEX_STATUS_File = 'queued'
        file_obj.INDEX_STAGE_File = 'queued'
        file_obj.INDEX_TASK_ID_File = ''
        file_obj.INDEX_ERROR_File = ''
        file_obj.INDEX_ERROR_TYPE_File = ''
        file_obj.INDEX_ERROR_DETAIL_File = ''
        file_obj.INDEX_RETRY_COUNT_File = 0
        file_obj.INDEX_MAX_RETRIES_File = getattr(settings, 'RAG_INDEX_MAX_RETRIES', 3)
        file_obj.INDEX_NEXT_RETRY_AT_File = None
        file_obj.INDEX_RETRYABLE_File = False
        file_obj.INDEX_CANCEL_REQUESTED_File = False
        file_obj.INDEX_CANCELLED_AT_File = None
        file_obj.save(update_fields=[
            'INDEX_STATUS_File',
            'INDEX_STAGE_File',
            'INDEX_TASK_ID_File',
            'INDEX_ERROR_File',
            'INDEX_ERROR_TYPE_File',
            'INDEX_ERROR_DETAIL_File',
            'INDEX_RETRY_COUNT_File',
            'INDEX_MAX_RETRIES_File',
            'INDEX_NEXT_RETRY_AT_File',
            'INDEX_RETRYABLE_File',
            'INDEX_CANCEL_REQUESTED_File',
            'INDEX_CANCELLED_AT_File',
        ])

    task = rag_index_file_task.apply_async(
        args=[file_id],
        kwargs={'rebuild': rebuild},
        queue=getattr(settings, 'CELERY_RAG_INDEX_QUEUE', 'rag_index'),
    )
    File.objects.filter(pk=file_id).update(INDEX_TASK_ID_File=task.id)
    file_obj = File.objects.get(pk=file_id)
    return task, file_obj


def enqueue_rag_delete_vectors_task(file_id):
    with transaction.atomic():
        file_obj = File.objects.select_for_update().get(pk=file_id)
        if file_obj.INDEX_STATUS_File in ACTIVE_RAG_TASK_STATUSES:
            return None, file_obj
        file_obj.INDEX_STATUS_File = 'deleting'
        file_obj.INDEX_STAGE_File = 'delete_vectors'
        file_obj.INDEX_TASK_ID_File = ''
        file_obj.INDEX_ERROR_File = ''
        file_obj.INDEX_ERROR_TYPE_File = ''
        file_obj.INDEX_ERROR_DETAIL_File = ''
        file_obj.INDEX_RETRY_COUNT_File = 0
        file_obj.INDEX_MAX_RETRIES_File = getattr(settings, 'RAG_INDEX_MAX_RETRIES', 3)
        file_obj.INDEX_NEXT_RETRY_AT_File = None
        file_obj.INDEX_RETRYABLE_File = False
        file_obj.INDEX_CANCEL_REQUESTED_File = False
        file_obj.INDEX_CANCELLED_AT_File = None
        file_obj.save(update_fields=[
            'INDEX_STATUS_File',
            'INDEX_STAGE_File',
            'INDEX_TASK_ID_File',
            'INDEX_ERROR_File',
            'INDEX_ERROR_TYPE_File',
            'INDEX_ERROR_DETAIL_File',
            'INDEX_RETRY_COUNT_File',
            'INDEX_MAX_RETRIES_File',
            'INDEX_NEXT_RETRY_AT_File',
            'INDEX_RETRYABLE_File',
            'INDEX_CANCEL_REQUESTED_File',
            'INDEX_CANCELLED_AT_File',
        ])

    task = rag_delete_file_vectors_task.apply_async(
        args=[file_id],
        queue=getattr(settings, 'CELERY_RAG_MAINTENANCE_QUEUE', 'rag_maintenance'),
    )
    File.objects.filter(pk=file_id).update(INDEX_TASK_ID_File=task.id)
    file_obj = File.objects.get(pk=file_id)
    return task, file_obj


@api_view(['POST'])
def rag_index_file(request, file_id):
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error

    try:
        file_obj = File.objects.get(id=file_id)
    except File.DoesNotExist:
        return error_response(
            message='文件不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if not can_manage_project_file(file_obj.ID_Project, person):
        return permission_denied('只有管理员、当前项目经理或当前项目资料人员可以进行文件入库')

    try:
        task, updated_file = enqueue_rag_index_task(file_obj.pk, rebuild=False)
        if task is None:
            return error_response(
                message='文件已有索引任务正在执行，请勿重复提交',
                code=409,
                data=serialize_file_index_status(updated_file),
                status_code=status.HTTP_409_CONFLICT,
            )
        invalidate_project_cache(updated_file.ID_Project_id)
        return success_response(
             data={
                'task_id': task.id,
                'file': serialize_file_index_status(updated_file),
            },
            message='文件向量入库任务已提交',
            status_code=status.HTTP_202_ACCEPTED,
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# 文件重新入库
@api_view(['POST'])
def rag_reindex_file(request, file_id):
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error
    try:
        file_obj = File.objects.get(id=file_id)
    except File.DoesNotExist:
        return error_response(
            message='文件不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )
    project = file_obj.ID_Project
    if not can_manage_project_file(project, person):
        return permission_denied('只有管理员、当前项目经理或当前项目资料员可以重新入库文件')
    try:
        task, updated_file = enqueue_rag_index_task(file_obj.pk, rebuild=True)
        if task is None:
            return error_response(
                message='文件已有索引任务正在执行，请勿重复提交',
                code=409,
                data=serialize_file_index_status(updated_file),
                status_code=status.HTTP_409_CONFLICT,
            )
        invalidate_project_cache(updated_file.ID_Project_id)
        return success_response(
            data={
                'task_id': task.id,
                'file': serialize_file_index_status(updated_file),
            },
            message='文件重新入库任务已提交',
            status_code=status.HTTP_202_ACCEPTED,
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

# 删除文件向量
@api_view(['DELETE'])
def rag_delete_file_vectors(request, file_id):
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error

    try:
        file_obj = File.objects.get(id=file_id)
    except File.DoesNotExist:
        return error_response(
            message='文件不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )

    project = file_obj.ID_Project

    if not can_manage_project_file(project, person):
        return permission_denied('只有管理员、当前项目经理或当前项目资料员可以删除文件向量')

    try:
        task, updated_file = enqueue_rag_delete_vectors_task(file_obj.pk)
        if task is None:
            return error_response(
                message='文件已有索引任务正在执行，请勿重复提交',
                code=409,
                data=serialize_file_index_status(updated_file),
                status_code=status.HTTP_409_CONFLICT,
            )
        invalidate_project_cache(updated_file.ID_Project_id)
        return success_response(
            data={
                'task_id': task.id,
                'file': serialize_file_index_status(updated_file),
            },
            message='文件向量删除任务已提交',
            status_code=status.HTTP_202_ACCEPTED,
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
def rag_cancel_index_task(request, file_id):
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error

    try:
        file_obj = File.objects.get(id=file_id)
    except File.DoesNotExist:
        return error_response(
            message='文件不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if not can_manage_project_file(file_obj.ID_Project, person):
        return permission_denied('只有管理员、当前项目经理或当前项目资料员可以取消文件入库任务')

    try:
        cancelled, updated_file = request_rag_index_cancel(file_obj)
        if not cancelled:
            return error_response(
                message='当前文件没有可取消的入库任务',
                code=409,
                data=serialize_file_index_status(updated_file),
                status_code=status.HTTP_409_CONFLICT,
            )

        invalidate_project_cache(updated_file.ID_Project_id)
        return success_response(
            data={
                'file': serialize_file_index_status(updated_file),
            },
            message='文件入库取消请求已提交',
            status_code=status.HTTP_202_ACCEPTED,
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
def rag_file_index_status(request, file_id):
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error

    try:
        file_obj = File.objects.get(id=file_id)
    except File.DoesNotExist:
        return error_response(
            message='文件不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if not is_admin(person) and not is_project_member(file_obj.ID_Project, person):
        return permission_denied('只有当前项目成员可以查看文件入库状态')

    return success_response(
        data=serialize_file_index_status(file_obj),
        message='获取文件入库状态成功',
        status_code=status.HTTP_200_OK,
    )


def build_rag_session_title(question):
    title = str(question or '').strip().replace('\n', ' ')
    if not title:
        return '新的文档问答'
    if len(title) > 40:
        return f'{title[:40]}...'
    return title


def get_project_for_rag(request, project_id, person):
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return None, error_response(
            message='项目不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if not is_admin(person) and not is_project_member(project, person):
        return None, permission_denied('只有当前项目成员可以使用项目文档问答')

    return project, None


def get_owned_rag_session(project, person, session_id):
    return RagChatSession.objects.filter(
        id=session_id,
        project=project,
        owner=person,
    ).first()


def get_or_create_rag_session(project, person, session_id, question):
    if session_id:
        session = get_owned_rag_session(project, person, session_id)
        if session:
            return session

    now = timezone.now()
    return RagChatSession.objects.create(
        project=project,
        owner=person,
        title=build_rag_session_title(question),
        last_message_at=now,
    )


def get_rag_session_history(session):
    max_messages = max(0, int(getattr(settings, 'RAG_CHAT_HISTORY_MAX_MESSAGES', 10)))
    if max_messages <= 0:
        return []

    messages = list(
        session.messages
        .filter(role__in=['user', 'assistant'])
        .order_by('-created_at', '-id')[:max_messages]
    )
    messages.reverse()
    return [
        {
            'role': message.role,
            'content': message.content,
        }
        for message in messages
        if message.content
    ]


def rag_message_to_history_item(message):
    return {
        'role': message.role,
        'content': message.content,
    }


def get_rag_memory_context(session):
    recent_limit = max(0, int(getattr(settings, 'RAG_CHAT_RECENT_MESSAGES', 10)))
    if recent_limit <= 0:
        return session.memory_summary or '', []

    messages = list(
        session.messages
        .filter(role__in=['user', 'assistant'])
        .order_by('-created_at', '-id')[:recent_limit]
    )
    messages.reverse()
    return session.memory_summary or '', [
        rag_message_to_history_item(message)
        for message in messages
        if message.content
    ]


def maybe_update_rag_session_summary(session):
    recent_limit = max(0, int(getattr(settings, 'RAG_CHAT_RECENT_MESSAGES', 10)))
    summary_limit = max(0, int(getattr(settings, 'RAG_CHAT_SUMMARY_MAX_MESSAGES', 70)))
    trigger_messages = max(
        recent_limit,
        int(getattr(settings, 'RAG_CHAT_SUMMARY_TRIGGER_MESSAGES', 12)),
    )
    update_interval = max(1, int(getattr(settings, 'RAG_CHAT_SUMMARY_UPDATE_INTERVAL_MESSAGES', 4)))
    if summary_limit <= 0:
        return session

    message_qs = session.messages.filter(role__in=['user', 'assistant'])
    total_messages = message_qs.count()
    if total_messages <= trigger_messages:
        return session
    if session.memory_summary and total_messages - session.summarized_message_count < update_interval:
        return session

    load_limit = recent_limit + summary_limit if recent_limit > 0 else summary_limit
    messages = list(message_qs.order_by('-created_at', '-id')[:load_limit])
    messages.reverse()
    if recent_limit > 0:
        summary_messages = messages[:-recent_limit]
    else:
        summary_messages = messages
    summary_messages = summary_messages[-summary_limit:]
    if not summary_messages:
        return session

    from app01 import views as views_facade

    summary = views_facade.summarize_chat_history_for_memory([
        rag_message_to_history_item(message)
        for message in summary_messages
        if message.content
    ])
    if not summary:
        return session

    now = timezone.now()
    RagChatSession.objects.filter(pk=session.pk).update(
        memory_summary=summary,
        summarized_message_count=total_messages,
        summary_updated_at=now,
    )
    session.memory_summary = summary
    session.summarized_message_count = total_messages
    session.summary_updated_at = now
    return session


def append_rag_chat_message(session, role, content, sources=None, metadata=None):
    message = RagChatMessage.objects.create(
        session=session,
        role=role,
        content=content or '',
        sources_json=sources or [],
        metadata_json=metadata or {},
    )
    now = timezone.now()
    message_count = RagChatMessage.objects.filter(session=session).count()
    RagChatSession.objects.filter(pk=session.pk).update(
        last_message_at=now,
        message_count=message_count,
    )
    session.last_message_at = now
    session.message_count = message_count
    return message


@api_view(['GET', 'POST'])
def rag_chat_sessions(request, project_id):
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error

    project, project_error = get_project_for_rag(request, project_id, person)
    if project_error:
        return project_error

    if request.method == 'GET':
        sessions = (
            RagChatSession.objects
            .filter(project=project, owner=person)
            .order_by('-last_message_at', '-updated_at')
        )
        page_sessions, pagination = paginate_queryset(sessions, request, default_page_size=20, max_page_size=50)
        return success_response(
            data={
                'sessions': RagChatSessionSerializer(page_sessions, many=True).data,
                'pagination': pagination,
            },
            message='获取 RAG 问答会话成功',
            status_code=status.HTTP_200_OK,
        )

    title = str(request.data.get('title') or '').strip() or '新的文档问答'
    session = RagChatSession.objects.create(
        project=project,
        owner=person,
        title=title[:120],
        last_message_at=timezone.now(),
    )
    return success_response(
        data={'session': RagChatSessionSerializer(session).data},
        message='创建 RAG 问答会话成功',
        status_code=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
def rag_chat_session_messages(request, project_id, session_id):
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error

    project, project_error = get_project_for_rag(request, project_id, person)
    if project_error:
        return project_error

    session = get_owned_rag_session(project, person, session_id)
    if not session:
        return error_response(
            message='RAG 问答会话不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )

    messages = session.messages.order_by('created_at', 'id')
    return success_response(
        data={
            'session': RagChatSessionSerializer(session).data,
            'messages': RagChatMessageSerializer(messages, many=True).data,
        },
        message='获取 RAG 问答消息成功',
        status_code=status.HTTP_200_OK,
    )


@api_view(['DELETE'])
def rag_chat_session_detail(request, project_id, session_id):
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error

    project, project_error = get_project_for_rag(request, project_id, person)
    if project_error:
        return project_error

    session = get_owned_rag_session(project, person, session_id)
    if not session:
        return error_response(
            message='RAG 问答会话不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )

    session.delete()
    return success_response(
        message='删除 RAG 问答会话成功',
        status_code=status.HTTP_200_OK,
    )


# 项目问答接口
@api_view(['POST'])
def rag_chat(request, project_id):
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error

    project, project_error = get_project_for_rag(request, project_id, person)
    if project_error:
        return project_error

    question = request.data.get('question')
    client_history = request.data.get('history') or []
    session_id = request.data.get('session_id')
    if not question:
        return error_response(
            message='请输入问题',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    admission = check_rag_chat_admission(person.pk, project_id)
    if not admission.allowed:
        response = error_response(
            message=admission.message,
            code=429,
            data={
                'retry_after': admission.retry_after,
            },
            status_code=admission.status_code,
        )
        if admission.retry_after:
            response['Retry-After'] = str(admission.retry_after)
        return response

    session = get_or_create_rag_session(project, person, session_id, question)
    history_summary, history = get_rag_memory_context(session)
    history = history or client_history
    append_rag_chat_message(session, 'user', str(question).strip())

    def stream_events():
        assistant_parts = []
        assistant_sources = []
        assistant_metadata = {}
        assistant_saved = False
        try:
            yield json.dumps(
                {
                    'type': 'session',
                    'session_id': session.pk,
                    'session': RagChatSessionSerializer(session).data,
                },
                ensure_ascii=False,
            ) + '\n'
            from app01 import views as views_facade

            for event in views_facade.answer_question_with_rag(
                question=question,
                project_id=project_id,
                limit=8,
                history=history,
                history_summary=history_summary,
            ):
                if event.get('type') == 'delta':
                    assistant_parts.append(event.get('content') or '')
                if event.get('type') == 'done':
                    assistant_sources = event.get('sources') or []
                    assistant_metadata = {
                        'degraded': bool(event.get('degraded')),
                        'degrade_reason': event.get('degrade_reason') or '',
                    }
                    append_rag_chat_message(
                        session,
                        'assistant',
                        ''.join(assistant_parts) or '没有生成回答',
                        sources=assistant_sources,
                        metadata=assistant_metadata,
                    )
                    maybe_update_rag_session_summary(session)
                    assistant_saved = True
                yield json.dumps(event, ensure_ascii=False) + '\n'
        except Exception as e:
            error_message = str(e)
            append_rag_chat_message(
                session,
                'assistant',
                error_message,
                metadata={'error': True},
            )
            assistant_saved = True
            yield json.dumps(
                {
                    'type': 'error',
                    'message': error_message,
                },
                ensure_ascii=False,
            ) + '\n'
        finally:
            if not assistant_saved and assistant_parts:
                append_rag_chat_message(
                    session,
                    'assistant',
                    ''.join(assistant_parts),
                    sources=assistant_sources,
                    metadata={**assistant_metadata, 'interrupted': True},
                )
                maybe_update_rag_session_summary(session)
            release_rag_chat_admission(admission)

    response = StreamingHttpResponse(
        stream_events(),
        content_type='application/x-ndjson; charset=utf-8',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-RAG-RateLimit'] = 'accepted'
    return response
