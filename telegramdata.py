import asyncio
import os
import pandas as pd
from telethon import TelegramClient
from telethon.errors import ChatAdminRequiredError, ChannelPrivateError

# ─── CONFIG ─────────────────────────
api_id = 37597265
api_hash = "650a8b45cb705150a2d3bb7f6cd41bee"
session = "all_groups"
OUTPUT = "phones_only.csv"

# ─── MAIN ───────────────────────────
async def main():
    client = TelegramClient(session, api_id, api_hash)
    await client.start()
    
    all_phones = []
    dialogs = await client.get_dialogs()
    print(f"📦 Total dialogs: {len(dialogs)}")
    
    for dialog in dialogs:
        entity = dialog.entity
        name = dialog.name or f"ID_{entity.id}"
        
        if not (dialog.is_group or dialog.is_channel):
            continue
        
        print(f"🔍 Checking: {name}")
        
        try:
            async for user in client.iter_participants(entity, limit=None, aggressive=True):
                if user.phone:  # Only keep if phone exists (very rare!)
                    record = {
                        "group_name": name,
                        "group_id": entity.id,
                        "user_id": user.id,
                        "username": user.username or "",
                        "first_name": user.first_name or "",
                        "phone": user.phone,
                    }
                    all_phones.append(record)
                    print(f"   Found phone: {user.phone} ({user.username or user.id})")
        
        except ChatAdminRequiredError:
            print(f"⛔ Admin required: {name}")
        except ChannelPrivateError:
            print(f"⛔ Private/not joined: {name}")
        except Exception as e:
            print(f"⛔ Error in {name}: {e}")
    
    await client.disconnect()
    
    if all_phones:
        df = pd.DataFrame(all_phones)
        df.drop_duplicates(subset="phone", inplace=True)
        df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"\n✅ Saved {len(df)} phones with data → {OUTPUT}")
    else:
        print("\n⚠️ No phone numbers found at all (most users hide them)")

asyncio.run(main())