"""
Reddit video downloader
"""

from rich.prompt import Prompt
from rich.console import Console
from rich.text import Text
import requests, time, os
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
import json

console=Console()
s=requests.Session()

def download_page(link, filename, status) -> requests.Response:
    """Makes requests and dowloads webpage"""
    rp=s.get(link, headers={"User-Agent":"Mozilla/5.0"})
    try:
        with open(filename,"wb") as f: f.write(rp.content)
    except PermissionError as e:
        console.log(Text("Permission error, try to run the script from shell or with root user permission", style="red"))
        status.update("[red]Download stopped, close the program")
        status.stop()
        input()
        exit()
    return rp

def find_content_id(page) -> str:
    """Searches for video id in the given webpage"""
    data = page.text[page.text.find("<shreddit-screenview-data")+len("<shreddit-screenview-data"):]
    data = data[data.find("data=\"")+6:]
    data = data[:data.find(">")-1]
    data=data.replace("&quot;","\"").replace("\n","").replace(" ","")
    data=data[:-1]
    page_url=json.loads(data)['post']['url']
    content_id=page_url.split("/")[-1]
    console.log("ID: ", content_id)
    return content_id

def donwload_video_and_audio(content_id) -> None:
    """Downloads the largest video size and audio"""

    size_list=[720, 480, 360, 240]
    for size in size_list:
        video_link="https://v.redd.it/"+content_id+f"/DASH_{size}.mp4"
        rv=s.get(video_link, headers={"User-Agent":"Mozilla/5.0"})
        if rv.status_code!=403: break
        
    console.log(f"Downloading video content ( {video_link} ).")
    with open("video.mp4","wb") as f:
        f.write(rv.content)
    
    audio_link="https://v.redd.it/"+content_id+"/DASH_audio.mp4"
    console.log(f"Downloading audio content ( {audio_link} ).")
    ra=s.get(audio_link, headers={"User-Agent":"Mozilla/5.0"})
    with open("audio.mp4","wb") as f:
        f.write(ra.content)

def build_video(content_id) -> str:
    """Inserts audio into the video"""
    video_clip = VideoFileClip('video.mp4')
    audio_clip = AudioFileClip('audio.mp4')
    video_clip.audio = audio_clip
    file_name=content_id+".mp4"
    video_clip.write_videofile(file_name, logger=None, verbose=False)
    return file_name

def clean_cache() -> None:
    """Removes temporary files"""
    os.remove("reddit.html")
    os.remove("video.mp4")
    os.remove("audio.mp4")

def get_scrape_download(link) -> None:
    """"Logs progress, scrapes and downloads content"""
    with console.status("[bold green]Donwloading video...", spinner="line") as status:

        console.log("Link looks good, donwloading page.")
        page=download_page(link, "reddit.html", status)

        console.log("Scraping content.")
        content_id=find_content_id(page)

        donwload_video_and_audio(content_id)

        console.log("Download completed.")
        status.update("[bold green]Composing final file...")

        console.log("Inserting audio into the video.")
        file_name=build_video(content_id)
    
    clean_cache()
    console.log("[bold][magenta]Done, file available at "+str(os.getcwd())+"\\"+file_name)

def ask_link():
    link = Prompt.ask("Enter link")
    if "https://www.reddit.com/r/" in link and "comments" in link:
        get_scrape_download(link)
    else:
        console.log(Text("This is not a reddit video link.", style="red"))
        ask_link()

ask_link()