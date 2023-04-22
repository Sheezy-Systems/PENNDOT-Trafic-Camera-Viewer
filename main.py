import av
import urllib.request
import pygame
import numpy as np
import cv2


def getVideoURL(CAMID):
    print("Fetching video URL for CAMID: " + CAMID + " ...")
    keyURL = "https://www.511pa.com/wowzKey.aspx"
    keyHeaders = {"Referer": "https://www.511pa.com/flowplayeri.aspx?CAMID=" + CAMID}
    keyRequest = urllib.request.Request(keyURL, headers=keyHeaders)
    key = urllib.request.urlopen(keyRequest).read().decode()
    url = "https://pa511wmedia101.ilchost.com/live/" + CAMID + ".stream/playlist.m3u8?wmsAuthSign=" + key

    playlist = None
    try:
        playlist = urllib.request.urlopen(url).read().decode()
    except Exception:
        return -1
    playlist = playlist.replace("RESOLUTION=320x240", "RESOLUTION=640x480")
    video_url = "https://pa511wmedia101.ilchost.com/live/" + CAMID+ ".stream/" + playlist.splitlines()[-1]
    return video_url

def getStream(container): 
    for stream in container.streams:
        if stream.type == 'video':
            video_stream = stream
            break

    if video_stream is None:
        print('No video stream found in the M3U8 file.')
        exit(1)

def changeCamera(increment, changeRegion):
    global CAMID, container
    #grey translucent rectangle over the video
    s = pygame.Surface((640,480))
    s.set_alpha(128)
    s.fill((255,255,255))
    screen.blit(s, (0,0))
    font = pygame.font.Font(None, 36)
    text = font.render("Searching...", 1, (10, 10, 10))
    textpos = text.get_rect(centerx=screen.get_width()/2)
    textpos.top = 480 - 36
    screen.blit(text, textpos)
    pygame.display.flip()
    
    #find next avaliable camera
    parts = CAMID.split("-")
    if changeRegion:
        parts[1] = str(int(parts[1]) + (1 if increment else -1)).zfill(2)
        parts[-1] = '001'
        if not increment:
            increment = True
    else:
        parts[-1] = str(int(parts[-1]) + (1 if increment else -1)).zfill(3) 

    CAMID = "-".join(parts)

    newUrl = getVideoURL(CAMID)
    while newUrl == -1:
        parts[-1] = str(max(int(parts[-1]) + (1 if increment else -1), 0)).zfill(3)
        if int(parts[-1]) == 0 and not increment:
            increment = True
        CAMID = "-".join(parts)
        newUrl = getVideoURL(CAMID)
    container = av.open(newUrl)

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((640, 480))

    CAMID = "CAM-06-027"
    video_url = getVideoURL(CAMID)
    video_stream = None
    container = av.open(video_url)

    video_stream = None
    getStream(container)

    while True:
        camera_changed = False
        for packet in container.demux(video_stream):
            if camera_changed:
                print("Camera changed")
                break

            for frame in packet.decode():
                if frame.format.name in ['yuv420p', 'yuv422p']:
                    # convert to opencv and scale
                    img = frame.to_ndarray(format='bgr24')
                    img = cv2.resize(img, (640, 480), interpolation=cv2.INTER_CUBIC)
                    img = np.rot90(img, k=-3)
                    img = cv2.flip(img, 0)

                    frame = av.VideoFrame.from_ndarray(img, format='bgr24')
                    img = pygame.surfarray.make_surface(frame.to_rgb().to_ndarray())
                    screen.blit(img, (0, 0))
                    pygame.display.flip()

                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_UP:
                                changeCamera(True, False)
                                camera_changed = True
                                break
                            elif event.key == pygame.K_LEFT:
                                changeCamera(False, False)
                                camera_changed = True
                                break
                            elif event.key == pygame.K_DOWN:
                                changeCamera(False, True)
                                camera_changed = True
                                break
                            elif event.key == pygame.K_RIGHT:
                                changeCamera(True, True)
                                camera_changed = True
                                break
                        if event.type == pygame.QUIT:
                            container.close() 
                            pygame.quit()
                            exit(0)

                    pygame.time.delay(66)

        if not camera_changed:
            video_url = getVideoURL(CAMID)
            try:
                container.close()
            except Exception:
                print("Error closing container")
                print(Exception)
                pass
            container = av.open(video_url)
            video_stream = container.streams.video[0]
            print("Done")