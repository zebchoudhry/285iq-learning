from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0008_add_parent_access_token"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="subscription_status",
            field=models.CharField(default="free", max_length=20),
        ),
        migrations.AddField(
            model_name="student",
            name="stripe_customer_id",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="student",
            name="stripe_subscription_id",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="student",
            name="subscription_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="student",
            name="parent_email",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
