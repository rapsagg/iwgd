from django.db import migrations


def create_default_topics(apps, schema_editor):
    Topic = apps.get_model('forum', 'Topic')
    User = apps.get_model('auth', 'User')
    
    # Get or create a system user for default topics
    system_user, created = User.objects.get_or_create(
        username='gaspar',
        defaults={'email': 'gmbos@iscte-iul.pt'}
    )
    
    Topic.objects.create(
        name='General',
        description='General discussion',
        creator=system_user
    )


def remove_default_topics(apps, schema_editor):
    Topic = apps.get_model('forum', 'Topic')
    Topic.objects.filter(name='General').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('forum', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_topics, reverse_code=remove_default_topics),
    ]
