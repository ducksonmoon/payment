from django.conf import settings


class API:
    api_key = settings.BSCSCAN_API_KEY
    trc20_contract_address = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    network = None
    receiver = ""

    def get_trc20_url(self):
        return f"https://api.trongrid.io/v1/accounts/{self.receiver}/transactions/trc20?limit=20&contract_address={self.trc20_contract_address}"

    def get_bep20_url(self):
        return f"https://api.bscscan.com/api?module=account&action=tokentx&address={self.receiver}&startblock=0&endblock=999999999&sort=desc&apikey={self.api_key}"

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

    def get_bsc_usd_transactions(wallet_address, api_key):
        url = "https://api.bscscan.com/api"
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",  # Binance-Peg BSC-USD contract address
            "address": wallet_address,
            "startblock": 0,
            "endblock": 999999999,
            "sort": "desc",
            "apikey": api_key,
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()
            return data["result"]
        except requests.exceptions.RequestException as e:
            print("Error fetching data:", e)
            return None
