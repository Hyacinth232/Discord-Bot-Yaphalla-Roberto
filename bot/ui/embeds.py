import discord

EMBED_URL = "https://www.yaphalla.com"
EMBED_COLOUR = 0xA996FF
VIDEO_EXTENSIONS = (".mp4", ".webm", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".m4v")


def _is_video_file(filename: str) -> bool:
    """Check if a file is a video based on its extension."""
    return bool(filename) and filename.lower().endswith(VIDEO_EXTENSIONS)


def make_embeds(text: str, footer: str, files: list[discord.File] | None = None) -> list[discord.Embed]:
    """
    Create Discord embeds for submission message.
    Only images are embedded; videos will be attached separately.

    Args:
        text: Embed description text
        footer: Footer text
        files: List of files (images will be embedded, videos will be attached separately)

    Returns:
        List of embeds, the first holding the text and each holding one image
    """
    image_files = [file for file in files or [] if not _is_video_file(file.filename)]

    main_embed = discord.Embed(url=EMBED_URL, description=text, colour=EMBED_COLOUR)
    main_embed.set_footer(text=footer)
    if image_files:
        main_embed.set_image(url=f"attachment://{image_files[0].filename}")
    embeds = [main_embed]

    # Embeds sharing a URL are shown by Discord as one gallery
    for file in image_files[1:]:
        embed = discord.Embed(url=EMBED_URL, colour=EMBED_COLOUR)
        embed.set_image(url=f"attachment://{file.filename}")
        embeds.append(embed)

    return embeds
