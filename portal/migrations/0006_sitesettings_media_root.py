from django.db import migrations, models
import portal.models
import portal.storage


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0005_sitesettings_auto_extract_colors'),
    ]

    operations = [
        # Add media_root field to SiteSettings
        migrations.AddField(
            model_name='sitesettings',
            name='media_root',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Full path where uploaded files are stored (e.g. /mnt/usb1). Leave empty to use the system default. Changing this does NOT move existing files — only new uploads will go here.',
                max_length=500,
                verbose_name='Media Storage Path',
            ),
        ),
        # Update storage backend on all file fields to DynamicMediaStorage
        migrations.AlterField(
            model_name='sitesettings',
            name='logo',
            field=models.ImageField(
                blank=True, null=True,
                help_text='Replaces the emoji icon in the sidebar',
                storage=portal.storage.DynamicMediaStorage(),
                upload_to='branding/',
            ),
        ),
        migrations.AlterField(
            model_name='category',
            name='cover_image',
            field=models.ImageField(
                blank=True, null=True,
                storage=portal.storage.DynamicMediaStorage(),
                upload_to='covers/',
            ),
        ),
        migrations.AlterField(
            model_name='contentitem',
            name='file',
            field=models.FileField(
                storage=portal.storage.DynamicMediaStorage(),
                upload_to=portal.models.content_upload_path,
            ),
        ),
        migrations.AlterField(
            model_name='contentitem',
            name='thumbnail',
            field=models.ImageField(
                blank=True, null=True,
                storage=portal.storage.DynamicMediaStorage(),
                upload_to='thumbnails/',
            ),
        ),
        migrations.AlterField(
            model_name='announcement',
            name='media_image',
            field=models.ImageField(
                blank=True, null=True,
                help_text='Upload an image/poster for this announcement',
                storage=portal.storage.DynamicMediaStorage(),
                upload_to='announcements/',
            ),
        ),
    ]
