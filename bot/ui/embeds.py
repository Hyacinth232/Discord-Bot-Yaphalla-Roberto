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
    main_embed.set_footer(text=footer)
    embeds = [main_embed]
    
    if not files:
        return embeds
        
    for file in files:
        embed = discord.Embed(url="https://www.yaphalla.com", colour=0xa996ff)
        embed.set_image(url="attachment://{}".format(file.filename))
        embeds.append(embed)
            
    return embeds

