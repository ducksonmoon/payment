import asyncio
import aiohttp
import time

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from . import serializers
from core.models import Transaction, Wallet
from network.api import API

FAILED = 3
DONE = 2


class Trigger(generics.CreateAPIView, API):
    queryset = Transaction.objects.all()
    serializer_class = serializers.TransactionSerializer

    async def check_txid_in_response(self, transaction, url):
        headers = {"accept": "application/json"}

        async with aiohttp.ClientSession() as session:
            end_time = time.time() + 3 * 60  # 3 minutes from now
            while time.time() < end_time:
                try:
                    async with session.get(url, headers=headers) as response:
                        response = await response.json()
                        for t in self.get_response_data(response):
                            if self.get_lookup_amount(t) == transaction.amount:
                                return True

                except Exception as e:
                    print(f"Error while checking: {e}")

                await asyncio.sleep(5)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.network = serializer.validated_data.get("network", None)
        self.receiver = serializer.validated_data.get("receiver", None)
        additional_data = {"receiver": self.receiver}
        data_to_create = {**serializer.validated_data, **additional_data}
        transaction = serializer.save(**data_to_create)

        if Wallet.objects.filter(address=self.receiver).count() == 0:
            response_data = {
                "status": "error",
                "message": "Wallet does not exist.",
                "invoice_number": transaction.invoice_number,
            }
            transaction.state = FAILED
            transaction.save()

            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            self.check_txid_in_response(transaction, self.get_api_url())
        )

        if result:
            transaction.state = DONE
            transaction.save()
            print("Transaction completed")
            response_data = {
                "status": "success",
                "message": "Transaction completed successfully.",
                "invoice_number": transaction.invoice_number,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        else:
            transaction.state = FAILED
            transaction.save()
            response_data = {
                "status": "error",
                "message": "Transaction failed.",
                "invoice_number": transaction.invoice_number,
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
