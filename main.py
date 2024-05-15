import discord
import requests
import time

TOKEN = 'MTIwMjY5OTg5NjIzNTM2MDM4Ng.G9Au4y.eBbwg3_cAyK-oBEY7zEeWNvZacd_JR5S6_Uh-w'
TARGET_CHANNEL_ID = 1240389965116866694
WEBHOOK_URLS = [
    "https://discord.com/api/webhooks/1240392282574819359/aeJGN0i8QeIh33SElTg3SPfU8kK0nL7hgClLAZUFZWDT066fHTv3Im2PBUZ8Nx5zFMns",
]

client = discord.Client()

def make_request(url, params=None):
    retry_attempts = 50
    for attempt in range(retry_attempts):
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response
        elif response.status_code == 429:
            print("Rate limit exceeded. Waiting for retry...")
            retry_after = int(response.headers.get('Retry-After', '5'))
            time.sleep(retry_after)
        else:
            print(f"Failed to fetch data from {url}. Status code: {response.status_code}")
            return None
    print(f"Reached maximum retry attempts. Unable to fetch data from {url}.")
    return None

def get_asset_thumbnail_url(asset_id):
    url = "https://thumbnails.roblox.com/v1/assets"
    params = {
        "assetIds": asset_id,
        "size": "420x420",
        "format": "Png",
        "isCircular": False
    }
    response = make_request(url, params=params)
    if response:
        try:
            data = response.json()
            if data["data"]:
                return data["data"][0]["imageUrl"]
            else:
                print(f"No data found for asset ID {asset_id} in thumbnail response.")
                return None
        except ValueError:
            print(f"Error decoding JSON for asset ID {asset_id}: {response.text}")
            return None
    return None

def get_asset_name(asset_id):
    url = f"https://economy.roblox.com/v2/assets/{asset_id}/details"
    response = make_request(url)
    if response:
        try:
            data = response.json()
            return data.get("Name", "Unknown Asset")
        except ValueError:
            print(f"Error decoding JSON for asset ID {asset_id}: {response.text}")
            return "Unknown Asset"
    return "Unknown Asset"

def send_thumbnail_to_discord(asset_id, webhook_urls):
    image_url = get_asset_thumbnail_url(asset_id)
    asset_name = get_asset_name(asset_id)
    if image_url:
        embed = {
            "title": "New PS99 Assets!",
            "description": f"Asset Name: {asset_name}",
            "thumbnail": {
                "url": image_url
            }
        }
        for webhook_url in webhook_urls:
            data = {
                "embeds": [embed]
            }
            response = requests.post(webhook_url, json=data)
            if response.status_code == 204:
                print(f"Asset ID {asset_id} sent successfully to webhook.")
            elif response.status_code == 429:
                print(f"Rate limit exceeded while sending thumbnail for asset ID {asset_id} to webhook {webhook_url}. Retrying...")
                retry_after = int(response.headers.get('Retry-After', '5'))
                time.sleep(retry_after)
                send_thumbnail_to_discord(asset_id, [webhook_url])
            else:
                print(f"Failed to send thumbnail for asset ID {asset_id} to webhook {webhook_url}. Status code: {response.status_code}")
                print("Response:", response.text)
    else:
        print(f"Failed to fetch asset image URL for asset ID {asset_id}.")

def extract_asset_id(title):
    # Remove the "Asset Id:" prefix and any surrounding whitespace
    if title.startswith("Asset Id:"):
        return title[len("Asset Id:"):].strip()
    return title.strip()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.channel.id == TARGET_CHANNEL_ID:
        if message.embeds:
            for embed in message.embeds:
                if embed.title:
                    asset_id = extract_asset_id(embed.title)
                    if asset_id:
                        print(f"Extracted Asset ID: {asset_id}")  # Debugging line
                        send_thumbnail_to_discord(asset_id, WEBHOOK_URLS)

client.run(TOKEN)
