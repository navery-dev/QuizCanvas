from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('quizapp', '0003_alter_users_email_alter_users_username'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizattempt',
            name='sectionID',
            field=models.ForeignKey(null=True, blank=True, to='quizapp.section', on_delete=models.SET_NULL, db_column='sectionID', related_name='sectionAttempts'),
        ),
    ]
