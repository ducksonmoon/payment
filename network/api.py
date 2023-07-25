def get_transactions_history():
    contract_address = (
        "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # USDT TRC20 contract address
    )
    wallet_address = "TF1bYz1BE4n6zo2D4J2kDRK8MuqfbaCHgu"  # wallet address
    url = f"https://api.trongrid.io/v1/accounts/{wallet_address}/transactions/trc20?limit=20&contract_address={contract_address}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)

    return response.json()["data"]


def check_wallet(txid) -> bool:
    wallet_history = get_transactions_history()
    for wallet_transaction in wallet_history:
        timestamp = wallet_transaction["block_timestamp"]
        wallet_transaction_datetime = datetime.datetime.fromtimestamp(timestamp / 1000)

        if (
            wallet_transaction["transaction_id"]
            == txid
            # and wallet_transaction_datetime >= transaction.created_time
        ):
            return True

    return False
