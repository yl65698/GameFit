from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_add_vr_type_to_pcspec'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pcspec',
            name='ram',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
    ]
