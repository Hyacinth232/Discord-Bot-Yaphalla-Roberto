import io

import aiohttp
import discord


def make_embeds(text: str, footer: str, files: list[discord.File] = None, logged_message_links: list[str] = None) -> list[discord.Embed]:
    """Create Discord embeds for submission message."""
    if logged_message_links:
        text += "\n-# Troubleshooting: " + " | ".join([f"[Link {i+1}]({link})" for i, link in enumerate(logged_message_links)])
    
    main_embed = discord.Embed(
        url="https://www.yaphalla.com",
        description=text,
        colour=0xa996ff,
    )
    if files:
        main_embed.set_image(url="attachment://{}".format(files[0].filename))
    
    main_embed.set_footer(text=footer)
    embeds = [main_embed]
    
    if not files or len(files) == 1:
        return embeds
    
    for file in files[1:]:
        embed = discord.Embed(url="https://www.yaphalla.com", colour=0xa996ff)
        embed.set_image(url="attachment://{}".format(file.filename))
        embeds.append(embed)
    return embeds

def get_embed_image_urls(embeds: list[discord.Embed]) -> list[dict[str, str]]:
    """
    Extract image URLs from embeds.
    
    Returns:
        List of dicts with 'url', 'proxy_url', and 'is_formation' keys
    """
    image_urls = []
    for embed in embeds:
        if embed.image and embed.image.url and embed.image.proxy_url:
            is_formation = 'formation_' in embed.image.url
            image_urls.append({
                'url': embed.image.url,  # url for filename
                'proxy_url': embed.image.proxy_url,  # url for downloading
                'is_formation': is_formation
            })
    return image_urls


async def download_embed_images(image_urls: list[dict[str, str]]) -> tuple[list[discord.File], list[discord.File]]:
    """
    Download images from embed URLs and create Discord file objects.
    
    Args:
        image_urls: List of dicts with 'url', 'proxy_url', and 'is_formation' keys
        
    Returns:
        Tuple of (formation_files, non_formation_files)
    """
    formation_files = []
    non_formation_files = []
    
    async with aiohttp.ClientSession() as session:
        for idx, image_info in enumerate(image_urls):
            try:
                async with session.get(image_info['proxy_url']) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                        
                        if image_info['url'].startswith('attachment://'):
                            filename = image_info['url'].replace('attachment://', '')
                        else:
                            filename = image_info['proxy_url'].split('/')[-1].split('?')[0] or f"image_{idx}.png"
                        
                        file = discord.File(io.BytesIO(image_data), filename=filename)
                        
                        if image_info['is_formation']:
                            formation_files.append(file)
                        else:
                            non_formation_files.append(file)
            except Exception as e:
                print(f"Failed to download image from embed: {e}")
    
    return formation_files, non_formation_files
