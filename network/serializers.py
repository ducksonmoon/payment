from rest_framework import serializers
from core.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ("invoice_number", "network", "txid", "amount", "receiver")

    def create(self, validated_data):
        transaction = Transaction.objects.create(**validated_data)
        return transaction
