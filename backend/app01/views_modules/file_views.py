from app01.views_modules.common import *


# ———————————————————— 文件 ————————————————————
# REST 文件模块：项目文件列表与上传接口
@api_view(['GET', 'POST'])
def rest_project_files(request, project_id):
    if request.method == 'GET':
        try:
            cache_key = build_project_cache_key(
                request,
                'project-files',
                project_id,
                *pagination_cache_parts(request),
            )

            def produce_project_files():
                files = (
                    File.objects
                    .filter(ID_Project=project_id)
                    .select_related('UPLOADER_Person')
                    .order_by('id')
                )
                page_files, pagination = paginate_queryset(files, request)
                serializer = FileSerializer(page_files, many=True)
                files_data = list(serializer.data)
                for file_data in files_data:
                    file_data['is_indexed'] = file_data.get('index_status') == 'completed'
                return {
                    'files': files_data,
                    'pagination': pagination,
                }

            return cached_success_response(
                request=request,
                cache_key=cache_key,
                producer=produce_project_files,
                message='获取文件列表成功',
                timeout=get_api_cache_timeout('API_CACHE_TTL_PROJECT_FILES', 10),
                status_code=status.HTTP_200_OK,
            )
        except Exception as e:
            return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # 登录校验
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error

    if not request.FILES.get('file'):
        return error_response(
            message='请选择要上传的文件',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        uploaded_file = request.FILES['file']
        file_name, file_extension = os.path.splitext(uploaded_file.name)
        project_instance = Project.objects.get(id=project_id)
        # 权限校验
        if not can_manage_project_file(project_instance, person):
            return permission_denied('只有管理员、当前项目经理或当前项目资料人员可以上传文件')
        file_instance = File.objects.create(
            FILE=uploaded_file,
            NAME_File=file_name,
            SIZE_File=uploaded_file.size,
            FORM_File=file_extension,
            ID_Project=project_instance,
            UPLOADER_Person=person,
        )
        create_audit_log(
            request=request,
            action='upload',
            module='文件',
            target_id=file_instance.pk,
            target_name=project_instance.NAME_Project,
            description=f'上传文件：{file_instance.NAME_File}{file_instance.FORM_File or ""}',
        )
        invalidate_project_cache(project_instance.id)
        return success_response(
            data={'file': FileSerializer(file_instance).data},
            message='文件上传成功',
            status_code=status.HTTP_201_CREATED,
        )
    except Project.DoesNotExist:
        return error_response(
            message='项目不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 文件预览
@api_view(['GET'])
def file_preview(request, file_id=None):
    try:
        file_obj = File.objects.get(id=file_id)
        person, auth_error = get_authenticated_person(request)
        if auth_error:
            html_content = (
                '<html><head><meta charset="utf-8"><style>'
                'body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;font-family:Segoe UI,Arial,sans-serif;}'
                '.error{color:#d32f2f;font-size:20px;}'
                '</style></head><body>'
                '<div class="error">请先登录</div>'
                '</body></html>'
            )
            return HttpResponse(html_content, status=401, content_type='text/html; charset=utf-8')
        # 权限校验
        if not is_admin(person) and not is_project_member(file_obj.ID_Project, person):
            html_content = (
                '<html><head><meta charset="utf-8"><style>'
                'body{margin:0;height:100vh;display:flex;align-items:center;justify-content:center;font-family:Segoe UI,Arial,sans-serif;}'
                '.error{color:#d32f2f;font-size:20px;}'
                '</style></head><body>'
                '<div class="error">只有当前项目成员可以预览文件</div>'
                '</body></html>'
            )
            return HttpResponse(html_content, status=403, content_type='text/html; charset=utf-8')
        file_path = file_obj.FILE.path
        file_extension = (file_obj.FORM_File or '').lower()
        file_name = f"{file_obj.NAME_File}{file_obj.FORM_File or ''}"

        if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            mime_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
            response = HttpResponse(file_content, content_type=mime_type)
            response['Content-Disposition'] = f'inline; filename="{smart_str(file_name)}"'
            create_audit_log(
                request=request,
                action='preview',
                module='文件',
                target_id=file_obj.pk,
                target_name=file_obj.ID_Project.NAME_Project,
                description=f'预览文件：文件名：{file_name}',
            )
            return response

        if file_extension == '.pdf':
            with open(file_path, 'rb') as f:
                file_content = f.read()
            response = HttpResponse(file_content, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{smart_str(file_name)}"'
            create_audit_log(
                request=request,
                action='preview',
                module='文件',
                target_id=file_obj.pk,
                target_name=file_obj.ID_Project.NAME_Project,
                description=f'预览文件：文件名：{file_name}',
            )
            return response

        if file_extension in ['.txt', '.md', '.py', '.json', '.js', '.css', '.html']:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                text_content = f.read()
            html_content = (
                '<html><head><meta charset="utf-8"><style>'
                'body{font-family:Segoe UI,Arial,sans-serif;padding:24px;line-height:1.7;white-space:pre-wrap;word-break:break-word;}'
                '</style></head><body>'
                f'{escape(text_content)}'
                '</body></html>'
            )
            create_audit_log(
                request=request,
                action='preview',
                module='文件',
                target_id=file_obj.pk,
                target_name=file_obj.ID_Project.NAME_Project,
                description=f'预览文件：文件名：{file_name}',
            )
            return HttpResponse(html_content, content_type='text/html; charset=utf-8')

        if file_extension == '.docx':
            document = Document(file_path)
            paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
            table_rows = []
            for table in document.tables:
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if cells:
                        table_rows.append(' | '.join(cells))
            combined_lines = paragraphs + table_rows
            preview_text = '\n\n'.join(combined_lines) if combined_lines else '文档中暂无可预览的文字内容'
            html_content = (
                '<html><head><meta charset="utf-8"><style>'
                'body{font-family:Segoe UI,Arial,sans-serif;padding:24px;line-height:1.8;white-space:pre-wrap;word-break:break-word;}'
                'h2{margin-top:0;} .meta{color:#666;margin-bottom:16px;font-size:14px;}'
                '</style></head><body>'
                f'<h2>{escape(file_name)}</h2>'
                f'<div class="meta">{escape("Word 预览")}</div>'
                f'{escape(preview_text)}'
                '</body></html>'
            )
            create_audit_log(
                request=request,
                action='preview',
                module='文件',
                target_id=file_obj.pk,
                target_name=file_obj.ID_Project.NAME_Project,
                description=f'预览文件：文件名：{file_name}',
            )
            return HttpResponse(html_content, content_type='text/html; charset=utf-8')

        if file_extension in ['.xlsx', '.xlsm']:
            workbook = load_workbook(file_path, data_only=True)
            sheets_html = []

            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                rows_html = []

                for row in sheet.iter_rows(values_only=True):
                    cells_html = ''.join(
                        f'<td>{escape(str(cell)) if cell is not None else ""}</td>'
                        for cell in row
                    )
                    rows_html.append(f'<tr>{cells_html}</tr>')

                sheets_html.append(
                    f'<h3>{escape(sheet_name)}</h3>'
                    f'<table>{"".join(rows_html)}</table>'
                )
            html_content = (
                '<html><head><meta charset="utf-8"><style>'
                'body{font-family:Segoe UI,Arial,sans-serif;padding:24px;line-height:1.7;}'
                'h2{margin-top:0;} h3{margin-top:24px;}'
                'table{border-collapse:collapse;margin-bottom:24px;max-width:100%;}'
                'td{border:1px solid #ddd;padding:6px 10px;min-width:80px;}'
                '</style></head><body>'
                f'<h2>{escape(file_name)}</h2>'
                f'{"".join(sheets_html)}'
                '</body></html>'
            )
            create_audit_log(
                request=request,
                action='preview',
                module='文件',
                target_id=file_obj.pk,
                target_name=file_obj.ID_Project.NAME_Project,
                description=f'预览文件：文件名：{file_name}',
            )
            return HttpResponse(html_content, content_type='text/html; charset=utf-8')

        html_content = (
            '<html><head><meta charset="utf-8"><style>'
            'body{font-family:Segoe UI,Arial,sans-serif;padding:24px;line-height:1.7;}'
            '.note{padding:16px;border-radius:8px;background:#f5f7fb;color:#333;}'
            '</style></head><body>'
            f'<h2>{escape(file_name)}</h2>'
            '<div class="note">暂不支持当前文件格式的在线预览，请下载后在本地打开查看。</div>'
            '</body></html>'
        )
        create_audit_log(
            request=request,
            action='preview',
            module='文件',
            target_id=file_obj.pk,
            target_name=file_obj.ID_Project.NAME_Project,
            description=f'预览文件：文件名：{file_name}',
        )
        return HttpResponse(html_content, content_type='text/html; charset=utf-8')
    except File.DoesNotExist:
        return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# 文件下载
@api_view(['GET'])
def file_download(request, file_id=None):
    # 登录校验
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error
    try:
        file_obj = File.objects.get(id=file_id)
        file_path = file_obj.FILE.path
        # 权限校验
        if not is_admin(person) and not is_project_member(file_obj.ID_Project, person):
            return permission_denied('只有当前项目成员可以下载文件')

        with open(file_path, 'rb') as f:
            file_content = f.read()

        response = HttpResponse(file_content, content_type='application/octet-stream; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{smart_str(file_obj.NAME_File)}"'
        response['Content-Length'] = os.path.getsize(file_path)
        create_audit_log(
            request=request,
            action='download',
            module='文件',
            target_id=file_obj.pk,
            target_name=file_obj.ID_Project.NAME_Project,
            description=f'下载文件：文件名：{file_obj.NAME_File}{file_obj.FORM_File or ""}',
        )
        return response
    except File.DoesNotExist:
        return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        print(f'Exception: {e}')
        return JsonResponse({'error': str(e)}, status=500)

# REST 文件模块：文件删除接口
@api_view(['DELETE'])
def rest_files(request, file_id):
    # 登录校验
    person, auth_error = get_authenticated_person(request)
    if auth_error:
        return auth_error
    try:
        file_obj = File.objects.get(id=file_id)
        project_id = file_obj.ID_Project_id
        # 权限校验
        if not can_manage_project_file(file_obj.ID_Project, person):
            return permission_denied('只有管理员、当前项目经理或当前项目资料人员可以删除文件')
        create_audit_log(
            request=request,
            action='delete',
            module='文件',
            target_id=file_obj.pk,
            target_name=file_obj.ID_Project.NAME_Project,
            description=f'删除文件：文件名：{file_obj.NAME_File}{file_obj.FORM_File or ""}',
        )
        # 从 ES 和 Qdrant 中同步删除
        delete_langchain_file_vectors(file_obj.pk)
        delete_file_chunks_from_elasticsearch(file_obj.pk)
        file_obj.delete()
        invalidate_project_cache(project_id)
        return success_response(
            data=None,
            message='文件删除成功',
            status_code=status.HTTP_200_OK,
        )
    except File.DoesNotExist:
        return error_response(
            message='文件不存在',
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return error_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 文件入 Qdrant 库
ACTIVE_RAG_TASK_STATUSES = {'queued', 'running', 'retrying', 'cancelling', 'deleting'}
CANCELLABLE_RAG_TASK_STATUSES = {'queued', 'running', 'retrying'}
