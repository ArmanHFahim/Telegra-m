import os
from dotenv import load_dotenv
load_dotenv()

import os
from dotenv import load_dotenv
load_dotenv()

import os
import asyncio
import pandas as pd
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from telethon import TelegramClient, errors
from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.tl.types import InputPhoneContact

# ────────────────────────────────────────────────
#                     CONFIG
# ────────────────────────────────────────────────

API_ID = int(os.getenv("API_ID", 37597265))int(os.getenv("API_ID", 37597265))
API_HASH = os.getenv("API_HASH", "650a8b45cb705150a2d3bb7f6cd41bee")
SESSION_NAME = "checker_session_v4"

INPUT_EXCEL     = Path("bd_numbers_state.xlsx")              # your source file
OUTPUT_EXCEL    = Path("ai_numbers_telegram_checked.xlsx")   # final YES results
CHECKPOINT_CSV  = Path("checkpoint_progress.csv")            # resume point + log

BATCH_SIZE      = 18           # 15–25 usually safest in 2025
SLEEP_BASE      = 5           # seconds between batches
SLEEP_JITTER    = 12          # random ± this value
MAX_RETRIES     = 2

# ────────────────────────────────────────────────
#                     LOGGING
# ────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  | %(levelname)-7s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("telegram_checker.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────
#              CHECKPOINT & STATE
# ────────────────────────────────────────────────

def load_checkpoint() -> tuple[set[str], int]:
    """ Returns: already_checked_phones set, last_successful_index """
    if not CHECKPOINT_CSV.is_file():
        return set(), 0

    try:
        df = pd.read_csv(CHECKPOINT_CSV, dtype=str)
        checked = set(df['phone'].dropna())
        last_idx = int(df['batch_end_index'].max()) if 'batch_end_index' in df.columns else 0
        return checked, last_idx + 1
    except Exception as e:
        logger.error(f"Cannot read checkpoint → starting from beginning  ({e})")
        return set(), 0


def append_to_checkpoint(phones_checked: List[Dict], batch_end_index: int):
    if not phones_checked:
        return

    df_new = pd.DataFrame(phones_checked)
    df_new['batch_end_index'] = batch_end_index
    df_new['checked_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if CHECKPOINT_CSV.is_file():
        df_old = pd.read_csv(CHECKPOINT_CSV, dtype=str)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_csv(CHECKPOINT_CSV, index=False, encoding='utf-8')


def append_yes_to_output(new_yes: List[Dict]):
    if not new_yes:
        return

    df_new = pd.DataFrame(new_yes)

    if OUTPUT_EXCEL.is_file():
        try:
            df_old = pd.read_excel(OUTPUT_EXCEL)
            df = pd.concat([df_old, df_new], ignore_index=True)
            df = df.drop_duplicates(subset=['phone'], keep='last')
        except Exception:
            df = df_new
    else:
        df = df_new

    df.to_excel(OUTPUT_EXCEL, index=False, engine='openpyxl')
    logger.info(f"Appended {len(df_new)} new YES → total in output: {len(df)}")


# ────────────────────────────────────────────────
#              PHONE NORMALIZATION
# ────────────────────────────────────────────────

def normalize_phone(raw: str) -> Optional[str]:
    n = str(raw).strip().replace(" ", "").replace("-", "").replace("+", "")
    if not n.isdigit():
        return None
    if len(n) < 10:
        return None
    if n.startswith("880"):
        return n
    if n.startswith("0"):
        return "880" + n[1:]
    if len(n) == 10:
        return "880" + n
    return None


# ────────────────────────────────────────────────
#              BATCH CHECK
# ────────────────────────────────────────────────

async def check_one_batch(
    client: TelegramClient,
    phones: List[str],
    start_global_index: int
) -> tuple[List[Dict], List[Dict]]:

    results_yes   = []
    results_check = []   # for checkpoint

    if not phones:
        return [], []

    contacts = [
        InputPhoneContact(
            client_id = start_global_index + i,
            phone     = f"+{phone}",
            first_name= "Chk",
            last_name = f"{start_global_index + i}"
        )
        for i, phone in enumerate(phones)
    ]

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = await client(ImportContactsRequest(contacts))

            found = {u.phone.lstrip("+"): u for u in result.users if u.phone}

            for phone in phones:
                user = found.get(phone)
                record = {
                    "phone": phone,
                    "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "batch_index": start_global_index,
                }

                if user:
                    record.update({
                        "first_name":   user.first_name or "",
                        "last_name":    user.last_name or "",
                        "username":     user.username or "",
                        "telegram_id":  user.id,
                        "status":       "YES"
                    })
                    results_yes.append(record)
                    logger.info(f"YES → {phone}  @{user.username or 'no-username'}")
                else:
                    record["status"] = "NO"
                    logger.info(f"NO  → {phone}")

                results_check.append(record)

            # Cleanup (critical!)
            if result.users:
                try:
                    await client(DeleteContactsRequest([u.id for u in result.users]))
                except Exception as e:
                    logger.warning(f"Delete failed: {e}")

            return results_yes, results_check

        except errors.FloodWaitError as e:
            wait = e.seconds + 15
            logger.warning(f"FloodWait {e.seconds}s → sleeping {wait}s (attempt {attempt})")
            await asyncio.sleep(wait)

        except Exception as e:
            logger.error(f"Batch error (attempt {attempt}): {type(e).__name__} → {e}")
            if attempt == MAX_RETRIES:
                return [], []
            await asyncio.sleep(30 * attempt)

    return [], []


# ────────────────────────────────────────────────
#                     MAIN
# ────────────────────────────────────────────────

async def main():
    if not INPUT_EXCEL.is_file():
        logger.error(f"Input file not found: {INPUT_EXCEL}")
        return

    logger.info("Reading input Excel ...")
    df_input = pd.read_excel(INPUT_EXCEL)

    if "phone" not in df_input.columns:
        logger.error("Excel must have 'phone' column")
        return

    # Normalize phones
    phones_all = []
    for raw in df_input["phone"].dropna():
        clean = normalize_phone(raw)
        if clean:
            phones_all.append(clean)

    phones_all = list(dict.fromkeys(phones_all))  # remove duplicates
    logger.info(f"Loaded & normalized {len(phones_all)} unique phones")

    # ── Resume logic ───────────────────────────────────────
    already_checked, start_from = load_checkpoint()
    logger.info(f"Resuming from index {start_from}  (already checked: {len(already_checked)})")

    phones_to_check = [
        p for p in phones_all[start_from:]
        if p not in already_checked
    ]

    if not phones_to_check:
        logger.info("No new numbers to check. Done.")
        return

    logger.info(f"Numbers left to check: {len(phones_to_check)}")

    # ── Telegram client ────────────────────────────────────
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    try:
        await client.start()
        if not await client.is_user_authorized():
            logger.error("Session not authorized → run manually first to login")
            return

        total_checked_this_run = 0
        total_yes_this_run = 0

        for i in range(0, len(phones_to_check), BATCH_SIZE):
            batch = phones_to_check[i : i + BATCH_SIZE]
            global_start_idx = start_from + i

            batch_no = (i // BATCH_SIZE) + 1
            total_batches = (len(phones_to_check) + BATCH_SIZE - 1) // BATCH_SIZE

            logger.info(f"Batch {batch_no}/{total_batches}  |  {len(batch)} numbers  |  global idx {global_start_idx}")

            yes_in_batch, checked_in_batch = await check_one_batch(client, batch, global_start_idx)

            # Save progress immediately
            append_to_checkpoint(checked_in_batch, global_start_idx + len(batch) - 1)
            append_yes_to_output(yes_in_batch)

            total_checked_this_run += len(checked_in_batch)
            total_yes_this_run += len(yes_in_batch)

            # Sleep
            sleep_time = max(10, SLEEP_BASE + (-SLEEP_JITTER + (hash(str(i)) % (2*SLEEP_JITTER))))
            if i + BATCH_SIZE < len(phones_to_check):
                logger.info(f"Waiting {sleep_time:.0f} seconds...")
                await asyncio.sleep(sleep_time)

        logger.info("───────────────────────────────────────────────")
        logger.info(f"Finished this run.")
        logger.info(f"Processed this session : {total_checked_this_run:,} numbers")
        logger.info(f"Found YES this session : {total_yes_this_run:,}")
        logger.info(f"Output file            : {OUTPUT_EXCEL}")

    except KeyboardInterrupt:
        logger.warning("Stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Critical error: {type(e).__name__} → {e}", exc_info=True)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())