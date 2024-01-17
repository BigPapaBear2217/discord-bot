import discord
from discord.ext import commands
import requests
import json
import os
import asyncio
from io import BytesIO
from PIL import Image, ImageOps
import time

TOKEN = ('')
API_KEY = ('')

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)


async def get_generated_images(api_url, payload):
    # Send the API request and get the response data
    response = requests.post(api_url, json=payload)
    response_data = response.json()

    # Check if the API returned any images
    image_urls = response_data.get("output")
    if not image_urls:
        return None

    loop = asyncio.get_running_loop()
    # Download the images and store them in a list
    tasks = []
    for image_url in image_urls:
        task = loop.run_in_executor(None, requests.get, image_url)
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    images = []
    for result in results:
        image_data = result.content
        image = Image.open(BytesIO(image_data))
        images.append(image)

    return images


import random

def create_image_grid(images, prefix="image", IMAGE_WIDTH=500, IMAGE_HEIGHT=500, border_width=10, border_color=(255, 0, 0)):
    num_images = len(images)
    num_rows = num_images // 2 + num_images % 2
    num_cols = 2 if num_images == 1 else 2

    grid_width = IMAGE_WIDTH * num_cols
    grid_height = IMAGE_HEIGHT * num_rows
    grid_image = Image.new(mode="RGB", size=(grid_width, grid_height), color="white")

    for i, image in enumerate(images):
        row = i // num_cols
        col = i % num_cols
        x = col * IMAGE_WIDTH
        y = row * IMAGE_HEIGHT
        grid_image.paste(image, (x, y))

        # Save the image to a file with a random delay and unique name
        filename = f"{prefix}_{i}_{int(time.time())}.png"
        delay = random.uniform(0.5, 2.0)
        time.sleep(delay)
        with open(filename, "wb") as f:
            image.save(f)

    # Add a red border to the grid
    grid_image = ImageOps.expand(grid_image, border=border_width, fill=border_color)

    # Save the final grid image to a file with a unique name
    filename = f"{prefix}_grid_{int(time.time())}.png"
    with open(filename, "wb") as f:
        grid_image.save(f)

    return grid_image

@bot.event
async def on_ready():
    print("Bot is ready.")


@bot.command(name='mid')
async def mid(ctx, *, prompt: str):
    
    url = "https://stablediffusionapi.com/api/v3/text2img"
    payload = {
        "key": API_KEY,
        "model_id": "midjourney",
        "prompt": prompt,
        "negative_prompt": "painting, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, deformed, ugly, blurry, bad anatomy, bad proportions, extra limbs, cloned face, skinny, glitchy, double torso, extra arms, extra hands, mangled fingers, missing lips, ugly face, distorted face, extra legs, anime ",
        "width": "512",
        "height": "512",
        "samples": "4",
        "num_inference_steps": "30",
        "safety_checker": "no",
        "enhance_prompt": "yes",
        "seed": None,
        "guidance_scale": 7.5,
        "webhook": None,
        "track_id": None
    }

    images = await get_generated_images(url, payload)
    if not images:
        await ctx.send("No images found.")
        return

    prefix = f"mid_{int(time.time())}"
    grid_image = create_image_grid(images, prefix=prefix)
    if not grid_image:
        await ctx.send("Error creating image grid.")
        return

    with BytesIO() as image_binary:
        grid_image.save(image_binary, "PNG")
        image_binary.seek(0)
        await ctx.send(file=discord.File(fp=image_binary, filename=f"{prefix}_grid.png"))
        await ctx.message.add_reaction("🔄")



@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user or reaction.emoji != "🔄":
        return

    message = reaction.message
    if not message.content.startswith('/mid'):
        return

    prompt = message.content.split("/mid", 1)[1].strip()

    # Add the code to generate a new image grid based on the prompt and send it to the channel
    # You can reuse the code you've written earlier for this purpose
    print(f"Received prompt: {prompt}")
    
    url = "https://stablediffusionapi.com/api/v3/text2img"
    payload = {
        "key": API_KEY,
        "model_id": "midjourney",
        "prompt": prompt,
        "negative_prompt": "painting, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, deformed, ugly, blurry, bad anatomy, bad proportions, extra limbs, cloned face, skinny, glitchy, double torso, extra arms, extra hands, mangled fingers, missing lips, ugly face, distorted face, extra legs, anime",
        "width": "520",
        "height": "520",
        "samples": "4",
        "num_inference_steps": "30",
        "safety_checker": "no",
        "enhance_prompt": "yes",
        "seed": None,
        "guidance_scale": 7.5,
        "webhook": None,
        "track_id": None
    }

    images = await get_generated_images(url, payload)
    if not images:
        await message.channel.send("No images found.")
        return

    grid_image = create_image_grid(images)
    if not grid_image:
        await message.channel.send("Error creating image grid.")
        return

    with BytesIO() as image_binary:
        grid_image.save(image_binary, "PNG")
        image_binary.seek(0)
        await message.channel.send(file=discord.File(fp=image_binary, filename="grid_image.png"))
        await reaction.remove(user)


bot.run(TOKEN)
