import asyncio
import aiohttp
import time

from django.conf import settings
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from . import serializers
from core.models import Transaction, Receiver, Wallet


class API:
    api_key = settings.BSCSCAN_API_KEY
    trc20_contract_address = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    network = None
    receiver = ""

    def get_trc20_url(self):
        return f"https://api.trongrid.io/v1/accounts/{self.receiver}/transactions/trc20?limit=20&contract_address={self.trc20_contract_address}"

    def get_bep20_url(self):
        return f"https://api.bscscan.com/api?module=account&action=txlist&address={self.receiver}&startblock=0&endblock=999999999&sort=desc&apikey={self.api_key}"

    def get_response_data(self, response):
        if self.network == 1:
            return response.get("data", [])
        if self.network == 2:
            return response.get("result", [])

    def get_lookup_key(self, t):
        if self.network == 1:
            return t.get("transaction_id")
        if self.network == 2:
            return t.get("hash")

    def get_lookup_amount(self, t):
        value = int(t.get("value"))
        if self.network == 1:
            decimal = t.get("token_info").get("decimals")
            return value / (10 ** int(decimal))
        if self.network == 2:
            return value / (10**18)

    def get_api_url(self):
        if self.network == 1:
            return self.get_trc20_url()
        if self.network == 2:
            return self.get_bep20_url()


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
        if Wallet.objects.filter(address="self.receiver") == 0:
            response_data = {
                "status": "error",
                "message": "Wallet does not exists.",
            }
            response = Response(response_data, status=status.HTTP_400_BAD_REQUEST)
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
