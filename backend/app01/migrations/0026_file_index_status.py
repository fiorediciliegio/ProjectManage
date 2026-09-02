# Generated for asynchronous RAG indexing status tracking.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0025_file_uploader_person'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='INDEX_STATUS_File',
            field=models.CharField(
                choices=[
                    ('not_indexed', '未入库'),
                    ('queued', '排队中'),
                    ('running', '入库中'),
                    ('completed', '已入库'),
                    ('failed', '入库失败'),
                    ('deleting', '删除中'),
                ],
                default='not_indexed',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='file',
            name='INDEX_TASK_ID_File',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='file',
            name='INDEX_ERROR_File',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='file',
            name='INDEXED_AT_File',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name='file',
            index=models.Index(fields=['INDEX_STATUS_File'], name='file_idx_status'),
        ),
        migrations.AddIndex(
            model_name='file',
            index=models.Index(fields=['ID_Project', 'INDEX_STATUS_File'], name='file_proj_idx_status'),
        ),
    ]
