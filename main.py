import discord
import socket
import socks
import requests
import asyncio

TOKEN = ''  # Replace with your bot token

# Define the proxy list in the format (IP, port, username, password)
proxies = [
    ('49.0.41.6', 14852, 'REXFTP', 'REXFTP86325'),
    ('103.35.109.22', 4040, 'REXFTP', 'REXFTP563258'),  # Wrong password for testing
    ('103.35.109.205', 1088, 'REXFTP', 'REXFTP158635'),
    ('111.221.5.150', 1088, 'REXFTP', ''),  # Empty password
    ('202.4.123.74', 1088, 'REXFTP', 'REXFTP125846'),  # Wrong password for testing
    ('203.83.184.17', 12546, 'REXFTP', 'REXFTP56324')
]

# Track the state of proxies (True for active, False for down, or Authentication Failed)
proxy_status = {proxy: None for proxy in proxies}

# Initialize Discord client
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Function to check if a proxy is active and handle authentication failure
def check_proxy(ip, port, username, password, test_url="http://httpbin.org/ip"):
    try:
        # Set the SOCKS5 proxy with authentication
        socks.set_default_proxy(socks.SOCKS5, ip, port, True, username, password)
        socket.socket = socks.socksocket

        # Test with a reliable URL (httpbin.org is a simple service that returns IP info)
        response = requests.get(test_url, timeout=10)
        
        # Check if the request was successful
        if response.status_code == 200:
            print(f"Proxy {ip}:{port} succeeded: {response.json()}")
            return True  # Proxy is active
        else:
            print(f"Proxy {ip}:{port} returned unexpected status: {response.status_code}")
            return False  # Proxy is inactive (failed to make a successful request)
    
    except socks.ProxyConnectionError:
        print(f"Proxy {ip}:{port} failed to connect.")
        return False  # Proxy is unreachable or refused the connection
    
    except socks.GeneralProxyError as e:
        print(f"Proxy {ip}:{port} general error: {e}")
        if "authentication" in str(e).lower():
            return "authentication_failed"  # Authentication failure
        return False  # Proxy is down for other reasons
    
    except requests.exceptions.ConnectTimeout:
        print(f"Proxy {ip}:{port} timed out while connecting.")
        return False  # Connection timeout
    
    except Exception as e:
        print(f"Proxy {ip}:{port} unexpected error: {e}")
        return False  # General failure

# Function to check all proxies and notify if status changes
async def check_all_proxies():
    global proxy_status

    print("Starting proxy checks...")  # Log to indicate checks have started
    
    for proxy in proxies:
        ip, port, username, password = proxy
        print(f"Checking proxy {ip}:{port}...")  # Debug log for proxy being checked
        status = check_proxy(ip, port, username, password)
        
        # Notify if the status changes
        if proxy_status[proxy] is None or proxy_status[proxy] != status:
            proxy_status[proxy] = status
            
            if status == True:
                await send_notification(f"Proxy {ip}:{port} is now ACTIVE.")
            elif status == "authentication_failed":
                await send_notification(f"Proxy {ip}:{port} AUTHENTICATION FAILED.")
            else:
                await send_notification(f"Proxy {ip}:{port} is DOWN.")
        else:
            print(f"Proxy {ip}:{port} status unchanged.")  # Debug log for unchanged status

# Function to send notifications to the first available channel
async def send_notification(message):
    for guild in client.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(message)
                print(f"Notification sent: {message}")  # Debug log for notification sent
                return  # Exit after sending the message to the first available channel

# Discord bot event when ready
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

    # Send "I am ready for work" to the first available text channel
    await send_notification("I am ready for work")

    # Start the proxy checking loop
    client.loop.create_task(proxy_check_loop())

# Function to check proxies every 30 seconds
async def proxy_check_loop():
    while True:
        await check_all_proxies()  # Run the proxy check
        await asyncio.sleep(30)  # Wait for 30 seconds before checking again

# Run the bot
client.run(TOKEN)
