import asyncio
import aiohttp
import time

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from . import serializers
from core.models import Transaction, Wallet
from network.api import API


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
                            if (
                                self.get_lookup_key(t) == transaction.txid
                                and self.get_lookup_amount(t) == transaction.amount
                            ):
                                return True

                except Exception as e:
                    print(f"Error while checking txid: {e}")

                await asyncio.sleep(5)

    def perform_create(self, serializer):
        self.network = serializer.validated_data.get("network", None)
        self.receiver = serializer.validated_data.get("receiver", None)

        if Wallet.objects.filter(address=self.receiver).count() == 0:
            response_data = {
                "status": "error",
                "message": "Wallet does not exists.",
            }
            response = Response(response_data, status=status.HTTP_403_FORBIDDEN)
            return response

        additional_data = {"receiver": self.receiver}
        data_to_create = {**serializer.validated_data, **additional_data}
        transaction = serializer.save(**data_to_create)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            self.check_txid_in_response(transaction, self.get_api_url())
        )

        if result:
            transaction.state = 2  # 2 corresponds to "Done" in STATE_TYPE choices
            transaction.save()
            print("Transaction completed")
            response_data = {
                "status": "success",
                "message": "Transaction completed successfully.",
                "transaction_id": transaction.id,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        else:
            transaction.state = 3  # 3 corresponds to "Failed" in STATE_TYPE choices
            transaction.save()
            response_data = {
                "status": "error",
                "message": "Transaction failed.",
            }
            response = Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        # Add custom header to instruct the client to keep the connection open for 2 minutes
        # keep_connection_open_time = datetime.now() + timedelta(minutes=2)
        # response["Keep-Alive"] = f"timeout=120, max=60"
        # response["Connection"] = "keep-alive"
        # response["Date"] = http_date(datetime.now().timestamp())
        # response["Expires"] = http_date(keep_connection_open_time.timestamp())
        return response
