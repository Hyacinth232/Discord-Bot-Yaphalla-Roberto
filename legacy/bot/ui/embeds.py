import io

import aiohttp
import discord


def _is_video_file(filename: str) -> bool:
    """Check if a file is a video based on its extension."""
    video_extensions = {'.mp4', '.webm', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.m4v'}
    if not filename:
        return False
    return any(filename.lower().endswith(ext) for ext in video_extensions)

def make_embeds(text: str, footer: str, files: list[discord.File] = None, logged_message_links: list[str] = None) -> list[discord.Embed]:
    """
    Create Discord embeds for submission message.
    Only images are embedded; videos will be attached separately.
    
    Args:
        text: Embed description text
        footer: Footer text
        files: List of files (images will be embedded, videos will be attached separately)
        logged_message_links: Optional list of troubleshooting links
        
    Returns:
        List of embeds with images embedded (videos are not embedded)
    """
    if logged_message_links:
        text += "\n-# Troubleshooting: " + " | ".join([f"[Link {i+1}]({link})" for i, link in enumerate(logged_message_links)])
    
    # Separate images from videos
    image_files = []
    
    if files:
        for file in files:
            # Only embed non-video files (images)
            if not _is_video_file(file.filename):
                image_files.append(file)
    
    main_embed = discord.Embed(
        url="https://www.yaphalla.com",
        description=text,
        colour=0xa996ff,
    )
    
    # Only embed the first image if available
    if image_files:
        main_embed.set_image(url="attachment://{}".format(image_files[0].filename))
    
    main_embed.set_footer(text=footer)
    embeds = [main_embed]
    
    # Add additional images as separate embeds
    if len(image_files) > 1:
        for file in image_files[1:]:
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
