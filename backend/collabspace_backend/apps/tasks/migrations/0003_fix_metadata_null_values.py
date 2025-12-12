from django.db import migrations

def fix_null_metadata(apps, schema_editor):
    """Fix all tasks with NULL or non-dict metadata."""
    Task = apps.get_model('tasks', 'Task')
    
    # Fix NULL values
    Task.objects.filter(metadata__isnull=True).update(metadata={})
    
    # Fix any non-dict values (safety check)
    for task in Task.objects.all():
        if not isinstance(task.metadata, dict):
            task.metadata = {}
            task.save(update_fields=['metadata'])
    
    print(f"✅ Fixed metadata for all tasks")


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', "0002_taskstatushistory_task_completed_at_and_more"),  # Replace with your last migration number
    ]

    operations = [
        migrations.RunPython(fix_null_metadata, reverse_code=migrations.RunPython.noop),
    ]