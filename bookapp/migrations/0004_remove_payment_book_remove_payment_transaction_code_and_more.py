# Generated by Django 4.2 on 2024-12-12 11:12

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookapp', '0003_alter_user_profile_picture_payment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='Book',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='transaction_code',
        ),
        migrations.AddField(
            model_name='payment',
            name='callback_received',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='payment',
            name='mpesa_check_out_id',
            field=models.CharField(blank=True, help_text='Checkout ID provided by M-Pesa', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='mpesa_checkout_request_id',
            field=models.CharField(blank=True, help_text='Unique identifier for the M-Pesa transaction request', max_length=255, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='mpesa_merchant_request_id',
            field=models.CharField(blank=True, help_text='Merchant request ID from M-Pesa', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='order',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payment', to='bookapp.order'),
        ),
        migrations.AddField(
            model_name='payment',
            name='phone_number',
            field=models.CharField(default='+254000000000', help_text='Phone number used for M-Pesa payment', max_length=15),
        ),
        migrations.AddField(
            model_name='payment',
            name='retry_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='payment',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0.01)]),
        ),
        migrations.AlterField(
            model_name='payment',
            name='mpesa_receipt_number',
            field=models.CharField(blank=True, help_text='M-Pesa receipt number', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['status', 'created_at'], name='bookapp_pay_status_ac244a_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['mpesa_checkout_request_id'], name='bookapp_pay_mpesa_c_fed6f7_idx'),
        ),
    ]
