from web3 import Web3
import json
import time
import random

# Konfigurasi dasar
RPC_URL = "https://tea-sepolia.g.alchemy.com/v2/vot1HrCuj9CmekoM2FKNnv6h4Mnzjyb_"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Konfigurasi token
TOKEN_CONTRACT_ADDRESS = "0x6b85460dB1766D21ee734BE3c0444bb4C922fEd7"  # Ganti dengan alamat kontrak token Anda

# ABI dengan fungsi transfer dan name
TOKEN_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

def load_private_key(filename="privatekey.txt"):
    """Membaca private key dari file 🔑"""
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise Exception(f"File {filename} tidak ditemukan 😞")
    except Exception as e:
        raise Exception(f"Error membaca private key: {str(e)} 😵")

def load_recipient_addresses(filename="wallet.txt"):
    """Membaca daftar alamat wallet dari file dan tambahkan delay acak 📜"""
    try:
        with open(filename, 'r') as f:
            recipients = [line.strip() for line in f if line.strip()]
            return [{"address": w3.to_checksum_address(addr), "delay": random.uniform(30, 90)} for addr in recipients]
    except FileNotFoundError:
        raise Exception(f"File {filename} tidak ditemukan 😞")
    except Exception as e:
        raise Exception(f"Error membaca wallet addresses: {str(e)} 😵")

def get_token_amount_choice():
    """Mendapatkan pilihan jumlah token dari pengguna 🎲"""
    print("Pilih opsi jumlah token yang akan dikirim: 🤔")
    print("1. Jumlah tetap untuk semua penerima 📏")
    print("2. Jumlah acak (100-1000 token) untuk setiap penerima 🎰")
    choice = input("Masukkan pilihan (1 atau 2): ").strip()
    
    if choice == "1":
        amount = float(input("Masukkan jumlah token (dalam unit token, bukan wei): "))
        return lambda: w3.to_wei(amount, 'ether')
    elif choice == "2":
        return lambda: w3.to_wei(random.uniform(100, 1000), 'ether')
    else:
        raise ValueError("Pilihan tidak valid, gunakan 1 atau 2 😡")

def send_bulk_token_transfers():
    """Mengirim token dengan jumlah berdasarkan pilihan pengguna 🚀"""
    private_key = load_private_key()
    sender_address = w3.eth.account.from_key(private_key).address
    
    recipients = load_recipient_addresses()
    if not recipients:
        raise ValueError("Daftar penerima kosong 😢")
    
    get_amount = get_token_amount_choice()
    
    token_contract = w3.eth.contract(
        address=TOKEN_CONTRACT_ADDRESS,
        abi=TOKEN_ABI
    )
    
    # Mendapatkan nama token
    try:
        token_name = token_contract.functions.name().call()
        print(f"💰 Menggunakan token: {token_name} 🎉")
    except Exception as e:
        print(f"⚠️ Gagal mendapatkan nama token: {str(e)} 😞")
        token_name = "Unknown Token"
    
    # Estimasi waktu total berdasarkan delay
    total_estimated_delay = sum(recipient["delay"] for recipient in recipients[:-1])  # Tidak termasuk delay setelah transaksi terakhir
    print(f"⏰ Estimasi waktu total untuk {len(recipients)} transaksi: {total_estimated_delay:.2f} detik (~{total_estimated_delay / 60:.2f} menit)")
    
    # Catat waktu mulai
    start_time = time.time()
    
    nonce = w3.eth.get_transaction_count(sender_address)
    
    for i, recipient in enumerate(recipients):
        try:
            amount = get_amount()
            
            transaction = token_contract.functions.transfer(
                recipient["address"],
                amount
            ).build_transaction({
                'from': sender_address,
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': w3.to_wei('50', 'gwei'),
                'chainId': 10218  # Chain ID untuk tea-sepolia
            })
            
            signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            token_amount = w3.from_wei(amount, 'ether')
            print(f"🎉 Transfer {token_amount} {token_name} ke {recipient['address']} - Tx Hash: {w3.to_hex(tx_hash)} ✅")
            nonce += 1
            
            if i < len(recipients) - 1:
                delay = recipient["delay"]
                print(f"⏳ Menunggu {delay:.2f} detik sebelum transaksi berikutnya... 😴")
                time.sleep(delay)
            
        except Exception as e:
            print(f"❌ Error saat transfer ke {recipient['address']}: {str(e)} 😞")
    
    # Catat waktu selesai dan hitung durasi
    end_time = time.time()
    total_time = end_time - start_time
    print(f"🏁 Semua transaksi selesai! Waktu total yang dibutuhkan: {total_time:.2f} detik (~{total_time / 60:.2f} menit)")

def main():
    print(">>> send_bulk_token_transfers() 🚀")
    send_bulk_token_transfers()

if __name__ == "__main__":
    main()