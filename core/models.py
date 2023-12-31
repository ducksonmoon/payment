import uuid
import datetime
from django.db import models


class Transaction(models.Model):
    amount = models.FloatField(default=0.0)
    txid = models.CharField(max_length=255)
    sender = models.CharField(max_length=255)
    receiver = models.CharField(max_length=255)
    created_time = models.DateTimeField(default=datetime.datetime.now(), editable=False)
    expire_time = models.DateTimeField(
        default=datetime.datetime.now() + datetime.timedelta(minutes=5), editable=False
    )
    ref = models.CharField(max_length=150, unique=True, default=uuid.uuid4)
    invoice_number = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    STATE_TYPE = [(1, "Pending"), (2, "Done"), (3, "Failed")]
    state = models.CharField(max_length=1, choices=STATE_TYPE, default=1)
    NETWORK_TYPE = [(1, "TRC20"), (2, "BEP20")]
    network = models.CharField(max_length=1, choices=NETWORK_TYPE)


class Wallet(models.Model):
    address = models.CharField(max_length=255)
    NETWORK_TYPE = [(1, "TRC20"), (2, "BEP20")]
    network = models.CharField(max_length=1, choices=NETWORK_TYPE)


class Receiver(models.Model):
    wallet = models.OneToOneField(Wallet, on_delete=models.PROTECT)
    update_time = models.DateTimeField(default=datetime.datetime.now(), editable=False)

    def save(self, *args, **kwargs):
        if self.pk:
            original_receiver = Receiver.objects.get(pk=self.pk)
            if original_receiver.wallet != self.wallet:
                self.update_time = timezone.now()
        super().save(*args, **kwargs)
