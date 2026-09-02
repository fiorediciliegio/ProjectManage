from django.db import migrations


def backfill_file_index_stage(apps, schema_editor):
    File = apps.get_model('app01', 'File')
    stage_by_status = {
        'not_indexed': 'idle',
        'queued': 'queued',
        'running': 'prepare',
        'completed': 'completed',
        'failed': 'failed',
        'deleting': 'delete_vectors',
    }

    for status, stage in stage_by_status.items():
        File.objects.filter(INDEX_STATUS_File=status).update(INDEX_STAGE_File=stage)


def reset_file_index_stage(apps, schema_editor):
    File = apps.get_model('app01', 'File')
    File.objects.all().update(INDEX_STAGE_File='idle')


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0027_file_index_error_detail_file_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_file_index_stage, reset_file_index_stage),
    ]
