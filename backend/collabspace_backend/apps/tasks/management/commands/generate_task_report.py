"""
Create management command: tasks/management/commands/generate_task_report.py

from django.core.management.base import BaseCommand
from apps.tasks.views import generate_task_report
from apps.projects.models import Project
import json

class Command(BaseCommand):
    help = 'Generate task report for a project'
    
    def add_arguments(self, parser):
        parser.add_argument('project_id', type=int)
        parser.add_argument('--output', type=str, default='report.json')
    
    def handle(self, *args, **options):
        project = Project.objects.get(id=options['project_id'])
        report = generate_task_report(project)
        
        with open(options['output'], 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.stdout.write(
            self.style.SUCCESS(f'Report generated: {options["output"]}')
        )
"""
