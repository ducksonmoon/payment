from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test

from core.models import *


def is_admin(user):
    return user.is_authenticated


@user_passes_test(is_admin)
def index(request):
    if request.method == "POST":
        address = request.POST.get("address")
        network = request.POST.get("network")
        Wallet.objects.create(address=address, network=network)

    qs = Transaction.objects.all().values()[::-1]
    state_mapping = ["WTF", "Pending", "Done", "Failed"]
    network_mapping = ["WTF", "TRC20", "BEP20"]

    for item in qs:
        item["state"] = state_mapping[int(item["state"])]
        item["network"] = network_mapping[int(item["network"])]

    return render(request, "index.html", {"qs": qs})
