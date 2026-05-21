"""
URL configuration for Projectmanagement project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from app01 import views
from django.conf import settings
urlpatterns = [
    path('admin/', admin.site.urls),
    path('projects/', views.rest_projects),
    path('projects/<int:project_id>/', views.rest_projects),
    path('projects/<int:project_id>/nodes/', views.rest_project_nodes_by_project),
    path('project-nodes/', views.rest_project_nodes),
    path('project-nodes/<int:node_id>/', views.rest_project_nodes),
    path('persons/', views.rest_persons),
    path('persons/<int:person_id>/', views.rest_persons),
    path('projects/<int:project_id>/persons/', views.rest_project_persons),
    path('projects/<int:project_id>/persons/<int:person_id>/', views.rest_project_person_detail),
    path('projects/<int:project_id>/files/', views.rest_project_files),
    path('files/<int:file_id>/', views.rest_files),
    path('projects/<int:project_id>/costs/', views.rest_project_costs),
    path('costs/<int:cost_id>/', views.rest_cost_detail),
    path('projects/<int:project_id>/quality/templates/', views.rest_quality_templates),
    path('quality-templates/<int:template_id>/', views.rest_quality_template_detail),
    path('quality-templates/<int:template_id>/items/', views.rest_quality_template_items),
    path('projects/<int:project_id>/quality/reports/', views.rest_quality_reports),
    path('quality-reports/<int:report_id>/', views.rest_quality_report_detail),
    path('projects/<int:project_id>/quality/stats/', views.rest_quality_stats),
    path('projects/<int:project_id>/safety/templates/', views.rest_safety_templates),
    path('safety-templates/<int:template_id>/', views.rest_safety_template_detail),
    path('safety-templates/<int:template_id>/items/', views.rest_safety_template_items),
    path('projects/<int:project_id>/safety/reports/', views.rest_safety_reports),
    path('projects/<int:project_id>/safety/issues/', views.rest_safety_issues),
    path('safety-issues/<int:report_id>/', views.rest_safety_issue_detail),
    path('projects/<int:project_id>/safety/issues/resolved/', views.rest_safety_resolved_issues),
    path('safety-reports/<int:report_id>/solutions/', views.rest_safety_report_solutions),
    path('audit-logs/', views.rest_audit_logs),
    #登录
    path('login/', views.login_view, name='login'),
    path('current-user/', views.current_user_view),
    path('logout/', views.logout_view),
    path('csrf/', views.csrf_token_view, name='csrf_token'),
    path('projectnode/collect/<int:project_id>/', views.projectnode_collect),
    path('person/collect/', views.person_collect),
    #人员职位统计（单个项目界面）
    path('person/project/collect/<int:project_id>/', views.person_collect),
    #预览文件
    path('file/preview/<int:file_id>/', views.file_preview),
    #下载文件
    path('file/download/<int:file_id>/', views.file_download),
    path('cost/collect/total/<int:project_id>/', views.project_cost_summary, name='project_cost_summary'),
    ##按月统计实际成本
    path('cost/collect/monthly/<int:project_id>/', views.project_monthly_cost_summary, name='project_monthly_cost_summary'),
    #RAG
    path('files/<int:file_id>/rag/index/', views.rag_index_file),
    path('projects/<int:project_id>/rag/chat/', views.rag_chat),
    path('files/<int:file_id>/rag/reindex/', views.rag_reindex_file),
    path('files/<int:file_id>/rag/vectors/', views.rag_delete_file_vectors),

]
