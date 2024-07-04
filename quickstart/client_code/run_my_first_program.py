"""
In this example, we:
1. connect to the local nillion-devnet
2. store the average calculation program
3. store secrets to be used in the computation
4. compute the average calculation program with the stored secrets and another computation time secret
"""

import asyncio
import py_nillion_client as nillion
import os

from py_nillion_client import NodeKey, UserKey
from dotenv import load_dotenv
from nillion_python_helpers import get_quote_and_pay, create_nillion_client, create_payments_config

from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.keypairs import PrivateKey

home = os.getenv("HOME")
load_dotenv(f"{home}/.config/nillion/nillion-devnet.env")

async def main():
    # 1. Initial setup
    # 1.1. Get cluster_id, grpc_endpoint, & chain_id from the .env file
    cluster_id = os.getenv("NILLION_CLUSTER_ID")
    grpc_endpoint = os.getenv("NILLION_NILCHAIN_GRPC")
    chain_id = os.getenv("NILLION_NILCHAIN_CHAIN_ID")
    # 1.2 pick a seed and generate user and node keys
    seed = "my_seed"
    userkey = UserKey.from_seed(seed)
    nodekey = NodeKey.from_seed(seed)

    # 2. Initialize NillionClient against nillion-devnet
    # Create Nillion Client for user
    client = create_nillion_client(userkey, nodekey)

    party_id = client.party_id
    user_id = client.user_id

    # 3. Pay for and store the program
    # Set the program name and path to the compiled program
    program_name = "average_calculation"
    program_mir_path = f"../nada_quickstart_programs/target/{program_name}.nada.bin"

    # Create payments config, client and wallet
    payments_config = create_payments_config(chain_id, grpc_endpoint)
    payments_client = LedgerClient(payments_config)
    payments_wallet = LocalWallet(
        PrivateKey(bytes.fromhex(os.getenv("NILLION_NILCHAIN_PRIVATE_KEY_0"))),
        prefix="nillion",
    )

    # Pay to store the program and obtain a receipt of the payment
    receipt_store_program = await get_quote_and_pay(
        client,
        nillion.Operation.store_program(program_mir_path),
        payments_wallet,
        payments_client,
        cluster_id,
    )

    # Store the program
    action_id = await client.store_program(
        cluster_id, program_name, program_mir_path, receipt_store_program
    )

    # Create a variable for the program_id, which is the {user_id}/{program_name}. We will need this later
    program_id = f"{user_id}/{program_name}"
    print("Stored program. action_id:", action_id)
    print("Stored program_id:", program_id)

    # 4. Create the secrets, add permissions, pay for and store them in the network
    # Create secrets named "X", "Y", and "Z" with any values, e.g., 10, 20, and 30
    new_secrets = nillion.NadaValues(
        {
            "X": nillion.SecretInteger(10),
            "Y": nillion.SecretInteger(20),
            "Z": nillion.SecretInteger(30),
        }
    )

    # Set the input party for the secrets
    # The party names need to match the party names that are storing "X", "Y", and "Z" in the program
    party_name = "Party1"

    # Set permissions for the client to compute on the program
    permissions = nillion.Permissions.default_for_user(client.user_id)
    permissions.add_compute_permissions({client.user_id: {program_id}})

    # Pay for and store the secrets in the network and print the returned store_id
    receipt_store = await get_quote_and_pay(
        client,
        nillion.Operation.store_values(new_secrets, ttl_days=5),
        payments_wallet,
        payments_client,
        cluster_id,
    )
    # Store the secrets
    store_id = await client.store_values(
        cluster_id, new_secrets, permissions, receipt_store
    )
    print(f"Computing using program {program_id}")
    print(f"Use secret store_id: {store_id}")

    # 5. Create compute bindings to set input and output parties, and pay for & run the computation
    compute_bindings = nillion.ProgramBindings(program_id)
    compute_bindings.add_input_party(party_name, party_id)
    compute_bindings.add_output_party(party_name, party_id)

    # Pay for the compute
    receipt_compute = await get_quote_and_pay(
        client,
        nillion.Operation.compute(program_id),
        payments_wallet,
        payments_client,
        cluster_id,
    )

    # Compute on the secrets
    compute_id = await client.compute(
        cluster_id,
        compute_bindings,
        [store_id],
        receipt_compute,
    )

    # 8. Return the computation result
    print(f"The computation was sent to the network. compute_id: {compute_id}")
    while True:
        compute_event = await client.next_compute_event()
        if isinstance(compute_event, nillion.ComputeFinishedEvent):
            print(f"✅  Compute complete for compute_id {compute_event.uuid}")
            print(f"🖥️  The result is {compute_event.result.value}")
            return compute_event.result.value


if __name__ == "__main__":
    asyncio.run(main())
