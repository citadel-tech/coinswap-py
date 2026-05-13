"""Simple wrapper layer around low-level coinswap bindings."""

from __future__ import annotations

from typing import Any, Optional

from .coinswap import AddressType, RpcConfig, SwapParams, Taker


class CoinswapTaker:
    """Tiny convenience wrapper around the native `Taker` object."""

    def __init__(self, taker: Any) -> None:
        self._taker = taker

    @classmethod
    def create(
        cls,
        data_dir: Optional[str],
        wallet_file_name: Optional[str],
        rpc_config: Optional[RpcConfig],
        control_port: Optional[int],
        tor_auth_password: Optional[str],
        zmq_addr: str,
        password: Optional[str],
    ) -> "CoinswapTaker":
        taker = Taker.init(
            data_dir=data_dir,
            wallet_file_name=wallet_file_name,
            rpc_config=rpc_config,
            control_port=control_port,
            tor_auth_password=tor_auth_password,
            zmq_addr=zmq_addr,
            password=password,
        )
        return cls(taker)

    def setup_logging(self, data_dir: Optional[str], log_level: str) -> None:
        self._taker.setup_logging(data_dir=data_dir, log_level=log_level)

    def prepare_coinswap(self, swap_params: SwapParams) -> str:
        return self._taker.prepare_coinswap(swap_params=swap_params)

    def start_coinswap(self, swap_id: str) -> Any:
        return self._taker.start_coinswap(swap_id=swap_id)

    def get_transactions(
        self,
        count: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> Any:
        return self._taker.get_transactions(count=count, skip=skip)

    def get_next_internal_addresses(
        self,
        count: int,
        address_type: AddressType,
    ) -> Any:
        return self._taker.get_next_internal_addresses(
            count=count,
            address_type=address_type,
        )

    def get_next_external_address(self, address_type: AddressType) -> Any:
        return self._taker.get_next_external_address(address_type=address_type)

    def list_all_utxo_spend_info(self) -> Any:
        return self._taker.list_all_utxo_spend_info()

    def backup(self, destination_path: str, password: Optional[str]) -> None:
        self._taker.backup(destination_path=destination_path, password=password)

    def lock_unspendable_utxos(self) -> None:
        self._taker.lock_unspendable_utxos()

    def send_to_address(
        self,
        address: str,
        amount: int,
        fee_rate: Optional[float] = None,
        manually_selected_outpoints: Optional[Any] = None,
    ) -> Any:
        return self._taker.send_to_address(
            address=address,
            amount=amount,
            fee_rate=fee_rate,
            manually_selected_outpoints=manually_selected_outpoints,
        )

    def get_balances(self) -> Any:
        return self._taker.get_balances()

    def sync_and_save(self) -> None:
        self._taker.sync_and_save()

    def sync_offerbook_and_wait(self) -> None:
        self._taker.sync_offerbook_and_wait()

    def fetch_offers(self) -> Any:
        return self._taker.fetch_offers()

    def display_offer(self, maker_offer: Any) -> str:
        return self._taker.display_offer(maker_offer=maker_offer)

    def get_wallet_name(self) -> str:
        return self._taker.get_wallet_name()

    def recover_active_swap(self) -> None:
        self._taker.recover_active_swap()

    def fetch_all_makers(self) -> Any:
        return self._taker.fetch_all_makers()


def create_client(
    data_dir: Optional[str],
    wallet_file_name: Optional[str],
    rpc_config: Optional[RpcConfig],
    control_port: Optional[int],
    tor_auth_password: Optional[str],
    zmq_addr: str,
    password: Optional[str],
) -> CoinswapTaker:
    """Factory helper for a simpler wrapper style."""
    return CoinswapTaker.create(
        data_dir=data_dir,
        wallet_file_name=wallet_file_name,
        rpc_config=rpc_config,
        control_port=control_port,
        tor_auth_password=tor_auth_password,
        zmq_addr=zmq_addr,
        password=password,
    )
