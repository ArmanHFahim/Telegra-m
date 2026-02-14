# multipule_acc.py
# Updated: detailed logging for every step + batch summaries

import os
import asyncio
import pandas as pd
import logging
import random
import multiprocessing as mp
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from telethon import TelegramClient, errors
from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.tl.types import InputPhoneContact

# ────────────────────────────────────────────────
#                     CONFIG
# ────────────────────────────────────────────────
INPUT_EXCEL    = Path("bd_numbers_state.xlsx")
OUTPUT_BASE    = Path("checked_results")
OUTPUT_BASE.mkdir(exist_ok=True)

BATCH_SIZE     = 20             # fixed to 20 as requested
SLEEP_BASE     = 8
SLEEP_JITTER   = 12
MAX_RETRIES    = 2

# ────────────────────────────────────────────────
#               YOUR ACCOUNTS (all 10)
# ────────────────────────────────────────────────
ACCOUNTS = [
    {"id": 1,  "api_id": 37597265, "api_hash": "650a8b45cb705150a2d3bb7f6cd41bee", "session": "checker_01"},
    {"id": 2,  "api_id": 37597265, "api_hash": "650a8b45cb705150a2d3bb7f6cd41bee", "session": "checker_02"},
    {"id": 3,  "api_id": 37597265, "api_hash": "650a8b45cb705150a2d3bb7f6cd41bee", "session": "checker_03"},
    {"id": 4,  "api_id": 37597265, "api_hash": "650a8b45cb705150a2d3bb7f6cd41bee", "session": "checker_04"},
    {"id": 5,  "api_id": 37597265, "api_hash": "650a8b45cb705150a2d3bb7f6cd41bee", "session": "checker_05"},
    {"id": 6,  "api_id": 37597265, "api_hash": "650a8b45cb705150a2d3bb7f6cd41bee", "session": "checker_06"},
    {"id": 7,  "api_id": 37597265, "api_hash": "650a8b45cb705150a2d3bb7f6cd41bee", "session": "checker_07"},
    {"id": 8,  "api_id": 37597265, "api_hash": "650a8b45cb705150a2d3bb7f6cd41bee", "session": "checker_08"},
    {"id": 9,  "api_id": 37597265, "api_hash": "650a8b45cb705150a2d3bb7f6cd41bee", "session": "checker_09"},
    {"id": 10, "api_id": 37597265, "api_hash": "650a8b45cb705150a2d3bb7f6cd41bee", "session": "checker_10"},
]

# ────────────────────────────────────────────────
def normalize_phone(raw: any) -> Optional[str]:
    if pd.isna(raw) or raw is None:
        return None
    if isinstance(raw, float) and raw.is_integer():
        digits = str(int(raw))
    else:
        digits = str(raw).strip()
    digits = ''.join(c for c in digits if c.isdigit())
    if not digits or len(digits) < 10:
        return None
    if digits.startswith('880') and len(digits) == 13:
        return digits
    if digits.startswith('880') and len(digits) == 14 and digits.endswith('0'):
        return digits[:-1]
    if digits.startswith('88') and len(digits) == 12:
        return '880' + digits[2:]
    if digits.startswith('0') and len(digits) == 11:
        return '880' + digits[1:]
    if len(digits) == 10:
        return '880' + digits
    if len(digits) == 11 and digits[0] in '13456789':
        return '880' + digits
    return None


def get_logger(account_id: int):
    logger = logging.getLogger(f"acc_{account_id}")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-6s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh = logging.FileHandler(f"telegram_checker_acc{account_id}.log", encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    return logger


def worker(account: dict, phone_list: List[str], worker_index: int):
    acc_id = account["id"]
    session_name = account["session"]
    api_id = account["api_id"]
    api_hash = account["api_hash"]

    logger = get_logger(acc_id)
    logger.info(f"Worker {worker_index} (ACC {acc_id}) STARTED | Total numbers assigned: {len(phone_list):,}")

    checkpoint_file = Path(f"checkpoint_acc{acc_id}.csv")
    temp_output = OUTPUT_BASE / f"yes_acc{acc_id}.xlsx"

    already_checked = set()
    start_from = 0

    if checkpoint_file.is_file():
        try:
            df = pd.read_csv(checkpoint_file, dtype=str)
            already_checked = set(df['phone'].dropna())
            if 'batch_end_local_idx' in df.columns:
                start_from = int(df['batch_end_local_idx'].max()) + 1
            logger.info(f"Resume loaded | Already checked: {len(already_checked):,} | Starting from index {start_from}")
        except Exception as e:
            logger.error(f"Checkpoint load failed: {e}")

    phones_to_check = [p for p in phone_list[start_from:] if p not in already_checked]
    total_to_check = len(phones_to_check)

    if total_to_check == 0:
        logger.info("No new numbers to check → worker finished early")
        return

    logger.info(f"Numbers to process this run: {total_to_check:,} | Batches expected: {(total_to_check + BATCH_SIZE - 1) // BATCH_SIZE}")

    client = TelegramClient(session_name, api_id, api_hash)

    async def run_check():
        try:
            await client.connect()
            if not await client.is_user_authorized():
                logger.error("Session is NOT authorized! Please run client.start() manually for this session first.")
                return

            logger.info("Telegram session connected and authorized successfully")

            total_yes_this_run = 0
            batch_count = 0

            for i in range(0, total_to_check, BATCH_SIZE):
                batch_idx = batch_count + 1
                batch = phones_to_check[i : i + BATCH_SIZE]
                offset = start_from + i

                logger.info(f"Batch {batch_idx} started | Sending {len(batch)} numbers")

                contacts = [
                    InputPhoneContact(
                        client_id = offset + j,
                        phone     = f"+{phone}",
                        first_name= "Chk",
                        last_name = str(offset + j)
                    )
                    for j, phone in enumerate(batch)
                ]

                success = False
                for attempt in range(1, MAX_RETRIES + 1):
                    try:
                        result = await client(ImportContactsRequest(contacts))
                        found = {u.phone.lstrip("+"): u for u in result.users if u.phone}

                        checked_records = []
                        yes_records = []
                        batch_yes = 0

                        for phone in batch:
                            user = found.get(phone)
                            record = {
                                "phone": phone,
                                "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "worker": acc_id,
                            }
                            if user:
                                record.update({
                                    "first_name": user.first_name or "",
                                    "last_name": user.last_name or "",
                                    "username": user.username or "",
                                    "telegram_id": user.id,
                                    "status": "YES"
                                })
                                yes_records.append(record)
                                batch_yes += 1
                                total_yes_this_run += 1
                                logger.info(f"YES → +{phone}  @{user.username or 'no-username'}")
                            else:
                                record["status"] = "NO"
                                # logger.debug(f"NO → +{phone}")

                            checked_records.append(record)

                        logger.info(f"Batch {batch_idx} finished | Found {batch_yes} YES in this batch")

                        # Cleanup contacts
                        if result.users:
                            try:
                                await client(DeleteContactsRequest([u.id for u in result.users]))
                                logger.debug("Contacts cleaned up successfully")
                            except Exception as cleanup_e:
                                logger.warning(f"Cleanup failed: {cleanup_e}")

                        # Save checkpoint
                        if checked_records:
                            df_new = pd.DataFrame(checked_records)
                            df_new['batch_end_local_idx'] = offset + len(batch) - 1

                            if checkpoint_file.is_file():
                                df_old = pd.read_csv(checkpoint_file, dtype=str)
                                df = pd.concat([df_old, df_new], ignore_index=True)
                            else:
                                df = df_new
                            df.to_csv(checkpoint_file, index=False, encoding='utf-8')
                            logger.debug("Checkpoint saved")

                        # Save YES results
                        if yes_records:
                            df_yes = pd.DataFrame(yes_records)
                            if temp_output.is_file():
                                try:
                                    df_old = pd.read_excel(temp_output)
                                    df_final = pd.concat([df_old, df_yes]).drop_duplicates(subset=['phone'], keep='last')
                                except:
                                    df_final = df_yes
                            else:
                                df_final = df_yes
                            df_final.to_excel(temp_output, index=False, engine='openpyxl')
                            logger.debug(f"Saved {len(yes_records)} new YES results")

                        success = True

                        # Sleep only if more batches remain
                        if i + BATCH_SIZE < total_to_check:
                            sleep_sec = max(10, SLEEP_BASE + random.uniform(-SLEEP_JITTER, SLEEP_JITTER))
                            logger.info(f"Waiting {sleep_sec:.1f}s before next batch...")
                            await asyncio.sleep(sleep_sec)

                        break

                    except errors.FloodWaitError as e:
                        wait = e.seconds + random.randint(30, 90)
                        logger.warning(f"FLOOD WAIT {e.seconds}s → sleeping {wait}s (attempt {attempt}/{MAX_RETRIES})")
                        await asyncio.sleep(wait)
                    except Exception as e:
                        logger.error(f"Batch {batch_idx} error (attempt {attempt}): {type(e).__name__} → {e}")
                        if attempt == MAX_RETRIES:
                            logger.warning(f"Batch {batch_idx} skipped after max retries")
                            break
                        await asyncio.sleep(40 * attempt)

                batch_count += 1

            logger.info(f"Worker {worker_index} (ACC {acc_id}) COMPLETED")
            logger.info(f"Total YES found this run: {total_yes_this_run:,} / {total_to_check:,} checked")

        except Exception as e:
            logger.error(f"Critical worker error: {type(e).__name__} → {e}", exc_info=True)
        finally:
            if await client.is_connected():
                await client.disconnect()
                logger.info("Telegram client disconnected")

    asyncio.run(run_check())


# ────────────────────────────────────────────────
def main():
    print("\n" + "═"*80)
    print("   TELEGRAM BULK CHECKER  —  Batch size = 20  —  Detailed logging enabled")
    print("═"*80 + "\n")

    if not INPUT_EXCEL.is_file():
        print(f"ERROR → Input file not found: {INPUT_EXCEL.absolute()}")
        return

    print(f"Reading input file: {INPUT_EXCEL.absolute()}")
    try:
        df = pd.read_excel(INPUT_EXCEL)
    except Exception as e:
        print(f"Cannot read Excel file: {e}")
        return

    print(f"Rows: {len(df):,} | Columns: {list(df.columns)}")

    if "phone" not in df.columns:
        print('ERROR: Column "phone" not found')
        return

    all_phones = [normalize_phone(x) for x in df["phone"] if normalize_phone(x) is not None]
    all_phones = list(dict.fromkeys(all_phones))
    print(f"\nTotal unique valid phones after normalization: {len(all_phones):,}")

    if len(all_phones) == 0:
        print("\n!!! NO VALID PHONE NUMBERS FOUND !!!")
        return

    n_workers = len(ACCOUNTS)
    if n_workers == 0:
        print("ERROR: No accounts defined in ACCOUNTS list")
        return

    chunk_size = max(1, (len(all_phones) + n_workers - 1) // n_workers)
    chunks = [all_phones[i:i + chunk_size] for i in range(0, len(all_phones), chunk_size)]

    print(f"\nLaunching {n_workers} parallel workers (~{chunk_size:,} numbers each)")
    print(f"Each worker will process in batches of {BATCH_SIZE} numbers\n")

    processes = []
    for idx, (acc, chunk) in enumerate(zip(ACCOUNTS, chunks), 1):
        if not chunk:
            print(f"Worker {idx} → no numbers assigned (skipping)")
            continue
        print(f"Starting Worker {idx} (ACC {acc['id']}) with {len(chunk):,} numbers")
        p = mp.Process(target=worker, args=(acc, chunk, idx))
        processes.append(p)
        p.start()

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\nInterrupted by user → terminating all workers...")
        for p in processes:
            p.terminate()

    print("\n" + "═"*80)
    print("All workers finished.")
    print(f"Check results in folder: {OUTPUT_BASE}")
    print("Each account's YES results saved in yes_accX.xlsx")
    print("═"*80 + "\n")


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()