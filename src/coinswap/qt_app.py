"""Minimal Qt app that runs the taker flow with wrapper methods."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from typing import Callable, Optional

from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .coinswap import AddressType, RpcConfig, SwapParams
from .wrapper import CoinswapTaker

WALLET_NAME = "python_wallet"
RPC_URL = "localhost:18442"
RPC_USERNAME = "user"
RPC_PASSWORD = "password"
TOR_CONTROL_PORT = 9051
TOR_AUTH_PASSWORD = "coinswap"
ZMQ_ADDR = "tcp://127.0.0.1:28332"
FUNDING_BTC = "0.42749329"
SEND_AMOUNT_SATS = 500000
MAKER_COUNT = 2
TX_COUNT = 3
REQUIRED_CONFIRMS = 1
ADDRESS_TYPE = "P2TR"

def cleanup_test_wallets(log: Callable[[str], None]) -> None:
    wallets_dir = os.path.expanduser("~/.coinswap/taker/wallets")
    if os.path.isdir(wallets_dir):
        for entry in os.listdir(wallets_dir):
            if not entry.startswith(WALLET_NAME):
                continue
            wallet_path = os.path.join(wallets_dir, entry)
            try:
                if os.path.isdir(wallet_path):
                    subprocess.run(["rm", "-rf", wallet_path], check=True)
                else:
                    os.remove(wallet_path)
                log(f"Cleaned up {wallet_path}")
            except Exception as exc:
                log(f"Warning: Could not clean {wallet_path}: {exc}")

    try:
        subprocess.run(
            [
                "docker",
                "exec",
                "coinswap-bitcoind",
                "bitcoin-cli",
                "-regtest",
                "-rpcport=18442",
                "-rpcuser=user",
                "-rpcpassword=password",
                "unloadwallet",
                WALLET_NAME,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        log("Unloaded wallet from Docker bitcoind")
    except Exception:
        log("Warning: Could not unload wallet from Docker bitcoind")

    try:
        result = subprocess.run(
            [
                "docker",
                "exec",
                "coinswap-bitcoind",
                "rm",
                "-rf",
                f"/home/bitcoin/.bitcoin/wallets/{WALLET_NAME}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            log(f"Removed {WALLET_NAME} wallet from Docker container")
        else:
            log("Warning: Failed to remove wallet from Docker container")
    except Exception:
        log("Warning: Failed to remove wallet from Docker container")


def setup_funding_wallet(taker_address: str, log: Callable[[str], None]) -> None:
    funding_wallet = "test"
    try:
        result = subprocess.run(
            [
                "docker",
                "exec",
                "coinswap-bitcoind",
                "bitcoin-cli",
                "-regtest",
                "-rpcport=18442",
                f"-rpcwallet={funding_wallet}",
                "-rpcuser=user",
                "-rpcpassword=password",
                "sendtoaddress",
                taker_address,
                FUNDING_BTC,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        txid = result.stdout.strip()
        log(f"Sent {FUNDING_BTC} BTC to taker address (txid: {txid[:16]}...)")
    except subprocess.CalledProcessError as exc:
        log(f"Failed to send BTC: {exc.stderr}")
        raise

    time.sleep(1)


class SwapWorker(QtCore.QObject):
    log = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()
    failed = QtCore.pyqtSignal(str)

    def run(self) -> None:
        try:
            self.log.emit("Starting taproot flow")
            self.log.emit("Cleaning up previous test data")
            cleanup_test_wallets(self.log.emit)

            rpc_config = RpcConfig(
                url=RPC_URL,
                username=RPC_USERNAME,
                password=RPC_PASSWORD,
                wallet_name=WALLET_NAME,
            )

            self.log.emit("Initializing taker")
            taker = CoinswapTaker.create(
                data_dir=None,
                wallet_file_name=WALLET_NAME,
                rpc_config=rpc_config,
                control_port=TOR_CONTROL_PORT,
                tor_auth_password=TOR_AUTH_PASSWORD,
                zmq_addr=ZMQ_ADDR,
                password=None,
            )

            self.log.emit("Setting up logging")
            try:
                taker.setup_logging(data_dir=None, log_level="Info")
            except Exception as exc:
                self.log.emit(f"Warning: Could not setup logging: {exc}")

            self.log.emit("Checking wallet name")
            wallet_name_check = taker.get_wallet_name()
            if wallet_name_check != WALLET_NAME:
                self.log.emit(f"Warning: wallet name mismatch: {wallet_name_check}")
            else:
                self.log.emit(f"Wallet name: {wallet_name_check}")

            self.log.emit("Syncing offerbook")
            taker.sync_offerbook_and_wait()

            self.log.emit("Generating addresses")
            external_address1 = taker.get_next_external_address(
                AddressType(addr_type=ADDRESS_TYPE)
            )
            external_address2 = taker.get_next_external_address(
                AddressType(addr_type=ADDRESS_TYPE)
            )
            self.log.emit(f"External address 1: {external_address1.address}")
            self.log.emit(f"External address 2: {external_address2.address}")

            internal_addresses = taker.get_next_internal_addresses(
                3, AddressType(addr_type=ADDRESS_TYPE)
            )
            try:
                internal_count = len(internal_addresses) - 1
            except TypeError:
                internal_count = 0
            self.log.emit(f"Generated {internal_count} internal addresses")

            self.log.emit("Checking initial balances")
            taker.sync_and_save()
            initial_balances = taker.get_balances()
            self.log.emit(f"Spendable: {initial_balances.spendable} sats")
            self.log.emit(f"Regular: {initial_balances.regular} sats")
            self.log.emit(f"Swap: {initial_balances.swap} sats")
            self.log.emit(f"Fidelity: {initial_balances.fidelity} sats")

            self.log.emit("Funding wallet")
            setup_funding_wallet(external_address1.address, self.log.emit)
            taker.sync_and_save()

            self.log.emit("Checking updated balances")
            updated_balances = taker.get_balances()
            self.log.emit(f"Spendable: {updated_balances.spendable} sats")
            self.log.emit(f"Regular: {updated_balances.regular} sats")
            self.log.emit(f"Swap: {updated_balances.swap} sats")
            self.log.emit(f"Fidelity: {updated_balances.fidelity} sats")

            self.log.emit("Listing UTXOs")
            utxos = taker.list_all_utxo_spend_info()
            self.log.emit(f"Found {len(utxos)} UTXO(s)")

            self.log.emit("Getting transactions")
            transactions = taker.get_transactions(None, None)
            self.log.emit(f"Found {len(transactions)} transaction(s)")

            self.log.emit("Fetching offers")
            try:
                fetch_offers_result = taker.fetch_offers()
                self.log.emit(f"Fetch offers result: {fetch_offers_result}")
            except Exception as exc:
                self.log.emit(f"Warning: Could not fetch offers: {exc}")

            self.log.emit("Preparing taproot coinswap")
            swap_params = SwapParams(
                protocol="Taproot",
                send_amount=SEND_AMOUNT_SATS,
                maker_count=MAKER_COUNT,
                tx_count=TX_COUNT,
                required_confirms=REQUIRED_CONFIRMS,
                manually_selected_outpoints=None,
                preferred_makers=None,
            )

            swap_id = taker.prepare_coinswap(swap_params=swap_params)
            swap_report = taker.start_coinswap(swap_id=swap_id)

            self.log.emit("Swap completed")
            outgoing_amount = getattr(
                swap_report, "outgoing_amount", getattr(swap_report, "target_amount", None)
            )
            fee_value = getattr(
                swap_report, "fee_paid_or_earned", getattr(swap_report, "total_fee", None)
            )
            total_fee_paid = abs(fee_value) if fee_value is not None else None
            self.log.emit(f"Swap ID: {swap_report.swap_id}")
            self.log.emit(
                f"Duration: {swap_report.swap_duration_seconds:.2f} seconds"
            )
            self.log.emit(f"Outgoing/Target Amount: {outgoing_amount} sats")
            self.log.emit(f"Total Fee Paid: {total_fee_paid} sats")
            self.log.emit(f"Maker Fees: {swap_report.total_maker_fees} sats")
            self.log.emit(f"Mining Fee: {swap_report.mining_fee} sats")
            self.log.emit(f"Fee Percentage: {swap_report.fee_percentage:.4f}%")
            self.log.emit(f"Makers Used: {swap_report.makers_count}")

            self.log.emit("Final balances")
            taker.sync_and_save()
            final_balances = taker.get_balances()
            self.log.emit(f"Spendable: {final_balances.spendable} sats")
            self.log.emit(f"Regular: {final_balances.regular} sats")
            self.log.emit(f"Swap: {final_balances.swap} sats")
            self.log.emit(f"Fidelity: {final_balances.fidelity} sats")
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}")
        finally:
            self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Coinswap Taproot Qt")
        self.setMinimumSize(720, 520)

        self._thread: Optional[QtCore.QThread] = None
        self._worker: Optional[SwapWorker] = None

        title = QLabel("Taproot swap (wrapper flow)")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("font-family: Menlo, monospace; font-size: 12px;")

        self.run_button = QPushButton("Run Taproot Swap")
        self.run_button.clicked.connect(self._run_flow)

        self.clear_button = QPushButton("Clear Log")
        self.clear_button.clicked.connect(self.log_view.clear)

        button_row = QHBoxLayout()
        button_row.addWidget(self.run_button)
        button_row.addWidget(self.clear_button)
        button_row.addStretch(1)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addLayout(button_row)
        layout.addWidget(self.log_view)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def _log(self, message: str) -> None:
        self.log_view.append(message)

    def _run_flow(self) -> None:
        if self._thread and self._thread.isRunning():
            return

        self.run_button.setEnabled(False)
        self._log("Starting...")

        self._thread = QtCore.QThread()
        self._worker = SwapWorker()
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self._log)
        self._worker.failed.connect(self._log)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(lambda: self.run_button.setEnabled(True))

        self._thread.start()


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
